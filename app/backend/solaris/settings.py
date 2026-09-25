"""Configuración del backend. Lee el `.env` de la raíz del repo (nunca versionado).

La clave de OpenRouter se guarda como `SecretStr`: su `repr`/`str` se enmascaran y
no debe registrarse nunca en logs.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# S4 (M2-T8): la clave de OpenRouter solo se envía a estos endpoints (https y host fijo). Un .env
# copiado o manipulado no puede desviar `Authorization: Bearer <clave>` a otro host.
OPENROUTER_BASE_URL_ALLOWLIST = frozenset({"https://openrouter.ai/api/v1"})


def check_openrouter_base_url(value: str) -> str:
    v = (value or "").strip().rstrip("/")
    if v not in OPENROUTER_BASE_URL_ALLOWLIST:
        allowed = ", ".join(sorted(OPENROUTER_BASE_URL_ALLOWLIST))
        raise ValueError(f"OPENROUTER_BASE_URL no permitida: solo {allowed}")
    return v


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
    openrouter_base_url: str = "https://openrouter.ai/api/v1"  # validada contra la allowlist (S4)
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
    # Rol de BD de la API en runtime (M4-T1, PAT-005): solo EXECUTE sobre rag.visible_*, sin SELECT
    # directo sobre rag.* ni acceso a erp/audit. Lo crea la migración 006; migrate fija su clave.
    # El superusuario (DATABASE_URL/POSTGRES_PASSWORD) queda para migraciones, ingesta y ACL.
    solaris_app_password: SecretStr | None = None
    app_db_name: str | None = None  # por defecto, postgres_db

    # Autenticación del demo (M4-T1, F09; ADR-0002: sin Keycloak). JWT HS256 firmado con
    # AUTH_JWT_SECRET (≥32 caracteres; sin él no hay login: falla cerrado). Expiración corta y
    # cierre por inactividad (E1-US4, dispositivos compartidos en planta). El rol NUNCA va en el
    # token: se resuelve en cada petición desde acl.json (una baja o un cambio aplica al momento).
    auth_jwt_secret: SecretStr | None = None
    auth_token_ttl_s: int = 1800  # vida máxima del token y de la sesión
    auth_idle_timeout_s: int = 900  # sin peticiones durante este tiempo → sesión cerrada
    auth_max_failed_logins: int = 5  # fallos seguidos por usuario antes del bloqueo temporal
    auth_lockout_s: int = 300
    acl_file: Path = REPO_ROOT / "app" / "data" / "synthetic" / "acl.json"
    # Contraseñas de demo de los 4 usuarios de acl.json (≥16 caracteres; vacía = ese usuario no
    # puede iniciar sesión). Campo = "demo_password_" + usuario con [^a-z0-9] → "_".
    demo_password_inaki_calidad: SecretStr | None = None
    demo_password_ander_turno: SecretStr | None = None
    demo_password_auditora_ext: SecretStr | None = None
    demo_password_jon_it: SecretStr | None = None
    models_file: Path = DEFAULT_MODELS_FILE

    # Embeddings (M2-T3, F01). Locales, sin API: ADR-0003 (OpenRouter) aplica a llamadas LLM, no a
    # embeddings. "fastembed" = multilingual-e5-large ONNX (1024 dims); "fake" = determinista, sin
    # descarga (tests). El modelo se descarga una vez, con revisión fijada, a `embed_model_dir`.
    embed_backend: Literal["fastembed", "fake"] = "fastembed"
    embed_model: str = "intfloat/multilingual-e5-large"
    embed_model_repo: str = "qdrant/multilingual-e5-large-onnx"
    embed_model_revision: str = "ac6781cd1cf88b8306a536d7c9d18a5bd57cc14b"
    embed_model_dir: Path = Path.home() / ".cache/solaris/models/multilingual-e5-large-onnx"
    embed_batch_size: int = 16

    # Rerank (M2-T5, F02): cross-encoder local vía fastembed (ONNX, sin torch ni API). "none" lo
    # desactiva; "fake" = solapamiento de tokens, determinista (tests). BAAI/bge-reranker-base es
    # MIT; jinaai/jina-reranker-v2-base-multilingual es mejor multilingüe pero CC-BY-NC-4.0 (no
    # comercial): se deja como alternativa configurable. Revisión fijada, como los embeddings.
    rerank_backend: Literal["fastembed", "fake", "none"] = "fastembed"
    rerank_model: str = "BAAI/bge-reranker-base"
    rerank_model_repo: str = "BAAI/bge-reranker-base"
    rerank_model_revision: str = "2cfc18c9415c912f9d8155881c133215df768a70"
    rerank_model_dir: Path = Path.home() / ".cache/solaris/models/bge-reranker-base"

    # Límites de la llamada LLM (acotados a propósito).
    llm_timeout_s: float = 60.0
    llm_max_retries: int = 2
    llm_backoff_s: float = 1.0

    # /ask (M2-T6): consultas por usuario y minuto (en memoria; 0 = sin límite).
    ask_rate_limit_per_min: int = 10

    # Cabeceras de atribución de OpenRouter (opcionales, sin datos personales).
    app_referer: str = "https://localhost/solaris-demo"
    app_title: str = "Solaris demo"

    @field_validator("openrouter_base_url")
    @classmethod
    def _base_url_allowlist(cls, v: str) -> str:
        return check_openrouter_base_url(v)


@lru_cache
def get_settings() -> Settings:
    return Settings()
