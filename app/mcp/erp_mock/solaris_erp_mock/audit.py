"""Registro de llamadas (permitidas, denegadas, escrituras rechazadas) del MCP erp-mock.

`AuditSink` es la interfaz que usan las herramientas. Desde M4-T2 (F08) el sink por defecto es
`PgAuditSink`: anexa cada evento a `audit.events` con el rol de BD `audit_writer` (solo INSERT; la
cadena de hash, el id y la fecha los fija el trigger de la BD, compartido con el backend).

Política **fail-closed**: si el evento no se puede registrar, `emit()` lanza `AuditUnavailable` y la
herramienta devuelve error (no hay lecturas del ERP sin rastro). `JsonlAuditSink` queda solo para
desarrollo sin BD, y hay que pedirlo explícitamente (`ERP_MOCK_AUDIT_SINK=jsonl`).
"""

import json
import re
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

import psycopg
from psycopg.types.json import Jsonb

SOURCE = "erp-mock"


class AuditSink(Protocol):
    def emit(self, event: dict[str, Any]) -> None: ...


class AuditUnavailable(RuntimeError):
    """No se pudo anexar el evento al audit log."""


# --- mapeo evento MCP -> fila de audit.events -----------------------------------------------------

REDACTED = "[REDACTED]"
_SECRET_KEY_RE = re.compile(
    r"^(?:.*[_-])?(?:pass(?:word|wd)?|secret|api[_-]?key|apikey|token|authorization|auth|"
    r"cookie|private[_-]?key|credentials?|dsn)$",
    re.IGNORECASE,
)
_SECRET_VALUE_RES = (
    (re.compile(r"\bsk-[A-Za-z0-9][A-Za-z0-9_\-]{7,}"), REDACTED),
    (re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._\-~+/=]{8,}"), f"Bearer {REDACTED}"),
    (re.compile(r"(?i)\b([a-z][a-z0-9+.\-]*://[^:/\s@]+):[^@\s]+@"), rf"\1:{REDACTED}@"),
)
MAX_STRING = 500


def _scrub(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(k): REDACTED if _SECRET_KEY_RE.match(str(k)) and v not in (None, "") else _scrub(v)
            for k, v in value.items()
        }
    if isinstance(value, list | tuple):
        return [_scrub(v) for v in value]
    if value is None or isinstance(value, bool | int | float):
        return value
    text = str(value).replace("\x00", "")
    for pattern, repl in _SECRET_VALUE_RES:
        text = pattern.sub(repl, text)
    return text if len(text) <= MAX_STRING else text[:MAX_STRING] + "…[truncado]"


def event_type_for(event: dict[str, Any]) -> str:
    """Tipo de `audit.events` para un evento del MCP (uno desconocido es un error de código)."""
    kind = event.get("event")
    if kind == "tool_call":
        return "tool_denied" if event.get("decision") == "deny" else "tool_call"
    if kind in ("write_attempt", "write_rejected"):
        return "write_attempt"
    if kind in ("unknown_tool", "schema_invalid"):
        return "tool_denied"
    raise ValueError(f"Evento de audit desconocido: {kind!r}")


def to_row(event: dict[str, Any]) -> tuple[Any, ...]:
    """(actor_user, actor_role, event_type, case_id, source, model, provider, payload)."""
    payload = {k: v for k, v in event.items() if k not in ("user", "role", "source", "event")}
    payload["mcp_event"] = event.get("event")

    def _s(v: Any) -> str | None:
        return None if v is None else str(_scrub(str(v)))[:200]

    return (
        _s(event.get("user")),
        _s(event.get("role")),
        event_type_for(event),
        _s(event.get("case_id")),
        SOURCE,
        None,
        None,
        Jsonb(_scrub(payload)),
    )


_INSERT = (
    "INSERT INTO audit.events "
    "(actor_user, actor_role, event_type, case_id, source, model, provider, payload) "
    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
)


class PgAuditSink:
    """Anexa a `audit.events` como `audit_writer`. Una conexión en autocommit, reutilizada."""

    ROLE = "audit_writer"

    def __init__(self, settings: Any) -> None:
        secret = settings.audit_writer_password
        if secret is None or not secret.get_secret_value():
            raise AuditUnavailable("Falta AUDIT_WRITER_PASSWORD en .env (audit fail-closed)")
        self.settings = settings
        self._conn: psycopg.Connection | None = None
        self._lock = threading.Lock()

    def _connect(self) -> psycopg.Connection:
        s = self.settings
        try:
            return psycopg.connect(
                host=s.erp_db_host,
                port=s.solaris_db_port,
                dbname=s.audit_db_name,
                user=self.ROLE,
                password=s.audit_writer_password.get_secret_value(),
                connect_timeout=s.erp_db_connect_timeout_s,
                application_name="solaris-erp-mock-audit",
                autocommit=True,
            )
        except psycopg.OperationalError as exc:
            raise AuditUnavailable("Audit no disponible (conexión rechazada)") from exc

    def emit(self, event: dict[str, Any]) -> None:
        params = to_row(event)
        with self._lock:
            for attempt in (1, 2):  # un reintento si la conexión reutilizada se ha caído
                if self._conn is None or self._conn.closed:
                    self._conn = self._connect()
                try:
                    self._conn.execute(_INSERT, params)
                    return
                except psycopg.OperationalError as exc:
                    self._conn = None
                    if attempt == 2:
                        raise AuditUnavailable("Audit no disponible (escritura fallida)") from exc
                except psycopg.Error as exc:
                    raise AuditUnavailable(
                        f"Audit rechazó el evento ({type(exc).__name__})"
                    ) from exc

    def close(self) -> None:
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None


class JsonlAuditSink:
    """Solo desarrollo sin BD (no es append-only ni tiene integridad)."""

    def __init__(self, log_dir: Path, filename: str = "erp_mock.jsonl") -> None:
        self.path = Path(log_dir) / filename
        self._lock = threading.Lock()

    def emit(self, event: dict[str, Any]) -> None:
        record = {"ts": datetime.now(UTC).isoformat(timespec="milliseconds"), **event}
        line = json.dumps(record, ensure_ascii=False, default=str)
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")


class MemoryAuditSink:
    """Sink en memoria para tests."""

    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def emit(self, event: dict[str, Any]) -> None:
        self.events.append(event)
