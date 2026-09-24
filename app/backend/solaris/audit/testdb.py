"""BD de tests `solaris_test` para el audit log (solo desarrollo).

Uso (desde app/backend):  uv run python -m solaris.audit.testdb

Los tests del audit anexan filas que, por diseño, no se pueden borrar. Para no ensuciar el audit
real del demo (`solaris`), se ejecutan contra `solaris_test`, que esta función **borra y recrea**
aplicando solo las migraciones de audit y del esquema RAG (`NNN_*audit*.sql`, `NNN_*rag*.sql`;
el ERP no: sus tests conectan a `solaris` como `erp_reader`). Los tests de ingesta (M2-T3) escriben
en `rag.*` de esta BD, no en la del demo. Los roles son de clúster: se reutilizan con las
contraseñas que ya fijó `solaris.db.migrate` (hay que haberlo ejecutado antes).
"""

import sys

from psycopg import sql

from solaris.db import connect
from solaris.db.migrate import discover
from solaris.settings import Settings, get_settings

TEST_DB = "solaris_test"


def _connect_to(s: Settings, dbname: str, **kwargs):
    """Conecta como el superusuario de dev a otra BD del mismo servidor."""
    if s.database_url is not None:
        return connect(s, dbname=dbname, **kwargs)  # el kwarg prevalece sobre la URL
    return connect(s.model_copy(update={"postgres_db": dbname}), **kwargs)


def _for_testdb(version: str) -> bool:
    return "_audit" in version or "_rag" in version


def recreate(settings: Settings | None = None) -> list[str]:
    s = settings or get_settings()
    if s.postgres_db == TEST_DB:
        raise RuntimeError("POSTGRES_DB apunta a la BD de tests: no se recrea")
    with _connect_to(s, "postgres", autocommit=True) as admin:
        admin.execute(
            sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(TEST_DB))
        )
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(TEST_DB)))
    applied: list[str] = []
    with _connect_to(s, TEST_DB) as conn, conn.transaction():
        for mig in discover():
            if _for_testdb(mig.version):
                conn.execute(mig.sql)  # type: ignore[arg-type]  # fichero del repo
                applied.append(mig.version)
    return applied


def main() -> int:
    applied = recreate()
    print(f"{TEST_DB} recreada con: {', '.join(applied)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
