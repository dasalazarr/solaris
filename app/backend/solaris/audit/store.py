"""Escritura, verificación y exportación del audit log `audit.events` (M4-T2, F08).

- `record()` escribe con el rol `audit_writer` (solo INSERT). El id, el `ts` y la cadena de hash los
  fija el trigger `audit.events_chain` bajo `pg_advisory_xact_lock`: todos los escritores (backend,
  MCP erp-mock...) comparten una única cadena, es seguro ante concurrencia y un escritor no puede
  falsificar hash, fecha ni orden.
- `verify_chain()` recalcula la cadena **en Python** (independiente de las funciones SQL, que un
  superusuario podría sustituir) y devuelve el primer id roto.
- `export_csv()` / `iter_export_csv()` leen con el rol `audit_reader` (solo SELECT).
"""

from __future__ import annotations

import csv
import hashlib
import io
import logging
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from solaris.audit.redact import redact_payload, scrub_text
from solaris.settings import Settings, get_settings

logger = logging.getLogger("solaris.audit")

EVENT_TYPES = frozenset(
    {
        "llm_call",
        "retrieval",
        "tool_call",
        "tool_denied",
        "write_attempt",
        "approval",
        "export",
        "auth",
        "ingest",  # M2-T3: un evento por documento ingerido (solo metadatos). Migración 004.
        "agent_step",  # M3-T3: un evento por nodo del grafo 8D (solo metadatos). Migración 009.
        "approval_denied",  # M3-T4: aprobar/reanudar/exportar sin permiso o sin aprobación. 010.
        "instruction_ignored",  # M3-T4: instrucción embebida detectada y neutralizada. 010.
    }
)
GENESIS = "0" * 64
CANON_VERSION = "solaris-audit-v1|"
_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
_US = timedelta(microseconds=1)
_COLUMNS = (
    "id, ts, actor_user, actor_role, event_type, case_id, source, model, provider, "
    "payload::text AS payload, prev_hash, hash"
)
CSV_FIELDS = (
    "id", "ts", "actor_user", "actor_role", "event_type", "case_id", "source", "model",
    "provider", "payload", "prev_hash", "hash",
)


class AuditError(RuntimeError):
    """Fallo del audit log."""


class AuditUnavailable(AuditError):
    """No hay credenciales o la BD no responde."""


@dataclass(frozen=True)
class Actor:
    """Identidad on-behalf-of. Se deriva del usuario autenticado, nunca del LLM ni del cuerpo."""

    user: str | None = None
    role: str | None = None


@dataclass(frozen=True)
class ChainReport:
    ok: bool
    checked: int
    first_broken_id: int | None = None
    reason: str | None = None
    head_id: int | None = None
    head_hash: str | None = None


# --- conexiones -------------------------------------------------------------------------------


def _connect_as(role: str, field: str, settings: Settings | None, **kwargs: Any):
    s = settings or get_settings()
    secret = getattr(s, field)
    if secret is None or not secret.get_secret_value():
        raise AuditUnavailable(f"Falta {field.upper()} en .env (rol {role})")
    kwargs.setdefault("connect_timeout", s.db_connect_timeout_s)
    kwargs.setdefault("application_name", "solaris-audit")
    try:
        return psycopg.connect(
            host=s.postgres_host,
            port=s.solaris_db_port,
            dbname=s.audit_db_name or s.postgres_db,
            user=role,
            password=secret.get_secret_value(),
            **kwargs,
        )
    except psycopg.OperationalError as exc:
        raise AuditUnavailable(f"Audit no disponible ({role}): conexión rechazada") from exc


def connect_writer(settings: Settings | None = None, **kwargs: Any) -> psycopg.Connection:
    return _connect_as("audit_writer", "audit_writer_password", settings, **kwargs)


def connect_reader(settings: Settings | None = None, **kwargs: Any) -> psycopg.Connection:
    return _connect_as("audit_reader", "audit_reader_password", settings, **kwargs)


def writer_configured(settings: Settings | None = None) -> bool:
    s = settings or get_settings()
    return s.audit_writer_password is not None and bool(s.audit_writer_password.get_secret_value())


