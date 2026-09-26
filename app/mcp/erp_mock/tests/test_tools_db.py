"""Herramientas contra el Postgres real, conectando como erp_reader."""

import psycopg
import pytest
from psycopg import sql

from solaris_erp_mock.acl import Caller, ErpAcl
from solaris_erp_mock.db import ErpRejected, QueryTrace, db_role_for

from .conftest import AUDITOR, CALIDAD


def test_containment_scope_matches_smoke_query_4(db):
    res = db.containment_scope(CALIDAD, ["AR-1003", "AR-1004"], "S-GOIE-260117")
    parts = {p["part_ref"]: p for p in res["data"]["parts"]}
    a3, a4 = parts["AR-1003"], parts["AR-1004"]
    assert (a3["lots"], a3["shipments"], a3["qty_shipped"], len(a3["lots_in_stock"])) == (
        7,
        9,
        10475,
        1,
    )
    assert (a4["lots"], a4["shipments"], a4["qty_shipped"], len(a4["lots_in_stock"])) == (
        5,
        8,
        7982,
        0,
    )
    assert {c["customer_code"] for c in a3["by_customer"]} == {"C-OEMN"}


def test_containment_scope_qty_not_shipped(db):
    """M3-T3 (F05): piezas buenas sin expedir por lote, sin tocar el seed (PAT-006).

    L26260-AR1004-01 está `released` pero solo se expidieron 1.180 de 2.361 buenas (2.400 − 39):
    1.181 piezas siguen en planta. L26266-AR1003-01 (in_stock) tiene 2.273 buenas sin expedir."""
    res = db.containment_scope(CALIDAD, ["AR-1003", "AR-1004"], "S-GOIE-260117")
    parts = {p["part_ref"]: p for p in res["data"]["parts"]}
    lots = {x["lot_code"]: x for p in parts.values() for x in p["lot_detail"]}
    l60 = lots["L26260-AR1004-01"]
    assert (l60["status"], l60["qty_ok"], l60["qty_shipped"], l60["qty_not_shipped"]) == (
        "released",
        2361,
        1180,
        1181,
    )
    assert lots["L26266-AR1003-01"]["qty_not_shipped"] == 2273
    assert lots["L26241-AR1003-02"]["qty_not_shipped"] == 0
    assert parts["AR-1004"]["lots_not_shipped"] == ["L26260-AR1004-01"]
    assert parts["AR-1003"]["lots_not_shipped"] == ["L26266-AR1003-01"]
    assert (parts["AR-1003"]["qty_not_shipped"], parts["AR-1004"]["qty_not_shipped"]) == (
        2273,
        1181,
    )
    # Invariante: buenas = enviadas + sin expedir en todos los lotes del alcance.
    assert all(x["qty_ok"] == x["qty_shipped"] + x["qty_not_shipped"] for x in lots.values())
    assert "qty_scrap" in res["query"][0]["sql"]


def test_material_where_used_and_customer(db):
    res = db.material_where_used(CALIDAD, "S-BIDA-260136")
    refs = {p["part_ref"]: p for p in res["data"]["parts"]}
    assert set(refs) == {"AR-1006", "AR-1010"}
    assert all(p["uses_weld_nut"] and p["customer_code"] == "C-OEMN" for p in refs.values())
    assert "shipments" not in res["query"][0]["sql"]  # sin envíos: solo elige piezas
    wire = {
        p["part_ref"]: p for p in db.material_where_used(CALIDAD, "S-GOIE-260117")["data"]["parts"]
    }
    assert {r for r, p in wire.items() if p["weld_cell"] == "CR-01"} == {"AR-1003", "AR-1004"}
    c = db.get_customer(CALIDAD, "C-RIBE")["data"]
    assert c["found"] and c["customer"]["report_language"] == "ES"
    assert db.get_customer(CALIDAD, "C-NADA")["data"]["found"] is False


