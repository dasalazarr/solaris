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
