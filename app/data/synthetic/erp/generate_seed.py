#!/usr/bin/env python3
"""Genera seed.sql del ERP mock de Componentes Arga S.L. (DATOS SINTÉTICOS, ADR-0004).

Determinista (semilla fija): `python3 app/data/synthetic/erp/generate_seed.py` reescribe seed.sql.
La fuente de verdad del escenario es app/data/synthetic/PLANT.md (§3 referencias, §4 proveedores,
§5 familias de recurrencia, §6 códigos, §11 registro de 8D y reclamaciones abiertas).
Solo stdlib; compatible con Python >= 3.9.
"""
from __future__ import annotations

import random
from datetime import date, timedelta
from pathlib import Path

OUT = Path(__file__).with_name("seed.sql")
RNG = random.Random(20260924)
START = date(2024, 1, 8)
TODAY = date(2026, 9, 24)

CUSTOMERS = [
    ("C-OEMN", "OEM Norte", "OEM", "TPL-8D-OEMN (OEM Norte 8D Report v3)", "EN", 24, 10),
    ("C-RIBE", "Ribera Chassis Systems", "Tier1", "TPL-8D-ARGA (plantilla interna)", "ES", 48, 15),
    ("C-LEIZ", "Leitzaran Seating", "Tier1", "TPL-8D-ARGA (plantilla interna)", "EN", 48, 15),
]

SUPPLIERS = [
    ("S-ULTZ", "Aceros Ultzama S.A.", "Bobina de acero DC04 y HSLA"),
    ("S-BIDA", "Fijaciones Bidasoa S.L.", "Tuercas soldables M6/M8"),
    ("S-GOIE", "Hilos y Gases Goierri S.L.", "Hilo MIG y gas de protección"),
    ("S-ARAK", "Química Araxes S.A.", "Pintura y química de cataforesis"),
    ("S-ZIDA", "Tratamientos Zidacos S.L.", "Afilado y rectificado de matrices (servicio)"),
    ("S-ERRO", "Embalajes Erro S.L.", "Cajas retornables y separadores"),
]

# ref, descripción, cliente, routing, material, espesor, característica, clase, prensa, matriz, célula, tuerca
PARTS = [
    ("AR-1001", "Soporte de cableado del vano motor", "C-OEMN", "L1>L3", "DC04", 1.5, "Posición de taladros", "SC", "PR-250", "MT-01", None, False),
    ("AR-1002", "Escuadra de fijación del parachoques trasero", "C-RIBE", "L1>L3", "DC04", 2.0, "Planitud", "SC", "PR-400", "MT-02", None, False),
    ("AR-1003", "Soporte de la bandeja de baterías (lado izquierdo)", "C-OEMN", "L1>L2>L3", "HSLA 420", 3.0, "Resistencia de la soldadura MIG", "CC", "PR-400", "MT-03", "CR-01", False),
    ("AR-1004", "Soporte de la bandeja de baterías (lado derecho)", "C-OEMN", "L1>L2>L3", "HSLA 420", 3.0, "Resistencia de la soldadura MIG", "CC", "PR-400", "MT-04", "CR-01", False),
    ("AR-1005", "Refuerzo del travesaño del subchasis", "C-RIBE", "L1>L2>L3", "HSLA 340", 2.5, "Penetración de la soldadura", "CC", "PR-400", "MT-05", "CR-02", False),
    ("AR-1006", "Soporte del compresor de climatización", "C-OEMN", "L1>L2>L3", "DC04", 2.0, "Par de la tuerca soldada", "SC", "PR-250", "MT-06", "SP-01", True),
    ("AR-1007", "Brida de anclaje del cinturón de seguridad", "C-LEIZ", "L1>L3", "HSLA 500", 3.5, "Diámetro del agujero y rebaba", "CC", "PR-250", "MT-07", None, False),
    ("AR-1008", "Placa de refuerzo de la bisagra del portón", "C-OEMN", "L1>L3", "DC04", 2.5, "Posición del taladro", "SC", "PR-250", "MT-08", None, False),
    ("AR-1009", "Soporte del radiador de baja temperatura", "C-OEMN", "L1>L2>L3", "DC04", 1.5, "Espesor del e-coat", "SC", "PR-250", "MT-09", "CR-02", False),
    ("AR-1010", "Soporte del inversor de potencia", "C-OEMN", "L1>L2>L3", "HSLA 420", 2.5, "Par de la tuerca soldada", "SC", "PR-400", "MT-10", "CR-02", True),
    ("AR-1011", "Escuadra del bastidor del asiento", "C-LEIZ", "L1>L2>L3", "HSLA 340", 2.0, "Resistencia del punto de soldadura", "CC", "PR-250", "MT-11", "SP-01", False),
    ("AR-1012", "Clip de sujeción del tubo de freno", "C-RIBE", "L1>L3", "Acero para muelles", 1.0, "Fuerza de retención", "SC", "PR-250", "MT-12", None, False),
]
PART = {p[0]: p for p in PARTS}
MIG_CELLS = {"CR-01", "CR-02"}

