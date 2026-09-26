"""M3-T3: esquema `eightd` y rol `eightd_app` (migración 008) contra el Postgres del demo.

Se salta si la migración no está aplicada o falta EIGHTD_APP_PASSWORD. Lo que escribe (un caso y
sus checkpoints) lo borra al final el superusuario de desarrollo: `eightd_app` no puede borrar.
"""

from __future__ import annotations

import asyncio

import psycopg
import pytest

from solaris.settings import get_settings


@pytest.fixture(scope="module")
def real_settings():
    s = get_settings()
    if s.eightd_app_password is None:
        pytest.skip("Falta EIGHTD_APP_PASSWORD en .env")
    try:
        from solaris.db import connect

        with connect(s) as c:
            ok = c.execute("SELECT 1 FROM rag.schema_migrations"
                           " WHERE version = '008_eightd_checkpoints'").fetchone()
    except Exception as exc:
        pytest.skip(f"Postgres no disponible: {type(exc).__name__}")
    if not ok:
        pytest.skip("Migración 008 no aplicada")
    return s


def _app_conn(s, **kw):
    return psycopg.connect(host=s.postgres_host, port=s.solaris_db_port, dbname=s.postgres_db,
                           user="eightd_app", password=s.eightd_app_password.get_secret_value(),
                           **kw)


def test_role_attributes_and_isolation(real_settings):
    with _app_conn(real_settings, autocommit=True) as c:
        row = c.execute("SELECT rolsuper, rolcreaterole, rolcreatedb, rolbypassrls"
                        " FROM pg_roles WHERE rolname = current_user").fetchone()
        assert row == (False, False, False, False)
        assert c.execute("SHOW search_path").fetchone()[0] == "eightd"
        for sql in ("SELECT 1 FROM rag.chunks LIMIT 1", "SELECT 1 FROM erp.lots LIMIT 1",
                    "SELECT 1 FROM audit.events LIMIT 1",
                    "SELECT 1 FROM rag.visible_chunks('admin') LIMIT 1",
                    "CREATE TABLE eightd.x (a int)", "DELETE FROM eightd.cases",
                    "DELETE FROM eightd.checkpoints", "TRUNCATE eightd.checkpoint_writes",
                    "UPDATE eightd.cases SET filename = 'x'"):
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                c.execute(sql)
        for role in ("solaris", "solaris_app", "erp_reader", "audit_writer"):
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                c.execute(f"SET ROLE {role}")


def test_checkpoint_tables_match_library_migrations(real_settings):
    from langgraph.checkpoint.postgres.base import BasePostgresSaver

    with _app_conn(real_settings, autocommit=True) as c:
        top = c.execute("SELECT max(v) FROM eightd.checkpoint_migrations").fetchone()[0]
    # Si la librería añade migraciones, hace falta una migración nueva en app/backend/migrations.
    assert top == len(BasePostgresSaver.MIGRATIONS) - 1


def test_graph_checkpoints_in_postgres_roundtrip(real_settings, settings):
    """El grafo (con LLM/MCP simulados) se ejecuta con el checkpointer de Postgres como
    eightd_app, termina en el interrupt y el estado se recupera desde otra conexión."""
    from solaris.agents.eight_d import graph as g
    from solaris.agents.eight_d.store import open_store
    from solaris.db import connect
    from tests.test_eightd import Harness, _eml

    h = Harness(settings)
    case_id = None

    async def go():
        nonlocal case_id
        async with open_store(real_settings) as store:
            h.store = store  # type: ignore[assignment]
            case_id = await store.create_case(complaint_id=None, created_by="inaki.calidad",
                                              created_role="calidad", source="upload",
                                              filename="c.eml", data=_eml())
            await g.run_case(store, h.deps(), case_id)
        async with open_store(real_settings) as store2:
            return await g.view(store2, case_id), await store2.get_case(case_id)

    try:
        v, row = asyncio.run(go())
        assert v["status"] == "pending_approval" and v["interrupt"]
        assert row.created_by == "inaki.calidad" and row.size == len(_eml())
    finally:
        if case_id:
            with connect(real_settings) as c:
                c.execute("DELETE FROM eightd.checkpoint_writes WHERE thread_id = %s", (case_id,))
                c.execute("DELETE FROM eightd.checkpoint_blobs WHERE thread_id = %s", (case_id,))
                c.execute("DELETE FROM eightd.checkpoints WHERE thread_id = %s", (case_id,))
                c.execute("DELETE FROM eightd.cases WHERE case_id = %s", (case_id,))
