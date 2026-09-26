"""Persistencia del 8D: tabla `eightd.cases` y checkpointer de LangGraph en Postgres (M3-T3).

Conexión como `eightd_app` (migración 008): solo el esquema `eightd`, SELECT/INSERT/UPDATE sin
DELETE, sin acceso a rag/erp/audit. Ni el superusuario ni `solaris_app` (que es de solo lectura).
El checkpointer es el oficial (`langgraph-checkpoint-postgres`, AsyncPostgresSaver) sobre tablas
creadas por la migración: no se llama a `setup()` (el rol no tiene CREATE).
"""

from __future__ import annotations

import hashlib
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

import psycopg
from psycopg.rows import dict_row

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
        self.saver = AsyncPostgresSaver(conn)

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


class MemoryCaseStore:
    """Mismo contrato en memoria (tests y ejecución sin BD)."""

    def __init__(self) -> None:
        from langgraph.checkpoint.memory import InMemorySaver

        self.saver = InMemorySaver()
        self.cases: dict[str, tuple[CaseRow, bytes]] = {}

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
