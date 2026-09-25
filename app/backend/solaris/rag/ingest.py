"""Ingesta del corpus documental en `rag.*` (M2-T3, F01).

Uso (desde app/backend):
    uv run python -m solaris.rag.ingest [DOCS] [--docs DOCS] [--dry-run] [--no-prune]

  * Allowlist (PAT-004): solo las rutas de `DOCS/manifest.json` (solaris.rag.manifest). Avisa de
    ficheros del manifest que no existen y de ficheros en disco fuera del manifest (se ignoran).
  * ACL heredada: re-sincroniza `rag.folder_acl` desde acl.json y cada documento, chunk y fila AMFE
    lleva el `folder` de su entrada del manifest. La visibilidad la decide SQL (PAT-005).
  * Chunking estructural con locator (solaris.rag.parsers) y filas AMFE (solaris.rag.fmea).
  * Embeddings locales de 1024 dims (solaris.rag.embed); no pasan por OpenRouter.
  * Idempotente: mismo (doc_id, versión, sha256) → no se toca; versión o contenido distintos →
    se reemplaza el documento entero (chunks y filas AMFE en cascada) en una transacción.
    Documentos en BD que ya no están en el manifest → se borran (salvo `--no-prune`).
  * Audit: un evento `ingest` por documento con SOLO metadatos (sin contenido), vía
    `solaris.audit.record_safe` (política AUDIT_REQUIRED).
"""

import argparse
import hashlib
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import psycopg
from psycopg.types.json import Jsonb

from solaris.audit import Actor, record_safe
from solaris.rag.acl import DEFAULT_ACL_FILE, load_folder_acl, sync_folder_acl
from solaris.rag.embed import embed, to_pgvector
from solaris.rag.fmea import FmeaRow, extract_fmea
from solaris.rag.locator import loc_label as _loc_label
from solaris.rag.manifest import DEFAULT_DOCS_DIR, DocEntry, load_manifest
from solaris.rag.parsers import Chunk, Parsed, parse
from solaris.settings import Settings, get_settings

INGEST_ACTOR = Actor("svc.ingest", "system")
FMEA_DOC_TYPES = frozenset({"amfe", "fmea"})


@dataclass
class DocResult:
    doc_id: str
    version: str
    folder: str
    action: str  # inserted | replaced | unchanged | moved | pruned | error | dry-run
    chunks: int = 0
    fmea_rows: int = 0
    ocr_pages: list[int] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass
class IngestReport:
    results: list[DocResult] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    rejected: list[str] = field(default_factory=list)
    acl_rows: int = 0
    seconds: float = 0.0

    def count(self, attr: str) -> int:
        return sum(getattr(r, attr) for r in self.results if r.action != "pruned")

    @property
    def errors(self) -> list[DocResult]:
        return [r for r in self.results if r.action == "error"]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def embedding_input(entry: DocEntry, chunk: Chunk) -> str:
    """Texto que se embebe: título + locator + contenido (el contenido se guarda sin prefijo)."""
    return f"{entry.title}\n{_loc_label(chunk.locator)}\n{chunk.content}"


def _audit(result: DocResult, sha: str | None, audit_settings: Settings) -> None:
    payload = {
        "doc_id": result.doc_id,
        "version": result.version,
        "folder": result.folder,
        "action": result.action,
        "sha256": sha,
        "chunks": result.chunks,
        "fmea_rows": result.fmea_rows,
        "ocr_pages": result.ocr_pages,
    }
    if result.action == "error":
        payload["error"] = result.notes[-1][:200] if result.notes else None
    record_safe("ingest", INGEST_ACTOR, payload, source="ingest", settings=audit_settings)


