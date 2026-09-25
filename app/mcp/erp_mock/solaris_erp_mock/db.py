"""Acceso de solo lectura al esquema `erp` con el rol `erp_reader`.

Tres capas de "solo lectura" (cualquiera basta): privilegios (solo SELECT), el
`default_transaction_read_only` del rol y, aquí, cada transacción abierta explícitamente READ ONLY.
Cada consulta devuelve su traza (SQL parametrizado + parámetros) para la UI (F05).

ACL por tabla en la BD (M4-T1, PAT-005, migración 007): `erp_reader` no tiene SELECT propio. En cada
transacción se hace `SET LOCAL ROLE erp_<rol>` con el rol de negocio que ya validó
`ErpAcl.resolve()` desde el `_meta`; ese rol solo tiene SELECT sobre las tablas que acl.json le
permite. Así la matriz `erp_tables` se aplica dos veces: en Python (mensaje claro + tool_denied) y
en la BD (aunque un bug de la app se saltara `ErpAcl.check`). Sin caller no hay rol: nada legible.
"""

import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import psycopg
from psycopg import sql
from psycopg.rows import dict_row

from solaris_erp_mock.audit import AuditSink
from solaris_erp_mock.config import ErpSettings

SOURCE = "erp-mock"
READ_ONLY_ROLE = "erp_reader"
BUSINESS_ROLE_PREFIX = "erp_"
_BUSINESS_ROLE_RE = re.compile(r"^[a-z][a-z0-9_]{0,30}$")

# Errores con los que la BD rechaza una escritura, un acceso no concedido o un rol inexistente.
_REJECTED = (
    psycopg.errors.ReadOnlySqlTransaction,
    psycopg.errors.InsufficientPrivilege,
    psycopg.errors.InvalidParameterValue,  # SET ROLE a un rol que no existe
)
_WRITE_SQLSTATE = "25006"  # read_only_sql_transaction



class ErpUnavailable(RuntimeError):
    """El ERP no responde o no hay credenciales: el agente debe decirlo, no inventar (F05)."""


class ErpRejected(RuntimeError):
    """La BD rechazó la sentencia (escritura o tabla no concedida)."""


def db_role_for(role: str) -> str:
    """Rol de BD (NOLOGIN) de un rol de negocio: 'planta' → 'erp_planta'."""
    if not isinstance(role, str) or not _BUSINESS_ROLE_RE.fullmatch(role):
        raise ErpRejected("Rol de negocio no válido para el ERP")
    return BUSINESS_ROLE_PREFIX + role


@dataclass(frozen=True)
class QueryTrace:
    sql: str
    params: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {"sql": " ".join(self.sql.split()), "params": to_jsonable(self.params)}


def to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: to_jsonable(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [to_jsonable(v) for v in value]
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    return value


class ErpReader:
    def __init__(self, settings: ErpSettings, audit: AuditSink) -> None:
        if settings.erp_db_user != READ_ONLY_ROLE:
            raise ValueError(f"El MCP erp-mock solo conecta como {READ_ONLY_ROLE!r}")
        self.settings = settings
        self.audit = audit

    def connect(self) -> psycopg.Connection:
        s = self.settings
        if s.erp_reader_password is None:
            raise ErpUnavailable("Falta ERP_READER_PASSWORD en .env")
        try:
            conn = psycopg.connect(
                host=s.erp_db_host,
                port=s.solaris_db_port,
                dbname=s.erp_db_name,
                user=READ_ONLY_ROLE,
                password=s.erp_reader_password.get_secret_value(),
                connect_timeout=s.erp_db_connect_timeout_s,
                application_name="solaris-erp-mock",
                row_factory=dict_row,
            )
        except psycopg.OperationalError as exc:
            raise ErpUnavailable("ERP no disponible (conexión rechazada o caída)") from exc
        conn.read_only = True  # psycopg abre cada transacción con BEGIN READ ONLY
        return conn

    def run(
        self, queries: list[QueryTrace], *, tool: str, caller: Any = None
    ) -> list[list[dict[str, Any]]]:
        """Ejecuta las consultas en UNA transacción READ ONLY y devuelve sus filas.

        Si la BD rechaza una sentencia (escritura o privilegio) se registra como
        `write_rejected` y se lanza `ErpRejected`.
        """
        results: list[list[dict[str, Any]]] = []
        role = getattr(caller, "role", None)
        db_role = db_role_for(role) if caller is not None else None
        with self.connect() as conn:
            try:
                with conn.transaction():
                    if db_role is not None:
                        conn.execute(
                            sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(db_role))
                        )
                    for q in queries:
                        cur = conn.execute(q.sql, q.params)  # type: ignore[arg-type]  # SQL fijo del módulo
                        rows = cur.fetchall() if cur.description is not None else []
                        results.append([to_jsonable(r) for r in rows])
            except _REJECTED as exc:
                self.audit.emit(
                    {
                        "event": (
                            "write_rejected" if exc.sqlstate == _WRITE_SQLSTATE else "db_denied"
                        ),
                        "db_role": db_role,
                        "source": SOURCE,
                        "tool": tool,
                        "user": getattr(caller, "user", None),
                        "role": getattr(caller, "role", None),
                        "sqlstate": exc.sqlstate,
                        "error": type(exc).__name__,
                        "query": [q.as_dict() for q in queries],
                    }
                )
                if exc.sqlstate == _WRITE_SQLSTATE:
                    msg = "el ERP es de solo lectura"
                else:
                    msg = "el rol del usuario no tiene permiso sobre esas tablas del ERP"
                raise ErpRejected(
                    f"La BD rechazó la sentencia ({type(exc).__name__}): {msg}"
                ) from exc
        return results