# Notas de lotes de material que alimentan las historias (PLANT.md §4–5). (proveedor, material, fecha) -> (código, nota, certificado_ok)
SPECIAL_MATERIAL = {
    ("S-GOIE", "Hilo MIG G3Si1 1,0 mm", date(2026, 8, 18)): ("S-GOIE-260117", "Cambio de fabricante de origen del hilo (mismo grado G3Si1)", True),
    ("S-ULTZ", "HSLA 340", date(2025, 2, 20)): (None, "Límite elástico medido en recepción en el mínimo de especificación", True),
    ("S-BIDA", "Tuerca soldable M8 Zn-Ni", date(2025, 4, 25)): (None, "Espesor de recubrimiento Zn-Ni en el límite superior", True),
    ("S-ARAK", "Química cataforesis", date(2024, 5, 27)): (None, "Reclamación interna: fosfatos en el baño por encima del objetivo", True),
}

# Registro canónico de 8D históricos (PLANT.md §11): id, cliente, ref, fecha de recepción, defecto, cantidad, familia (solo interna, no se exporta)
HIST_8D = [
    ("8D-ARGA-2024-004", "C-OEMN", "AR-1003", date(2024, 5, 14), "Grieta en el cordón MIG del soporte de baterías; rotura en la prueba de arrancamiento del cliente", 38, "A"),
    ("8D-ARGA-2024-007", "C-RIBE", "AR-1002", date(2024, 6, 20), "Escuadras deformadas en la recepción; cajas retornables dañadas", 120, None),
    ("8D-ARGA-2024-009", "C-OEMN", "AR-1009", date(2024, 7, 9), "Poros y cráteres en el e-coat; corrosión en la prueba de niebla salina", 260, None),
    ("8D-ARGA-2024-012", "C-LEIZ", "AR-1007", date(2024, 11, 5), "Rebaba > 0,2 mm en el agujero de anclaje; el cinturón no monta", 410, "B"),
    ("8D-ARGA-2024-013", "C-OEMN", "AR-1006", date(2024, 12, 3), "Par de arrancamiento de la tuerca soldada por debajo de la especificación", 75, None),
    ("8D-ARGA-2025-002", "C-OEMN", "AR-1003", date(2025, 2, 11), "Falta de fusión en el cordón MIG; pieza rota en la línea de montaje", 22, "A"),
    ("8D-ARGA-2025-005", "C-RIBE", "AR-1005", date(2025, 4, 8), "Refuerzo deformado bajo carga en la validación del cliente; material en el límite", 64, None),
    ("8D-ARGA-2025-006", "C-RIBE", "AR-1002", date(2025, 5, 13), "Planitud fuera de tolerancia (0,8 mm frente a 0,5 mm)", 300, None),
    ("8D-ARGA-2025-008", "C-OEMN", "AR-1010", date(2025, 6, 17), "Tuerca soldada gira al apretar; par bajo", 48, None),
    ("8D-ARGA-2025-010", "C-LEIZ", "AR-1007", date(2025, 8, 26), "Diámetro del agujero de anclaje por debajo de la tolerancia y rebaba", 520, "B"),
    ("8D-ARGA-2025-011", "C-OEMN", "AR-1001", date(2025, 9, 16), "Posición de los taladros desplazada 1,2 mm; el clip de cableado no monta", 180, None),
    ("8D-ARGA-2025-014", "C-OEMN", "AR-1003", date(2025, 11, 18), "Grieta en la zona de la raíz del cordón MIG detectada en la auditoría de producto del cliente", 16, "A"),
    ("8D-ARGA-2025-015", "C-RIBE", "AR-1012", date(2025, 12, 9), "Fuerza de retención del clip baja; el tubo de freno se suelta en la prueba", 900, None),
    ("8D-ARGA-2026-001", "C-LEIZ", "AR-1011", date(2026, 2, 10), "Punto de soldadura sin fusión (pegado) en la escuadra", 35, None),
    ("8D-ARGA-2026-003", "C-OEMN", "AR-1008", date(2026, 4, 21), "Posición del taladro fuera de tolerancia; la bisagra no alinea", 90, None),
]

