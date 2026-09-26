"""Lecturas del corpus para el 8D COMO el usuario (PAT-005): filas del AMFE y familias de AMFE.

Solo `rag.visible_fmea_rows(role)` y `rag.visible_documents(role)` con el rol resuelto desde
acl.json para el Principal (nunca un rol de la petición ni del LLM). Conexión `solaris_app`.
Cada lectura deja un evento `retrieval` con los doc_id/filas devueltos (nunca el contenido).
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from solaris.audit import record_safe
from solaris.rag.acl import resolve_role
from solaris.settings import Settings, get_settings

if TYPE_CHECKING:
    from solaris.auth.core import Principal

# Un AMFE "de pieza" cubre como mucho unas pocas referencias (familia LH/RH, misma tuerca…); uno
# que cubre casi todas es de LÍNEA (p. ej. cataforesis EC-01) y solo aplica si el defecto es de ese
# proceso. Así "no hay AMFE de AR-1012" es cierto aunque AR-1012 pase por la cataforesis.
MAX_PARTS_PART_FMEA = 4
_LINE_PROCESS = {"coating": re.compile(r"(?i)catafor|e-?coat|\bEC-?01\b")}
_PART_RE = re.compile(r"^[A-Z]{2}-\d{4}$")

_SQL_DOCS = (
    "SELECT d.doc_id, d.version, d.title, d.part_refs, d.folder"
    " FROM rag.visible_documents(%(role)s) d"
    " WHERE d.doc_type = 'amfe' AND d.part_refs && %(parts)s::text[] ORDER BY d.doc_id"
)
_SQL_ROWS = (
    "SELECT f.doc_id, f.version, f.sheet, f.row_no, f.process_step, f.failure_mode, f.effect,"
    " f.severity, f.cause, f.occurrence, f.prevention_control, f.detection_control, f.detection,"
    " f.rpn, f.folder FROM rag.visible_fmea_rows(%(role)s) f"
    " WHERE (f.doc_id, f.version) IN (SELECT x, y FROM unnest(%(docs)s::text[], %(vers)s::text[])"
    " AS t(x, y)) ORDER BY f.doc_id, f.sheet, f.row_no"
)


def _conn(settings: Settings):
    from solaris.db import connect_app

    return connect_app(settings)


def fmea_documents(principal: Principal, part_ref: str, category: str, *,
                   settings: Settings | None = None, conn: Any = None) -> dict[str, Any]:
    """AMFE aplicables a la pieza: los de pieza (≤ 4 referencias) y, si el defecto es de un
    proceso de línea (recubrimiento), el AMFE de esa línea. Devuelve también la familia de
    piezas de los AMFE de pieza (misma tuerca, LH/RH…), que D1 usa para buscar antecedentes."""
    s = settings or get_settings()
    role = resolve_role(principal.user, s.acl_file)
    if role is None or not _PART_RE.match(part_ref or ""):
        return {"part_docs": [], "line_docs": [], "family": [part_ref] if part_ref else []}
    own = conn is None
    c = conn or _conn(s)
    try:
        rows = c.execute(_SQL_DOCS, {"role": role, "parts": [part_ref]}).fetchall()
    finally:
        if own:
            c.close()
    docs = [dict(zip(("doc_id", "version", "title", "part_refs", "folder"), r, strict=True))
            for r in rows]
    part_docs = [d for d in docs if len(d["part_refs"] or []) <= MAX_PARTS_PART_FMEA]
    rx = _LINE_PROCESS.get(category)
    line_docs = [d for d in docs if d not in part_docs and rx is not None
                 and (rx.search(d["title"] or "") or rx.search(d["doc_id"]))]
    family = sorted({p for d in part_docs for p in d["part_refs"]} | {part_ref})
    return {"part_docs": part_docs, "line_docs": line_docs, "family": family}


def fmea_rows(principal: Principal, docs: list[dict[str, Any]], *,
              settings: Settings | None = None, conn: Any = None,
              case_id: str | None = None) -> list[dict[str, Any]]:
    """Filas visibles de los AMFE indicados (ya filtrados por ACL en `fmea_documents`)."""
    s = settings or get_settings()
    role = resolve_role(principal.user, s.acl_file)
    if role is None or not docs:
        return []
    own = conn is None
    c = conn or _conn(s)
    try:
        cur = c.execute(_SQL_ROWS, {"role": role, "docs": [d["doc_id"] for d in docs],
                                    "vers": [d["version"] for d in docs]})
        cols = [x.name for x in cur.description]
        rows = [dict(zip(cols, r, strict=True)) for r in cur.fetchall()]
    finally:
        if own:
            c.close()
    record_safe("retrieval", principal.actor, {
        "kind": "fmea_rows", "role": role,
        "documents": [{"doc_id": d["doc_id"], "version": d["version"]} for d in docs],
        "rows": [{"doc_id": r["doc_id"], "sheet": r["sheet"], "row": r["row_no"]} for r in rows],
    }, settings=s, case_id=case_id)
    return rows
