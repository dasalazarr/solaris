"""M2-T3: ingesta del corpus (F01).

BD aislada `solaris_test` (conftest.audit_settings la recrea con las migraciones de RAG y audit).
Embeddings `fake` (sin descarga). El OCR sí se ejecuta (rapidocr).
"""

import dataclasses
import json
import shutil
from collections.abc import Iterator

import psycopg
import pytest

from solaris.rag.embed import DIM, embed
from solaris.rag.fmea import parse_rating
from solaris.rag.ingest import IngestReport, ingest, ingest_entry
from solaris.rag.manifest import DEFAULT_DOCS_DIR, load_manifest

MANIFEST = json.loads((DEFAULT_DOCS_DIR / "manifest.json").read_text(encoding="utf-8"))
DOCS = {d["doc_id"]: d for d in MANIFEST["documents"]}
SCANNED = "IT-L1-PR250-04"


# --- Sin BD ---------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "expected"),
    [(8, 8), ("8 (ver nota)", 8), ("2-3", 3), ("3*", 3), (" 4", 4), ("alta", None),
     (None, None), (0, None), ("11", None), (7.0, 7)],
)
def test_parse_rating_tolerates_dirty_values(value, expected):
    assert parse_rating(value) == expected


def test_parse_rpn():
    assert parse_rating("~80", 1, 1000) == 80
    assert parse_rating("#¡VALOR!", 1, 1000) is None


def test_fake_embeddings_are_deterministic_and_1024(settings):
    s = settings.model_copy(update={"embed_backend": "fake"})
    a, b, c = embed(["grieta en W2", "grieta en W2", "rebaba en el agujero"], settings=s)
    assert len(a) == DIM and a == b and a != c
    assert abs(sum(x * x for x in a) - 1.0) < 1e-9


