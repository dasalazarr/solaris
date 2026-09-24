"""M4-T2 (F08): el MCP erp-mock anexa tool_call / tool_denied / write_attempt en audit.events.

Escribe en la BD de tests `solaris_test` (la crea/recrea el backend:
`cd app/backend && uv run python -m solaris.audit.testdb`, o su suite de tests). Para leer lo
escrito, el test usa `audit_reader` (el proceso MCP en producción solo conoce `audit_writer`).
"""

from collections.abc import Iterator
from itertools import pairwise

import psycopg
import pytest
from mcp.shared.memory import create_connected_server_and_client_session
from psycopg.rows import dict_row
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from solaris_erp_mock.acl import ErpAcl
from solaris_erp_mock.audit import AuditUnavailable, PgAuditSink, event_type_for, to_row
from solaris_erp_mock.config import REPO_ROOT, ErpSettings
from solaris_erp_mock.db import ErpReader
from solaris_erp_mock.server import build_server
from solaris_erp_mock.tools import ErpTools

TEST_DB = "solaris_test"
CALIDAD_META = {"solaris/user": "inaki.calidad", "solaris/role": "calidad"}
PLANTA_META = {"solaris/user": "ander.turno", "solaris/role": "planta"}


class _ReaderSettings(BaseSettings):
    """Solo tests: credenciales de audit_reader para comprobar lo escrito."""

    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env", env_file_encoding="utf-8", extra="ignore"
    )
    audit_reader_password: SecretStr | None = None


# --- sin BD -----------------------------------------------------------------------------------


def test_event_mapping_and_scrub():
    assert event_type_for({"event": "tool_call", "decision": "allow"}) == "tool_call"
    assert event_type_for({"event": "tool_call", "decision": "deny"}) == "tool_denied"
    assert event_type_for({"event": "write_attempt"}) == "write_attempt"
    assert event_type_for({"event": "write_rejected"}) == "write_attempt"
    assert event_type_for({"event": "unknown_tool"}) == "tool_denied"
    assert event_type_for({"event": "schema_invalid"}) == "tool_denied"
    with pytest.raises(ValueError):
        event_type_for({"event": "whatever"})
    row = to_row(
        {"event": "tool_call", "decision": "allow", "user": "u", "role": "calidad",
         "args": {"password": "p4ss", "note": "Bearer abcdefghijkl sk-or-v1-1234567890"}}
    )
    assert row[:3] == ("u", "calidad", "tool_call") and row[4] == "erp-mock"
    payload = row[7].obj
    assert payload["args"]["password"] == "[REDACTED]"
    note = payload["args"]["note"]
    assert "abcdefghijkl" not in note and "sk-or-v1" not in note


def test_sink_fails_closed_without_password():
    with pytest.raises(AuditUnavailable):
        PgAuditSink(ErpSettings(_env_file=None))


# --- con BD -----------------------------------------------------------------------------------


@pytest.fixture
def audit_settings(settings: ErpSettings) -> ErpSettings:
    if settings.audit_writer_password is None:
        pytest.skip("Falta AUDIT_WRITER_PASSWORD en .env")
    return settings.model_copy(update={"audit_db_name": TEST_DB})


@pytest.fixture
def reader(audit_settings: ErpSettings) -> Iterator[psycopg.Connection]:
    pw = _ReaderSettings().audit_reader_password
    if pw is None:
        pytest.skip("Falta AUDIT_READER_PASSWORD en .env")
    try:
        conn = psycopg.connect(
            host=audit_settings.erp_db_host, port=audit_settings.solaris_db_port, dbname=TEST_DB,
            user="audit_reader", password=pw.get_secret_value(), autocommit=True,
            row_factory=dict_row,
        )
    except psycopg.OperationalError as exc:
        pytest.skip(f"{TEST_DB} no disponible (ejecuta antes solaris.audit.testdb): {exc}")
    with conn:
        yield conn


@pytest.fixture
def pg_server(_db_ok, audit_settings, settings):
    sink = PgAuditSink(audit_settings)
    tools = ErpTools(ErpReader(settings, sink), ErpAcl.load(settings.erp_acl_file), sink)
    yield build_server(settings, sink, tools)
    sink.close()


def _events_after(reader: psycopg.Connection, start: int) -> list[dict]:
    return reader.execute(
        "SELECT id, actor_user, actor_role, event_type, source, payload, prev_hash, hash "
        "FROM audit.events WHERE id > %s ORDER BY id",
        (start,),
    ).fetchall()


@pytest.mark.anyio
async def test_mcp_emits_tool_call_and_denials_to_audit_events(pg_server, reader):
    start = reader.execute("SELECT coalesce(max(id), 0) AS m FROM audit.events").fetchone()["m"]
    async with create_connected_server_and_client_session(pg_server) as client:
        ok = await client.call_tool(
            "containment_scope",
            {"part_refs": ["AR-1003"], "material_lot_code": "S-GOIE-260117"},
            meta=CALIDAD_META,
        )
        denied = await client.call_tool(
            "get_shipments", {"lot_code": "L26241-AR1003-02"}, meta=PLANTA_META
        )
        write = await client.call_tool(
            "update_lot", {"lot_code": "L26241-AR1003-02", "status": "released"},
            meta=CALIDAD_META,
        )
        bad = await client.call_tool("get_lot", {"lot_code": "x'; DROP TABLE"}, meta=CALIDAD_META)
    assert not ok.isError and denied.isError and write.isError and bad.isError

    ev = _events_after(reader, start)
    assert [e["event_type"] for e in ev] == [
        "tool_call", "tool_denied", "write_attempt", "tool_denied"
    ]
    assert all(e["source"] == "erp-mock" for e in ev)
    call, deny, wr, schema = ev
    assert (call["actor_user"], call["actor_role"]) == ("inaki.calidad", "calidad")
    assert call["payload"]["tool"] == "containment_scope" and call["payload"]["outcome"] == "ok"
    assert call["payload"]["query"] and call["payload"]["decision"] == "allow"
    assert call["payload"]["rows"] and sum(call["payload"]["rows"]) > 0  # consulta con datos
    assert deny["actor_role"] == "planta" and "shipments" in deny["payload"]["reason"]
    assert wr["payload"]["tool"] == "update_lot" and wr["payload"]["decision"] == "deny"
    assert schema["payload"]["mcp_event"] == "schema_invalid"
    assert schema["payload"]["errors"][0]["loc"] == ["lot_code"]
    assert "DROP TABLE" not in str(schema["payload"])  # no se guarda el valor recibido
    for a, b in pairwise(ev):
        assert b["prev_hash"] == a["hash"]


@pytest.mark.anyio
async def test_mcp_fails_closed_if_audit_unavailable(_db_ok, audit_settings, settings):
    broken = audit_settings.model_copy(update={"audit_writer_password": SecretStr("wrong-pass")})
    sink = PgAuditSink(broken)
    tools = ErpTools(ErpReader(settings, sink), ErpAcl.load(settings.erp_acl_file), sink)
    server = build_server(settings, sink, tools)
    async with create_connected_server_and_client_session(server) as client:
        r = await client.call_tool("get_lot", {"lot_code": "L26241-AR1003-02"}, meta=CALIDAD_META)
    assert r.isError and "Audit no disponible" in r.content[0].text
    assert "L26241" not in r.content[0].text  # no se devuelven datos sin rastro
