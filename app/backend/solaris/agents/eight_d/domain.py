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
# Relaciones que puede devolver el LLM (enum del esquema; el prompt no cambia en M3-T7).
RELATIONS = ("misma_causa_probable", "sintoma_similar_causa_distinta", "analogia",
             "no_relacionado")
# Relación que solo asigna el servidor (M3-T7): mismo síntoma calculado con datos del ERP, con la
# causa sin juzgar o degradada por contradicción. Nunca "misma causa".
SAME_SYMPTOM = "mismo_sintoma"
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


# --- D4: relación con 8D anteriores (M3-T7, reglas deterministas del servidor) -------------------
#
# Regla 1 (mismo síntoma): un 8D del ERP de la misma pieza o de su familia de AMFE cuyo defecto
#   registrado cae en la MISMA categoría que la reclamación (`classify_defect`, con la ficha de la
#   pieza reclamada) es "mismo síntoma": siempre se lista y el LLM no puede marcarlo
#   `no_relacionado`. Para defectos de material, la "familia" es la del material: otra pieza del
#   mismo cliente cuyo lote reclamado usó acero del mismo proveedor (regla 1b, `analogia`).
# Regla 2 (coherencia de la causa): `misma_causa_probable` se degrada si la reclamación contiene un
#   hecho que contradice la firma del antecedente en su D2 (5W2H):
#   - análisis negativo: un analito que el antecedente encontró (EDX, XRF…) figura como "no
#     detectado" / "sin …" en la reclamación → `descartada`;
#   - característica conforme: una característica que el antecedente midió fuera de
#     especificación figura conforme en la reclamación → `a_verificar`.
#   Solo reglas explícitas sobre las filas What/How del 5W2H y las tablas de resultados; nunca
#   sobre el texto que escribe el modelo.

SYMPTOM_BASES = ("same_part", "amfe_family", "material_family")


def symptom_match(category: str, part: dict[str, Any], prior_defect: str, prior_part: str | None,
                  family: list[str]) -> dict[str, Any] | None:
    """Mismo síntoma entre la reclamación (categoría ya calculada) y una reclamación anterior del
    ERP: misma pieza o familia de AMFE y misma categoría de defecto. None si no lo es."""
    if category == "other" or not prior_part:
        return None
    prior_cat = classify_defect(prior_defect, process_flags(part))
    if prior_cat != category:
        return None
    if prior_part == part.get("ref"):
        basis = "same_part"
    elif prior_part in family:
        basis = "amfe_family"
    else:
        return None
    return {"same": True, "basis": basis, "category": category}


def process_flags(part: dict[str, Any]) -> dict[str, Any]:
    """Ficha de la pieza SIN su característica especial: el defecto anterior se clasifica por su
    propio texto (la característica de la pieza actual lo sesgaría hacia la misma categoría)."""
    return {"uses_weld_nut": part.get("uses_weld_nut"), "weld_cell": part.get("weld_cell")}


def supplier_of(material_lot_code: str | None) -> str | None:
    """Proveedor de un lote de material por su código (<proveedor>-<AA><nnnn>)."""
    code = (material_lot_code or "").strip()
    return code.rsplit("-", 1)[0] if re.fullmatch(r"S-[A-Z]{3,6}-\d{6}", code) else None


def material_family_match(category: str, part: dict[str, Any], prior_defect: str,
                          current_steel: str | None,
                          prior_steel: str | None) -> dict[str, Any] | None:
    """Regla 1b: defecto de material en otra pieza con acero del mismo proveedor."""
    if category != "material" or classify_defect(prior_defect, process_flags(part)) != "material":
        return None
    a, b = supplier_of(current_steel), supplier_of(prior_steel)
    if not a or a != b:
        return None
    return {"same": True, "basis": "material_family", "category": category, "supplier": a}


# Analitos: símbolo (sensible a mayúsculas) y nombres (sin acentos, minúsculas).
ANALYTES: dict[str, tuple[str, ...]] = {
    "P": ("phosphorus", "phosphate", "fosforo", "fosfato"),
    "Zn": ("zinc", "cinc"),
    "Si": ("silicon", "silicate", "silicio", "silicato"),
    "Mn": ("manganese", "manganeso"),
    "Fe": ("iron", "hierro"),
    "Cl": ("chlorine", "chloride", "cloro", "cloruro"),
    "S": ("sulfur", "sulphur", "sulfate", "azufre", "sulfato"),
    "Ca": ("calcium", "calcio"),
    "Na": ("sodium", "sodio"),
    "Cu": ("copper", "cobre"),
    "Cr": ("chromium", "cromo"),
    "Ni": ("nickel", "niquel"),
}
_ANALYSIS_RE = re.compile(r"(?i)\b(?:EDX|EDS|XRF|SEM|spectro\w*|espectro\w*|analysis|analisis)\b")
_ANALYTE_TOKEN = (r"(?:" + "|".join(sorted(ANALYTES, key=len, reverse=True)) + r"|(?i:"
                  + "|".join(n for ns in ANALYTES.values() for n in ns) + r")\w*)")