# --- escritura --------------------------------------------------------------------------------

_INSERT = (
    "INSERT INTO audit.events "
    "(actor_user, actor_role, event_type, case_id, source, model, provider, payload) "
    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
)


def record(
    event_type: str,
    actor: Actor | tuple[str | None, str | None] | None,
    payload: dict[str, Any] | None = None,
    *,
    case_id: str | None = None,
    model: str | None = None,
    provider: str | None = None,
    source: str = "backend",
    conn: psycopg.Connection | None = None,
    settings: Settings | None = None,
) -> None:
    """Anexa un evento. El payload se redacta (sin secretos; prompts truncados o hasheados).

    Sin `conn`, abre una conexión como `audit_writer` en autocommit (un evento = una transacción
    corta, para no retener el lock de la cadena). Con `conn`, escribe en la transacción del
    llamante (que debe ser READ COMMITTED: el trigger rechaza otros niveles).
    """
    if event_type not in EVENT_TYPES:
        raise ValueError(f"event_type no válido: {event_type!r}")
    s = settings or get_settings()
    if actor is None:
        actor = Actor()
    elif isinstance(actor, tuple):
        actor = Actor(*actor)
    clean = redact_payload(payload, s)

    def _s(v: str | None, n: int = 200) -> str | None:
        return None if v is None else scrub_text(str(v), s)[:n]

    params = (
        _s(actor.user), _s(actor.role), event_type, _s(case_id), source, _s(model), _s(provider),
        Jsonb(clean),
    )
    if conn is not None:
        conn.execute(_INSERT, params)
        return
    with connect_writer(s, autocommit=True) as c:
        c.execute(_INSERT, params)


def record_safe(event_type: str, actor: Any, payload: dict[str, Any] | None = None, **kw: Any):
    """`record()` según la política `AUDIT_REQUIRED`: si es False, un fallo solo deja un warning."""
    s: Settings = kw.get("settings") or get_settings()
    try:
        record(event_type, actor, payload, **kw)
    except Exception as exc:
        if s.audit_required:
            raise AuditError(f"No se pudo registrar el evento {event_type}") from exc
        logger.warning("audit: evento %s NO registrado (%s)", event_type, type(exc).__name__)


# --- verificación -----------------------------------------------------------------------------


def _ns(v: str | None) -> str:
    return "~" if v is None else f"{len(v.encode('utf-8'))}:{v}"


def compute_hash(prev_hash: str, row: dict[str, Any]) -> str:
    """Réplica en Python de `audit.event_hash()` (canónico v1).

    `row['payload']` es el `payload::text` de la BD (formato jsonb, determinista por valor).
    """
    epoch_us = (row["ts"] - _EPOCH) // _US
    canon = CANON_VERSION + "".join(
        _ns(v)
        for v in (
            str(row["id"]), str(epoch_us), row["actor_user"], row["actor_role"],
            row["event_type"], row["case_id"], row["source"], row["model"], row["provider"],
            row["payload"],
        )
    )
    return hashlib.sha256((prev_hash + canon).encode("utf-8")).hexdigest()


def verify_chain(
    conn: psycopg.Connection | None = None,
    settings: Settings | None = None,
    *,
    anchor: tuple[int, str] | None = None,
) -> ChainReport:
    """Recorre `audit.events` por id y comprueba enlace (`prev_hash`) y contenido (`hash`).

    `anchor=(id, hash)`: una cabeza guardada fuera de la BD (p. ej. en una exportación previa).
    Detecta además el truncado de la cola o la reescritura completa de la cadena hasta ese punto.
    """
    own = conn is None
    c = conn or connect_reader(settings)
    try:
        prev = GENESIS
        checked = 0
        last_id: int | None = None
        anchor_seen = anchor is None
        with c.cursor(name="audit_verify", row_factory=dict_row) as cur:
            cur.itersize = 1000
            cur.execute(f"SELECT {_COLUMNS} FROM audit.events ORDER BY id")  # noqa: S608  # columnas fijas
            for row in cur:
                checked += 1
                if row["prev_hash"] != prev:
                    return ChainReport(False, checked, row["id"], "prev_hash no enlaza")
                if compute_hash(prev, row) != row["hash"]:
                    return ChainReport(False, checked, row["id"], "hash no casa con el contenido")
                if anchor is not None and row["id"] == anchor[0]:
                    if row["hash"] != anchor[1]:
                        return ChainReport(False, checked, row["id"], "no coincide con el ancla")
                    anchor_seen = True
                prev, last_id = row["hash"], row["id"]
        if not anchor_seen:
            return ChainReport(False, checked, anchor[0], "falta la fila del ancla")  # type: ignore[index]
        return ChainReport(True, checked, head_id=last_id, head_hash=prev if last_id else None)
    finally:
        if own:
            c.close()


