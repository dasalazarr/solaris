"""Lógica de dominio del 8D D1–D4 en Python puro (sin LangGraph, sin E/S). M3-T3, F04.

- `classify_defect`: categoría del defecto (soldadura MIG, tuerca soldada, material, recubrimiento,
  estampación) a partir del texto VISIBLE de la reclamación y de la ficha de la pieza del ERP.
- `team_roles` + `match_names`: D1. Los roles salen del cliente, de la pieza y del lote; los
  nombres, SOLO de la sección D1 de 8D anteriores que el usuario puede ver (con su cita). Sin
  evidencia → "por asignar": nunca se inventa una persona.
- `choose_material` / `select_scope_parts` / `lot_row` / `summarize_scope`: D3. Qué lote de
  material define el alcance, qué piezas lo consumieron y el resumen por lote con
  `qty_not_shipped`.
- Textos y estados de D4 (las reglas sobre la salida del modelo están en `nodes._validate_*`).
"""

from __future__ import annotations

import re
import unicodedata
from datetime import date
from typing import Any

# --- idioma --------------------------------------------------------------------------------------

LANGS = ("ES", "EN")


def norm_lang(value: Any, default: str = "ES") -> str:
    v = str(value or "").strip().upper()[:2]
    return v if v in LANGS else default


def _fold(text: str) -> str:
    t = unicodedata.normalize("NFKD", (text or "").lower())
    return "".join(ch for ch in t if not unicodedata.combining(ch))


# --- categoría del defecto -----------------------------------------------------------------------

CATEGORIES = ("weld_nut", "coating", "weld_seam", "material", "stamping", "other")
_CAT_WORDS: dict[str, tuple[str, ...]] = {
    "weld_nut": ("weld nut", "tuerca", "nut ", "push-out", "push out", "torque", "par de "),
    "coating": ("e-coat", "ecoat", "cataforesis", "coating", "paint", "pintura", "crater",
                "poro", "pores"),
    "weld_seam": ("mig", "weld seam", "cordon", "soldadura", "weld", "pull-out", "fusion",
                  "arrancamiento"),
    "material": ("hardness", "dureza", "retention", "retencion", "spring", "muelle", "tensile",
                 "traccion", "material", "coil", "bobina", "brittle", "fragil"),
    "stamping": ("burr", "rebaba", "hole", "agujero", "diameter", "diametro", "taladro",
                 "flatness", "planitud", "punch", "punzon"),
}


def classify_defect(text: str, part: dict[str, Any]) -> str:
    """Categoría del defecto: la de más coincidencias entre las posibles para la pieza (la
    tuerca soldada exige `uses_weld_nut`; la soldadura MIG, célula de soldadura). Empate → el
    orden de CATEGORIES."""
    t = _fold(text) + " " + _fold(str(part.get("special_char") or ""))
    hits = {c: sum(t.count(w) for w in ws) for c, ws in _CAT_WORDS.items()}
    if not part.get("uses_weld_nut"):
        hits["weld_nut"] = 0
    if not part.get("weld_cell"):
        hits["weld_seam"] = 0
    best = max(CATEGORIES[:-1], key=lambda c: (hits[c], -CATEGORIES.index(c)))
    return best if hits[best] > 0 else "other"


def mentions_weld(text: str) -> bool:
    t = _fold(text)
    return any(w in t for w in ("mig", "weld", "soldadura", "cordon", "seam"))


# --- D3: alcance de la contención ----------------------------------------------------------------

# categoría → tipo de lote de material que define el alcance (None = criterio de utillaje)
MATERIAL_FOR = {"weld_seam": "wire", "weld_nut": "nut", "material": "steel", "coating": None,
                "stamping": None, "other": None}


def choose_material(category: str, defect_text: str, lot: dict[str, Any]) -> tuple[str | None,
                                                                                     str | None]:
    """(tipo, código) del lote de material que define el alcance, o (None, None).

    Recubrimiento a lo largo de la soldadura → hilo de soldadura (no la química del baño, que
    comparten todas las piezas: usarla como único criterio sobredimensiona la contención)."""
    kind = MATERIAL_FOR.get(category)
    if category == "coating" and mentions_weld(defect_text) and lot.get("wire_lot_code"):
        kind = "wire"
    if kind is None:
        return None, None
    code = lot.get(f"{kind}_lot_code")
    return (kind, code) if code else (None, None)


