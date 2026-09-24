"""Allowlist de la ingesta (M2-T3, PAT-004): solo se ingieren las rutas de `manifest.json`.

La carpeta del corpus nunca se recorre para decidir qué ingerir. Solo se recorre para AVISAR de
ficheros que están en disco pero no en el manifest (que se ignoran). Además de la allowlist, hay una
denylist por construcción (defensa en profundidad): aunque el manifest listase `PLANT.md`,
`acl.json`, `erp/`, `evals/`, `complaints/`, `_build/` o un `.py`, la entrada se rechaza.
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from solaris.settings import REPO_ROOT

DEFAULT_DOCS_DIR = REPO_ROOT / "app" / "data" / "synthetic" / "docs"
ALLOWED_SUFFIXES = frozenset({".docx", ".pdf", ".xlsx"})
DENY_NAMES = frozenset({"manifest.json", "PLANT.md", "acl.json"})
DENY_DIRS = frozenset({"_build", "erp", "evals", "complaints"})
DENY_SUFFIXES = frozenset({".py", ".pyc", ".md", ".json", ".sql"})
MAX_FILE_BYTES = 50 * 1024 * 1024
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_VERSION_RE = re.compile(r"^v\d{1,3}$")
_FOLDER_RE = re.compile(r"^[a-z0-9_-]+(/[a-z0-9_-]+)*$")
_LANGS = {"es": "es", "en": "en", "mixed": "mixed"}


class ManifestError(ValueError):
    pass


@dataclass(frozen=True)
class DocEntry:
    doc_id: str
    version: str
    title: str
    rel_path: str
    path: Path
    folder: str
    doc_type: str
    language: str
    part_refs: tuple[str, ...]
    acl_roles: tuple[str, ...]
    sheets: tuple[str, ...] = ()
    sections: tuple[str, ...] = ()


@dataclass
class Manifest:
    root: Path
    entries: list[DocEntry]
    warnings: list[str] = field(default_factory=list)
    rejected: list[str] = field(default_factory=list)  # entradas del manifest descartadas
    missing: list[str] = field(default_factory=list)  # doc_id listados cuyo fichero no existe


def denied(rel: PurePosixPath) -> str | None:
    """Motivo por el que una ruta relativa está excluida por construcción, o None."""
    if rel.name in DENY_NAMES:
        return f"nombre excluido ({rel.name})"
    if any(part in DENY_DIRS for part in rel.parts[:-1]):
        return "carpeta excluida"
    if rel.suffix.lower() in DENY_SUFFIXES:
        return f"extensión excluida ({rel.suffix})"
    return None


def _safe_rel(root: Path, raw: str) -> tuple[PurePosixPath, Path]:
    rel = PurePosixPath(raw)
    if rel.is_absolute() or ".." in rel.parts or not rel.parts or "\\" in raw:
        raise ManifestError(f"ruta no relativa o con '..': {raw!r}")
    path = root / Path(*rel.parts)
    # resolve() sigue symlinks: un enlace que apunte fuera de la raíz se rechaza.
    if not path.resolve().is_relative_to(root.resolve()):
        raise ManifestError(f"ruta fuera del corpus: {raw!r}")
    return rel, path


def load_manifest(
    docs_dir: Path = DEFAULT_DOCS_DIR, acl_folders: dict[str, list[str]] | None = None
) -> Manifest:
    root = docs_dir.resolve()
    mpath = root / "manifest.json"
    if not mpath.is_file():
        raise ManifestError(f"No existe {mpath}")
    data = json.loads(mpath.read_text(encoding="utf-8"))
    docs = data.get("documents")
    if not isinstance(docs, list):
        raise ManifestError("manifest.json debe tener 'documents' (lista)")

    m = Manifest(root=root, entries=[])
    seen_ids: set[str] = set()
    listed: set[str] = set()
    for i, d in enumerate(docs):
        where = f"documents[{i}]"
        try:
            doc_id, version = str(d["doc_id"]), str(d["version"])
            folder, raw_path = str(d["folder"]), str(d["path"])
            if not _ID_RE.match(doc_id) or not _VERSION_RE.match(version):
                raise ManifestError(f"doc_id/version no válidos: {doc_id!r} {version!r}")
            if not _FOLDER_RE.match(folder):
                raise ManifestError(f"folder no válido: {folder!r}")
            rel, path = _safe_rel(root, raw_path)
            listed.add(rel.as_posix())
            if reason := denied(rel):
                raise ManifestError(f"{raw_path}: {reason}")
            if rel.suffix.lower() not in ALLOWED_SUFFIXES:
                raise ManifestError(f"{raw_path}: formato no soportado")
            if rel.parent.as_posix() != folder:
                raise ManifestError(f"{raw_path}: no está en su folder {folder!r}")
            if doc_id in seen_ids:
                raise ManifestError(f"doc_id repetido: {doc_id}")
            lang = _LANGS.get(str(d.get("language", "")).lower())
            if lang is None:
                raise ManifestError(f"language no válido: {d.get('language')!r}")
        except (KeyError, TypeError) as exc:
            m.rejected.append(f"{where}: campo obligatorio ausente ({exc})")
            continue
        except ManifestError as exc:
            m.rejected.append(f"{where}: {exc}")
            continue
        if not path.is_file():
            m.warnings.append(f"{doc_id}: el fichero del manifest no existe ({raw_path})")
            m.missing.append(doc_id)
            continue
        if path.stat().st_size > MAX_FILE_BYTES:
            m.rejected.append(f"{where}: {raw_path} supera {MAX_FILE_BYTES} bytes")
            continue
        seen_ids.add(doc_id)
        acl_roles = tuple(d.get("acl_roles") or ())
        if acl_folders is not None:
            if folder not in acl_folders:
                m.warnings.append(
                    f"{doc_id}: la carpeta {folder!r} no está en acl.json (invisible para todos)"
                )
            elif sorted(acl_folders[folder]) != sorted(acl_roles):
                m.warnings.append(
                    f"{doc_id}: acl_roles del manifest {sorted(acl_roles)} difieren de acl.json "
                    f"{sorted(acl_folders[folder])}; manda acl.json (rag.folder_acl)"
                )
        m.entries.append(
            DocEntry(
                doc_id=doc_id,
                version=version,
                title=str(d.get("title") or doc_id)[:300],
                rel_path=rel.as_posix(),
                path=path,
                folder=folder,
                doc_type=str(d.get("doc_type") or "otro").lower()[:32],
                language=lang,
                part_refs=tuple(str(p) for p in d.get("part_refs") or ()),
                acl_roles=acl_roles,
                sheets=tuple(d.get("sheets") or ()),
                sections=tuple(d.get("sections") or ()),
            )
        )
    m.warnings.extend(unlisted_files(root, listed))
    return m


def unlisted_files(root: Path, listed: set[str]) -> list[str]:
    """Avisos por ficheros en disco que NO están en el manifest (no se ingieren)."""
    out: list[str] = []
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.name.startswith("."):
            continue
        rel = PurePosixPath(p.relative_to(root).as_posix())
        if rel.as_posix() in listed or denied(rel):
            continue
        out.append(f"fichero fuera del manifest, ignorado: {rel.as_posix()}")
    return out
