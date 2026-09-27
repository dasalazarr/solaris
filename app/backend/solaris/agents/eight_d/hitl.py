"""HITL del 8D (M3-T4, F06): versión del borrador, ediciones del aprobador y % editado.

Python puro, sin E/S salvo leer `acl.json`. Lo usan la API (`POST /8d/{id}/approve|reject|export`)
y el nodo `hitl_gate` del grafo, que **vuelve a comprobar** todo desde el registro guardado en el
servidor (nunca desde el valor de reanudación ni desde la petición).

- **Versión** = sha256 del JSON canónico de D1–D4 (claves ordenadas, sin espacios). La aprobación
  se liga a esa versión exacta: si el borrador cambió desde que el aprobador lo vio → 409.
- **Ediciones**: `[{"path": ["d2", "rows", 0, "text"], "value": "..."}]`. Solo reemplazan hojas
  escalares que ya existen (texto, número, booleano o nulo) por otro escalar: no se añade ni se
  quita estructura, y las claves de trazabilidad (`LOCKED_KEYS`: citas, consultas ERP, vínculos al
  AMFE) no se editan: siguen siendo las que generó el servidor.
- **% editado** (métrica de H01, M5-T4): caracteres cambiados (opcodes de difflib por hoja editada)
  sobre el total de caracteres de las hojas del borrador original, con 2 decimales y tope en 100.
- **Aprobadores**: `acl.json → hitl_approvers`, releído en cada petición (PAT-008).
"""

from __future__ import annotations

import copy
import difflib
import hashlib
import json
from pathlib import Path
from typing import Any

SECTIONS = ("d1", "d2", "d3", "d4")
MAX_EDITS = 200
MAX_PATH_DEPTH = 12
MAX_VALUE_CHARS = 4000
MAX_COMMENT_CHARS = 2000
# Trazabilidad que el aprobador NO edita: citas, consultas ERP y vínculos al AMFE siguen siendo los
# que generó el servidor (si una cita está mal, se rechaza el borrador).
LOCKED_KEYS = frozenset({"citations", "citation", "evidence", "query_index", "query_indexes",
                         "locator", "fmea_link", "documents", "sources", "erp_queries", "segment"})
Scalar = str | int | float | bool | None


class EditError(ValueError):
    """Edición no válida (→ 422). El mensaje no incluye el valor."""


def approvers(acl_file: Path) -> frozenset[str]:
    """Roles que pueden aprobar un 8D, desde `acl.json` (se relee en cada llamada). Solo roles
    declarados en `roles`; si falta la clave, nadie aprueba (falla cerrado)."""
    data = json.loads(Path(acl_file).read_text(encoding="utf-8"))
    roles = set(data.get("roles") or [])
    raw = data.get("hitl_approvers")
    if not isinstance(raw, list):
        return frozenset()
    return frozenset(r for r in raw if isinstance(r, str) and r in roles)


def draft_of(values: dict[str, Any]) -> dict[str, Any]:
    return {k: values.get(k) for k in SECTIONS}


def canonical(draft: dict[str, Any]) -> str:
    return json.dumps(draft, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def draft_hash(draft: dict[str, Any]) -> str:
    return hashlib.sha256(canonical(draft).encode("utf-8")).hexdigest()


def _is_scalar(v: Any) -> bool:
    return v is None or isinstance(v, (str, int, float, bool))


def _leaves(node: Any, path: tuple[Any, ...] = ()) -> list[tuple[tuple[Any, ...], Scalar]]:
    if isinstance(node, dict):
        return [x for k in sorted(node) for x in _leaves(node[k], (*path, k))]
    if isinstance(node, list):
        return [x for i, v in enumerate(node) for x in _leaves(v, (*path, i))]
    return [(path, node)]


def _text(v: Scalar) -> str:
    return "" if v is None else str(v)


def validate_edits(raw: Any) -> list[dict[str, Any]]:
    """Forma de `edits` (sin mirar el borrador). Lanza EditError."""
    if raw is None:
        return []
    if not isinstance(raw, list) or len(raw) > MAX_EDITS:
        raise EditError(f"`edits` debe ser una lista de como máximo {MAX_EDITS} ediciones")
    out: list[dict[str, Any]] = []
    for n, e in enumerate(raw):
        if not isinstance(e, dict) or set(e) != {"path", "value"}:
            raise EditError(f"Edición {n}: solo se admiten `path` y `value`")
        path, value = e["path"], e["value"]
        if (not isinstance(path, list) or not 2 <= len(path) <= MAX_PATH_DEPTH
                or path[0] not in SECTIONS
                or not all((isinstance(p, str) and 0 < len(p) <= 64)
                           or (isinstance(p, int) and not isinstance(p, bool) and 0 <= p < 10000)
                           for p in path)):
            raise EditError(f"Edición {n}: `path` no válido")
        if any(isinstance(p, str) and p in LOCKED_KEYS for p in path):
            raise EditError(f"Edición {n}: las citas y la trazabilidad no se editan")
        if not _is_scalar(value) or (isinstance(value, str) and len(value) > MAX_VALUE_CHARS):
            raise EditError(f"Edición {n}: `value` debe ser un escalar (texto ≤ "
                            f"{MAX_VALUE_CHARS} caracteres)")
        if isinstance(value, float) and value != value:  # NaN
            raise EditError(f"Edición {n}: `value` no válido")
        out.append({"path": list(path), "value": value})
    return out


def apply_edits(draft: dict[str, Any], edits: list[dict[str, Any]]) -> tuple[dict[str, Any],
                                                                             list[list[Any]]]:
    """Aplica las ediciones sobre una copia. Devuelve (borrador final, rutas que cambiaron)."""
    final = copy.deepcopy(draft)
    changed: list[list[Any]] = []
    for n, e in enumerate(edits):
        path = e["path"]
        node: Any = final
        for p in path[:-1]:
            ok = (isinstance(node, dict) and isinstance(p, str) and p in node) or (
                isinstance(node, list) and isinstance(p, int) and p < len(node))
            if not ok:
                raise EditError(f"Edición {n}: la ruta no existe en el borrador")
            node = node[p]
        last = path[-1]
        ok = (isinstance(node, dict) and isinstance(last, str) and last in node) or (
            isinstance(node, list) and isinstance(last, int) and last < len(node))
        if not ok:
            raise EditError(f"Edición {n}: la ruta no existe en el borrador")
        if not _is_scalar(node[last]):
            raise EditError(f"Edición {n}: solo se editan valores (texto o número), no estructura")
        if node[last] != e["value"] or type(node[last]) is not type(e["value"]):
            node[last] = e["value"]
            if path not in changed:
                changed.append(list(path))
    return final, changed


def pct_edited(original: dict[str, Any], final: dict[str, Any]) -> float:
    """% de caracteres del borrador original que el aprobador cambió (0–100, 2 decimales)."""
    before = dict(_leaves(original))
    after = dict(_leaves(final))
    total = sum(len(_text(v)) for v in before.values())
    changed = 0
    for path, old in before.items():
        new = after.get(path)
        a, b = _text(old), _text(new)
        if a == b and type(old) is type(new):
            continue
        sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
        changed += sum(max(i2 - i1, j2 - j1) for tag, i1, i2, j1, j2 in sm.get_opcodes()
                       if tag != "equal") or 1
    if total == 0:
        return 0.0 if changed == 0 else 100.0
    return round(min(100.0, 100.0 * changed / total), 2)