def select_scope_parts(category: str, kind: str, part: dict[str, Any],
                       where_used: list[dict[str, Any]]) -> list[str]:
    """Piezas del alcance entre las que consumieron el lote de material.

    - hilo en soldadura MIG → piezas de la misma célula (mismo proceso y consumible);
    - tuerca → todas las piezas con tuerca soldada que consumieron ese lote;
    - acero (defecto de material) → todas las piezas que consumieron la bobina;
    - recubrimiento a lo largo del cordón → solo la pieza reclamada.
    Siempre incluye la pieza reclamada y solo piezas del mismo cliente o del lote (sin ampliar a
    otros clientes salvo que compartan el lote de material)."""
    ref = part.get("ref")
    refs = {ref} if ref else set()
    for p in where_used:
        if kind == "wire" and category == "weld_seam":
            if p.get("weld_cell") and p.get("weld_cell") == part.get("weld_cell"):
                refs.add(p["part_ref"])
        elif kind == "nut":
            if p.get("uses_weld_nut"):
                refs.add(p["part_ref"])
        elif kind == "steel":
            refs.add(p["part_ref"])
    return sorted(r for r in refs if r)


def lot_row(x: dict[str, Any], *, ships: list[dict[str, Any]], claimed: str | None,
            priority_shift: str | None, notified: date | None) -> dict[str, Any]:
    ok = x.get("qty_ok")
    if ok is None and x.get("qty_produced") is not None:
        ok = int(x["qty_produced"]) - int(x.get("qty_scrap") or 0)
    shipped = x.get("qty_shipped")
    if shipped is None:
        shipped = sum(int(s["qty"]) for s in ships if s["lot_code"] == x["lot_code"])
    not_shipped = x.get("qty_not_shipped")
    if not_shipped is None and ok is not None:
        not_shipped = max(0, ok - shipped)
    prod = x.get("production_date")
    prod_d = date.fromisoformat(prod) if isinstance(prod, str) else prod
    after = bool(notified and prod_d and prod_d >= notified)
    flags = []
    if x["lot_code"] == claimed:
        flags.append("claimed")
    if priority_shift and x.get("shift") == priority_shift:
        flags.append("priority_shift")
    if after:
        flags.append("produced_after_notification")
    if x.get("status") == "in_stock":
        flags.append("in_stock")
    if not_shipped:
        flags.append("parts_in_plant")
    action = "sort_at_customer" if shipped else "none"
    if not_shipped:
        action = "block_in_plant" if not shipped else "block_in_plant_and_sort_at_customer"
    return {"lot_code": x["lot_code"], "part_ref": x.get("part_ref"),
            "production_date": prod_d.isoformat() if prod_d else None, "shift": x.get("shift"),
            "status": x.get("status"), "qty_ok": ok, "qty_shipped": shipped,
            "qty_not_shipped": not_shipped,
            "shipments": sorted(s["shipment_id"] for s in ships if s["lot_code"] == x["lot_code"]),
            "flags": flags, "action": action}


def summarize_scope(rows: list[dict[str, Any]], ships: list[dict[str, Any]]) -> dict[str, Any]:
    per_part: dict[str, int] = {}
    for r in rows:
        per_part[r["part_ref"]] = per_part.get(r["part_ref"], 0) + 1
    lots = {r["lot_code"] for r in rows}
    in_scope = [s for s in ships if s["lot_code"] in lots]
    customers: dict[str, dict[str, int]] = {}
    for s in in_scope:
        c = customers.setdefault(s["customer_code"], {"shipments": 0, "qty": 0})
        c["shipments"] += 1
        c["qty"] += int(s["qty"])
    return {
        "lots": len(rows), "per_part": dict(sorted(per_part.items())),
        "shipments": len({s["shipment_id"] for s in in_scope}),
        "shipped_qty": sum(int(s["qty"]) for s in in_scope),
        "qty_not_shipped": sum(int(r["qty_not_shipped"] or 0) for r in rows),
        "lots_in_stock": sorted(r["lot_code"] for r in rows if r["status"] == "in_stock"),
        "lots_not_shipped": sorted(r["lot_code"] for r in rows if r["qty_not_shipped"]),
        "lots_produced_after_notification": sorted(
            r["lot_code"] for r in rows if "produced_after_notification" in r["flags"]),
        "priority_lots": sorted(r["lot_code"] for r in rows if "priority_shift" in r["flags"]),
        "by_customer": [{"customer_code": k, **v} for k, v in sorted(customers.items())],
    }