_SEP = r"\s*(?:,|/|(?i:\band\b|\bor\b|\bnor\b|\by\b|\be\b|\bo\b|\bni\b))\s*"
_LIST = rf"{_ANALYTE_TOKEN}(?:{_SEP}{_ANALYTE_TOKEN})*"
_NEG_AFTER = re.compile(rf"(?<![A-Za-z])({_LIST})\s+(?i:(?:were\s+|was\s+|are\s+|is\s+)?"
                        r"(?:not\s+detected|not\s+found|absent|no\s+detectad\w*|"
                        r"no\s+encontrad\w*|ausentes?))")
_NEG_BEFORE = re.compile(rf"(?i:\b(?:sin|without|free\s+of|no)\b)\s+({_LIST})(?![A-Za-z])")
_NEGATED_BEFORE = re.compile(r"(?i)\b(?:sin|without|no|not|ni|nor|free\s+of)\s*$")


def _analytes_in(text: str) -> list[tuple[str, int]]:
    """(símbolo, posición) de los analitos citados en `text` (símbolos exactos; nombres sin
    acentos y sin distinguir mayúsculas)."""
    t = _fold_keep_case(text)
    out: list[tuple[str, int]] = []
    for sym, names in ANALYTES.items():
        for m in re.finditer(rf"(?<![A-Za-z]){re.escape(sym)}(?![A-Za-z])", t):
            out.append((sym, m.start()))
        for n in names:
            for m in re.finditer(rf"(?i)\b{n}\w*", t):
                out.append((sym, m.start()))
    return out


def analytes_found(text: str) -> set[str]:
    """Analitos que un análisis (EDX, XRF…) ENCONTRÓ: los citados tras la palabra del análisis en
    la misma frase o fila, salvo los negados."""
    found: set[str] = set()
    t = _fold_keep_case(text)
    for m in _ANALYSIS_RE.finditer(t):
        tail = re.split(r"[.;\n|]\s", t[m.end():m.end() + 200] + " ", maxsplit=1)[0]
        for sym, pos in _analytes_in(tail):
            if not _NEGATED_BEFORE.search(tail[max(0, pos - 12):pos]):
                found.add(sym)
    return found


def analytes_absent(text: str) -> set[str]:
    """Analitos declarados NO detectados ("P and Zn not detected", "sin P ni Zn")."""
    out: set[str] = set()
    t = " ".join(_fold_keep_case(text).split())
    for rx in (_NEG_AFTER, _NEG_BEFORE):
        for m in rx.finditer(t):
            out |= {sym for sym, _ in _analytes_in(m.group(1))}
    return out


CHARACTERISTICS: dict[str, tuple[str, ...]] = {
    "thickness": ("thickness", "espesor"),
    "angle": ("angle", "angulo"),
    "hardness": ("hardness", "dureza"),
    "diameter": ("diameter", "diametro"),
    "flatness": ("flatness", "planitud"),
    "penetration": ("penetration", "penetracion"),
    "torque": ("torque-out", "torque"),
    "burr": ("burr", "rebaba"),
    "retention": ("retention", "retencion"),
    "position": ("position", "posicion"),
    "deformation": ("deformation", "deformacion"),
}
_NUM = r"\d+(?:[.,]\d+)?"
_UNIT = r"(?:µm|um|mm|°|kN|Nm|N|HV1|HV|MPa|ppm)?"
_SPEC_WORDS = (r"(?:spec(?:ification)?|requirement|requisito|nominal|tolerance|tolerancia|"
               r"drawing|plano|especificacion)")
_MEAS_SPEC_RE = re.compile(
    rf"(?P<meas>{_NUM}(?:\s*(?:–|-|to|a)\s*{_NUM})?)\s*{_UNIT}[^()\n|;]{{0,24}}?"
    rf"\(\s*(?:{_SPEC_WORDS}:?\s*)(?P<spec>[^)]{{1,40}})\)")
_CONFORM_RE = re.compile(r"(?<!no )(?<!non-)(?<!not )(?<!non )\b(?:conform\w*|within\s+spec"
                         r"\w*|dentro\s+de\s+(?:especificacion|tolerancia)|in\s+tolerance)\b")


def _num(x: str) -> float:
    return float(x.replace(",", "."))


def _interval(text: str) -> tuple[float, float] | None:
    t = text.replace("Ø", "").strip()
    m = re.match(rf"(?:≥|>=)\s*({_NUM})", t)
    if m:
        return _num(m.group(1)), float("inf")
    m = re.match(rf"(?:≤|<=)\s*({_NUM})", t)
    if m:
        return float("-inf"), _num(m.group(1))
    m = re.match(rf"({_NUM})\s*{_UNIT}\s*±\s*({_NUM})", t)
    if m:
        c, d = _num(m.group(1)), _num(m.group(2))
        return c - d, c + d
    m = re.match(rf"({_NUM})\s*{_UNIT}\s*(?:–|-|to|a)\s*({_NUM})", t)
    if m:
        return _num(m.group(1)), _num(m.group(2))
    return None


def _first_characteristic(text: str) -> str | None:
    folded = _fold(text)
    best: tuple[int, str] | None = None
    for key, words in CHARACTERISTICS.items():
        for w in words:
            i = folded.find(w)
            if i >= 0 and (best is None or i < best[0]):
                best = (i, key)
    return best[1] if best else None


