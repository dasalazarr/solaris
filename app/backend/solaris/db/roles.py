"""Contraseñas de los roles de BD de servicio (M3-T1).

Los roles se crean en migraciones versionadas (sin secretos). La contraseña se fija aquí desde
`.env` con un verificador SCRAM-SHA-256 calculado en el cliente (libpq `PQencryptPasswordConn`): el
texto plano nunca viaja al servidor ni puede acabar en su log de sentencias.
"""

import psycopg
from psycopg import sql

from solaris.settings import Settings, get_settings

# rol de BD -> campo de Settings con su contraseña
SERVICE_ROLES: dict[str, str] = {"erp_reader": "erp_reader_password"}


def set_service_role_passwords(
    conn: psycopg.Connection, settings: Settings | None = None
) -> list[str]:
    """Fija la contraseña de cada rol de servicio existente cuyo secreto esté en `.env`.

    Devuelve los roles actualizados. Un rol sin secreto se deja sin contraseña (no puede iniciar
    sesión con scram-sha-256: falla cerrado).
    """
    s = settings or get_settings()
    done: list[str] = []
    for role, field in SERVICE_ROLES.items():
        secret = getattr(s, field)
        if secret is None or not secret.get_secret_value():
            continue
        exists = conn.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (role,)).fetchone()
        if exists is None:
            continue
        verifier = conn.pgconn.encrypt_password(
            secret.get_secret_value().encode("utf-8"), role.encode("utf-8"), b"scram-sha-256"
        )
        conn.execute(
            sql.SQL("ALTER ROLE {} PASSWORD {}").format(
                sql.Identifier(role), sql.Literal(verifier.decode("ascii"))
            )
        )
        done.append(role)
    return done
