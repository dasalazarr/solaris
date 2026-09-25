"""ACL por carpeta del corpus (F01). Fuente: app/data/synthetic/acl.json (solo lectura).

Uso (desde app/backend):  uv run python -m solaris.rag.acl   # re-sincroniza rag.folder_acl

La sincronización reemplaza el contenido de `rag.folder_acl` en una transacción: un cambio de
permisos en el origen se refleja en el siguiente re-sync (criterio de F01),
incluidas las revocaciones.
"""

import json
import sys
from pathlib import Path

import psycopg

from solaris.settings import REPO_ROOT

DEFAULT_ACL_FILE = REPO_ROOT / "app" / "data" / "synthetic" / "acl.json"


class ACLError(ValueError):
    pass


def load_folder_acl(path: Path = DEFAULT_ACL_FILE) -> list[tuple[str, str]]:
    """Devuelve pares (folder, role) ordenados. Valida que cada rol esté declarado en `roles`."""
    data = json.loads(path.read_text(encoding="utf-8"))
    roles = data.get("roles")
    folders = data.get("folders")
    if not isinstance(roles, list) or not isinstance(folders, dict):
        raise ACLError("acl.json debe tener 'roles' (lista) y 'folders' (objeto)")
    declared = set(roles)
    pairs: set[tuple[str, str]] = set()
    for folder, folder_roles in folders.items():
        if not isinstance(folder_roles, list):
            raise ACLError(f"Roles de {folder!r} deben ser una lista")
        for role in folder_roles:
            if role not in declared:
                raise ACLError(f"Rol no declarado {role!r} en la carpeta {folder!r}")
            pairs.add((folder, role))
    return sorted(pairs)


def resolve_role(user: str, path: Path = DEFAULT_ACL_FILE) -> str | None:
    """Rol de negocio de `user` según `acl.json` (users → role). None si el usuario no existe o su
    rol no está declarado en `roles`. Se relee en cada llamada: una baja se aplica al momento.

    Es el ÚNICO origen del rol para la recuperación (M2-T5): nunca un parámetro de la petición ni
    la salida del LLM (PAT-005). En M4-T1 `user` vendrá del usuario autenticado (F09).
    """
    if not isinstance(user, str) or not user:
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    users = data.get("users")
    roles = data.get("roles")
    if not isinstance(users, dict) or not isinstance(roles, list):
        raise ACLError("acl.json debe tener 'users' (objeto) y 'roles' (lista)")
    entry = users.get(user)
    role = entry.get("role") if isinstance(entry, dict) else None
    return role if isinstance(role, str) and role in roles else None


def sync_folder_acl(conn: psycopg.Connection, path: Path = DEFAULT_ACL_FILE) -> int:
    """Reemplaza rag.folder_acl con el contenido de acl.json. Devuelve el número de filas."""
    pairs = load_folder_acl(path)
    with conn.transaction(), conn.cursor() as cur:
        cur.execute("DELETE FROM rag.folder_acl")
        cur.executemany("INSERT INTO rag.folder_acl (folder, role) VALUES (%s, %s)", pairs)
    return len(pairs)


def main() -> int:
    from solaris.db import connect

    with connect() as conn:
        n = sync_folder_acl(conn)
    print(f"rag.folder_acl sincronizada: {n} filas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