def test_new_tools_denied_for_planta_and_auditor(db, sink):
    from solaris_erp_mock.acl import AccessDenied

    from .conftest import PLANTA

    with pytest.raises(AccessDenied):
        db.get_customer(PLANTA, "C-OEMN")
    with pytest.raises(AccessDenied):
        db.material_where_used(AUDITOR, "S-GOIE-260117")
    assert sink.events[-1]["decision"] == "deny"


def test_get_lot_familia_a(db):
    res = db.get_lot(CALIDAD, "L26241-AR1003-02")
    d = res["data"]
    assert d["found"] is True
    assert d["lot"]["wire_lot_code"] == "S-GOIE-260117"
    assert d["lot"]["weld_cell"] == "CR-01" and d["lot"]["shift"] == "noche"
    assert d["material_lots"]["wire"]["lot_code"] == "S-GOIE-260117"
    assert d["material_lots"]["wire"]["supplier_code"] == "S-GOIE"
    assert d["part"]["ref"] == "AR-1003"


def test_response_includes_query_and_source(db, sink):
    res = db.get_lot(CALIDAD, "L26241-AR1003-02")
    assert res["source"] == "erp-mock"
    assert res["query"] and all({"sql", "params"} <= q.keys() for q in res["query"])
    assert "FROM erp.lots" in res["query"][0]["sql"]
    assert res["query"][0]["params"] == {"lot_code": "L26241-AR1003-02"}
    ev = sink.events[-1]
    assert ev["decision"] == "allow" and ev["outcome"] == "ok" and ev["query"] == res["query"]


def test_auditor_search_complaints_allowed(db, sink):
    res = db.search_complaints(AUDITOR, part_ref="AR-1003")
    assert res["data"]["count"] >= 4
    assert any(c["report_8d_id"] for c in res["data"]["complaints"])
    assert sink.events[-1]["decision"] == "allow" and sink.events[-1]["role"] == "auditor"


def test_search_complaints_never_exposes_family(db):
    res = db.search_complaints(CALIDAD)
    assert res["data"]["count"] == 20

    def keys(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                yield k
                yield from keys(v)
        elif isinstance(obj, list):
            for v in obj:
                yield from keys(v)

    bad = [k for k in keys(res) if "family" in k.lower() or "recurren" in k.lower()]
    assert bad == []


def test_other_tools(db):
    assert db.get_supplier(CALIDAD, "S-GOIE")["data"]["found"] is True
    ml = db.get_material_lot(CALIDAD, "S-GOIE-260117")["data"]["material_lot"]
    assert ml["supplier_code"] == "S-GOIE"
    lots = db.find_lots(
        CALIDAD, "AR-1003", "2026-01-01", "2026-12-31", wire_lot_code="S-GOIE-260117"
    )["data"]
    assert lots["count"] == 7
    ships = db.get_shipments(CALIDAD, lot_code="L26241-AR1003-02")["data"]
    assert ships["count"] >= 1


def test_planta_find_lots_allowed(db):
    from .conftest import PLANTA

    res = db.find_lots(PLANTA, "AR-1003", "2026-01-01", "2026-12-31", shift="noche")
    assert res["data"]["count"] >= 1


# --- Solo lectura por diseño ----------------------------------------------------------------


def test_write_through_reader_rejected_and_logged(db, sink):
    q = QueryTrace(
        "UPDATE erp.lots SET status = 'released' WHERE lot_code = %(c)s", {"c": "L26241-AR1003-02"}
    )
    with pytest.raises(ErpRejected):
        db.reader.run([q], tool="test_write", caller=None)
    ev = sink.events[-1]
    assert (
        ev["event"] == "write_rejected" and ev["sqlstate"] == "25006"
    )  # read_only_sql_transaction


def test_write_rejected_even_without_read_only_tx(raw_reader_conn):
    """Aunque se fuerce READ WRITE en la sesión, el rol no tiene privilegios de escritura."""
    with pytest.raises(psycopg.errors.ReadOnlySqlTransaction):
        raw_reader_conn.execute("INSERT INTO erp.suppliers VALUES ('S-X', 'x', 'x')")
    raw_reader_conn.execute("SET SESSION CHARACTERISTICS AS TRANSACTION READ WRITE")
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        raw_reader_conn.execute("INSERT INTO erp.suppliers VALUES ('S-X', 'x', 'x')")
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        raw_reader_conn.execute("UPDATE erp.lots SET status = 'released'")


def test_reader_cannot_read_rag(raw_reader_conn):
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        raw_reader_conn.execute("SELECT count(*) FROM rag.chunks")
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        raw_reader_conn.execute("SELECT count(*) FROM rag.visible_chunks('admin')")


def test_reader_role_attributes(raw_reader_conn):
    row = raw_reader_conn.execute(
        "SELECT rolsuper, rolcreaterole, rolcreatedb, rolbypassrls, rolreplication"
        " FROM pg_roles WHERE rolname = current_user"
    ).fetchone()
    assert row == (False, False, False, False, False)
    assert raw_reader_conn.execute("SELECT current_user").fetchone()[0] == "erp_reader"


# --- ACL del ERP en la BD (M4-T1, PAT-005, migración 007) ------------------------------------


def _erp_tables(conn) -> list[str]:
    return [
        r[0]
        for r in conn.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'erp' ORDER BY 1"
        ).fetchall()
    ]


