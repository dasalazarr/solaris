"""Lógica de dominio de las herramientas (Python puro, sin MCP): ACL → SQL fijo → registro.

Todas las consultas son SQL estático con parámetros con nombre (nada de SQL dinámico): lo que se
registra y se muestra en la UI es exactamente lo que se ejecutó. Las columnas se enumeran de forma
explícita (nunca `SELECT *`), de modo que una columna nueva no se expone sin revisarla (PAT-004).
"""

import re
import time
from collections.abc import Callable
from datetime import date
from typing import Any

from solaris_erp_mock.acl import AccessDenied, Caller, ErpAcl
from solaris_erp_mock.audit import AuditSink
from solaris_erp_mock.db import SOURCE, ErpReader, ErpRejected, ErpUnavailable, QueryTrace

PART_REF_RE = r"^[A-Z]{2}-\d{4}$"
CODE_RE = r"^[A-Z0-9][A-Z0-9-]{1,39}$"  # lotes, proveedores, clientes
SHIFTS = ("mañana", "tarde", "noche")
LOT_STATUSES = ("released", "in_stock", "blocked")
COMPLAINT_STATUSES = ("open", "closed")
MAX_PART_REFS = 20
MAX_ROWS = 200


class ToolInputError(ValueError):
    pass


def _match(pattern: str, value: str | None, name: str) -> None:
    if value is not None and not re.fullmatch(pattern, value):
        raise ToolInputError(f"{name} con formato no válido")


def _one_of(options: tuple[str, ...], value: str | None, name: str) -> None:
    if value is not None and value not in options:
        raise ToolInputError(f"{name} debe ser uno de: {', '.join(options)}")


# --- SQL fijo -------------------------------------------------------------------------------

_SQL_LOT = """
SELECT l.lot_code, l.part_ref, l.order_id, l.production_date, l.shift, l.press, l.weld_cell,
       l.qty_produced, l.qty_scrap, l.status,
       l.steel_lot_code, l.wire_lot_code, l.nut_lot_code, l.ecoat_lot_code,
       p.description AS part_description, p.customer_code, p.routing, p.material AS part_material,
       p.thickness_mm, p.special_char, p.char_class, p.die, p.uses_weld_nut
FROM erp.lots l JOIN erp.parts p ON p.ref = l.part_ref
WHERE l.lot_code = %(lot_code)s
"""

_SQL_LOT_MATERIALS = """
SELECT m.lot_code, m.supplier_code, m.material, m.received_date, m.qty, m.unit,
       m.certificate_ok, m.notes
FROM erp.lots l
JOIN erp.material_lots m
  ON m.lot_code IN (l.steel_lot_code, l.wire_lot_code, l.nut_lot_code, l.ecoat_lot_code)
WHERE l.lot_code = %(lot_code)s
"""

_SQL_SHIPMENTS = """
SELECT s.shipment_id, s.lot_code, l.part_ref, s.customer_code, s.ship_date, s.qty
FROM erp.shipments s JOIN erp.lots l ON l.lot_code = s.lot_code
WHERE (%(lot_code)s::text IS NULL OR s.lot_code = %(lot_code)s)
  AND (%(part_ref)s::text IS NULL OR l.part_ref = %(part_ref)s)
  AND (%(from_date)s::date IS NULL OR s.ship_date >= %(from_date)s)
  AND (%(to_date)s::date IS NULL OR s.ship_date <= %(to_date)s)
ORDER BY s.ship_date, s.shipment_id
LIMIT 200
"""

_SQL_FIND_LOTS = """
SELECT l.lot_code, l.part_ref, l.order_id, l.production_date, l.shift, l.press, l.weld_cell,
       l.qty_produced, l.qty_scrap, l.status,
       l.steel_lot_code, l.wire_lot_code, l.nut_lot_code, l.ecoat_lot_code
FROM erp.lots l
WHERE l.part_ref = %(part_ref)s
  AND l.production_date BETWEEN %(from_date)s AND %(to_date)s
  AND (%(wire_lot_code)s::text IS NULL OR l.wire_lot_code = %(wire_lot_code)s)
  AND (%(steel_lot_code)s::text IS NULL OR l.steel_lot_code = %(steel_lot_code)s)
  AND (%(weld_cell)s::text IS NULL OR l.weld_cell = %(weld_cell)s)
  AND (%(shift)s::text IS NULL OR l.shift = %(shift)s)
  AND (%(status)s::text IS NULL OR l.status = %(status)s)
ORDER BY l.production_date, l.lot_code
LIMIT 200
"""

