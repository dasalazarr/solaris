"""Configuración del servidor MCP erp-mock. Lee el `.env` de la raíz del repo (nunca versionado).

A propósito solo declara las credenciales de `erp_reader` (solo SELECT sobre erp) y de
`audit_writer` (solo INSERT en audit.events): este proceso no conoce POSTGRES_PASSWORD ni
DATABASE_URL (superusuario), así que no puede conectar con más privilegios.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PACKAGE_DIR.parent  # app/mcp/erp_mock
REPO_ROOT = PROJECT_DIR.parents[2]
DEFAULT_ACL_FILE = REPO_ROOT / "app" / "data" / "synthetic" / "acl.json"
DEFAULT_LOG_DIR = PROJECT_DIR / "logs"


class ErpSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    erp_reader_password: SecretStr | None = None
    erp_db_host: str = "127.0.0.1"
    solaris_db_port: int = 5433
    erp_db_name: str = "solaris"
    erp_db_user: str = "erp_reader"  # solo se admite este rol (ver db.py)
    erp_db_connect_timeout_s: int = 5
    erp_acl_file: Path = DEFAULT_ACL_FILE
    erp_mock_log_dir: Path = DEFAULT_LOG_DIR
    # Audit (M4-T2, F08): por defecto a audit.events con el rol audit_writer; "jsonl" solo en dev.
    erp_mock_audit_sink: Literal["db", "jsonl"] = "db"
    audit_writer_password: SecretStr | None = None
    audit_db_name: str = "solaris"


@lru_cache
def get_settings() -> ErpSettings:
    return ErpSettings()