# --- D1: equipo ----------------------------------------------------------------------------------

ROLE_LABELS: dict[str, dict[str, str]] = {
    "champion": {"ES": "Champion / Responsable de Calidad", "EN": "Champion / Quality Manager"},
    "leader": {"ES": "Líder 8D / Ingeniería de calidad cliente",
               "EN": "8D leader / Customer Quality Engineer"},
    "welding": {"ES": "Ingeniería de procesos de soldadura {line}",
                "EN": "Welding process engineering {line}"},
    "coating": {"ES": "Ingeniería L3 (cataforesis)", "EN": "Engineering L3 (e-coat)"},
    "die": {"ES": "Matricería L1 ({die})", "EN": "Tool shop L1 ({die})"},
    "production": {"ES": "Producción {line}", "EN": "Production {line}"},
    "night_shift": {"ES": "Jefe del turno de noche {line}", "EN": "Night shift leader {line}"},
    "shift_leader": {"ES": "Producción {line} (jefe de turno)",
                     "EN": "Production {line} (shift leader)"},
    "lab": {"ES": "Laboratorio / metrología", "EN": "Laboratory / metrology"},
    "maintenance": {"ES": "Mantenimiento", "EN": "Maintenance"},
    "purchasing": {"ES": "Compras / calidad de proveedor ({supplier})",
                   "EN": "Purchasing / supplier quality ({supplier})"},
}
# Palabras de la columna "rol" de la D1 de un 8D anterior que identifican cada función.
ROLE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "champion": ("champion", "quality manager", "responsable de calidad"),
    "leader": ("8d leader", "lider 8d", "customer quality engineer", "calidad cliente"),
    "welding": ("welding process", "soldadura"),
    "coating": ("e-coat", "ecoat", "cataforesis", "coating", "paint"),
    "die": ("tool shop", "die ", "matricer", "toolmaker"),
    "night_shift": ("night shift", "turno de noche"),
    "shift_leader": ("shift leader", "jefe de turno"),
    "production": ("production manager", "responsable de produccion", "jefe de produccion"),
    "lab": ("metrology", "laboratory", "lab ", "laboratorio", "metrologia"),
    "maintenance": ("maintenance", "mantenimiento"),
    "purchasing": ("purchasing", "supplier quality", "compras", "calidad de proveedor", "buyer"),
}


def line_of(part: dict[str, Any], lot: dict[str, Any]) -> str:
    if lot.get("weld_cell") or part.get("weld_cell"):
        return "L2"
    return "L1"


def team_roles(category: str, part: dict[str, Any], lot: dict[str, Any],
               supplier: str | None, weld_related: bool) -> list[dict[str, Any]]:
    """Roles del equipo D1 (clave, obligatorio) según el defecto, la pieza y el lote."""
    line = line_of(part, lot)
    roles: list[tuple[str, bool, dict[str, str]]] = [("champion", True, {}), ("leader", True, {})]
    if category in ("weld_seam", "weld_nut"):
        cell = lot.get("weld_cell") or part.get("weld_cell") or ""
        roles.append(("welding", True, {"line": f"L2 ({cell})" if cell else "L2"}))
        roles.append(("production", True, {"line": "L2"}))
        if lot.get("shift") == "noche":
            roles.append(("night_shift", True, {"line": "L2"}))
    elif category == "coating":
        roles.append(("coating", True, {}))
        if weld_related:
            cell = lot.get("weld_cell") or part.get("weld_cell") or ""
            roles.append(("welding", True, {"line": f"L2 ({cell})" if cell else "L2"}))
    elif category == "stamping":
        roles.append(("die", True, {"die": part.get("die") or "?"}))
        roles.append(("maintenance", True, {}))
        roles.append(("shift_leader", False, {"line": line}))
    elif category == "material":
        roles.append(("purchasing", True, {"supplier": supplier or "?"}))
        roles.append(("lab", True, {}))
        roles.append(("die", False, {"die": part.get("die") or "?"}))
        roles.append(("shift_leader", False, {"line": line}))
    if not any(r[0] == "lab" for r in roles):
        roles.append(("lab", category == "weld_nut", {}))
    if category in ("weld_seam", "weld_nut") and not any(r[0] == "maintenance" for r in roles):
        roles.append(("maintenance", False, {}))
    if supplier and not any(r[0] == "purchasing" for r in roles):
        roles.append(("purchasing", category == "weld_nut", {"supplier": supplier}))
    return [{"key": k, "required": req, "params": p} for k, req, p in roles]


