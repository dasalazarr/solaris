"""Autenticación del demo (M4-T1, F09). Sin FastAPI: credenciales, JWT, sesiones y bloqueo.

Diseño (ADR-0002: auth simple, sin Keycloak):
- **Usuarios** = los de `acl.json` (`users`). **Contraseñas** de demo desde `.env`
  (`DEMO_PASSWORD_<USUARIO>`, ≥16 caracteres). Usuario sin contraseña configurada → no entra.
- **Token**: JWT HS256 firmado con `AUTH_JWT_SECRET` (≥32 caracteres), con `iss`, `aud`, `sub`,
  `sid`, `iat`, `nbf` y `exp` obligatorios y algoritmo fijado (sin `none` ni confusión de claves).
  **El rol no va en el token**: se resuelve en el servidor desde `acl.json` en cada petición.
- **Sesión** en memoria (`sid`): vida máxima `AUTH_TOKEN_TTL_S` y cierre por inactividad
  `AUTH_IDLE_TIMEOUT_S` (E1-US4). Logout la revoca. Un reinicio del backend cierra todas las
  sesiones (falla cerrado). Limitación: un solo proceso (uvicorn con 1 worker), suficiente
  para el demo.
- **Bloqueo** tras `AUTH_MAX_FAILED_LOGINS` fallos seguidos de un mismo usuario, `AUTH_LOCKOUT_S`.
"""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import jwt

from solaris.audit import Actor
from solaris.rag.acl import resolve_role
from solaris.settings import Settings

ISSUER = "solaris-demo"
AUDIENCE = "solaris-api"
ALGORITHM = "HS256"
MIN_SECRET_CHARS = 32
MIN_PASSWORD_CHARS = 16
_REQUIRED_CLAIMS = ["iss", "aud", "sub", "sid", "iat", "nbf", "exp"]
_SLUG_RE = re.compile(r"[^a-z0-9]")
# Comparación de tiempo constante también para usuarios desconocidos (no revela si existen).
_DUMMY_DIGEST = hashlib.sha256(b"solaris-no-such-user").digest()


class AuthError(Exception):
    """Credenciales o token no válidos (→ 401). El mensaje es genérico a propósito."""


class AuthUnavailable(AuthError):
    """Auth sin configurar (falta el secreto): falla cerrado (→ 503)."""


class LockedOut(AuthError):
    """Demasiados fallos seguidos (→ 429)."""


@dataclass(frozen=True)
class Principal:
    """Usuario autenticado. `role` sale SIEMPRE de acl.json en el servidor."""

    user: str
    role: str
    sid: str

    @property
    def actor(self) -> Actor:
        """Identidad on-behalf-of para el audit y `llm.route(actor=...)`."""
        return Actor(self.user, self.role)


def password_field(user: str) -> str:
    return "demo_password_" + _SLUG_RE.sub("_", user.lower())


def _secret(settings: Settings) -> str:
    s = settings.auth_jwt_secret
    value = s.get_secret_value() if s is not None else ""
    if len(value) < MIN_SECRET_CHARS:
        raise AuthUnavailable("Autenticación no configurada")
    return value


def check_password(user: str, password: str, settings: Settings) -> bool:
    """True si `user` existe en acl.json, tiene contraseña de demo válida y coincide."""
    role = resolve_role(user, settings.acl_file)
    stored = getattr(settings, password_field(user), None) if role is not None else None
    expected = stored.get_secret_value() if stored is not None else ""
    given = hashlib.sha256(password.encode("utf-8")).digest()
    if len(expected) < MIN_PASSWORD_CHARS:
        hmac.compare_digest(given, _DUMMY_DIGEST)
        return False
    return hmac.compare_digest(given, hashlib.sha256(expected.encode("utf-8")).digest())


# --- JWT --------------------------------------------------------------------------------------


def issue_token(user: str, sid: str, settings: Settings, now: float | None = None) -> str:
    t = int(now if now is not None else time.time())
    claims = {
        "iss": ISSUER, "aud": AUDIENCE, "sub": user, "sid": sid,
        "iat": t, "nbf": t, "exp": t + settings.auth_token_ttl_s,
    }
    return jwt.encode(claims, _secret(settings), algorithm=ALGORITHM)