def _insert_document(
    conn: psycopg.Connection,
    entry: DocEntry,
    sha: str,
    parsed: Parsed,
    vectors: list[list[float]],
    fmea: list[FmeaRow],
) -> None:
    conn.execute(
        "INSERT INTO rag.documents (doc_id, version, title, path, folder, doc_type, language,"
        " part_refs, pages, sha256) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (
            entry.doc_id, entry.version, entry.title, entry.rel_path, entry.folder,
            entry.doc_type, entry.language, list(entry.part_refs), parsed.pages, sha,
        ),
    )
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO rag.chunks (doc_id, version, chunk_no, page, section, content, embedding,"
            " folder, locator) VALUES (%s, %s, %s, %s, %s, %s, %s::vector, %s, %s)",
            [
                (
                    entry.doc_id, entry.version, i, c.page, c.section, c.content,
                    to_pgvector(v), entry.folder, Jsonb(c.locator),
                )
                for i, (c, v) in enumerate(zip(parsed.chunks, vectors, strict=True))
            ],
        )
        if fmea:
            cols = ("process_step", "function", "failure_mode", "effect", "severity", "cause",
                    "occurrence", "prevention_control", "detection_control", "detection", "rpn",
                    "actions")
            cur.executemany(
                f"INSERT INTO rag.fmea_rows (doc_id, version, row_no, {', '.join(cols)}, raw,"  # noqa: S608 - columnas fijas
                f" folder, sheet) VALUES (%s, %s, %s, {', '.join(['%s'] * len(cols))}, %s, %s, %s)",
                [
                    (
                        entry.doc_id, entry.version, r.row_no,
                        *(r.fields.get(c) for c in cols),
                        Jsonb({"sheet": r.sheet, "cells": r.raw}), entry.folder, r.sheet,
                    )
                    for r in fmea
                ],
            )


def ingest_entry(
    conn: psycopg.Connection | None,
    entry: DocEntry,
    *,
    settings: Settings,
    dry_run: bool = False,
    ocr: bool = True,
) -> tuple[DocResult, str]:
    sha = sha256_file(entry.path)
    res = DocResult(entry.doc_id, entry.version, entry.folder, "dry-run")
    existing: list[tuple[str, str, str]] = []
    if conn is not None:
        existing = conn.execute(
            "SELECT version, sha256, folder FROM rag.documents WHERE doc_id = %s",
            (entry.doc_id,),
        ).fetchall()
    if not dry_run and existing == [(entry.version, sha, entry.folder)]:
        res.action = "unchanged"
        res.chunks, res.fmea_rows = conn.execute(  # type: ignore[union-attr]
            "SELECT (SELECT count(*) FROM rag.chunks WHERE doc_id = %(d)s),"
            " (SELECT count(*) FROM rag.fmea_rows WHERE doc_id = %(d)s)",
            {"d": entry.doc_id},
        ).fetchone()
        return res, sha
    if not dry_run and len(existing) == 1 and existing[0][:2] == (entry.version, sha):
        # Mismo contenido, carpeta distinta: se mueve (ON UPDATE CASCADE → chunks y fmea_rows).
        with conn.transaction():  # type: ignore[union-attr]
            conn.execute(  # type: ignore[union-attr]
                "UPDATE rag.documents SET folder = %s, ingested_at = now()"
                " WHERE doc_id = %s AND version = %s",
                (entry.folder, entry.doc_id, entry.version),
            )
        res.action = "moved"
        return res, sha

    parsed = parse(entry.path, ocr=ocr)
    if not parsed.chunks:
        raise ValueError("el documento no produjo ningún chunk")
    fmea = extract_fmea(entry.path) if entry.doc_type in FMEA_DOC_TYPES else []
    res.chunks, res.fmea_rows = len(parsed.chunks), len(fmea)
    res.ocr_pages, res.notes = parsed.ocr_pages, parsed.notes
    if dry_run:
        return res, sha
    vectors = embed([embedding_input(entry, c) for c in parsed.chunks], settings=settings)
    with conn.transaction():  # type: ignore[union-attr]
        conn.execute("DELETE FROM rag.documents WHERE doc_id = %s", (entry.doc_id,))  # type: ignore[union-attr]
        _insert_document(conn, entry, sha, parsed, vectors, fmea)  # type: ignore[arg-type]
    res.action = "replaced" if existing else "inserted"
    return res, sha


