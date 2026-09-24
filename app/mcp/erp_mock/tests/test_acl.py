"""ACL por rol (on-behalf-of) — sin BD: la denegación ocurre antes de tocar la BD."""

import pytest

from solaris_erp_mock.acl import AccessDenied, ErpAcl
from solaris_erp_mock.config import DEFAULT_ACL_FILE

from .conftest import PLANTA


def test_planta_get_shipments_denied_and_logged(tools, sink):
    with pytest.raises(AccessDenied, match="shipments"):
        tools.get_shipments(PLANTA, lot_code="L26241-AR1003-02")
    [ev] = sink.events
    assert ev["event"] == "tool_call" and ev["tool"] == "get_shipments"
    assert ev["decision"] == "deny" and ev["user"] == "ander.turno" and ev["role"] == "planta"
    assert "query" not in ev  # no se llegó a ejecutar nada


@pytest.mark.parametrize(
    "identity",
    [(None, None), ("", "calidad"), ("intruso", "admin"), ("ander.turno", "admin")],
)
def test_bad_identity_denied(tools, sink, identity):
    with pytest.raises(AccessDenied):
        tools.search_complaints(identity)
    assert sink.events[-1]["decision"] == "deny"


def test_acl_matrix_from_repo():
    acl = ErpAcl.load(DEFAULT_ACL_FILE)
    assert acl.tables["planta"] == frozenset({"lots", "production_orders"})
    assert acl.tables["auditor"] == frozenset({"complaints"})
    assert acl.tables["calidad"] is None and acl.tables["admin"] is None
    planta = acl.resolve("ander.turno", None)
    acl.check(planta, frozenset({"lots"}))
    with pytest.raises(AccessDenied):
        acl.check(planta, frozenset({"lots", "parts"}))


def test_invalid_input_rejected_before_db(tools, sink):
    from solaris_erp_mock.tools import ToolInputError

    with pytest.raises(ToolInputError):
        tools.get_lot(("inaki.calidad", None), lot_code="x'; DROP TABLE erp.lots;--")
    assert sink.events[-1]["outcome"] == "invalid_input"