def decode_token(token: str, settings: Settings) -> dict[str, Any]:
    secret = _secret(settings)
    try:
        claims = jwt.decode(
            token, secret, algorithms=[ALGORITHM], audience=AUDIENCE, issuer=ISSUER,
            options={"require": _REQUIRED_CLAIMS}, leeway=5,
        )
    except jwt.PyJWTError as exc:
        raise AuthError("Token no válido") from exc
    if not isinstance(claims.get("sub"), str) or not isinstance(claims.get("sid"), str):
        raise AuthError("Token no válido")
    return claims


# --- sesiones e inactividad -------------------------------------------------------------------


@dataclass
class _Session:
    user: str
    created: float
    last_seen: float


class SessionStore:
    """Sesiones en memoria con cierre por inactividad. Seguro entre hilos."""

    def __init__(self, clock: Callable[[], float] = time.monotonic, max_sessions: int = 1000):
        self._clock = clock
        self._max = max_sessions
        self._lock = threading.Lock()
        self._s: OrderedDict[str, _Session] = OrderedDict()

    def create(self, user: str) -> str:
        sid = secrets.token_urlsafe(24)
        now = self._clock()
        with self._lock:
            self._s[sid] = _Session(user, now, now)
            while len(self._s) > self._max:  # tope de memoria: cae la más antigua
                self._s.popitem(last=False)
        return sid

    def touch(self, sid: str, user: str, settings: Settings) -> bool:
        """Valida la sesión y renueva su actividad. Caducada o inactiva → se borra y False."""
        now = self._clock()
        with self._lock:
            s = self._s.get(sid)
            if s is None or s.user != user:
                return False
            if (now - s.last_seen > settings.auth_idle_timeout_s
                    or now - s.created > settings.auth_token_ttl_s):
                del self._s[sid]
                return False
            s.last_seen = now
            return True

    def revoke(self, sid: str) -> None:
        with self._lock:
            self._s.pop(sid, None)

    def age_idle(self, sid: str, seconds: float) -> None:
        """Solo tests: simula `seconds` sin actividad."""
        with self._lock:
            if sid in self._s:
                self._s[sid].last_seen -= seconds

    def clear(self) -> None:
        with self._lock:
            self._s.clear()


class LoginThrottle:
    """Bloqueo temporal por usuario tras N fallos seguidos (en memoria, acotado)."""

    def __init__(self, clock: Callable[[], float] = time.monotonic, max_keys: int = 1000):
        self._clock = clock
        self._max = max_keys
        self._lock = threading.Lock()
        self._fails: OrderedDict[str, tuple[int, float]] = OrderedDict()

    def check(self, key: str, settings: Settings) -> None:
        with self._lock:
            n, since = self._fails.get(key, (0, 0.0))
            if n >= settings.auth_max_failed_logins:
                if self._clock() - since < settings.auth_lockout_s:
                    raise LockedOut("Demasiados intentos fallidos")
                del self._fails[key]

    def failed(self, key: str) -> None:
        with self._lock:
            n, _ = self._fails.pop(key, (0, 0.0))
            self._fails[key] = (n + 1, self._clock())
            while len(self._fails) > self._max:
                self._fails.popitem(last=False)

    def succeeded(self, key: str) -> None:
        with self._lock:
            self._fails.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._fails.clear()


SESSIONS = SessionStore()
THROTTLE = LoginThrottle()


def login(user: str, password: str, settings: Settings) -> tuple[Principal, str]:
    """Credenciales → (Principal, token). Lanza AuthError/LockedOut/AuthUnavailable."""
    _secret(settings)  # sin secreto no se valida nada (y no cuenta como fallo)
    key = user[:64]
    THROTTLE.check(key, settings)
    if not check_password(user, password, settings):
        THROTTLE.failed(key)
        raise AuthError("Credenciales no válidas")
    role = resolve_role(user, settings.acl_file)
    if role is None:  # carrera con una baja en acl.json
        raise AuthError("Credenciales no válidas")
    THROTTLE.succeeded(key)
    sid = SESSIONS.create(user)
    return Principal(user, role, sid), issue_token(user, sid, settings)


def authenticate(token: str, settings: Settings) -> Principal:
    """Token → Principal: firma, claims, sesión viva y rol actual desde acl.json."""
    claims = decode_token(token, settings)
    user, sid = claims["sub"], claims["sid"]
    if not SESSIONS.touch(sid, user, settings):
        raise AuthError("Sesión caducada o cerrada")
    role = resolve_role(user, settings.acl_file)
    if role is None:
        SESSIONS.revoke(sid)
        raise AuthError("Usuario sin acceso")
    return Principal(user, role, sid)
