"""Runner mínimo de migraciones SQL.

Uso (desde app/backend):  uv run python -m solaris.db.migrate [--dry-run]

Aplica en orden alfabético los ficheros `NNN_nombre.sql` de `app/backend/migrations/` que aún no
figuran en `rag.schema_migrations`. Cada migración corre en su propia transacción junto con su
registro (todo o nada). Un lock asesor impide dos runners a la vez. Si el contenido de una migración
ya aplicada cambia (sha256 distinto), se aborta: las migraciones son inmutables, se añade
otra nueva.

Tras aplicar, fija las contraseñas de los roles de servicio desde `.env` (solaris.db.roles).
"""

import argparse
import hashlib
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import psycopg

from solaris.settings import BACKEND_DIR

MIGRATIONS_DIR = BACKEND_DIR / "migrations"
_NAME_RE = re.compile(r"^(\d{3})_[a-z0-9_]+\.sql$")
_LOCK_KEY = 0x501A815  # constante arbitraria para pg_advisory_xact_lock

_BOOTSTRAP = """
CREATE SCHEMA IF NOT EXISTS rag;
CREATE TABLE IF NOT EXISTS rag.schema_migrations (
    version     text PRIMARY KEY,
    sha256      text NOT NULL,
    applied_at  timestamptz NOT NULL DEFAULT now()
);
"""


class MigrationError(RuntimeError):
    pass


@dataclass(frozen=True)
class Migration:
    version: str  # nombre sin extensión, p. ej. '001_rag'
    path: Path
    sql: str
    sha256: str


def discover(migrations_dir: Path = MIGRATIONS_DIR) -> list[Migration]:
    """Migraciones válidas, ordenadas. Rechaza nombres mal formados o números repetidos."""
    found: list[Migration] = []
    seen: set[str] = set()
    for path in sorted(migrations_dir.glob("*.sql")):
        m = _NAME_RE.match(path.name)
        if not m:
            raise MigrationError(
                f"Nombre de migración no válido: {path.name} (esperado NNN_nombre.sql)"
            )
        if m.group(1) in seen:
            raise MigrationError(f"Número de migración repetido: {m.group(1)}")
        seen.add(m.group(1))
        sql = path.read_text(encoding="utf-8")
        found.append(
            Migration(path.stem, path, sql, hashlib.sha256(sql.encode("utf-8")).hexdigest())
        )
    return found


def apply_pending(
    conn: psycopg.Connection, migrations_dir: Path = MIGRATIONS_DIR, dry_run: bool = False
) -> list[str]:
    """Aplica las migraciones pendientes y devuelve sus versiones.

    Usa `conn.transaction()`: si el llamador ya tiene una transacción abierta (tests), cada paso es
    un savepoint dentro de ella y el llamador decide si confirma o revierte.
    """
    migrations = discover(migrations_dir)
    with conn.transaction():
        conn.execute("SELECT pg_advisory_xact_lock(%s)", (_LOCK_KEY,))
        conn.execute(_BOOTSTRAP)
        applied = dict(conn.execute("SELECT version, sha256 FROM rag.schema_migrations").fetchall())

        for mig in migrations:
            if mig.version in applied and applied[mig.version] != mig.sha256:
                raise MigrationError(
                    f"La migración {mig.version} ya aplicada ha cambiado de contenido; "
                    "no se editan migraciones aplicadas, crea una nueva."
                )
        pending = [m for m in migrations if m.version not in applied]
        if dry_run:
            return [m.version for m in pending]
        for mig in pending:
            with conn.transaction():
                conn.execute(mig.sql)  # type: ignore[arg-type]  # fichero del repo, no entrada externa
                conn.execute(
                    "INSERT INTO rag.schema_migrations (version, sha256) VALUES (%s, %s)",
                    (mig.version, mig.sha256),
                )
    return [m.version for m in pending]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Aplica las migraciones SQL pendientes.")
    parser.add_argument("--dry-run", action="store_true", help="solo lista las pendientes")
    args = parser.parse_args(argv)

    from solaris.db import connect
    from solaris.db.roles import set_service_role_passwords

    with connect() as conn:
        done = apply_pending(conn, dry_run=args.dry_run)
        roles = [] if args.dry_run else set_service_role_passwords(conn)
    verb = "Pendientes" if args.dry_run else "Aplicadas"
    print(f"{verb}: {', '.join(done) if done else 'ninguna'}")
    if not args.dry_run:
        print(f"Contraseña fijada para: {', '.join(roles) if roles else 'ningún rol de servicio'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