# --- lectura y exportación --------------------------------------------------------------------


def _where(filters: dict[str, Any]) -> tuple[str, list[Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    for col in ("event_type", "actor_user", "actor_role", "case_id", "source"):
        v = filters.get(col)
        if v is not None:
            clauses.append(f"{col} = %s")
            params.append(v)
    if filters.get("from_ts") is not None:
        clauses.append("ts >= %s")
        params.append(filters["from_ts"])
    if filters.get("to_ts") is not None:
        clauses.append("ts < %s")
        params.append(filters["to_ts"])
    if filters.get("before_id") is not None:
        clauses.append("id < %s")
        params.append(filters["before_id"])
    return (" WHERE " + " AND ".join(clauses)) if clauses else "", params


def query_events(
    *, limit: int = 50, settings: Settings | None = None, conn: psycopg.Connection | None = None,
    **filters: Any,
) -> list[dict[str, Any]]:
    """Eventos más recientes primero, con filtros exactos y paginación por `before_id`."""
    limit = max(1, min(int(limit), 200))
    where, params = _where(filters)
    sql = f"SELECT {_COLUMNS} FROM audit.events{where} ORDER BY id DESC LIMIT %s"  # noqa: S608
    own = conn is None
    c = conn or connect_reader(settings)
    try:
        rows = c.cursor(row_factory=dict_row).execute(sql, [*params, limit]).fetchall()  # type: ignore[arg-type]
    finally:
        if own:
            c.close()
    return rows


_FORMULA_START = ("=", "+", "-", "@", "\t", "\r")


def _csv_cell(v: Any) -> str:
    """Neutraliza la inyección de fórmulas al abrir el CSV en una hoja de cálculo."""
    if v is None:
        return ""
    if isinstance(v, datetime):
        return v.astimezone(UTC).isoformat()
    text = str(v)
    return "'" + text if text.startswith(_FORMULA_START) else text


def iter_export_csv(
    from_ts: datetime | None = None,
    to_ts: datetime | None = None,
    *,
    settings: Settings | None = None,
    conn: psycopg.Connection | None = None,
) -> Iterator[str]:
    """CSV en streaming (cabecera + filas por id ascendente). `payload` es el JSON almacenado."""
    where, params = _where({"from_ts": from_ts, "to_ts": to_ts})
    sql = f"SELECT {_COLUMNS} FROM audit.events{where} ORDER BY id"  # noqa: S608
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")

    def flush() -> str:
        out = buf.getvalue()
        buf.seek(0)
        buf.truncate()
        return out

    writer.writerow(CSV_FIELDS)
    yield flush()
    own = conn is None
    c = conn or connect_reader(settings)
    try:
        with c.cursor(name="audit_export", row_factory=dict_row) as cur:
            cur.itersize = 500
            cur.execute(sql, params)  # type: ignore[arg-type]
            for row in cur:
                writer.writerow([_csv_cell(row[f]) for f in CSV_FIELDS])
                yield flush()
    finally:
        if own:
            c.close()


def export_csv(
    from_ts: datetime | None = None,
    to_ts: datetime | None = None,
    *,
    settings: Settings | None = None,
    conn: psycopg.Connection | None = None,
) -> str:
    return "".join(iter_export_csv(from_ts, to_ts, settings=settings, conn=conn))
