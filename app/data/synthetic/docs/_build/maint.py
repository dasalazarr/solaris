"""Historias de mantenimiento derivadas del ERP: afilados de MT-07 y cambios de boquilla en CR-01.

Los 8D y los documentos de mantenimiento leen las MISMAS cifras de aquí, para que sean coherentes.
"""
from __future__ import annotations

import random
from datetime import date, timedelta
from functools import lru_cache

import erp_seed as erp

# ----------------------------------------------------------------------------- MT-07 (AR-1007, PR-250)
MT07_INTERVAL_CHANGE = date(2025, 1, 20)        # plan de afilado v3: 40.000 -> 60.000 golpes
MT07_START_COUNTER = 14000                      # golpes acumulados a 08/01/2024 (último afilado 11/2023)
# Afilados forzados por la historia (se hacen ANTES del lote de esa fecha):
MT07_FORCED = {
    date(2024, 4, 16): "Preventivo (plan)",
    date(2024, 10, 1): "Preventivo con retraso (sin hueco en S-ZIDA)",
    date(2024, 12, 17): "Adelantado por parada navideña de S-ZIDA",
    date(2025, 7, 22): "Preventivo (plan)",
    date(2026, 2, 10): "Preventivo (plan)",
}
# Ventanas en las que el afilado no se hace aunque toque (la matriz sigue en prensa)
MT07_NO_SHARPEN = [(date(2024, 4, 17), date(2024, 9, 30)), (date(2024, 12, 18), date(2025, 7, 21)),
                   (date(2025, 7, 23), date(2026, 2, 9)), (date(2026, 2, 11), date(2026, 9, 30))]


@lru_cache(maxsize=1)
def mt07_history():
    """Devuelve (afilados, contador_por_lote). afilado = dict(fecha, golpes, motivo, ot)."""
    c, events, per_lot = MT07_START_COUNTER, [], {}
    seq = 0
    for l in erp.lots_of("AR-1007"):
        d = l["production_date"]
        itv = 40000 if d < MT07_INTERVAL_CHANGE else 60000
        blocked = any(a <= d <= b for a, b in MT07_NO_SHARPEN)
        forced = MT07_FORCED.get(d)
        if forced or (not blocked and c + l["qty_produced"] > itv):
            seq += 1
            sd = d - timedelta(days=3)
            events.append({"date": sd, "strokes": c, "reason": forced or "Preventivo (plan)",
                           "interval": itv, "ot": f"OT-MT-{sd.strftime('%y')}-{seq:03d}"})
            c = 0
        c += l["qty_produced"]
        per_lot[l["lot_code"]] = c
    return events, per_lot


def mt07_counter(lot_code: str) -> int:
    return mt07_history()[1][lot_code]


# ----------------------------------------------------------------------------- CR-01 boquillas
LOG_START = date(2025, 2, 24)   # acción inmediata del 8D-ARGA-2025-002
LOG_END = date(2026, 9, 23)
OPERATORS = {"mañana": ["M. Sanz", "I. Lopetegi", "P. Otano"], "tarde": ["E. Mujika", "R. Iriarte", "A. Beloki"],
             "noche": ["G. Etxarri", "T. Munarriz", "J. Oroz"]}
LEADS = {"mañana": "X. Urrutia", "tarde": "J. Elizalde", "noche": "A. Goñi"}
FORCE_NO_NIGHT = {date(2025, 10, 8), date(2026, 8, 29), date(2026, 8, 26), date(2026, 9, 16)}


def _night_prob(d: date) -> float:
    if d < date(2025, 5, 1):
        return 0.55
    if d < date(2025, 11, 21):
        return 0.38
    if d < date(2026, 1, 10):
        return 0.85   # charla del 21/11/2025 (8D-ARGA-2025-014)
    if d < date(2026, 4, 1):
        return 0.45
    return 0.25


def _wire_changes():
    seen = {}
    for l in sorted(erp.load()["lots"], key=lambda l: l["production_date"]):
        if l["weld_cell"] == "CR-01" and l["wire_lot_code"] not in seen:
            seen[l["wire_lot_code"]] = l["production_date"]
    return seen


@lru_cache(maxsize=1)
def cr01_log():
    rng = random.Random(20260925)
    rows = []
    wire = {d: code for code, d in _wire_changes().items() if LOG_START <= d <= LOG_END}
    d = LOG_START
    while d <= LOG_END:
        if d.weekday() == 6:  # domingo sin producción
            d += timedelta(days=1)
            continue
        for shift, h0, p in (("mañana", 6, 0.96), ("tarde", 14, 0.94), ("noche", 22, _night_prob(d))):
            if shift == "noche" and d in FORCE_NO_NIGHT:
                p = 0.0
            if rng.random() < p:
                rows.append([d, shift, f"{h0:02d}:{rng.randint(2, 25):02d}", "CR-01", "Boquilla + tubo de contacto",
                             "Preventivo 8 h", rng.choice(OPERATORS[shift]), LEADS[shift], ""])
            if rng.random() < 0.05:
                hh = (h0 + rng.randint(2, 6)) % 24
                rows.append([d, shift, f"{hh:02d}:{rng.randint(0, 59):02d}", "CR-01", "Tubo de contacto",
                             "Correctivo", rng.choice(OPERATORS[shift]), LEADS[shift],
                             rng.choice(["Salpicaduras / arco inestable", "Hilo pegado en el tubo", "Obstrucción de boquilla"])])
        if d in wire:
            rows.append([d, "mañana", "07:40", "CR-01", "Bobina de hilo", "Cambio de lote", "M. Sanz", LEADS["mañana"],
                         f"Nuevo lote {wire[d]}. Programa P12 sin cambios"])
        d += timedelta(days=1)
    return rows


def night_stats(a: date, b: date):
    """(noches con cambio preventivo registrado, noches con producción) entre a y b."""
    nights = {r[0] for r in cr01_log() if r[1] == "noche" and r[5] == "Preventivo 8 h" and a <= r[0] <= b}
    total = sum(1 for i in range((b - a).days + 1) if (a + timedelta(days=i)).weekday() != 6)
    return len(nights), total


def day_stats(a: date, b: date):
    ok = {(r[0], r[1]) for r in cr01_log() if r[1] in ("mañana", "tarde") and r[5] == "Preventivo 8 h" and a <= r[0] <= b}
    total = 2 * sum(1 for i in range((b - a).days + 1) if (a + timedelta(days=i)).weekday() != 6)
    return len(ok), total