# Reclamaciones nuevas abiertas (M1-T4 redacta los documentos). id, cliente, ref, lote, fecha, defecto, cantidad
OPEN_COMPLAINTS = [
    ("C-OEMN-2026-0312", "C-OEMN", "AR-1003", "L26241-AR1003-02", date(2026, 9, 22), "Crack in MIG weld seam of battery tray bracket LH; 3 parts failed pull-out test at assembly", 3),
    ("C-LEIZ-2026-0088", "C-LEIZ", "AR-1007", "L26245-AR1007-01", date(2026, 9, 18), "Burr > 0.2 mm and undersized anchor hole; seat belt anchor bolt does not fit", 240),
    ("C-OEMN-2026-0327", "C-OEMN", "AR-1009", "L26250-AR1009-01", date(2026, 9, 23), "Pores and craters in e-coat on LT radiator bracket", 60),
    ("C-RIBE-2026-0140", "C-RIBE", "AR-1012", "L26236-AR1012-03", date(2026, 9, 16), "Fuerza de retención del clip por debajo de 45 N en la inspección de recepción", 500),
    ("C-OEMN-2026-0331", "C-OEMN", "AR-1010", "L26252-AR1010-01", date(2026, 9, 23), "Weld nut spins at torque; low push-out force on inverter bracket", 12),
]
# Lotes especiales de las reclamaciones abiertas: lote -> (fecha, turno)
SPECIAL_LOTS = {
    "L26241-AR1003-02": (date(2026, 8, 29), "noche"),
    "L26245-AR1007-01": (date(2026, 9, 2), "tarde"),
    "L26250-AR1009-01": (date(2026, 9, 7), "mañana"),
    "L26236-AR1012-03": (date(2026, 8, 24), "noche"),
    "L26252-AR1010-01": (date(2026, 9, 9), "tarde"),
}


def q(v) -> str:
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, date):
        return f"'{v.isoformat()}'"
    return "'" + str(v).replace("'", "''") + "'"


def insert(table: str, cols: list[str], rows: list[tuple]) -> str:
    if not rows:
        return ""
    body = ",\n".join("  (" + ", ".join(q(v) for v in r) + ")" for r in rows)
    return f"INSERT INTO erp.{table} ({', '.join(cols)}) VALUES\n{body};\n\n"


def lot_code(d: date, ref: str, n: int) -> str:
    return f"L{d.strftime('%y')}{d.timetuple().tm_yday:03d}-{ref.replace('-', '')}-{n:02d}"


def build_material_lots():
    """Lotes de material recibidos periódicamente por (proveedor, material)."""
    streams = [("S-ULTZ", m, 30, "kg") for m in ["DC04", "HSLA 340", "HSLA 420", "HSLA 500", "Acero para muelles"]]
    streams += [("S-GOIE", "Hilo MIG G3Si1 1,0 mm", 42, "kg"), ("S-BIDA", "Tuerca soldable M8 Zn-Ni", 30, "ud"),
                ("S-ARAK", "Química cataforesis", 28, "l")]
    lots, counters = [], {}
    for sup, mat, every, unit in streams:
        d = START - timedelta(days=RNG.randint(5, 20))
        while d <= TODAY:
            yy = d.strftime("%y")
            counters[(sup, yy)] = counters.get((sup, yy), 120) + RNG.randint(1, 3)
            code, note, cert = f"{sup}-{yy}{counters[(sup, yy)]:04d}", None, True
            # Lote especial cercano a la fecha pedida
            for (ssup, smat, sdate), (scode, snote, scert) in SPECIAL_MATERIAL.items():
                if ssup == sup and smat == mat and abs((d - sdate).days) < every / 2:
                    d = sdate
                    code = scode or code
                    note, cert = snote, scert
            qty = {"kg": RNG.randint(8, 24) * 1000, "ud": RNG.randint(20, 60) * 1000, "l": RNG.randint(2, 6) * 1000}[unit]
            lots.append((code, sup, mat, d, qty, unit, cert, note))
            d += timedelta(days=every + RNG.randint(-4, 4))
    lots.sort(key=lambda r: r[3])
    return lots


def latest(lots, sup, mat, when):
    cands = [l for l in lots if l[1] == sup and l[2] == mat and l[3] <= when]
    return cands[-1][0]