def _clauses(text: str) -> list[str]:
    t = " ".join((text or "").split())
    return [c for c in re.split(r"(?<=[.;|])\s+|(?<=:)\s+(?=[A-ZÁÉÍÓÚ])", t) if c.strip()]


def _meas_vs_spec(text: str) -> list[tuple[str, bool]]:
    """(característica, dentro de especificación) de cada "medida (spec …)" del texto."""
    out = []
    t = " ".join((text or "").split())
    for m in _MEAS_SPEC_RE.finditer(t):
        spec = _interval(m.group("spec"))
        nums = [_num(x) for x in re.findall(_NUM, m.group("meas"))]
        if spec is None or not nums:
            continue
        key = _first_characteristic(t[max(0, m.start() - 90):m.start()])
        if key is None:
            continue
        # la característica es la primera nombrada en la cláusula que precede a la medida
        pre = re.split(r"[.;|]\s", t[max(0, m.start() - 90):m.start()])[-1]
        key = _first_characteristic(pre) or key
        out.append((key, spec[0] <= min(nums) and max(nums) <= spec[1]))
    return out


def characteristics_out_of_spec(fivew2h: str) -> set[str]:
    """Características medidas FUERA de especificación en las filas What/How del 5W2H."""
    return {k for k, ok in _meas_vs_spec(fivew2h) if not ok}


def characteristics_conforming(text: str) -> set[str]:
    """Características que la reclamación da por conformes: medida dentro del requisito citado
    o frase con la característica y "conforme"/"within specification"."""
    out = {k for k, ok in _meas_vs_spec(text) if ok}
    for c in _clauses(text):
        f = _fold(c)
        if _CONFORM_RE.search(f):
            key = _first_characteristic(c)
            if key:
                out.add(key)
    return out


_FIVEW2H_ROW = re.compile(r"(?im)^\s*(?:what|how|que|como)\s*\|(.*)$")


def fivew2h_signature_text(d2_text: str) -> str:
    """Filas What/How (Qué/Cómo) del 5W2H de la D2 de un 8D: la firma del defecto anterior."""
    rows = [m.group(1) for m in _FIVEW2H_ROW.finditer(_fold_keep_case(d2_text))]
    return "\n".join(rows)


def _fold_keep_case(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    return "".join(ch for ch in t if not unicodedata.combining(ch))


def cause_contradictions(complaint_text: str, antecedent_d2: str) -> list[dict[str, Any]]:
    """Hechos de la reclamación que contradicen la firma (5W2H) del 8D anterior."""
    sig = fivew2h_signature_text(antecedent_d2)
    if not sig:
        return []
    out: list[dict[str, Any]] = []
    neg = sorted(analytes_found(sig) & analytes_absent(complaint_text))
    if neg:
        out.append({"kind": "analysis_negative", "items": neg})
    conf = sorted(characteristics_out_of_spec(sig) & characteristics_conforming(complaint_text))
    if conf:
        out.append({"kind": "characteristic_conforming", "items": conf})
    return out


def cause_check_status(contradictions: list[dict[str, Any]]) -> str:
    """descartada si un análisis negativo contradice la firma; si solo difiere una característica,
    a_verificar; sin contradicciones, compatible."""
    kinds = {c["kind"] for c in contradictions}
    if "analysis_negative" in kinds:
        return "descartada"
    return "a_verificar" if kinds else "compatible"


def apply_relation_rules(item: dict[str, Any], cand: dict[str, Any],
                         contradictions: list[dict[str, Any]] | None,
                         rules: frozenset[str]) -> dict[str, Any]:
    """Aplica las reglas 1/1b/2 a un antecedente ya validado (relación del LLM o `sin_valorar`).
    Devuelve el elemento con `relation`, `presented_as_same_cause`, `symptom`, `cause_check` y
    `flags` actualizados. Puro: lo usan el nodo D4 y el arnés de respuestas grabadas."""
    out = {**item, "flags": list(item.get("flags") or [])}
    symptom = cand.get("symptom")
    basis = (symptom or {}).get("basis")
    rel = out["relation"]
    if "cause_coherence" in rules and rel == "misma_causa_probable" and contradictions:
        status = cause_check_status(contradictions)
        out["cause_check"] = {"status": status, "contradictions": contradictions}
        rel = "sintoma_similar_causa_distinta" if status == "descartada" else SAME_SYMPTOM
        out["flags"].append(f"same_cause_{status}")
    floor_rules = {"same_part": "same_symptom", "amfe_family": "same_symptom",
                   "material_family": "material_family"}
    if basis and floor_rules.get(basis) in rules and rel in ("no_relacionado", "sin_valorar",
                                                             "analogia"):
        new = "analogia" if basis == "material_family" else SAME_SYMPTOM
        if new != rel:
            out["flags"].append(f"relation_floor_{basis}")
            rel = new
    out["relation"] = rel
    out["presented_as_same_cause"] = rel == "misma_causa_probable"
    out["symptom"] = symptom
    return out