def ingest(
    conn: psycopg.Connection | None,
    docs_dir: Path = DEFAULT_DOCS_DIR,
    *,
    settings: Settings | None = None,
    audit_settings: Settings | None = None,
    acl_file: Path = DEFAULT_ACL_FILE,
    dry_run: bool = False,
    prune: bool = True,
    ocr: bool = True,
) -> IngestReport:
    """Ingiere el corpus. `conn` = superusuario de la BD destino, en autocommit (cada documento es
    su propia transacción y el evento de audit se escribe tras su COMMIT). None solo con dry_run."""
    t0 = time.perf_counter()
    s = settings or get_settings()
    a = audit_settings or s
    if conn is None and not dry_run:
        raise ValueError("Sin conexión solo se admite --dry-run")
    if conn is not None and not conn.autocommit:
        raise ValueError("La conexión de ingesta debe ir en autocommit (una transacción por doc)")
    acl_folders: dict[str, list[str]] = {}
    for folder, role in load_folder_acl(acl_file):
        acl_folders.setdefault(folder, []).append(role)
    manifest = load_manifest(docs_dir, acl_folders)
    rep = IngestReport(warnings=list(manifest.warnings), rejected=list(manifest.rejected))
    if not dry_run:
        rep.acl_rows = sync_folder_acl(conn, acl_file)  # type: ignore[arg-type]

    for entry in manifest.entries:
        sha: str | None = None
        try:
            result, sha = ingest_entry(
                None if dry_run else conn, entry, settings=s, dry_run=dry_run, ocr=ocr
            )
        except Exception as exc:  # un documento roto no aborta la ingesta del resto
            # (su bloque conn.transaction() ya se revirtió)
            result = DocResult(
                entry.doc_id, entry.version, entry.folder, "error",
                notes=[f"{type(exc).__name__}: {str(exc)[:160]}"],
            )
        rep.results.append(result)
        if not dry_run:
            _audit(result, sha, a)

    if prune and not dry_run:
        keep = [e.doc_id for e in manifest.entries] + manifest.missing
        with conn.transaction():  # type: ignore[union-attr]
            gone = conn.execute(  # type: ignore[union-attr]
                "DELETE FROM rag.documents WHERE doc_id <> ALL(%s)"
                " RETURNING doc_id, version, folder",
                (keep,),
            ).fetchall()
        for doc_id, version, folder in gone:
            r = DocResult(doc_id, version, folder, "pruned")
            rep.results.append(r)
            _audit(r, None, a)
    rep.seconds = time.perf_counter() - t0
    return rep


# --- CLI -------------------------------------------------------------------------------------


def _print_report(rep: IngestReport, dry_run: bool) -> None:
    for r in rep.results:
        extra = f" ocr={r.ocr_pages}" if r.ocr_pages else ""
        notes = f"  [{'; '.join(r.notes)}]" if r.notes else ""
        print(
            f"  {r.action:<9} {r.doc_id:<22} {r.version:<4} {r.folder:<34} "
            f"chunks={r.chunks:<3} fmea={r.fmea_rows}{extra}{notes}"
        )
    for w in rep.warnings:
        print(f"AVISO: {w}")
    for w in rep.rejected:
        print(f"RECHAZADO: {w}")
    docs = [r for r in rep.results if r.action not in ("pruned", "error")]
    by_action: dict[str, int] = {}
    for r in rep.results:
        by_action[r.action] = by_action.get(r.action, 0) + 1
    print(
        f"{'[dry-run] ' if dry_run else ''}Documentos: {len(docs)} · chunks: {rep.count('chunks')}"
        f" · filas AMFE: {rep.count('fmea_rows')} · acciones: {by_action}"
        f" · ACL: {rep.acl_rows} filas · {rep.seconds:.1f} s"
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Ingesta del corpus (solo rutas de manifest.json).")
    ap.add_argument("docs_pos", nargs="?", type=Path, help="carpeta del corpus (con manifest.json)")
    ap.add_argument("--docs", type=Path, default=None, help=f"por defecto {DEFAULT_DOCS_DIR}")
    ap.add_argument("--dry-run", action="store_true", help="solo parsea y cuenta; no escribe")
    ap.add_argument("--no-prune", action="store_true", help="no borra docs fuera del manifest")
    args = ap.parse_args(argv)
    docs_dir = (args.docs or args.docs_pos or DEFAULT_DOCS_DIR).resolve()

    if args.dry_run:
        rep = ingest(None, docs_dir, dry_run=True)
    else:
        from solaris.db import connect

        with connect(autocommit=True) as conn:
            rep = ingest(conn, docs_dir, prune=not args.no_prune)
    _print_report(rep, args.dry_run)
    return 1 if rep.errors else 0


if __name__ == "__main__":
    sys.exit(main())
