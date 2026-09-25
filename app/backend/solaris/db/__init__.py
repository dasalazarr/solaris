"""Acceso a Postgres (psycopg 3). Conexión construida desde `Settings`, sin registrar secretos.

Dos roles (M4-T1, PAT-005):
- `connect_app()` — **la API en runtime**: rol `solaris_app`, sin SELECT sobre `rag.*` (solo EXECUTE
  sobre `rag.visible_*`), sin acceso a `erp` ni a `audit`, transacciones read-only por defecto.
- `connect()` — **administración**: el superusuario del contenedor (DATABASE_URL o
  POSTGRES_PASSWORD). Solo para migraciones (`solaris.db.migrate`), ingesta
  (`solaris.rag.ingest`), sync de ACL (`solaris.rag.acl`) y la BD de tests. Nunca desde un endpoint.
"""

import psycopg

from solaris.settings import Settings, get_settings

APP_ROLE = "solaris_app"


class DbUnavailable(RuntimeError):
    """Faltan credenciales o la BD no responde."""


def connect(settings: Settings | None = None, **kwargs) -> psycopg.Connection:
    """Conexión ADMINISTRATIVA. `DATABASE_URL` si existe; si no, las piezas del docker-compose.

    La contraseña se pasa como argumento (no se interpola en una URL que pudiera acabar en logs).
    """
    s = settings or get_settings()
    kwargs.setdefault("connect_timeout", s.db_connect_timeout_s)
    kwargs.setdefault("application_name", "solaris-admin")
    if s.database_url is not None:
        return psycopg.connect(s.database_url.get_secret_value(), **kwargs)
    if s.postgres_password is None:
        raise RuntimeError("Falta DATABASE_URL o POSTGRES_PASSWORD en .env")
    return psycopg.connect(
        host=s.postgres_host,
        port=s.solaris_db_port,
        user=s.postgres_user,
        dbname=s.postgres_db,
        password=s.postgres_password.get_secret_value(),
        **kwargs,
    )


def connect_app(settings: Settings | None = None, **kwargs) -> psycopg.Connection:
    """Conexión de RUNTIME como `solaris_app` (mínimo privilegio). Sin clave → DbUnavailable."""
    s = settings or get_settings()
    secret = s.solaris_app_password
    if secret is None or not secret.get_secret_value():
        raise DbUnavailable("Falta SOLARIS_APP_PASSWORD en .env (rol solaris_app)")
    kwargs.setdefault("connect_timeout", s.db_connect_timeout_s)
    kwargs.setdefault("application_name", "solaris-backend")
    try:
        return psycopg.connect(
            host=s.postgres_host,
            port=s.solaris_db_port,
            dbname=s.app_db_name or s.postgres_db,
            user=APP_ROLE,
            password=secret.get_secret_value(),
            **kwargs,
        )
    except psycopg.OperationalError as exc:
        raise DbUnavailable("BD no disponible (solaris_app): conexión rechazada") from exc
