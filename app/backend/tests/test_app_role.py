"""M4-T1 (PAT-005): el rol de runtime `solaris_app` no puede saltarse la ACL del corpus.

Contra `solaris_test` (migraciones 001/003/004/005/006), conectando COMO solaris_app.
"""

from collections.abc import Iterator

import psycopg
import pytest

from solaris.db import APP_ROLE, DbUnavailable, connect_app
from solaris.db.migrate import MIGRATIONS_DIR, discover

RAG_TABLES = ("rag.chunks", "rag.fmea_rows", "rag.documents", "rag.folder_acl")
FUNCS = ("rag.visible_chunks(text)", "rag.visible_fmea_rows(text)",
         "rag.visible_documents(text)")


@pytest.fixture(autouse=True)
def _no_real_network():
    yield  # solo Postgres local vía libpq


def test_migration_006_has_no_secrets_and_no_direct_grants():
    mig = {m.version: m for m in discover(MIGRATIONS_DIR)}["006_rag_app_role"]
    code = "\n".join(ln for ln in mig.sql.splitlines() if not ln.lstrip().startswith("--")).upper()
    assert "PASSWORD" not in code
    grant = ("GRANT SELECT ON RAG.CHUNKS, RAG.FMEA_ROWS, RAG.DOCUMENTS, RAG.FOLDER_ACL"
             " TO RAG_DEFINER")
    assert grant in code
    assert "TO SOLARIS_APP" in code and "SELECT ON RAG.CHUNKS TO SOLARIS_APP" not in code


def test_connect_app_without_password_fails_closed(settings):
    with pytest.raises(DbUnavailable):
        connect_app(settings)


@pytest.fixture(scope="module")
def app_settings(audit_settings):
    from solaris.audit import testdb

    if audit_settings.solaris_app_password is None:
        pytest.skip("Falta SOLARIS_APP_PASSWORD en .env (uv run python -m solaris.db.migrate)")
    return audit_settings.model_copy(update={"app_db_name": testdb.TEST_DB})


@pytest.fixture
def app_conn(app_settings) -> Iterator[psycopg.Connection]:
    with connect_app(app_settings, autocommit=True) as c:
        yield c


def test_is_really_solaris_app_without_privileges(app_conn):
    row = app_conn.execute(
        "SELECT current_user, rolsuper, rolcreaterole, rolcreatedb, rolbypassrls, rolinherit"
        " FROM pg_roles WHERE rolname = current_user"
    ).fetchone()
    assert row == (APP_ROLE, False, False, False, False, False)
    assert app_conn.execute("SHOW default_transaction_read_only").fetchone()[0] == "on"


@pytest.mark.parametrize("table", RAG_TABLES)
def test_cannot_select_rag_tables_directly(app_conn, table):
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        app_conn.execute(f"SELECT * FROM {table} LIMIT 1")  # noqa: S608  # constantes del test


def test_can_use_visible_functions(app_conn):
    for fn in ("visible_chunks", "visible_fmea_rows", "visible_documents"):
        app_conn.execute(f"SELECT count(*) FROM rag.{fn}('calidad')").fetchone()  # noqa: S608
        assert app_conn.execute(
            f"SELECT count(*) FROM rag.{fn}('rol-inexistente')"  # noqa: S608
        ).fetchone()[0] == 0


def test_cannot_write_rag_or_audit_or_read_erp(app_conn):
    app_conn.execute("SET SESSION CHARACTERISTICS AS TRANSACTION READ WRITE")
    for stmt in (
        "INSERT INTO rag.folder_acl VALUES ('direccion/confidencial', 'planta')",
        "DELETE FROM rag.chunks",
        "INSERT INTO audit.events (event_type, payload) VALUES ('auth', '{}')",
        "SELECT * FROM audit.events LIMIT 1",
        "SELECT rolpassword FROM pg_authid LIMIT 1",
        "CREATE TEMP TABLE t (x int)",
        "CREATE TABLE public.t (x int)",
    ):
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            app_conn.execute(stmt)  # type: ignore[arg-type]


def test_functions_are_hardened(app_conn):
    """SECURITY DEFINER como rag_definer (no superusuario), search_path fijo, sin PUBLIC."""
    for fn in FUNCS:
        row = app_conn.execute(
            "SELECT p.prosecdef, pg_get_userbyid(p.proowner), p.proconfig,"
            " has_function_privilege('public', p.oid, 'EXECUTE')"
            " FROM pg_proc p WHERE p.oid = %s::regprocedure", (fn,),
        ).fetchone()
        assert row[0] is True and row[1] == "rag_definer", fn
        assert row[2] == ["search_path=pg_catalog, pg_temp"], fn
        assert row[3] is False, fn


def test_public_has_no_temp_or_connect(app_conn):
    db = app_conn.execute("SELECT current_database()").fetchone()[0]
    for priv in ("TEMP", "CONNECT"):
        assert app_conn.execute(
            "SELECT has_database_privilege('public', %s, %s)", (db, priv)
        ).fetchone()[0] is False
    assert app_conn.execute(
        "SELECT has_database_privilege(current_user, %s, 'TEMP')", (db,)
    ).fetchone()[0] is False


def test_other_service_roles_cannot_execute_visible_functions(app_settings):
    """Ni el MCP (erp_reader) ni los roles del audit pueden llamar a las funciones del corpus."""
    from solaris.audit import connect_reader, connect_writer

    for conn_fn in (connect_reader, connect_writer):
        with conn_fn(app_settings, autocommit=True) as c, \
                pytest.raises(psycopg.errors.InsufficientPrivilege):
            c.execute("SELECT count(*) FROM rag.visible_chunks('admin')")