def _readable(conn, db_role: str, tables: list[str]) -> set[str]:
    ok: set[str] = set()
    for t in tables:
        try:
            with conn.transaction():
                conn.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(db_role)))
                conn.execute(sql.SQL("SELECT 1 FROM erp.{} LIMIT 0").format(sql.Identifier(t)))
            ok.add(t)
        except psycopg.errors.InsufficientPrivilege:
            pass
    return ok


def test_reader_without_business_role_reads_nothing(raw_reader_conn):
    for t in _erp_tables(raw_reader_conn):
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            raw_reader_conn.execute(
                sql.SQL("SELECT 1 FROM erp.{} LIMIT 0").format(sql.Identifier(t))
            )


def test_db_grants_match_acl_json(raw_reader_conn, settings):
    """La matriz de la migración 007 coincide con acl.json → erp_tables (detecta deriva)."""
    acl = ErpAcl.load(settings.erp_acl_file)
    tables = _erp_tables(raw_reader_conn)
    assert tables
    for role, allowed in acl.tables.items():
        expected = set(tables) if allowed is None else set(allowed)
        assert _readable(raw_reader_conn, db_role_for(role), tables) == expected, role


def test_reader_cannot_escalate_to_privileged_roles(raw_reader_conn):
    for role in ("solaris", "solaris_app", "audit_writer", "audit_owner", "pg_read_all_data"):
        with pytest.raises(psycopg.errors.InsufficientPrivilege), raw_reader_conn.transaction():
            raw_reader_conn.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))


def test_db_blocks_table_even_if_python_acl_is_bypassed(db, sink):
    """Segunda capa: aunque se saltara ErpAcl.check, la BD no deja a planta leer envíos."""
    q = QueryTrace("SELECT count(*) FROM erp.shipments", {})
    with pytest.raises(ErpRejected, match="no tiene permiso"):
        db.reader.run([q], tool="test_bypass", caller=Caller("ander.turno", "planta"))
    ev = sink.events[-1]
    assert ev["event"] == "db_denied" and ev["db_role"] == "erp_planta"
    assert ev["sqlstate"] == "42501"
    ok = db.reader.run(
        [QueryTrace("SELECT count(*) AS n FROM erp.lots", {})],
        tool="t",
        caller=Caller("ander.turno", "planta"),
    )
    assert ok[0][0]["n"] > 0


@pytest.mark.parametrize("role", ["fantasma", "planta; RESET ROLE", "Admin", ""])
def test_unknown_or_malformed_business_role_rejected(db, role):
    with pytest.raises(ErpRejected):
        db.reader.run([QueryTrace("SELECT 1", {})], tool="t", caller=Caller("x", role))
