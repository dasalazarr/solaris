"""Endpoints de autenticación: `POST /auth/login`, `POST /auth/logout`, `GET /auth/me` (M4-T1)."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from solaris.audit import Actor, record_safe
from solaris.auth.core import SESSIONS, AuthError, AuthUnavailable, LockedOut, login
from solaris.auth.deps import AuthSettings, CurrentUser

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginIn(BaseModel):
    username: Annotated[str, Field(min_length=1, max_length=64)]
    password: Annotated[str, Field(min_length=1, max_length=256)]


def _audit_login(settings, user: str | None, role: str | None, outcome: str, **extra: Any) -> None:
    record_safe("auth", Actor(user, role), {"action": "login", "outcome": outcome, **extra},
                settings=settings)


@router.post("/login")
def login_endpoint(body: LoginIn, settings: AuthSettings) -> dict[str, Any]:
    try:
        principal, token = login(body.username, body.password, settings)
    except AuthUnavailable as exc:
        raise HTTPException(503, "Autenticación no disponible") from exc
    except LockedOut as exc:
        _audit_login(settings, None, None, "locked", attempted_user=body.username[:64])
        raise HTTPException(429, "Demasiados intentos fallidos; espera y reintenta") from exc
    except AuthError as exc:
        # Nunca la contraseña; el usuario intentado sí (recortado) para detectar sondeos.
        _audit_login(settings, None, None, "denied", attempted_user=body.username[:64])
        raise HTTPException(401, "Credenciales no válidas",
                            headers={"WWW-Authenticate": "Bearer"}) from exc
    _audit_login(settings, principal.user, principal.role, "ok")
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.auth_token_ttl_s,
        "idle_timeout_s": settings.auth_idle_timeout_s,
        "user": principal.user,
        "role": principal.role,
    }


@router.post("/logout", status_code=204)
def logout(principal: CurrentUser, settings: AuthSettings) -> None:
    SESSIONS.revoke(principal.sid)
    record_safe("auth", principal.actor, {"action": "logout", "outcome": "ok"}, settings=settings)


@router.get("/me")
def me(principal: CurrentUser) -> dict[str, str]:
    return {"user": principal.user, "role": principal.role}
