"""Autenticación y autorización del demo (M4-T1, F09). Ver `solaris.auth.core`."""

from solaris.auth.core import (
    SESSIONS,
    THROTTLE,
    AuthError,
    AuthUnavailable,
    LockedOut,
    Principal,
    authenticate,
    login,
)
from solaris.auth.deps import CurrentUser, auth_settings, current_user, require_roles

__all__ = [
    "SESSIONS",
    "THROTTLE",
    "AuthError",
    "AuthUnavailable",
    "CurrentUser",
    "LockedOut",
    "Principal",
    "auth_settings",
    "authenticate",
    "current_user",
    "login",
    "require_roles",
]
