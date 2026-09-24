"""Fixtures. Los tests de BD conectan SOLO como `erp_reader` y se saltan si no hay BD o rol."""

from collections.abc import Iterator

import psycopg
import pytest

from solaris_erp_mock.acl import ErpAcl
from solaris_erp_mock.audit import MemoryAuditSink
from solaris_erp_mock.config import ErpSettings, get_settings
from solaris_erp_mock.db import ErpReader
from solaris_erp_mock.tools import ErpTools

CALIDAD = ("inaki.calidad", "calidad")
PLANTA = ("ander.turno", "planta")
AUDITOR = ("auditora.ext", "auditor")


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def settings() -> ErpSettings:
    return get_settings()


@pytest.fixture
def sink() -> MemoryAuditSink:
    return MemoryAuditSink()


@pytest.fixture
def tools(settings: ErpSettings, sink: MemoryAuditSink) -> ErpTools:
    return ErpTools(ErpReader(settings, sink), ErpAcl.load(settings.erp_acl_file), sink)


@pytest.fixture(scope="session")
def _db_ok() -> None:
    s = get_settings()
    if s.erp_db_host not in ("127.0.0.1", "localhost"):
        pytest.skip("Los tests de BD solo corren contra el Postgres local")
    try:
        conn = ErpReader(s, MemoryAuditSink()).connect()
    except Exception as exc:
        pytest.skip(f"Postgres/erp_reader no disponible: {type(exc).__name__}")
    conn.close()


@pytest.fixture
def db(_db_ok: None, tools: ErpTools) -> ErpTools:
    return tools


@pytest.fixture
def raw_reader_conn(_db_ok: None, settings: ErpSettings) -> Iterator[psycopg.Connection]:
    """Conexión cruda como erp_reader, sin el READ ONLY que añade ErpReader."""
    conn = psycopg.connect(
        host=settings.erp_db_host,
        port=settings.solaris_db_port,
        dbname=settings.erp_db_name,
        user="erp_reader",
        password=settings.erp_reader_password.get_secret_value(),
        autocommit=True,
    )
    with conn:
        yield conn
