"""M2-T2: esquema RAG y filtrado ACL en SQL.

Los tests de BD se saltan si Postgres no está disponible o el esquema no está migrado.
Cada test corre dentro de una transacción con `force_rollback`: no deja datos en la BD compartida.
"""

import json
from collections.abc import Iterator

import psycopg
import pytest

from solaris.db.migrate import MIGRATIONS_DIR, MigrationError, apply_pending, discover
from solaris.rag.acl import ACLError, load_folder_acl, sync_folder_acl

DIM = 1024
SHA = "0" * 64


# --- Sin BD ---------------------------------------------------------------------------------


def test_load_folder_acl_from_repo_file():
    pairs = load_folder_acl()
    assert ("calidad/8d", "calidad") in pairs
    assert ("calidad/8d", "planta") not in pairs
    assert [r for f, r in pairs if f == "direccion/confidencial"] == ["admin"]


def test_load_folder_acl_rejects_undeclared_role(tmp_path):
    p = tmp_path / "acl.json"
    p.write_text(json.dumps({"roles": ["calidad"], "folders": {"x/y": ["calidad", "root"]}}))
    with pytest.raises(ACLError):
        load_folder_acl(p)


def test_discover_orders_and_validates(tmp_path):
    assert discover(MIGRATIONS_DIR)[0].version == "001_rag"
    (tmp_path / "002_b.sql").write_text("SELECT 1;")
    (tmp_path / "001_a.sql").write_text("SELECT 1;")
    assert [m.version for m in discover(tmp_path)] == ["001_a", "002_b"]
    (tmp_path / "bad.sql").write_text("SELECT 1;")
    with pytest.raises(MigrationError):
        discover(tmp_path)


# --- Con BD ---------------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _no_real_network():
    """Anula el guard de conftest en este módulo: psycopg usa libpq (no el socket de Python) y la
    conexión va solo al Postgres local del docker-compose (127.0.0.1)."""
    yield


@pytest.fixture(scope="module")
def _db() -> Iterator[psycopg.Connection]:
    from solaris.db import connect
    from solaris.settings import get_settings

    s = get_settings()
    if s.database_url is None and s.postgres_host not in ("127.0.0.1", "localhost"):
        pytest.skip("Los tests de BD solo corren contra el Postgres local")
    try:
        conn = connect(s, connect_timeout=2)
    except Exception as exc:  # BD no levantada o sin credenciales
        pytest.skip(f"Postgres no disponible: {type(exc).__name__}")
    with conn:
        if conn.execute("SELECT to_regclass('rag.chunks')").fetchone()[0] is None:
            pytest.skip("Esquema rag no migrado: uv run python -m solaris.db.migrate")
        conn.rollback()
        yield conn


@pytest.fixture
def db(_db: psycopg.Connection) -> Iterator[psycopg.Connection]:
    with _db.transaction(force_rollback=True):
        yield _db


def _vec(i: int) -> str:
    v = [0.0] * DIM
    v[i] = 1.0
    return "[" + ",".join(map(str, v)) + "]"


def _insert_doc(conn, doc_id: str, folder: str, n_chunks: int = 2) -> None:
    conn.execute(
        "INSERT INTO rag.documents (doc_id, version, title, path, folder, doc_type, language,"
        " part_refs, pages, sha256) VALUES (%s, 'A', %s, %s, %s, 'test', 'es', %s, %s, %s)",
        (
            doc_id,
            f"Test {doc_id}",
            f"{folder}/{doc_id}.pdf",
            folder,
            ["AR-1004"],
            n_chunks or None,
            SHA,
        ),
    )
    for i in range(n_chunks):
        conn.execute(
            "INSERT INTO rag.chunks (doc_id, version, chunk_no, page, section, content, embedding,"
            " folder) VALUES (%s, 'A', %s, %s, 'D4', %s, %s::vector, %s)",
            (doc_id, i, i + 1, f"{doc_id} rebaba en AR-1004 pág. {i + 1}", _vec(i), folder),
        )


@pytest.fixture
def seeded(db):
    assert sync_folder_acl(db) > 0
    _insert_doc(db, "TEST-8D-001", "calidad/8d")
    _insert_doc(db, "TEST-IT-001", "produccion/instrucciones-trabajo")
    _insert_doc(db, "TEST-DIR-001", "direccion/confidencial")
    return db


