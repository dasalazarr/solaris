"""Humo del protocolo MCP: cliente en memoria y cliente stdio."""

import sys

import pytest
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.shared.memory import create_connected_server_and_client_session

from solaris_erp_mock.config import PROJECT_DIR
from solaris_erp_mock.server import build_server

EXPECTED = {
    "get_lot",
    "get_shipments",
    "find_lots",
    "containment_scope",
    "get_supplier",
    "get_material_lot",
    "search_complaints",
    "material_where_used",
    "get_customer",
}
CALIDAD_META = {"solaris/user": "inaki.calidad", "solaris/role": "calidad"}
PLANTA_META = {"solaris/user": "ander.turno", "solaris/role": "planta"}


@pytest.fixture
def server(settings, sink, tools):
    return build_server(settings, sink, tools)


@pytest.mark.anyio
async def test_list_tools_read_only_without_identity_args(server):
    async with create_connected_server_and_client_session(server) as client:
        listed = (await client.list_tools()).tools
    assert {t.name for t in listed} == EXPECTED
    for t in listed:
        assert t.annotations.readOnlyHint is True and t.annotations.destructiveHint is False
        props = set(t.inputSchema.get("properties", {}))
        assert not props & {"user", "role", "ctx"}, t.name  # la identidad no la pone el LLM


@pytest.mark.anyio
async def test_call_tool_denied_without_meta_and_for_planta(server, sink):
    async with create_connected_server_and_client_session(server) as client:
        r1 = await client.call_tool("search_complaints", {})
        r2 = await client.call_tool(
            "get_shipments", {"lot_code": "L26241-AR1003-02"}, meta=PLANTA_META
        )
    assert r1.isError and "Acceso denegado" in r1.content[0].text
    assert r2.isError and "shipments" in r2.content[0].text
    assert [e["decision"] for e in sink.events] == ["deny", "deny"]


@pytest.mark.anyio
async def test_write_tool_does_not_exist_and_is_logged(server, sink):
    async with create_connected_server_and_client_session(server) as client:
        r = await client.call_tool(
            "update_lot", {"lot_code": "L26241-AR1003-02", "status": "released"}, meta=CALIDAD_META
        )
    assert r.isError and "solo lectura" in r.content[0].text
    ev = sink.events[-1]
    assert ev["event"] == "write_attempt" and ev["tool"] == "update_lot"
    assert ev["user"] == "inaki.calidad"


@pytest.mark.anyio
async def test_call_tool_containment_via_protocol(db, server):
    async with create_connected_server_and_client_session(server) as client:
        r = await client.call_tool(
            "containment_scope",
            {"part_refs": ["AR-1003", "AR-1004"], "material_lot_code": "S-GOIE-260117"},
            meta=CALIDAD_META,
        )
    assert not r.isError, r.content
    body = r.structuredContent
    assert body["source"] == "erp-mock" and body["query"]
    assert [p["qty_shipped"] for p in body["data"]["parts"]] == [10475, 7982]


@pytest.mark.anyio
async def test_stdio_transport_lists_tools():
    from mcp import ClientSession

    params = StdioServerParameters(
        command=sys.executable, args=["-m", "solaris_erp_mock.server"], cwd=str(PROJECT_DIR)
    )
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        names = {t.name for t in (await session.list_tools()).tools}
    assert names == EXPECTED
