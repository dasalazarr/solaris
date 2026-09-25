"""Dependencias FastAPI: `current_user()` y `require_roles(...)` (M4-T1, F09).

Solo se acepta `Authorization: Bearer <jwt>` (sin cookies: no hay CSRF). El rol **nunca** se lee de
la petición (cabeceras, query, cuerpo) ni de la salida del LLM: `authenticate()` lo resuelve desde
acl.json con el `sub` de un token verificado.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from solaris.audit import record_safe
from solaris.auth.core import AuthError, AuthUnavailable, Principal, authenticate
from solaris.settings import Settings, get_settings

_bearer = HTTPBearer(auto_error=False)
_UNAUTHORIZED = {"WWW-Authenticate": "Bearer"}


def auth_settings() -> Settings:
    return get_settings()


AuthSettings = Annotated[Settings, Depends(auth_settings)]


def current_user(
    settings: AuthSettings,
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> Principal:
    """Usuario autenticado `{user, role}`. 401 si falta el token, es inválido o la sesión expiró."""
    if creds is None or creds.scheme.lower() != "bearer" or not creds.credentials:
        raise HTTPException(401, "No autenticado", headers=_UNAUTHORIZED)
    try:
        return authenticate(creds.credentials, settings)
    except AuthUnavailable as exc:
        raise HTTPException(503, "Autenticación no disponible") from exc
    except AuthError as exc:
        raise HTTPException(401, "No autenticado", headers=_UNAUTHORIZED) from exc


CurrentUser = Annotated[Principal, Depends(current_user)]


def require_roles(*roles: str) -> Callable[..., Principal]:
    """Dependencia que exige uno de `roles`. Un 403 se registra en el audit (`auth`)."""
    allowed = frozenset(roles)

    def _dep(principal: CurrentUser, settings: AuthSettings, request: Request) -> Principal:
        if principal.role not in allowed:
            record_safe(
                "auth",
                principal.actor,
                {"action": "authorize", "outcome": "forbidden", "path": request.url.path,
                 "required": sorted(allowed)},
                settings=settings,
            )
            raise HTTPException(403, "Permiso insuficiente")
        return principal

    _dep.__name__ = f"require_{'_or_'.join(sorted(allowed))}"
    return _dep
