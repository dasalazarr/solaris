"""Funciones de puntuación del runner de evals (M2-T7). Python puro, sin BD ni LLM.

Reglas de coincidencia de citas: app/evals/golden/README.md, "Métricas y puntuación".
  * mismo `doc_id` y `version`, y locator compatible:
      PDF → misma página · DOCX → misma sección · XLSX → misma hoja y filas que se solapan;
  * la clave `part` que añade el chunker se ignora.

Diferencias de formato entre el golden y los chunks (M2-T3) que se absorben aquí:
  * filas: el golden usa "a-b" (texto) y el chunk `[a, b]` (lista);
  * sección DOCX no 8D: el chunk guarda `section` = título Heading 1 truncado a 120 caracteres y
    `heading` = título completo (≤200). Se acepta la igualdad con cualquiera de los dos o el prefijo
    cuando `section` está truncado.
"""

from __future__ import annotations

import math
import re
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

SECTION_TRUNC = 120  # solaris.rag.parsers.parse_docx: heading[:120]


# --- locators -----------------------------------------------------------------------------------


def parse_rows(v: Any) -> tuple[int, int] | None:
    """`"13-13"`, `"11–12"`, `[11, 12]`, `(11, 12)` o `12` → (a, b) con a ≤ b. Inválido → None."""
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return (v, v)
    if isinstance(v, str):
        m = re.fullmatch(r"\s*(\d+)\s*(?:[-–]\s*(\d+)\s*)?", v)
        if not m:
            return None
        a = int(m.group(1))
        b = int(m.group(2)) if m.group(2) else a
    elif isinstance(v, list | tuple) and len(v) == 2 and all(
        isinstance(x, int) and not isinstance(x, bool) for x in v
    ):
        a, b = v
    else:
        return None
    return (a, b) if a <= b else None


def rows_overlap(a: tuple[int, int], b: tuple[int, int]) -> bool:
    return a[0] <= b[1] and b[0] <= a[1]


def _section_match(expected: str, loc: Mapping[str, Any]) -> bool:
    sec, head = loc.get("section"), loc.get("heading")
    if not isinstance(expected, str) or not expected:
        return False
    if expected in (sec, head):
        return True
    return isinstance(sec, str) and len(sec) >= SECTION_TRUNC and expected.startswith(sec)


def locator_compatible(expected: Mapping[str, Any], got: Mapping[str, Any]) -> bool:
    """¿El locator de un chunk (`got`) cae en la unidad citable esperada?"""
    if not isinstance(expected, Mapping) or not isinstance(got, Mapping):
        return False
    if "page" in expected:
        p = got.get("page")
        return isinstance(p, int) and not isinstance(p, bool) and p == expected["page"]
    if "sheet" in expected:
        if got.get("sheet") != expected["sheet"]:
            return False
        ea, ga = parse_rows(expected.get("rows")), parse_rows(got.get("rows"))
        return ea is not None and ga is not None and rows_overlap(ea, ga)
    if "section" in expected:
        return _section_match(expected["section"], got)
    return False


def citation_match(expected: Mapping[str, Any], got: Mapping[str, Any], *, doc_only: bool = False
                   ) -> bool:
    """`got` = `Hit.citation()` o un dict con doc_id/version/locator."""
    if expected.get("doc_id") != got.get("doc_id"):
        return False
    if doc_only:
        return True
    return expected.get("version") == got.get("version") and locator_compatible(
        expected.get("locator") or {}, got.get("locator") or {}
    )


# --- ranking ------------------------------------------------------------------------------------


def first_match_rank(expected: Sequence[Mapping[str, Any]], got: Sequence[Mapping[str, Any]],
                     *, doc_only: bool = False) -> int | None:
    """Rango 1-based del primer resultado que coincide con alguna cita esperada (o None)."""
    for i, g in enumerate(got, 1):
        if any(citation_match(e, g, doc_only=doc_only) for e in expected):
            return i
    return None


def hit_at_k(rank: int | None, k: int) -> bool:
    return rank is not None and rank <= k


def reciprocal_rank(rank: int | None, k: int | None = None) -> float:
    if rank is None or (k is not None and rank > k):
        return 0.0
    return 1.0 / rank


def recall_at_k(ranks: Iterable[int | None], k: int) -> float | None:
    """Fracción de ítems con al menos una cita esperada en el top-k (hit rate). Sin ítems → None."""
    rs = list(ranks)
    return sum(hit_at_k(r, k) for r in rs) / len(rs) if rs else None


