import pytest
from pydantic import SecretStr

from solaris.settings import DEFAULT_MODELS_FILE, Settings

FAKE_KEY = "sk-or-test-not-a-real-key"


@pytest.fixture
def settings() -> Settings:
    # _env_file=None: los tests no leen el .env real del repo.
    return Settings(
        _env_file=None,
        openrouter_api_key=SecretStr(FAKE_KEY),
        models_file=DEFAULT_MODELS_FILE,
        llm_timeout_s=1.0,
        llm_max_retries=1,
        llm_backoff_s=0.0,
    )


@pytest.fixture(autouse=True)
def _no_real_network(monkeypatch):
    """Cinturón y tirantes: si algo escapa a respx, falla en vez de salir a la red."""
    import socket

    def _boom(*args, **kwargs):
        raise AssertionError("Llamada de red real en tests")

    monkeypatch.setattr(socket.socket, "connect", _boom)
    monkeypatch.setattr(socket, "create_connection", _boom)


@pytest.fixture(scope="session")
def audit_settings() -> Settings:
    """Settings reales (.env) apuntando el audit a la BD de tests `solaris_test`, recreada una vez
    por sesión (las filas del audit no se pueden borrar: no se ensucia el audit del demo)."""
    from solaris.audit import testdb
    from solaris.settings import get_settings

    s = get_settings().model_copy(update={"audit_db_name": testdb.TEST_DB})
    if s.audit_writer_password is None or s.audit_reader_password is None:
        pytest.skip("Faltan AUDIT_WRITER_PASSWORD/AUDIT_READER_PASSWORD en .env")
    try:
        testdb.recreate(s)
    except Exception as exc:
        pytest.skip(f"Postgres no disponible para solaris_test: {type(exc).__name__}")
    return s


@pytest.fixture
def audit_su(audit_settings):
    """Conexión como superusuario de dev a solaris_test, dentro de una transacción revertida."""
    from solaris.audit import testdb

    with (
        testdb._connect_to(audit_settings, testdb.TEST_DB) as conn,
        conn.transaction(force_rollback=True),
    ):
        yield conn
