"""Configuración del backend. Lee el `.env` de la raíz del repo (nunca versionado).

La clave de OpenRouter se guarda como `SecretStr`: su `repr`/`str` se enmascaran y
no debe registrarse nunca en logs.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parents[1]
DEFAULT_MODELS_FILE = BACKEND_DIR / "config" / "models.yaml"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openrouter_api_key: SecretStr | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    # Postgres: DATABASE_URL tiene prioridad; si falta, se compone con las piezas del
    # docker-compose (POSTGRES_PASSWORD, SOLARIS_DB_PORT). La contraseña nunca se registra.
    database_url: SecretStr | None = None
    postgres_host: str = "127.0.0.1"
    solaris_db_port: int = 5433
    postgres_user: str = "solaris"
    postgres_db: str = "solaris"
    postgres_password: SecretStr | None = None
    db_connect_timeout_s: int = 5
    models_file: Path = DEFAULT_MODELS_FILE

    # Límites de la llamada LLM (acotados a propósito).
    llm_timeout_s: float = 60.0
    llm_max_retries: int = 2
    llm_backoff_s: float = 1.0

    # Cabeceras de atribución de OpenRouter (opcionales, sin datos personales).
    app_referer: str = "https://localhost/solaris-demo"
    app_title: str = "Solaris demo"


@lru_cache
def get_settings() -> Settings:
    return Settings()