_SCOPE_FILTER = """
WHERE l.part_ref = ANY(%(part_refs)s)
  AND %(material_lot_code)s IN (l.steel_lot_code, l.wire_lot_code, l.nut_lot_code, l.ecoat_lot_code)
"""

_SQL_SCOPE_LOTS = (
    """
SELECT l.lot_code, l.part_ref, l.production_date, l.shift, l.weld_cell, l.qty_produced,
       l.qty_scrap, l.status
FROM erp.lots l"""
    + _SCOPE_FILTER
    + "ORDER BY l.part_ref, l.production_date, l.lot_code"
)

_SQL_SCOPE_SHIPMENTS = (
    """
SELECT s.shipment_id, s.lot_code, l.part_ref, s.customer_code, s.ship_date, s.qty
FROM erp.lots l JOIN erp.shipments s ON s.lot_code = l.lot_code"""
    + _SCOPE_FILTER
    + "ORDER BY l.part_ref, s.ship_date, s.shipment_id"
)

_SQL_SUPPLIER = "SELECT code, name, supplies FROM erp.suppliers WHERE code = %(code)s"

# M3-T3: idioma y plantilla del informe 8D que exige el cliente (el borrador se redacta en él).
_SQL_CUSTOMER = """
SELECT code, name, customer_type, report_template, report_language, containment_hours, report_days
FROM erp.customers WHERE code = %(code)s
"""

# M3-T3: trazabilidad hacia delante de un lote de material (qué piezas lo consumieron). Solo
# atributos de pieza y recuentos de lotes: sin envíos ni cantidades, para elegir las piezas del
# alcance ANTES de consultar envíos (así la contención no devuelve envíos de otros clientes).
_SQL_WHERE_USED = """
SELECT p.ref AS part_ref, p.customer_code, p.weld_cell, p.uses_weld_nut, p.press, p.die,
       count(*) AS lots, min(l.production_date) AS first_production_date,
       max(l.production_date) AS last_production_date
FROM erp.lots l JOIN erp.parts p ON p.ref = l.part_ref
WHERE %(material_lot_code)s IN (l.steel_lot_code, l.wire_lot_code, l.nut_lot_code, l.ecoat_lot_code)
GROUP BY p.ref, p.customer_code, p.weld_cell, p.uses_weld_nut, p.press, p.die
ORDER BY p.ref
LIMIT 200
"""

_SQL_MATERIAL_LOT = """
SELECT lot_code, supplier_code, material, received_date, qty, unit, certificate_ok, notes
FROM erp.material_lots WHERE lot_code = %(lot_code)s
"""

# Columnas explícitas: la familia de recurrencia no existe en el ERP y nunca se expone (PAT-004).
COMPLAINT_COLUMNS = (
    "complaint_id",
    "customer_code",
    "part_ref",
    "lot_code",
    "received_date",
    "defect",
    "qty_affected",
    "status",
    "report_8d_id",
)
_SQL_COMPLAINTS = f"""
SELECT {", ".join("c." + c for c in COMPLAINT_COLUMNS)}
FROM erp.complaints c
WHERE (%(part_ref)s::text IS NULL OR c.part_ref = %(part_ref)s)
  AND (%(customer_code)s::text IS NULL OR c.customer_code = %(customer_code)s)
  AND (%(from_date)s::date IS NULL OR c.received_date >= %(from_date)s)
  AND (%(status)s::text IS NULL OR c.status = %(status)s)
ORDER BY c.received_date, c.complaint_id
LIMIT 200
"""  # noqa: S608  # columnas de una tupla constante del módulo, no de la entrada


# --- Herramientas ---------------------------------------------------------------------------


