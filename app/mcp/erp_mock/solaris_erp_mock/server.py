"""Servidor MCP erp-mock (FastMCP, transporte stdio).

Uso (desde app/mcp/erp_mock):  uv run solaris-erp-mock      # stdio

Identidad on-behalf-of: el usuario y el rol NO son argumentos de las herramientas (el LLM no los ve
en el esquema ni puede rellenarlos). El backend orquestador los deriva del usuario autenticado y
los inyecta en el `_meta` de cada `tools/call`:

    session.call_tool("get_lot", {"lot_code": ...},
                      meta={"solaris/user": "inaki.calidad", "solaris/role": "calidad"})

Sin `_meta` válido, toda llamada se deniega. Solo se ofrece stdio: el único cliente es el backend,
que lanza este proceso. Un transporte HTTP exigiría autenticar al cliente antes de fiarse de `_meta`
(decisión M4-T1: se mantiene solo stdio; ver raw/sessions/2026-09-25_security_M4-T1.md). En el
backend, `_meta` lo construye únicamente `solaris.mcp_obo` desde el usuario autenticado. Además,
desde M4-T1 la BD aplica la ACL por tabla: cada transacción hace `SET LOCAL ROLE erp_<rol>` (db.py).
"""

import argparse
import re
import sys
from datetime import date
from typing import Annotated, Any

import anyio
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import Field, ValidationError

from solaris_erp_mock.acl import AccessDenied, ErpAcl
from solaris_erp_mock.audit import AuditSink, AuditUnavailable, JsonlAuditSink, PgAuditSink
from solaris_erp_mock.config import ErpSettings, get_settings
from solaris_erp_mock.db import SOURCE, ErpReader, ErpRejected, ErpUnavailable
from solaris_erp_mock.tools import (
    CODE_RE,
    COMPLAINT_STATUSES,
    LOT_STATUSES,
    MAX_PART_REFS,
    PART_REF_RE,
    SHIFTS,
    ErpTools,
    ToolInputError,
)

META_USER = "solaris/user"
META_ROLE = "solaris/role"
_WRITE_VERB_RE = re.compile(
    r"^(insert|update|delete|create|set|write|modify|drop|alter|put|patch|upsert|remove|close|release|block)",
    re.IGNORECASE,
)

READ_ONLY = ToolAnnotations(
    readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False
)

LotCode = Annotated[
    str, Field(pattern=CODE_RE, description="Código de lote, p. ej. L26241-AR1003-02")
]
PartRef = Annotated[
    str, Field(pattern=PART_REF_RE, description="Referencia de pieza, p. ej. AR-1003")
]
Code = Annotated[str, Field(pattern=CODE_RE)]


def _identity(ctx: Context) -> tuple[str | None, str | None]:
    meta = ctx.request_context.meta
    extra: dict[str, Any] = (meta.model_extra or {}) if meta is not None else {}
    user, role = extra.get(META_USER), extra.get(META_ROLE)
    return (user if isinstance(user, str) else None, role if isinstance(role, str) else None)


class ErpMockServer(FastMCP):
    """FastMCP que además registra llamadas a herramientas inexistentes (p. ej. `update_lot`)."""

    audit: AuditSink

    def _identity_or_none(self) -> tuple[str | None, str | None]:
        try:
            return _identity(self.get_context())
        except Exception:  # sin contexto de petición
            return (None, None)

    def _emit(self, event: dict[str, Any]) -> None:
        try:
            self.audit.emit(event)
        except AuditUnavailable as exc:
            raise ToolError("Audit no disponible: la llamada no se ejecuta.") from exc

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        if self._tool_manager.get_tool(name) is None:
            user, role = self._identity_or_none()
            self._emit(
                {
                    "event": "write_attempt" if _WRITE_VERB_RE.match(name) else "unknown_tool",
                    "source": SOURCE,
                    "tool": name,
                    "user": user,
                    "role": role,
                    "decision": "deny",
                    "reason": "herramienta inexistente: el ERP es de solo lectura",
                    "arg_names": sorted(str(k) for k in (arguments or {}))[:20],
                }
            )
            raise ToolError(f"Herramienta desconocida: {name}. El ERP es de solo lectura.")
        try:
            return await super().call_tool(name, arguments)
        except ToolError as exc:
            # Rechazo por esquema (pydantic) antes de llegar a ErpTools: también se registra
            # (punto 5 de M3-T1). Solo ubicación y tipo del error, no los valores recibidos.
            if isinstance(exc.__cause__, ValidationError):
                user, role = self._identity_or_none()
                self._emit(
                    {
                        "event": "schema_invalid",
                        "source": SOURCE,
                        "tool": name,
                        "user": user,
                        "role": role,
                        "decision": "deny",
                        "reason": "argumentos no válidos según el esquema de la herramienta",
                        "errors": [
                            {"loc": [str(p) for p in e.get("loc", ())], "type": e.get("type")}
                            for e in exc.__cause__.errors()[:20]
                        ],
                    }
                )
            raise