def mrr(ranks: Iterable[int | None], k: int | None = None) -> float | None:
    rs = list(ranks)
    return sum(reciprocal_rank(r, k) for r in rs) / len(rs) if rs else None


def required_docs_covered(required: Iterable[str], got: Sequence[Mapping[str, Any]], k: int
                          ) -> tuple[bool, list[str]]:
    """¿Están TODOS los `required_doc_ids` en el top-k? Devuelve (ok, faltan)."""
    seen = {g.get("doc_id") for g in got[:k]}
    missing = [d for d in required if d not in seen]
    return (not missing, missing)


def percentile(values: Sequence[float], p: float) -> float | None:
    """Percentil con interpolación lineal (como numpy 'linear'). Sin valores → None."""
    if not values:
        return None
    xs = sorted(values)
    if len(xs) == 1:
        return float(xs[0])
    pos = (len(xs) - 1) * p / 100.0
    lo, hi = math.floor(pos), math.ceil(pos)
    return float(xs[lo] + (xs[hi] - xs[lo]) * (pos - lo))


# --- ACL ----------------------------------------------------------------------------------------


def _in_folder(folder: str, parents: Iterable[str]) -> bool:
    return any(folder == p or folder.startswith(p.rstrip("/") + "/") for p in parents)


def acl_violations(got: Sequence[Mapping[str, Any]], *, visible_folders: Iterable[str],
                   forbidden_doc_ids: Iterable[str] = (), forbidden_folders: Iterable[str] = ()
                   ) -> list[dict[str, Any]]:
    """Fragmentos que el usuario no debería ver: fuera de sus carpetas (acl.json) o prohibidos por
    el ítem del golden. Cualquier elemento en la lista = fallo crítico."""
    vis, fdoc, ffold = list(visible_folders), set(forbidden_doc_ids), list(forbidden_folders)
    out = []
    for g in got:
        folder, doc = str(g.get("folder", "")), g.get("doc_id")
        reasons = []
        if not _in_folder(folder, vis):
            reasons.append("carpeta_no_visible")
        if doc in fdoc:
            reasons.append("doc_prohibido")
        if _in_folder(folder, ffold):
            reasons.append("carpeta_prohibida")
        if reasons:
            out.append({"doc_id": doc, "folder": folder, "reasons": reasons})
    return out


def visible_folders_for(role: str | None, acl: Mapping[str, Any]) -> list[str]:
    if role is None:
        return []
    return sorted(f for f, roles in (acl.get("folders") or {}).items() if role in roles)


# --- suite qa (M2-T6): texto de la respuesta ---------------------------------------------------

_DASHES = str.maketrans({"–": "-", "—": "-", "−": "-", " ": " ", " ": " ", " ": " "})


def normalize_text(s: str) -> str:
    """Minúsculas, espacios colapsados, guiones unificados y separadores numéricos normalizados:
    `9,4` = `9.4`; `60.000` = `60,000` = `60000` (golden/README.md, `must_include`)."""
    t = s.translate(_DASHES).lower()
    t = re.sub(r"(?<=\d)[.,](?=\d{3}(?!\d))", "", t)  # separador de miles
    t = re.sub(r"(?<=\d),(?=\d)", ".", t)  # coma decimal
    return re.sub(r"\s+", " ", t).strip()


def must_include_hits(answer: str, must_include: Iterable[str]) -> tuple[bool, list[str]]:
    """(todos presentes, los que faltan)."""
    a = normalize_text(answer)
    missing = [m for m in must_include if normalize_text(m) not in a]
    return (not missing, missing)


def citation_precision(system: Sequence[Mapping[str, Any]], expected: Sequence[Mapping[str, Any]]
                       ) -> tuple[int, int]:
    """(citas del sistema que coinciden con alguna esperada, total de citas del sistema)."""
    ok = sum(any(citation_match(e, c) for e in expected) for c in system)
    return ok, len(system)


# --- contención (8d_cases) ---------------------------------------------------------------------


def compare_sets(expected: Iterable[str], got: Iterable[str]) -> dict[str, Any]:
    e, g = set(expected), set(got)
    return {
        "expected": len(e), "got": len(g), "recall": (len(e & g) / len(e)) if e else 1.0,
        "missing": sorted(e - g), "extra": sorted(g - e), "exact": e == g,
    }