def _write_corpus(tmp_path, doc_ids: list[str], extra_entries: list[dict]) -> None:
    docs = []
    for doc_id in doc_ids:
        d = DOCS[doc_id]
        dst = tmp_path / d["path"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(DEFAULT_DOCS_DIR / d["path"], dst)
        docs.append(d)
    (tmp_path / "manifest.json").write_text(
        json.dumps({"documents": docs + extra_entries}), encoding="utf-8"
    )


def test_allowlist_ignores_files_outside_manifest(tmp_path):
    _write_corpus(tmp_path, ["8D-ARGA-2025-014", "IT-L2-CR02-02"], [
        {**DOCS["8D-ARGA-2025-002"]},  # listado pero sin fichero → aviso
        {**DOCS["IT-L2-CR02-02"], "doc_id": "X-BUILD", "path": "_build/common.py",
         "folder": "_build"},
        {**DOCS["IT-L2-CR02-02"], "doc_id": "X-PLANT", "path": "PLANT.md", "folder": "calidad"},
        {**DOCS["IT-L2-CR02-02"], "doc_id": "X-ESC", "path": "../acl.json", "folder": "calidad"},
        {**DOCS["IT-L2-CR02-02"], "doc_id": "X-ERP", "path": "calidad/erp/seed.xlsx",
         "folder": "calidad/erp"},
    ])
    trap = tmp_path / "calidad/8d/8D-TRAMPA_v1.docx"
    shutil.copy(DEFAULT_DOCS_DIR / DOCS["8D-ARGA-2025-014"]["path"], trap)
    (tmp_path / "PLANT.md").write_text("verdad del escenario")

    m = load_manifest(tmp_path)
    assert sorted(e.doc_id for e in m.entries) == ["8D-ARGA-2025-014", "IT-L2-CR02-02"]
    assert m.missing == ["8D-ARGA-2025-002"]
    assert any("8D-TRAMPA_v1.docx" in w for w in m.warnings)
    assert not any("PLANT.md" in w for w in m.warnings)  # excluido por construcción, sin ruido
    assert len(m.rejected) == 4

    rep = ingest(None, tmp_path, dry_run=True)
    assert sorted(r.doc_id for r in rep.results) == ["8D-ARGA-2025-014", "IT-L2-CR02-02"]


# --- Con BD (solaris_test) ------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _no_real_network():
    """psycopg usa libpq contra el Postgres local; rapidocr y el embedder fake no usan red."""
    yield


@pytest.fixture(scope="module")
def rag_settings(audit_settings):
    return audit_settings.model_copy(update={"embed_backend": "fake"})


@pytest.fixture(scope="module")
def conn(audit_settings) -> Iterator[psycopg.Connection]:
    from solaris.audit import testdb

    with testdb._connect_to(audit_settings, testdb.TEST_DB, autocommit=True) as c:
        if c.execute("SELECT to_regclass('rag.chunks')").fetchone()[0] is None:
            pytest.skip("solaris_test sin esquema rag")
        yield c


@pytest.fixture(scope="module")
def first_run(conn, rag_settings) -> IngestReport:
    return ingest(conn, settings=rag_settings, audit_settings=rag_settings)


def test_first_run_ingests_every_manifest_doc(first_run):
    assert not first_run.errors, [r.notes for r in first_run.errors]
    assert not first_run.rejected
    assert {r.doc_id for r in first_run.results} == set(DOCS)
    assert {r.action for r in first_run.results} == {"inserted"}
    assert first_run.acl_rows > 0


def test_every_doc_has_chunks_with_locator_and_folder(first_run, conn):
    rows = conn.execute(
        "SELECT doc_id, version, folder, page, section, locator FROM rag.chunks"
    ).fetchall()
    by_doc: dict[str, list] = {}
    for r in rows:
        by_doc.setdefault(r[0], []).append(r)
    for doc_id, d in DOCS.items():
        chunks = by_doc.get(doc_id)
        assert chunks, f"{doc_id} sin chunks"
        for _, version, folder, page, section, loc in chunks:
            assert version == d["version"] and folder == d["folder"]
            if d["path"].endswith(".pdf"):
                assert loc["page"] == page and 1 <= page <= d["pages"]
            elif d["path"].endswith(".xlsx"):
                assert loc["sheet"] in d["sheets"] and loc["rows"][0] <= loc["rows"][1]
            else:
                assert loc["section"] == section and section
        if d.get("sections"):  # 8D: cabecera + D1..D8
            got = {c[4] for c in chunks}
            assert set(d["sections"]) <= got, f"{doc_id}: faltan {set(d['sections']) - got}"


def test_documents_metadata(first_run, conn):
    n, pdf_pages = conn.execute(
        "SELECT count(*), sum(pages) FILTER (WHERE path LIKE '%%.pdf') FROM rag.documents"
    ).fetchone()
    assert n == len(DOCS)
    assert pdf_pages == sum(d["pages"] for d in DOCS.values() if d["path"].endswith(".pdf"))
    assert conn.execute(
        "SELECT count(*) FROM rag.chunks WHERE embedding IS NULL"
    ).fetchone()[0] == 0


def test_acl_inherited_planta_sees_no_8d(first_run, conn):
    def visible(role: str, folder: str) -> int:
        return conn.execute(
            "SELECT count(*) FROM rag.visible_chunks(%s) WHERE folder = %s", (role, folder)
        ).fetchone()[0]

    assert visible("planta", "calidad/8d") == 0
    assert visible("calidad", "calidad/8d") > 0
    assert visible("planta", "produccion/instrucciones-trabajo") > 0
    assert visible("calidad", "direccion/confidencial") == 0
    assert visible("admin", "direccion/confidencial") > 0
    assert conn.execute(
        "SELECT count(*) FROM rag.visible_fmea_rows('planta')"
    ).fetchone()[0] == 0
    # Ninguna fila visible para planta sale de una carpeta sin permiso en acl.json.
    allowed = {f for f, roles in json.loads(
        (DEFAULT_DOCS_DIR.parent / "acl.json").read_text())["folders"].items() if "planta" in roles}
    seen = {r[0] for r in conn.execute("SELECT DISTINCT folder FROM rag.visible_chunks('planta')")}
    assert seen <= allowed


def test_scanned_pdf_is_ocrd(first_run, conn):
    r = next(r for r in first_run.results if r.doc_id == SCANNED)
    assert r.ocr_pages == [1, 2]
    rows = conn.execute(
        "SELECT page, content, locator FROM rag.chunks WHERE doc_id = %s ORDER BY chunk_no",
        (SCANNED,),
    ).fetchall()
    assert {p for p, _, _ in rows} == {1, 2}
    assert all(loc.get("ocr") is True for _, _, loc in rows)
    text = " ".join(c for _, c, _ in rows)
    assert "PR-250" in text and "IT-L1-PR250-04" in text


def test_fmea_rows_for_every_amfe_including_dirty(first_run, conn):
    counts = dict(conn.execute(
        "SELECT doc_id, count(*) FROM rag.fmea_rows GROUP BY doc_id"
    ).fetchall())
    amfes = [k for k, d in DOCS.items() if d["doc_type"] == "AMFE"]
    assert amfes and all(counts.get(a, 0) > 0 for a in amfes), counts
    assert set(counts) == set(amfes)  # los planes de control no generan filas AMFE
    # AMFE sucio: "2-3" → 3 (conservador), "alta" → NULL con el valor original en raw.
    occ, sev, raw = conn.execute(
        "SELECT occurrence, severity, raw FROM rag.fmea_rows"
        " WHERE doc_id = 'AMFE-AR1006-01' AND row_no = 12"
    ).fetchone()
    assert occ == 3 and sev == 8
    sev13, raw13 = conn.execute(
        "SELECT severity, raw FROM rag.fmea_rows WHERE doc_id = 'AMFE-AR1006-01' AND row_no = 13"
    ).fetchone()
    assert sev13 is None and raw13["cells"]["F13"]["value"] == "alta"
    assert raw["sheet"] == "AMFE tuercas"
    # La hoja "viejo" (copia v2, "NO USAR") no genera filas.
    assert conn.execute(
        "SELECT count(*) FROM rag.fmea_rows WHERE sheet <> 'AMFE tuercas'"
        " AND doc_id = 'AMFE-AR1006-01'"
    ).fetchone()[0] == 0


def test_reingest_is_idempotent(first_run, conn, rag_settings):
    before = conn.execute(
        "SELECT count(*), min(id), max(id) FROM rag.chunks"
    ).fetchone()
    rep = ingest(conn, settings=rag_settings, audit_settings=rag_settings)
    assert {r.action for r in rep.results} == {"unchanged"}
    assert rep.count("chunks") == first_run.count("chunks")
    assert conn.execute("SELECT count(*), min(id), max(id) FROM rag.chunks").fetchone() == before
    assert conn.execute("SELECT count(*) FROM rag.documents").fetchone()[0] == len(DOCS)


def test_new_version_replaces_old(first_run, conn, rag_settings):
    entry = next(e for e in load_manifest().entries if e.doc_id == "IT-L2-CR02-02")
    bumped = dataclasses.replace(entry, version="v99")
    res, _ = ingest_entry(conn, bumped, settings=rag_settings)
    assert res.action == "replaced"
    versions = [r[0] for r in conn.execute(
        "SELECT DISTINCT version FROM rag.chunks WHERE doc_id = %s", (entry.doc_id,))]
    assert versions == ["v99"]
    res, _ = ingest_entry(conn, entry, settings=rag_settings)  # restaura la versión del manifest
    assert res.action == "replaced"
    assert conn.execute(
        "SELECT version FROM rag.documents WHERE doc_id = %s", (entry.doc_id,)
    ).fetchall() == [(entry.version,)]


def test_ingest_events_are_audited_without_content(first_run, audit_settings):
    from solaris.audit import connect_reader

    with connect_reader(audit_settings) as c:
        rows = c.execute(
            "SELECT actor_user, source, payload FROM audit.events WHERE event_type = 'ingest'"
        ).fetchall()
    assert len(rows) >= len(DOCS)
    keys = {"doc_id", "version", "folder", "action", "sha256", "chunks", "fmea_rows", "ocr_pages"}
    for user, source, payload in rows:
        assert user == "svc.ingest" and source == "ingest"
        assert set(payload) <= keys | {"error"}
    assert {p["doc_id"] for _, _, p in rows} >= set(DOCS)
