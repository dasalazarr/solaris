"""Acceso a Postgres (psycopg 3). Conexión construida desde `Settings`, sin registrar secretos."""

import psycopg

from solaris.settings import Settings, get_settings


def connect(settings: Settings | None = None, **kwargs) -> psycopg.Connection:
    """Abre una conexión. `DATABASE_URL` si existe; si no, las piezas del docker-compose.

    La contraseña se pasa como argumento (no se interpola en una URL que pudiera acabar en logs).
    """
    s = settings or get_settings()
    kwargs.setdefault("connect_timeout", s.db_connect_timeout_s)
    kwargs.setdefault("application_name", "solaris-backend")
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
