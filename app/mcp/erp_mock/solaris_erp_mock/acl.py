"""ACL por tabla del ERP según el rol del usuario (acl.json → `erp_tables`, `users`).

El rol NUNCA lo decide el LLM: el backend orquestador lo deriva del usuario autenticado y lo
inyecta en el `_meta` de la petición MCP (ver server.py). Aquí se valida contra acl.json:
usuario conocido, rol coherente con el usuario y tablas permitidas para ese rol. Todo lo demás
se deniega (deny-by-default).
"""

import json
from dataclasses import dataclass
from pathlib import Path


class AccessDenied(PermissionError):
    """Denegación con un motivo apto para mostrar al usuario."""


@dataclass(frozen=True)
class Caller:
    user: str
    role: str


@dataclass(frozen=True)
class ErpAcl:
    users: dict[str, str]  # user -> role
    tables: dict[str, frozenset[str] | None]  # role -> tablas (None = todas)

    @classmethod
    def load(cls, path: Path) -> "ErpAcl":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        roles = set(data["roles"])
        users = {u: info["role"] for u, info in data["users"].items()}
        tables: dict[str, frozenset[str] | None] = {}
        for role, spec in data["erp_tables"].items():
            if role not in roles:
                raise ValueError(f"Rol no declarado en erp_tables: {role!r}")
            tables[role] = None if spec == "*" else frozenset(spec)
        return cls(users=users, tables=tables)

    def resolve(self, user: str | None, role: str | None) -> Caller:
        """Valida la identidad inyectada por el backend. Rol ausente = rol del usuario."""
        if not user:
            raise AccessDenied("Falta el contexto de usuario (lo inyecta el backend, no el modelo)")
        expected = self.users.get(user)
        if expected is None:
            raise AccessDenied(f"Usuario desconocido: {user!r}")
        if role is not None and role != expected:
            raise AccessDenied(f"El rol {role!r} no corresponde al usuario {user!r}")
        return Caller(user=user, role=expected)

    def check(self, caller: Caller, tables: frozenset[str]) -> None:
        if caller.role not in self.tables:
            raise AccessDenied(f"El rol {caller.role!r} no tiene acceso al ERP")
        allowed = self.tables[caller.role]
        if allowed is None:
            return
        missing = sorted(tables - allowed)
        if missing:
            raise AccessDenied(
                f"El rol {caller.role!r} no tiene permiso sobre las tablas del ERP: "
                f"{', '.join(missing)}"
            )
