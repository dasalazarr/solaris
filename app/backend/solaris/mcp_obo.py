"""Llamadas al MCP erp-mock en nombre del usuario autenticado (on-behalf-of, M4-T1 → M3-T3).

El servidor erp-mock (app/mcp/erp_mock/solaris_erp_mock/server.py) lee la identidad del `_meta` de
cada `tools/call` (claves `solaris/user`, `solaris/role`), nunca de los argumentos de la
herramienta.
Este helper es el ÚNICO sitio del backend que construye ese `_meta`, y lo hace solo desde el
`Principal` de `current_user()`:

    from solaris.mcp_obo import call_erp_tool
    result = await call_erp_tool(session, principal, "get_lot", {"lot_code": "L26241-AR1003-02"})

Reglas (M3-T1 punto 1, R03):
- Los `arguments` los puede proponer el LLM: si traen claves de identidad (`_meta`, `user`, `role`,
  `solaris/*`...) se rechaza la llamada; el `_meta` nunca se copia de la salida del modelo.
- Transporte solo stdio (el backend lanza el proceso): no hay un tercero que pueda inyectar `_meta`.
  Con un transporte de red habría que autenticar al cliente o firmar el `_meta` (ver traza M4-T1).

`session` es cualquier objeto con `call_tool(name, arguments, meta=...)` asíncrono
(`mcp.ClientSession` desde mcp>=1.20). No se importa `mcp` aquí: el backend aún no lo necesita.
"""

from __future__ import annotations

from typing import Any, Protocol

from solaris.auth.core import Principal
from solaris.rag.acl import resolve_role
from solaris.settings import Settings, get_settings

META_USER = "solaris/user"
META_ROLE = "solaris/role"
_IDENTITY_KEYS = frozenset({"_meta", "meta", "user", "role", "username", "actor", "on_behalf_of"})


class OboError(PermissionError):
    """Llamada MCP rechazada antes de salir: identidad ausente o suplantada en los argumentos."""


class ToolSession(Protocol):
    async def call_tool(
        self, name: str, arguments: dict[str, Any] | None = None, *, meta: dict[str, Any] | None
    ) -> Any: ...


def obo_meta(principal: Principal, settings: Settings | None = None) -> dict[str, str]:
    """`_meta` on-behalf-of para el MCP. El rol se revalida contra acl.json en este momento."""
    if not isinstance(principal, Principal):
        raise OboError("Hace falta el Principal de current_user() (no un texto ni un dict)")
    s = settings or get_settings()
    role = resolve_role(principal.user, s.acl_file)
    if role is None or role != principal.role:
        raise OboError("El usuario ya no tiene ese rol en acl.json")
    return {META_USER: principal.user, META_ROLE: role}


def check_arguments(arguments: dict[str, Any] | None) -> dict[str, Any]:
    args = dict(arguments or {})
    bad = sorted(
        k for k in args
        if str(k).lower() in _IDENTITY_KEYS or str(k).startswith("solaris/")
    )
    if bad:
        raise OboError(f"Argumentos de identidad no permitidos en una herramienta: {bad}")
    return args


async def call_erp_tool(
    session: ToolSession,
    principal: Principal,
    name: str,
    arguments: dict[str, Any] | None = None,
    *,
    settings: Settings | None = None,
) -> Any:
    """`tools/call` al MCP con `_meta` = identidad del usuario autenticado."""
    args = check_arguments(arguments)
    return await session.call_tool(name, args, meta=obo_meta(principal, settings))
