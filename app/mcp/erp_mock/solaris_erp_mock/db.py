"""Acceso de solo lectura al esquema `erp` con el rol `erp_reader`.

Tres capas de "solo lectura" (cualquiera basta): privilegios del rol (solo SELECT sobre erp.*),
`default_transaction_read_only` del rol y, aquí, cada transacción abierta explícitamente READ ONLY.
Cada consulta devuelve su traza (SQL parametrizado + parámetros) para la UI (F05).
"""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import psycopg
from psycopg.rows import dict_row

from solaris_erp_mock.audit import AuditSink
from solaris_erp_mock.config import ErpSettings

SOURCE = "erp-mock"
READ_ONLY_ROLE = "erp_reader"

# Errores con los que la BD rechaza una escritura o un acceso no concedido.
_REJECTED = (psycopg.errors.ReadOnlySqlTransaction, psycopg.errors.InsufficientPrivilege)


class ErpUnavailable(RuntimeError):
    """El ERP no responde o no hay credenciales: el agente debe decirlo, no inventar (F05)."""


class ErpRejected(RuntimeError):
    """La BD rechazó la sentencia (escritura o tabla no concedida)."""


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
        with self.connect() as conn:
            try:
                with conn.transaction():
                    for q in queries:
                        cur = conn.execute(q.sql, q.params)  # type: ignore[arg-type]  # SQL fijo del módulo
                        rows = cur.fetchall() if cur.description is not None else []
                        results.append([to_jsonable(r) for r in rows])
            except _REJECTED as exc:
                self.audit.emit(
                    {
                        "event": "write_rejected",
                        "source": SOURCE,
                        "tool": tool,
                        "user": getattr(caller, "user", None),
                        "role": getattr(caller, "role", None),
                        "sqlstate": exc.sqlstate,
                        "error": type(exc).__name__,
                        "query": [q.as_dict() for q in queries],
                    }
                )
                raise ErpRejected(
                    f"La BD rechazó la sentencia ({type(exc).__name__}): el ERP es de solo lectura"
                ) from exc
        return results
