"""M3-T1: migración 002 (rol erp_reader) y fijación de su contraseña desde .env."""

from collections.abc import Iterator

import psycopg
import pytest
from pydantic import SecretStr

from solaris.db.migrate import MIGRATIONS_DIR, discover
from solaris.db.roles import set_service_role_passwords
from solaris.settings import Settings


def test_migration_002_present_and_without_secrets():
    migs = {m.version: m for m in discover(MIGRATIONS_DIR)}
    assert "002_erp_reader" in migs
    lines = migs["002_erp_reader"].sql.splitlines()
    code = [ln for ln in lines if not ln.lstrip().startswith("--")]
    sql = "\n".join(code).upper()
    assert "PASSWORD" not in sql  # la clave nunca va en la migración
    assert "GRANT SELECT ON ALL TABLES IN SCHEMA ERP TO ERP_READER" in sql


def test_no_password_no_change():
    assert set_service_role_passwords(None, Settings(_env_file=None)) == []  # type: ignore[arg-type]


@pytest.fixture(autouse=True)
def _no_real_network():
    yield  # psycopg usa libpq; solo Postgres local (ver test_rag_schema)


@pytest.fixture
def db() -> Iterator[psycopg.Connection]:
    from solaris.db import connect
    from solaris.settings import get_settings

    try:
        conn = connect(get_settings(), connect_timeout=2)
    except Exception as exc:
        pytest.skip(f"Postgres no disponible: {type(exc).__name__}")
    with conn:
        if conn.execute("SELECT 1 FROM pg_roles WHERE rolname = 'erp_reader'").fetchone() is None:
            pytest.skip("Rol erp_reader no creado: uv run python -m solaris.db.migrate")
        with conn.transaction(force_rollback=True):
            yield conn


def test_set_password_uses_scram_verifier(db):
    s = Settings(_env_file=None, erp_reader_password=SecretStr("test-only-not-real"))
    assert set_service_role_passwords(db, s) == ["erp_reader"]
    # pg_authid solo lo lee un superusuario: el backend de dev lo es (deuda PAT-005, M4-T1)
    stored = db.execute("SELECT rolpassword FROM pg_authid WHERE rolname = 'erp_reader'").fetchone()
    assert stored[0].startswith("SCRAM-SHA-256$") and "test-only-not-real" not in stored[0]
