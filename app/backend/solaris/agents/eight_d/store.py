"""Persistencia del 8D: tabla `eightd.cases` y checkpointer de LangGraph en Postgres (M3-T3).

Conexión como `eightd_app` (migración 008): solo el esquema `eightd`, SELECT/INSERT/UPDATE sin
DELETE, sin acceso a rag/erp/audit. Ni el superusuario ni `solaris_app` (que es de solo lectura).
El checkpointer es el oficial (`langgraph-checkpoint-postgres`, AsyncPostgresSaver) sobre tablas
creadas por la migración: no se llama a `setup()` (el rol no tiene CREATE).

M3-T4 (HITL): `eightd.approvals` (migración 011), una decisión por caso, solo INSERT (sin UPDATE ni
DELETE): el borrador aprobado queda congelado en la BD.
"""

from __future__ import annotations

import copy
import hashlib
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from solaris.db import DbUnavailable
from solaris.settings import Settings, get_settings

ROLE = "eightd_app"


@dataclass(frozen=True)
class CaseRow:
    case_id: str
    complaint_id: str | None
    created_by: str
    created_role: str
    created_at: Any
    source: str
    filename: str
    sha256: str
    size: int


@dataclass(frozen=True)
class Decision:
    """Decisión humana sobre el borrador (M3-T4, tabla `eightd.approvals`, migración 011)."""

    case_id: str
    decision: str  # approved | rejected
    decided_by: str
    decided_role: str
    decided_at: Any
    version: str
    approved_version: str | None
    pct_edited: float
    edits: list[Any]
    edited_paths: list[Any]
    comment: str | None
    reason: str | None
    draft_original: dict[str, Any]
    draft_final: dict[str, Any] | None


_JSON_COLS = ("edits", "edited_paths", "draft_original", "draft_final")


def strict_serde() -> Any:
    """Serializador de checkpoints en modo estricto (M3-T6, punto S-T3-2).

    Por defecto, `JsonPlusSerializer` reconstruye al leer cualquier tipo msgpack por módulo y
    nombre (solo avisa): quien pudiera escribir en `eightd.checkpoint_*` podría provocar
    ejecución de código al cargar un checkpoint. El estado del 8D es solo JSON, así que se limita
    a la lista segura de la librería (`SAFE_MSGPACK_TYPES`: fechas, UUID, `Interrupt`, `Send`…),
    sin `pickle_fallback`."""
    from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

    return JsonPlusSerializer(pickle_fallback=False, allowed_msgpack_modules=None)


async def connect(settings: Settings | None = None) -> psycopg.AsyncConnection:
    s = settings or get_settings()
    secret = s.eightd_app_password
    if secret is None or not secret.get_secret_value():
        raise DbUnavailable("Falta EIGHTD_APP_PASSWORD en .env (rol eightd_app)")
    try:
        return await psycopg.AsyncConnection.connect(
            host=s.postgres_host, port=s.solaris_db_port, dbname=s.eightd_db_name or s.postgres_db,
            user=ROLE, password=secret.get_secret_value(), connect_timeout=s.db_connect_timeout_s,
            application_name="solaris-8d", autocommit=True, prepare_threshold=0,
            row_factory=dict_row)
    except psycopg.OperationalError as exc:
        raise DbUnavailable("BD no disponible (eightd_app): conexión rechazada") from exc


@asynccontextmanager
async def open_store(settings: Settings | None = None) -> AsyncIterator[PgCaseStore]:
    conn = await connect(settings)
    try:
        yield PgCaseStore(conn)
    finally:
        await conn.close()


