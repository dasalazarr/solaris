"""M4-T1: helper on-behalf-of para que el orquestador 8D (M3-T3) llame al MCP erp-mock."""

import asyncio
import json

import pytest

from solaris.auth.core import Principal
from solaris.mcp_obo import META_ROLE, META_USER, OboError, call_erp_tool, obo_meta
from solaris.settings import REPO_ROOT


class FakeSession:
    def __init__(self):
        self.calls = []

    async def call_tool(self, name, arguments=None, *, meta=None):
        self.calls.append((name, arguments, meta))
        return {"ok": True}


def _call(session, principal, name, args, settings):
    return asyncio.run(call_erp_tool(session, principal, name, args, settings=settings))


def test_meta_keys_match_the_mcp_server_contract():
    server = (REPO_ROOT / "app/mcp/erp_mock/solaris_erp_mock/server.py").read_text()
    assert f'META_USER = "{META_USER}"' in server and f'META_ROLE = "{META_ROLE}"' in server


def test_meta_comes_from_the_authenticated_principal(settings):
    s = FakeSession()
    p = Principal("ander.turno", "planta", "sid")
    assert _call(s, p, "find_lots", {"part_ref": "AR-1003"}, settings) == {"ok": True}
    assert s.calls == [("find_lots", {"part_ref": "AR-1003"},
                        {META_USER: "ander.turno", META_ROLE: "planta"})]


@pytest.mark.parametrize("args", [
    {"_meta": {META_USER: "jon.it", META_ROLE: "admin"}},
    {"lot_code": "L1", "role": "admin"},
    {"lot_code": "L1", "user": "jon.it"},
    {"lot_code": "L1", META_USER: "jon.it"},
    {"lot_code": "L1", "Role": "admin"},
])
def test_identity_in_llm_arguments_is_rejected(settings, args):
    """Los argumentos los propone el LLM: nunca pueden fijar ni sobrescribir la identidad."""
    s = FakeSession()
    with pytest.raises(OboError):
        _call(s, Principal("ander.turno", "planta", "sid"), "get_lot", args, settings)
    assert s.calls == []


def test_requires_a_principal_and_current_role(settings, tmp_path):
    s = FakeSession()
    for bad in ("jon.it", {"user": "jon.it", "role": "admin"}, None):
        with pytest.raises(OboError):
            _call(s, bad, "get_lot", {}, settings)
    # Principal manipulado en memoria (rol que acl.json no le da) → rechazado
    with pytest.raises(OboError):
        obo_meta(Principal("ander.turno", "admin", "sid"), settings)
    # Baja en acl.json entre la autenticación y la llamada → rechazado
    acl = json.loads((REPO_ROOT / "app/data/synthetic/acl.json").read_text())
    del acl["users"]["ander.turno"]
    path = tmp_path / "acl.json"
    path.write_text(json.dumps(acl))
    with pytest.raises(OboError):
        obo_meta(Principal("ander.turno", "planta", "sid"), settings.model_copy(
            update={"acl_file": path}))
    assert s.calls == []