def main() -> None:
    mlots = build_material_lots()
    shifts = ["mañana", "tarde", "noche"]
    lots, orders, shipments = {}, [], []
    order_seq, ship_seq = {}, {}

    def add_lot(code, ref, d, shift):
        p = PART[ref]
        yy = d.strftime("%y")
        order_seq[yy] = order_seq.get(yy, 0) + 1
        oid = f"OF-{yy}-{order_seq[yy]:05d}"
        qty = RNG.randint(8, 30) * 100
        scrap = int(qty * RNG.uniform(0.003, 0.02))
        status = "in_stock" if (TODAY - d).days <= 4 else "released"
        orders.append((oid, ref, qty, d, "open" if (TODAY - d).days <= 14 else "closed"))
        lots[code] = [code, ref, oid, d, shift, p[8], p[10], qty, scrap,
                      latest(mlots, "S-ULTZ", p[4], d),
                      latest(mlots, "S-GOIE", "Hilo MIG G3Si1 1,0 mm", d) if p[10] in MIG_CELLS else None,
                      latest(mlots, "S-BIDA", "Tuerca soldable M8 Zn-Ni", d) if p[11] else None,
                      latest(mlots, "S-ARAK", "Química cataforesis", d),
                      status]

    # Producción rutinaria: un lote por referencia y semana
    for i, p in enumerate(PARTS):
        d = START + timedelta(days=i % 5)
        k = 0
        while d <= TODAY - timedelta(days=1):
            add_lot(lot_code(d, p[0], 1), p[0], d, shifts[k % 3])
            d += timedelta(days=7)
            k += 1
    # Lotes especiales de reclamaciones abiertas
    for code, (d, shift) in SPECIAL_LOTS.items():
        ref = "AR-" + code.split("-")[1][2:]
        if code not in lots:
            add_lot(code, ref, d, shift)
        lots[code][4] = shift
    # Envíos
    for code, l in sorted(lots.items(), key=lambda kv: kv[1][3]):
        if l[13] != "released":
            continue
        ref, d = l[1], l[3]
        cust = PART[ref][2]
        remaining = l[7] - l[8]
        parts = 2 if RNG.random() < 0.3 else 1
        for j in range(parts):
            sd = d + timedelta(days=RNG.randint(2, 7) + j * 3)
            if sd > TODAY:
                continue
            yy = sd.strftime("%y")
            ship_seq[yy] = ship_seq.get(yy, 0) + 1
            qty = remaining if j == parts - 1 else remaining // 2
            remaining -= qty
            shipments.append((f"AL-{yy}-{ship_seq[yy]:05d}", code, cust, sd, qty))

    # Reclamaciones históricas: lote rutinario 20–45 días antes, turno de noche para la familia A
    complaints = []
    for rid, cust, ref, rdate, defect, qty, fam in HIST_8D:
        cands = [l for l in lots.values() if l[1] == ref and 20 <= (rdate - l[3]).days <= 45]
        lot = sorted(cands, key=lambda l: l[3])[0]
        if fam == "A":
            lot[4] = "noche"
        seq = int(rid.split("-")[-1]) * 7 + 100
        complaints.append((f"{cust}-{rdate.year}-{seq:04d}", cust, ref, lot[0], rdate, defect, qty, "closed", rid))
    for cid, cust, ref, lcode, rdate, defect, qty in OPEN_COMPLAINTS:
        complaints.append((cid, cust, ref, lcode, rdate, defect, qty, "open", None))

    out = ["-- GENERADO por generate_seed.py — no editar a mano. DATOS SINTÉTICOS (ADR-0004).\n\n"]
    out.append(insert("customers", ["code", "name", "customer_type", "report_template", "report_language", "containment_hours", "report_days"], CUSTOMERS))
    out.append(insert("suppliers", ["code", "name", "supplies"], SUPPLIERS))
    out.append(insert("parts", ["ref", "description", "customer_code", "routing", "material", "thickness_mm", "special_char", "char_class", "press", "die", "weld_cell", "uses_weld_nut"], PARTS))
    out.append(insert("material_lots", ["lot_code", "supplier_code", "material", "received_date", "qty", "unit", "certificate_ok", "notes"], mlots))
    out.append(insert("production_orders", ["order_id", "part_ref", "planned_qty", "start_date", "status"], orders))
    out.append(insert("lots", ["lot_code", "part_ref", "order_id", "production_date", "shift", "press", "weld_cell", "qty_produced", "qty_scrap", "steel_lot_code", "wire_lot_code", "nut_lot_code", "ecoat_lot_code", "status"], [tuple(l) for l in sorted(lots.values(), key=lambda l: (l[3], l[0]))]))
    out.append(insert("shipments", ["shipment_id", "lot_code", "customer_code", "ship_date", "qty"], shipments))
    out.append(insert("complaints", ["complaint_id", "customer_code", "part_ref", "lot_code", "received_date", "defect", "qty_affected", "status", "report_8d_id"], complaints))
    OUT.write_text("".join(out), encoding="utf-8")
    print(f"seed.sql: {len(mlots)} lotes de material, {len(lots)} lotes, {len(shipments)} envíos, {len(complaints)} reclamaciones")


if __name__ == "__main__":
    main()