def build_server(
    settings: ErpSettings | None = None,
    audit: AuditSink | None = None,
    tools: ErpTools | None = None,
) -> ErpMockServer:
    s = settings or get_settings()
    if audit is not None:
        sink = audit
    elif s.erp_mock_audit_sink == "jsonl":
        sink = JsonlAuditSink(s.erp_mock_log_dir)  # solo dev: sin integridad
    else:
        sink = PgAuditSink(s)  # falla al arrancar si falta AUDIT_WRITER_PASSWORD
    t = tools or ErpTools(ErpReader(s, sink), ErpAcl.load(s.erp_acl_file), sink)

    mcp = ErpMockServer(
        "solaris-erp-mock",
        instructions=(
            "ERP mock de Componentes Arga S.L. (datos sintéticos). Solo lectura. Cada respuesta "
            "incluye `query` (SQL parametrizado ejecutado) y `source`. Si una herramienta falla, "
            "dilo: no inventes datos."
        ),
    )
    mcp.audit = sink

    async def run(fn: Any, ctx: Context, **kwargs: Any) -> dict[str, Any]:
        identity = _identity(ctx)
        try:
            return await anyio.to_thread.run_sync(lambda: fn(identity, **kwargs))
        except AccessDenied as exc:
            raise ToolError(f"Acceso denegado: {exc}") from exc
        except ToolInputError as exc:
            raise ToolError(f"Entrada no válida: {exc}") from exc
        except ErpUnavailable as exc:
            raise ToolError(f"ERP no disponible: {exc}. No hay datos; no los inventes.") from exc
        except ErpRejected as exc:
            raise ToolError(str(exc)) from exc
        except AuditUnavailable as exc:
            raise ToolError("Audit no disponible: la llamada no se ejecuta.") from exc

    @mcp.tool(annotations=READ_ONLY)
    async def get_lot(lot_code: LotCode, ctx: Context) -> dict[str, Any]:
        """Lote de producción con su pieza y sus lotes de material (acero, hilo, tuerca, e-coat) y
        las notas de recepción. Tablas: lots, parts, material_lots."""
        return await run(t.get_lot, ctx, lot_code=lot_code)

    @mcp.tool(annotations=READ_ONLY)
    async def get_shipments(
        ctx: Context,
        lot_code: LotCode | None = None,
        part_ref: PartRef | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> dict[str, Any]:
        """Envíos (albaranes) de un lote, o de una pieza en un rango de fechas de envío.
        Indica lot_code, o bien part_ref + from_date + to_date. Tablas: shipments, lots."""
        return await run(
            t.get_shipments,
            ctx,
            lot_code=lot_code,
            part_ref=part_ref,
            from_date=from_date,
            to_date=to_date,
        )

    @mcp.tool(annotations=READ_ONLY)
    async def find_lots(
        part_ref: PartRef,
        from_date: date,
        to_date: date,
        ctx: Context,
        wire_lot_code: Code | None = None,
        steel_lot_code: Code | None = None,
        weld_cell: Code | None = None,
        shift: Annotated[str | None, Field(description=f"Uno de {SHIFTS}")] = None,
        status: Annotated[str | None, Field(description=f"Uno de {LOT_STATUSES}")] = None,
    ) -> dict[str, Any]:
        """Lotes de una pieza fabricados en un rango de fechas, con filtros opcionales (hilo,
        acero, célula de soldadura, turno, estado). Sirve para acotar la contención. Tabla: lots."""
        return await run(
            t.find_lots,
            ctx,
            part_ref=part_ref,
            from_date=from_date,
            to_date=to_date,
            wire_lot_code=wire_lot_code,
            steel_lot_code=steel_lot_code,
            weld_cell=weld_cell,
            shift=shift,
            status=status,
        )

    @mcp.tool(annotations=READ_ONLY)
    async def containment_scope(
        part_refs: Annotated[list[PartRef], Field(min_length=1, max_length=MAX_PART_REFS)],
        material_lot_code: Code,
        ctx: Context,
    ) -> dict[str, Any]:
        """Alcance de la contención: lotes de las piezas indicadas que consumieron el lote de
        material, envíos y piezas enviadas por cliente, y lotes aún en stock. Tablas: lots,
        shipments."""
        return await run(
            t.containment_scope, ctx, part_refs=part_refs, material_lot_code=material_lot_code
        )

    @mcp.tool(annotations=READ_ONLY)
    async def get_supplier(code: Code, ctx: Context) -> dict[str, Any]:
        """Proveedor por código (p. ej. S-GOIE). Tabla: suppliers."""
        return await run(t.get_supplier, ctx, code=code)

    @mcp.tool(annotations=READ_ONLY)
    async def get_material_lot(lot_code: Code, ctx: Context) -> dict[str, Any]:
        """Lote de material recibido (proveedor, material, certificado, notas de recepción).
        Tabla: material_lots."""
        return await run(t.get_material_lot, ctx, lot_code=lot_code)

    @mcp.tool(annotations=READ_ONLY)
    async def search_complaints(
        ctx: Context,
        part_ref: PartRef | None = None,
        customer_code: Code | None = None,
        from_date: date | None = None,
        status: Annotated[str | None, Field(description=f"Uno de {COMPLAINT_STATUSES}")] = None,
    ) -> dict[str, Any]:
        """Reclamaciones de cliente registradas en el ERP, con el id del informe 8D si existe
        (report_8d_id). Tabla: complaints."""
        return await run(
            t.search_complaints,
            ctx,
            part_ref=part_ref,
            customer_code=customer_code,
            from_date=from_date,
            status=status,
        )

    return mcp


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Servidor MCP erp-mock (solo lectura).")
    parser.add_argument("--transport", choices=["stdio"], default="stdio")
    parser.parse_args(argv)
    build_server().run("stdio")
    return 0


if __name__ == "__main__":
    sys.exit(main())