_D1_ROW_RE = re.compile(r"^\s*([^|\n]{3,60})\|\s*([^|\n]{3,90})\|\s*([^|\n]{2,60})\s*$", re.M)


def d1_members(text: str) -> list[tuple[str, str, str]]:
    """Filas (nombre, rol, departamento) de una sección D1 ("Name | Role | Department")."""
    out = []
    for name, role, dept in _D1_ROW_RE.findall(text or ""):
        n, r = name.strip(), role.strip()
        if _fold(n) in ("name", "nombre") or not re.search(r"[A-Za-zÁÉÍÓÚÑáéíóúñ]{2,}\s+\S", n):
            continue
        out.append((n, r, dept.strip()))
    return out


def match_names(roles: list[dict[str, Any]], d1_hits: list[Any]) -> None:
    """Rellena `suggested` y `citation` de cada rol con personas que aparecen en la D1 de 8D
    anteriores visibles para el usuario. Por rol, la persona más frecuente; empate → el 8D más
    relevante (orden de `d1_hits`). Una persona no se propone para dos roles."""
    used: set[str] = set()
    for r in roles:
        kws = ROLE_KEYWORDS.get(r["key"], ())
        line = (r["params"].get("line") or "")[:2]
        counts: dict[str, list[Any]] = {}
        for h in d1_hits:
            for name, role, dept in d1_members(h.content):
                fr = _fold(role) + " "
                if not any(k in fr for k in kws):
                    continue
                if r["key"] == "production" and line and line.lower() not in fr + _fold(dept):
                    continue
                counts.setdefault(name, []).append(h)
        best = sorted((n for n in counts if n not in used),
                      key=lambda n: (-len(counts[n]), d1_hits.index(counts[n][0])))
        if best:
            h = counts[best[0]][0]
            used.add(best[0])
            r["suggested"] = best[0]
            r["citation"] = {"doc_id": h.doc_id, "version": h.version, "locator": h.locator}
        else:
            r["suggested"] = None
            r["citation"] = None


def role_label(key: str, params: dict[str, str], lang: str) -> str:
    tpl = ROLE_LABELS[key][norm_lang(lang)]
    try:
        return tpl.format(**{"line": "", "die": "", "supplier": "", **params}).strip()
    except (KeyError, IndexError):
        return tpl


# --- D4: reglas del servidor ---------------------------------------------------------------------

STATUSES = ("probable", "a_verificar", "descartada")
RELATIONS = ("misma_causa_probable", "sintoma_similar_causa_distinta", "analogia",
             "no_relacionado")
CATEGORIES_6M = ("man", "machine", "method", "material", "measurement", "environment")
MECHANISMS = ("occurrence", "non_detection", "contributing")
TEXT = {
    "no_fmea": {"ES": "No hay AMFE de {part} en el repositorio accesible: hipótesis fuera del "
                      "AMFE; hueco a cerrar.",
                "EN": "No PFMEA for {part} in the accessible repository: hypothesis outside the "
                      "PFMEA; gap to close."},
    "gap_default": {"ES": "Causa no contemplada en el AMFE: valorar añadir la fila.",
                    "EN": "Cause not covered by the PFMEA: consider adding the row."},
    "link_dropped": {"ES": "El vínculo al AMFE propuesto no corresponde a ninguna fila "
                           "existente y se ha descartado.",
                     "EN": "The proposed PFMEA link does not match any existing row and was "
                           "discarded."},
    "no_evidence": {"ES": "Sin evidencia citada válida: a verificar.",
                    "EN": "No valid cited evidence: to be verified."},
    "not_in_complaint": {"ES": "No consta en la reclamación.",
                         "EN": "Not stated in the complaint."},
}


def t(key: str, lang: str, **kw: Any) -> str:
    return TEXT[key][norm_lang(lang)].format(**kw)