class ErpTools:
    """Cada método: resuelve la identidad, aplica la ACL por tabla, ejecuta y registra."""

    def __init__(self, reader: ErpReader, acl: ErpAcl, audit: AuditSink) -> None:
        self.reader = reader
        self.acl = acl
        self.audit = audit

    def _call(
        self,
        tool: str,
        identity: tuple[str | None, str | None],
        tables: set[str],
        args: dict[str, Any],
        queries: Callable[[], list[QueryTrace]],
        shape: Callable[[list[list[dict[str, Any]]]], Any],
    ) -> dict[str, Any]:
        t0 = time.perf_counter()
        event: dict[str, Any] = {
            "event": "tool_call",
            "source": SOURCE,
            "tool": tool,
            "user": identity[0],
            "role": identity[1],
            "tables": sorted(tables),
            "args": args,
        }
        try:
            caller = self.acl.resolve(*identity)
            event["role"] = caller.role
            self.acl.check(caller, frozenset(tables))
        except AccessDenied as exc:
            self.audit.emit({**event, "decision": "deny", "reason": str(exc)})
            raise
        try:
            qs = queries()
        except ToolInputError as exc:
            self.audit.emit(
                {**event, "decision": "allow", "outcome": "invalid_input", "reason": str(exc)}
            )
            raise
        trace = [q.as_dict() for q in qs]
        try:
            rows = self.reader.run(qs, tool=tool, caller=caller)
        except (ErpUnavailable, ErpRejected) as exc:
            self.audit.emit(
                {
                    **event,
                    "decision": "allow",
                    "outcome": "error",
                    "error": type(exc).__name__,
                    "query": trace,
                }
            )
            raise
        data = shape(rows)
        self.audit.emit(
            {
                **event,
                "decision": "allow",
                "outcome": "ok",
                "rows": [len(r) for r in rows],
                "duration_ms": round((time.perf_counter() - t0) * 1000, 1),
                "query": trace,
            }
        )
        return {"source": SOURCE, "tool": tool, "query": trace, "data": data}

    # get_lot -------------------------------------------------------------------------------
    def get_lot(self, identity: tuple[str | None, str | None], lot_code: str) -> dict[str, Any]:
        def queries() -> list[QueryTrace]:
            _match(CODE_RE, lot_code, "lot_code")
            p = {"lot_code": lot_code}
            return [QueryTrace(_SQL_LOT, p), QueryTrace(_SQL_LOT_MATERIALS, p)]

        def shape(rows: list[list[dict[str, Any]]]) -> dict[str, Any]:
            if not rows[0]:
                return {"found": False, "lot_code": lot_code}
            r = rows[0][0]
            mats = {m["lot_code"]: m for m in rows[1]}
            part_keys = (
                "part_description",
                "customer_code",
                "routing",
                "part_material",
                "thickness_mm",
                "special_char",
                "char_class",
                "die",
                "uses_weld_nut",
            )
            role_cols = {
                "steel": "steel_lot_code",
                "wire": "wire_lot_code",
                "nut": "nut_lot_code",
                "ecoat": "ecoat_lot_code",
            }
            return {
                "found": True,
                "lot": {k: v for k, v in r.items() if k not in part_keys},
                "part": {"ref": r["part_ref"], **{k: r[k] for k in part_keys}},
                "material_lots": {
                    kind: mats.get(r[col]) if r[col] else None for kind, col in role_cols.items()
                },
            }

        return self._call(
            "get_lot",
            identity,
            {"lots", "parts", "material_lots"},
            {"lot_code": lot_code},
            queries,
            shape,
        )

    # get_shipments -------------------------------------------------------------------------
    def get_shipments(
        self,
        identity: tuple[str | None, str | None],
        lot_code: str | None = None,
        part_ref: str | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> dict[str, Any]:
        args = {
            "lot_code": lot_code,
            "part_ref": part_ref,
            "from_date": from_date,
            "to_date": to_date,
        }

        def queries() -> list[QueryTrace]:
            _match(CODE_RE, lot_code, "lot_code")
            _match(PART_REF_RE, part_ref, "part_ref")
            if (lot_code is None) == (part_ref is None):
                raise ToolInputError("Indica lot_code, o bien part_ref con from_date y to_date")
            if part_ref is not None and (from_date is None or to_date is None):
                raise ToolInputError("Con part_ref son obligatorios from_date y to_date")
            return [QueryTrace(_SQL_SHIPMENTS, dict(args))]

        def shape(rows: list[list[dict[str, Any]]]) -> dict[str, Any]:
            ships = rows[0]
            return {
                "shipments": ships,
                "count": len(ships),
                "qty_total": sum(s["qty"] for s in ships),
            }

        return self._call("get_shipments", identity, {"shipments", "lots"}, args, queries, shape)

    # find_lots -----------------------------------------------------------------------------
    def find_lots(
        self,
        identity: tuple[str | None, str | None],
        part_ref: str,
        from_date: date,
        to_date: date,
        wire_lot_code: str | None = None,
        steel_lot_code: str | None = None,
        weld_cell: str | None = None,
        shift: str | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        args = {
            "part_ref": part_ref,
            "from_date": from_date,
            "to_date": to_date,
            "wire_lot_code": wire_lot_code,
            "steel_lot_code": steel_lot_code,
            "weld_cell": weld_cell,
            "shift": shift,
            "status": status,
        }

        def queries() -> list[QueryTrace]:
            _match(PART_REF_RE, part_ref, "part_ref")
            _match(CODE_RE, wire_lot_code, "wire_lot_code")
            _match(CODE_RE, steel_lot_code, "steel_lot_code")
            _match(CODE_RE, weld_cell, "weld_cell")
            _one_of(SHIFTS, shift, "shift")
            _one_of(LOT_STATUSES, status, "status")
            if from_date > to_date:
                raise ToolInputError("from_date posterior a to_date")
            return [QueryTrace(_SQL_FIND_LOTS, dict(args))]

        def shape(rows: list[list[dict[str, Any]]]) -> dict[str, Any]:
            return {"lots": rows[0], "count": len(rows[0]), "truncated": len(rows[0]) >= MAX_ROWS}

        return self._call("find_lots", identity, {"lots"}, args, queries, shape)

    # containment_scope ---------------------------------------------------------------------
    def containment_scope(
        self, identity: tuple[str | None, str | None], part_refs: list[str], material_lot_code: str
    ) -> dict[str, Any]:
        refs = sorted(set(part_refs))
        args = {"part_refs": refs, "material_lot_code": material_lot_code}

        def queries() -> list[QueryTrace]:
            if not refs or len(refs) > MAX_PART_REFS:
                raise ToolInputError(f"part_refs debe tener entre 1 y {MAX_PART_REFS} referencias")
            for r in refs:
                _match(PART_REF_RE, r, "part_refs")
            _match(CODE_RE, material_lot_code, "material_lot_code")
            return [
                QueryTrace(_SQL_SCOPE_LOTS, dict(args)),
                QueryTrace(_SQL_SCOPE_SHIPMENTS, dict(args)),
            ]

        def shape(rows: list[list[dict[str, Any]]]) -> dict[str, Any]:
            lots, ships = rows
            shipped_by_lot: dict[str, int] = {}
            for s in ships:
                shipped_by_lot[s["lot_code"]] = shipped_by_lot.get(s["lot_code"], 0) + s["qty"]
            for lot in lots:
                # M3-T3 (F05): piezas buenas fabricadas que no se han expedido. Un lote `released`
                # enviado solo en parte tiene piezas en planta que también hay que bloquear.
                ok = lot["qty_produced"] - lot["qty_scrap"]
                lot["qty_ok"] = ok
                lot["qty_shipped"] = shipped_by_lot.get(lot["lot_code"], 0)
                lot["qty_not_shipped"] = max(0, ok - lot["qty_shipped"])
            parts = []
            for ref in refs:
                p_lots = [lot for lot in lots if lot["part_ref"] == ref]
                p_ships = [s for s in ships if s["part_ref"] == ref]
                by_customer: dict[str, dict[str, int]] = {}
                for s in p_ships:
                    c = by_customer.setdefault(s["customer_code"], {"shipments": 0, "qty": 0})
                    c["shipments"] += 1
                    c["qty"] += s["qty"]
                parts.append(
                    {
                        "part_ref": ref,
                        "lots": len(p_lots),
                        "shipments": len(p_ships),
                        "qty_shipped": sum(s["qty"] for s in p_ships),
                        "lots_in_stock": [
                            x["lot_code"] for x in p_lots if x["status"] == "in_stock"
                        ],
                        "lots_blocked": [x["lot_code"] for x in p_lots if x["status"] == "blocked"],
                        "qty_not_shipped": sum(x["qty_not_shipped"] for x in p_lots),
                        "lots_not_shipped": [
                            x["lot_code"] for x in p_lots if x["qty_not_shipped"] > 0
                        ],
                        "by_customer": [
                            {"customer_code": k, **v} for k, v in sorted(by_customer.items())
                        ],
                        "lot_detail": p_lots,
                        "shipment_detail": p_ships,
                    }
                )
            return {"material_lot_code": material_lot_code, "parts": parts}

        return self._call(
            "containment_scope", identity, {"lots", "shipments"}, args, queries, shape
        )

    # material_where_used -------------------------------------------------------------------
    def material_where_used(
        self, identity: tuple[str | None, str | None], material_lot_code: str
    ) -> dict[str, Any]:
        args = {"material_lot_code": material_lot_code}

        def queries() -> list[QueryTrace]:
            _match(CODE_RE, material_lot_code, "material_lot_code")
            return [QueryTrace(_SQL_WHERE_USED, dict(args))]

        def shape(rows: list[list[dict[str, Any]]]) -> dict[str, Any]:
            return {"material_lot_code": material_lot_code, "parts": rows[0], "count": len(rows[0])}

        return self._call("material_where_used", identity, {"lots", "parts"}, args, queries, shape)

    # get_customer --------------------------------------------------------------------------
    def get_customer(self, identity: tuple[str | None, str | None], code: str) -> dict[str, Any]:
        def queries() -> list[QueryTrace]:
            _match(CODE_RE, code, "code")
            return [QueryTrace(_SQL_CUSTOMER, {"code": code})]

        def shape(rows: list[list[dict[str, Any]]]) -> dict[str, Any]:
            return {"found": bool(rows[0]), "customer": rows[0][0] if rows[0] else None}

        return self._call("get_customer", identity, {"customers"}, {"code": code}, queries, shape)

    # get_supplier / get_material_lot -------------------------------------------------------
    def get_supplier(self, identity: tuple[str | None, str | None], code: str) -> dict[str, Any]:
        def queries() -> list[QueryTrace]:
            _match(CODE_RE, code, "code")
            return [QueryTrace(_SQL_SUPPLIER, {"code": code})]

        def shape(rows: list[list[dict[str, Any]]]) -> dict[str, Any]:
            return {"found": bool(rows[0]), "supplier": rows[0][0] if rows[0] else None}

        return self._call("get_supplier", identity, {"suppliers"}, {"code": code}, queries, shape)

    def get_material_lot(
        self, identity: tuple[str | None, str | None], lot_code: str
    ) -> dict[str, Any]:
        def queries() -> list[QueryTrace]:
            _match(CODE_RE, lot_code, "lot_code")
            return [QueryTrace(_SQL_MATERIAL_LOT, {"lot_code": lot_code})]

        def shape(rows: list[list[dict[str, Any]]]) -> dict[str, Any]:
            return {"found": bool(rows[0]), "material_lot": rows[0][0] if rows[0] else None}

        return self._call(
            "get_material_lot", identity, {"material_lots"}, {"lot_code": lot_code}, queries, shape
        )

    # search_complaints ---------------------------------------------------------------------
    def search_complaints(
        self,
        identity: tuple[str | None, str | None],
        part_ref: str | None = None,
        customer_code: str | None = None,
        from_date: date | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        args = {
            "part_ref": part_ref,
            "customer_code": customer_code,
            "from_date": from_date,
            "status": status,
        }

        def queries() -> list[QueryTrace]:
            _match(PART_REF_RE, part_ref, "part_ref")
            _match(CODE_RE, customer_code, "customer_code")
            _one_of(COMPLAINT_STATUSES, status, "status")
            return [QueryTrace(_SQL_COMPLAINTS, dict(args))]

        def shape(rows: list[list[dict[str, Any]]]) -> dict[str, Any]:
            # Proyección explícita: aunque alguien añada columnas, solo salen las permitidas.
            complaints = [{k: r[k] for k in COMPLAINT_COLUMNS} for r in rows[0]]
            return {"complaints": complaints, "count": len(complaints)}

        return self._call("search_complaints", identity, {"complaints"}, args, queries, shape)


__all__ = ["AccessDenied", "Caller", "ErpTools", "ToolInputError"]