def _visible(conn, role: str | None, folder: str) -> int:
    return conn.execute(
        "SELECT count(*) FROM rag.visible_chunks(%s) WHERE folder = %s AND doc_id LIKE 'TEST-%%'",
        (role, folder),
    ).fetchone()[0]


def test_planta_sees_no_8d_chunks(seeded):
    assert _visible(seeded, "planta", "calidad/8d") == 0
    assert _visible(seeded, "planta", "produccion/instrucciones-trabajo") == 2


def test_calidad_sees_8d_chunks(seeded):
    assert _visible(seeded, "calidad", "calidad/8d") == 2


def test_calidad_sees_no_confidential_chunks(seeded):
    assert _visible(seeded, "calidad", "direccion/confidencial") == 0
    assert _visible(seeded, "admin", "direccion/confidencial") == 2


def test_unknown_or_null_role_sees_nothing(seeded):
    for role in (None, "", "invitado", "calidad' OR '1'='1"):
        n = seeded.execute(
            "SELECT count(*) FROM rag.visible_chunks(%s) WHERE doc_id LIKE 'TEST-%%'", (role,)
        ).fetchone()[0]
        assert n == 0


def test_folder_without_acl_is_invisible_even_for_admin(seeded):
    seeded.execute("DELETE FROM rag.folder_acl WHERE folder = 'calidad/8d'")
    assert _visible(seeded, "admin", "calidad/8d") == 0


def test_vector_ranking_after_acl_filter(seeded):
    # La consulta apunta exactamente al chunk 0 de los documentos: para 'planta' el mejor
    # resultado nunca puede ser del 8D, porque el filtro ocurre antes del ORDER BY.
    rows = seeded.execute(
        "SELECT doc_id, page FROM rag.visible_chunks(%s) WHERE doc_id LIKE 'TEST-%%'"
        " ORDER BY embedding <=> %s::vector LIMIT 5",
        ("planta", _vec(0)),
    ).fetchall()
    assert rows and all(d == "TEST-IT-001" for d, _ in rows)
    assert rows[0] == ("TEST-IT-001", 1)


def test_tsv_simple_keeps_part_codes(seeded):
    rows = seeded.execute(
        "SELECT DISTINCT doc_id FROM rag.visible_chunks(%s)"
        " WHERE tsv @@ websearch_to_tsquery('simple', %s) AND doc_id LIKE 'TEST-%%'",
        ("calidad", "AR-1004 rebaba"),
    ).fetchall()
    assert {r[0] for r in rows} == {"TEST-8D-001", "TEST-IT-001"}


def test_denormalized_folder_must_match_document(db):
    sync_folder_acl(db)
    _insert_doc(db, "TEST-8D-002", "calidad/8d", n_chunks=0)
    with pytest.raises(psycopg.errors.ForeignKeyViolation), db.transaction():
        db.execute(
            "INSERT INTO rag.chunks (doc_id, version, chunk_no, page, content, folder)"
            " VALUES ('TEST-8D-002', 'A', 0, 1, 'x', 'produccion/instrucciones-trabajo')"
        )


def test_folder_change_cascades_to_chunks_and_fmea(db):
    sync_folder_acl(db)
    _insert_doc(db, "TEST-AMFE-001", "calidad/amfe", n_chunks=1)
    db.execute(
        "INSERT INTO rag.fmea_rows (doc_id, version, row_no, failure_mode, severity, occurrence,"
        " detection, rpn, raw, folder) VALUES ('TEST-AMFE-001', 'A', 5, 'rebaba', 7, 4, 5, 140,"
        " %s, 'calidad/amfe')",
        (json.dumps({"B": "rebaba"}),),
    )
    assert (
        db.execute(
            "SELECT count(*) FROM rag.visible_fmea_rows('planta') WHERE doc_id = 'TEST-AMFE-001'"
        ).fetchone()[0]
        == 0
    )
    db.execute(
        "UPDATE rag.documents SET folder = 'calidad/planes-control' WHERE doc_id = 'TEST-AMFE-001'"
    )
    assert _visible(db, "planta", "calidad/planes-control") == 1
    assert (
        db.execute(
            "SELECT count(*) FROM rag.visible_fmea_rows('planta') WHERE doc_id = 'TEST-AMFE-001'"
        ).fetchone()[0]
        == 1
    )


def test_migrations_up_to_date_and_runner_idempotent(db):
    assert apply_pending(db, dry_run=True) == []
    assert apply_pending(db) == []