class PgCaseStore:
    """Casos + checkpointer sobre una conexión `eightd_app`."""

    def __init__(self, conn: psycopg.AsyncConnection) -> None:
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

        self.conn = conn
        self.saver = AsyncPostgresSaver(conn, serde=strict_serde())

    async def create_case(self, *, complaint_id: str | None, created_by: str, created_role: str,
                          source: str, filename: str, data: bytes) -> str:
        case_id = str(uuid.uuid4())
        await self.conn.execute(
            "INSERT INTO eightd.cases (case_id, complaint_id, created_by, created_role, source,"
            " filename, sha256, size, file) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (case_id, complaint_id, created_by, created_role, source, filename[:200],
             hashlib.sha256(data).hexdigest(), len(data), data))
        return case_id

    async def get_case(self, case_id: str) -> CaseRow | None:
        cur = await self.conn.execute(
            "SELECT case_id::text, complaint_id, created_by, created_role, created_at, source,"
            " filename, sha256, size FROM eightd.cases WHERE case_id = %s", (case_id,))
        row = await cur.fetchone()
        return CaseRow(**row) if row else None

    async def load_file(self, case_id: str) -> tuple[bytes, str]:
        cur = await self.conn.execute(
            "SELECT file, filename FROM eightd.cases WHERE case_id = %s", (case_id,))
        row = await cur.fetchone()
        if row is None:
            raise LookupError("caso no encontrado")
        return bytes(row["file"]), row["filename"]

    async def save_decision(self, case_id: str, **d: Any) -> bool:
        """Guarda la decisión si el caso aún no tiene ninguna. False si ya la tenía (→ 409)."""
        j = {k: (Jsonb(d[k]) if d[k] is not None else None) for k in _JSON_COLS}
        cur = await self.conn.execute(
            "INSERT INTO eightd.approvals (case_id, decision, decided_by, decided_role, version,"
            " approved_version, pct_edited, edits, edited_paths, comment, reason, draft_original,"
            " draft_final) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            " ON CONFLICT (case_id) DO NOTHING RETURNING case_id",
            (case_id, d["decision"], d["decided_by"], d["decided_role"], d["version"],
             d["approved_version"], d["pct_edited"], j["edits"], j["edited_paths"],
             d["comment"], d["reason"], j["draft_original"], j["draft_final"]))
        return await cur.fetchone() is not None

    async def undecided_cases(self, limit: int = 100) -> list[CaseRow]:
        """Casos sin decisión humana, del más reciente al más antiguo (bandeja L03)."""
        cur = await self.conn.execute(
            "SELECT c.case_id::text, c.complaint_id, c.created_by, c.created_role, c.created_at,"
            " c.source, c.filename, c.sha256, c.size FROM eightd.cases c"
            " LEFT JOIN eightd.approvals a ON a.case_id = c.case_id WHERE a.case_id IS NULL"
            " ORDER BY c.created_at DESC LIMIT %s", (limit,))
        return [CaseRow(**r) for r in await cur.fetchall()]

    async def get_decision(self, case_id: str) -> Decision | None:
        cur = await self.conn.execute(
            "SELECT case_id::text, decided_at, decision, decided_by, decided_role, version,"
            " approved_version, pct_edited, edits, edited_paths, comment, reason,"
            " draft_original, draft_final FROM eightd.approvals WHERE case_id = %s", (case_id,))
        row = await cur.fetchone()
        if row is None:
            return None
        row["pct_edited"] = float(row["pct_edited"])
        return Decision(**row)


class MemoryCaseStore:
    """Mismo contrato en memoria (tests y ejecución sin BD)."""

    def __init__(self) -> None:
        from langgraph.checkpoint.memory import InMemorySaver

        self.saver = InMemorySaver()
        self.cases: dict[str, tuple[CaseRow, bytes]] = {}
        self.decisions: dict[str, Decision] = {}

    async def create_case(self, *, complaint_id: str | None, created_by: str, created_role: str,
                          source: str, filename: str, data: bytes) -> str:
        case_id = str(uuid.uuid4())
        from datetime import UTC, datetime

        self.cases[case_id] = (CaseRow(case_id, complaint_id, created_by, created_role,
                                       datetime.now(UTC), source, filename,
                                       hashlib.sha256(data).hexdigest(), len(data)), data)
        return case_id

    async def get_case(self, case_id: str) -> CaseRow | None:
        x = self.cases.get(case_id)
        return x[0] if x else None

    async def load_file(self, case_id: str) -> tuple[bytes, str]:
        row, data = self.cases[case_id]
        return data, row.filename

    async def save_decision(self, case_id: str, **d: Any) -> bool:
        from datetime import UTC, datetime

        if case_id in self.decisions:
            return False
        self.decisions[case_id] = Decision(case_id=case_id, decided_at=datetime.now(UTC),
                                           **{**copy.deepcopy(d),
                                              "pct_edited": float(d["pct_edited"])})
        return True

    async def get_decision(self, case_id: str) -> Decision | None:
        return self.decisions.get(case_id)

    async def undecided_cases(self, limit: int = 100) -> list[CaseRow]:
        rows = [r for r, _ in self.cases.values() if r.case_id not in self.decisions]
        return sorted(rows, key=lambda r: r.created_at, reverse=True)[:limit]
