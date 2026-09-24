"""Extracción de filas de AMFE a `rag.fmea_rows` (adelanto de M2-T4, F03).

Parser tolerante, pensado para el AMFE "sucio" (AMFE-AR1006-01): cabecera desplazada y en dos
filas, celdas combinadas, filas vacías y valores S/O/D como "8 (ver nota)", "2-3", "3*", "alta" o
" 4". La exactitud por campo se mide en M2-T4; aquí basta con poblar la tabla de forma razonable.

Reglas:
  * Solo hojas con una columna "Modo de fallo" en las 30 primeras filas (la hoja "viejo" del AMFE
    sucio no la tiene y queda fuera; su contenido sí se indexa como chunk).
  * Cabecera en dos filas si la fila siguiente solo tiene etiquetas cortas no numéricas.
  * Las columnas "Tras acciones" (S/O/D revisados) se ignoran para los campos tipados.
  * Una fila se extrae si tiene ≥ 2 campos mapeados no vacíos. `raw` guarda la fila tal cual
    (celdas originales, sin el relleno de combinadas) para trazabilidad.
  * Valoraciones: número dentro de 1–10; en un rango "2-3" se toma el mayor (criterio conservador
    del AMFE); texto sin número ("alta") → NULL. NPR: 1–1000; "#¡VALOR!" → NULL.
"""

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from solaris.rag.parsers import cell_text, iter_sheets, load_grid

TEXT_FIELDS = (
    "process_step", "function", "failure_mode", "effect", "cause", "prevention_control",
    "detection_control", "actions",
)
RATING_FIELDS = ("severity", "occurrence", "detection")
_RANGE_RE = re.compile(r"^\s*~?\s*(\d+)\s*[-–/]\s*(\d+)")
_NUM_RE = re.compile(r"\d+")
_SEP = " // "  # une la etiqueta superior y la inferior de una cabecera en dos filas


@dataclass
class FmeaRow:
    sheet: str
    row_no: int
    fields: dict[str, Any]
    raw: dict[str, Any]


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s.lower()).strip()


def parse_rating(v: Any, lo: int = 1, hi: int = 10) -> int | None:
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, int | float):
        n = int(v) if float(v).is_integer() else None
    else:
        s = str(v).strip()
        if m := _RANGE_RE.match(s):
            n = max(int(m.group(1)), int(m.group(2)))
        elif m := _NUM_RE.search(s):
            n = int(m.group(0))
        else:
            n = None
    return n if n is not None and lo <= n <= hi else None


def _field_for(label: str) -> str | None:
    full = _norm(label)
    if not full or "tras" in full or "after" in full:
        return None
    key = full.split(_SEP)[-1].strip(" .:")
    if key in ("npr", "rpn") or key.startswith("npr"):
        return "rpn"
    if key in ("s", "sev", "severidad", "gravedad", "severity"):
        return "severity"
    if key in ("o", "ocurr", "ocurrencia", "occurrence"):
        return "occurrence"
    if key in ("d", "det", "detectabilidad"):
        return "detection"
    if "modo de fallo" in key or "failure mode" in key:
        return "failure_mode"
    if key.startswith(("efecto", "effect")):
        return "effect"
    if key.startswith(("causa", "cause")):
        return "cause"
    if "prevenc" in key or "prevention" in key:
        return "prevention_control"
    if "deteccion" in key or "detection" in key:
        return "detection_control"
    if "accion" in key or "action" in key:
        return "actions"
    if "paso" in key or "proceso" in key or "process step" in key:
        return "process_step"
    if "funcion" in key or "requisito" in key or "function" in key:
        return "function"
    return None


def _find_header(grid: dict[int, dict[int, Any]]) -> int | None:
    for r in sorted(grid)[:30]:
        for v in grid[r].values():
            if isinstance(v, str) and ("modo de fallo" in _norm(v) or "failure mode" in _norm(v)):
                return r
    return None


def _is_subheader(top: dict[int, Any], nxt: dict[int, Any]) -> bool:
    diffs = [v for c, v in nxt.items() if cell_text(v) != cell_text(top.get(c))]
    return bool(diffs) and all(
        isinstance(v, str) and len(v.strip()) <= 25 and not v.strip().isdigit() for v in diffs
    )


def extract_sheet(ws) -> list[FmeaRow]:
    grid = load_grid(ws)
    h = _find_header(grid)
    if h is None:
        return []
    top = grid[h]
    sub = grid.get(h + 1, {})
    two_rows = _is_subheader(top, sub)
    first_data = h + 2 if two_rows else h + 1
    cols = sorted(set(top) | (set(sub) if two_rows else set()))
    labels: dict[int, str] = {}
    for c in cols:
        t, s = cell_text(top.get(c)), cell_text(sub.get(c)) if two_rows else ""
        labels[c] = t if not s or s == t else (f"{t}{_SEP}{s}" if t else s)
    mapping: dict[int, str] = {}
    used: set[str] = set()
    for c in cols:
        f = _field_for(labels[c])
        if f and f not in used:
            mapping[c] = f
            used.add(f)
    if "failure_mode" not in used:
        return []

    originals: dict[tuple[int, int], Any] = {
        (c.row, c.column): c.value for row in ws.iter_rows() for c in row if c.value is not None
    }
    rows: list[FmeaRow] = []
    for r in sorted(k for k in grid if k >= first_data):
        cells = grid[r]
        fields: dict[str, Any] = {}
        for c, f in mapping.items():
            v = cells.get(c)
            if f in RATING_FIELDS:
                fields[f] = parse_rating(v)
            elif f == "rpn":
                fields[f] = parse_rating(v, 1, 1000)
            else:
                t = cell_text(v)
                fields[f] = t or None
        filled = sum(
            1 for c, f in mapping.items() if cell_text(cells.get(c)) and f != "rpn"
        )
        if filled < 2:
            continue
        raw = {
            ws.cell(row=r, column=c).coordinate: {
                "header": labels.get(c, ""),
                "value": cell_text(originals[(r, c)]),
            }
            for c in sorted(cells)
            if (r, c) in originals
        }
        rows.append(FmeaRow(ws.title, r, fields, raw))
    return rows


def extract_fmea(path: Path) -> list[FmeaRow]:
    """Filas de la primera hoja con cabecera AMFE (la PK de fmea_rows es doc+versión+fila)."""
    for ws, _hidden in iter_sheets(path):
        rows = extract_sheet(ws)
        if rows:
            return rows
    return []
