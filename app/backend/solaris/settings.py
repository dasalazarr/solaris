"""Configuración del backend. Lee el `.env` de la raíz del repo (nunca versionado).

La clave de OpenRouter se guarda como `SecretStr`: su `repr`/`str` se enmascaran y
no debe registrarse nunca en logs.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

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
    # Rol solo lectura del MCP erp-mock (M3-T1): lo crea la migración 002; migrate fija la clave.
    erp_reader_password: SecretStr | None = None
    # Audit log (M4-T2, F08): roles audit_writer (solo INSERT) y audit_reader (solo SELECT) que crea
    # la migración 003; migrate fija sus claves. El backend NO usa el superusuario para el audit.
    audit_writer_password: SecretStr | None = None
    audit_reader_password: SecretStr | None = None
    audit_db_name: str | None = None  # por defecto, postgres_db
    # Prompts y respuestas en el payload: "truncate" (sha256 + primeros N caracteres, sin secretos)
    # o "hash" (solo sha256 y longitud). Antes de un piloto con datos reales: "hash".
    audit_prompt_mode: Literal["truncate", "hash"] = "truncate"
    audit_prompt_max_chars: int = 400
    # Fallo del audit: False = se registra un warning y la operación sigue (demo); True = la
    # operación falla (fail-closed, obligatorio antes de un piloto).
    audit_required: bool = False
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
