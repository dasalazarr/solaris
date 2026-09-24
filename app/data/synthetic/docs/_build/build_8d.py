"""Genera los 15 8D históricos (PLANT.md §11) en calidad/8d/.

Lotes, fechas, cantidades y envíos salen del ERP mock (erp_seed); el texto técnico, de eightd_cases.
"""
from __future__ import annotations

from datetime import timedelta

import erp_seed as erp
from common import Doc, fdate, fnum
from eightd_cases import CASES, PEOPLE

L = {
    "ES": dict(team="D1 · Equipo", prob="D2 · Descripción del problema (5W2H)", cont="D3 · Acciones de contención",
               rc="D4 · Análisis de causa raíz", pca="D5 · Acciones correctivas permanentes (elegidas)",
               impl="D6 · Implantación y validación", prev="D7 · Acciones para prevenir la repetición",
               close="D8 · Cierre y reconocimiento del equipo", name="Nombre", role="Función", dept="Área",
               lot="Lote", ref="Ref.", prod="Fecha fab.", shift="Turno", good="Cant. OK fab.",
               shipped="Enviado (albaranes)", stock="Stock Arga", action="Acción", result="Resultado",
               ish="Diagrama de Ishikawa (6M)", cat="Categoría", cause="Causa potencial", ver="Verificación / estado",
               why_o="5 porqués — ocurrencia", why_d="5 porqués — no detección", rco="Causa raíz de ocurrencia",
               rcd="Causa raíz de no detección", rcv="Verificación de la causa raíz", act="Acción", typ="Tipo",
               owner="Responsable", due="Fecha objetivo", st="Estado", res="Resultados de la validación",
               doc="Documento / sistema", stmt="Declaración del problema", sort="Selección en cliente",
               summary="Resumen de la contención", why="Por qué", w5h2="5W2H"),
    "EN": dict(team="D1 · Team", prob="D2 · Problem description (5W2H)", cont="D3 · Interim containment actions",
               rc="D4 · Root cause analysis", pca="D5 · Permanent corrective actions (chosen)",
               impl="D6 · Implementation and validation", prev="D7 · Actions to prevent recurrence",
               close="D8 · Closure and team recognition", name="Name", role="Role", dept="Department",
               lot="Lot", ref="Part", prod="Prod. date", shift="Shift", good="Qty OK produced",
               shipped="Shipped (delivery notes)", stock="Arga stock", action="Action", result="Result",
               ish="Ishikawa diagram (6M)", cat="Category", cause="Potential cause", ver="Verification / status",
               why_o="5 Whys — occurrence", why_d="5 Whys — non-detection", rco="Root cause — occurrence",
               rcd="Root cause — non-detection", rcv="Root cause verification", act="Action", typ="Type",
               owner="Owner", due="Due date", st="Status", res="Validation results",
               doc="Document / system", stmt="Problem statement", sort="Customer-side sorting",
               summary="Containment summary", why="Why", w5h2="5W2H"),
}
SHIFT_EN = {"mañana": "morning", "tarde": "afternoon", "noche": "night"}


def _shift(s, lang):
    return s if lang == "ES" else SHIFT_EN[s]


def containment_rows(case, lang):
    c = erp.complaint_for_8d(case["id"])
    lot0 = erp.by_key("lots", "lot_code")[c["lot_code"]]
    R = c["received_date"]
    refs = [c["part_ref"]] + case.get("extra_refs", [])
    rows, tot_stock = [], 0
    for ref in refs:
        for l in erp.lots_of(ref):
            if not (lot0["production_date"] <= l["production_date"] <= R):
                continue
            good = l["qty_produced"] - l["qty_scrap"]
            ships = [s for s in erp.shipments_of(l["lot_code"]) if s["ship_date"] <= R]
            shipped = sum(s["qty"] for s in ships)
            stock = good - shipped
            tot_stock += stock
            rej = case.get("rejects", {}).get(l["lot_code"], 0)
            ship_txt = f"{fnum(shipped, lang)} ({', '.join(s['shipment_id'] for s in ships)})" if ships else "0"
            if lang == "ES":
                act = "Bloqueo + selección 100 %" if stock else "Selección en cliente"
                res = f"{rej} NOK" if rej else "0 NOK"
            else:
                act = "Blocked + 100 % sorting" if stock else "Sorting at customer"
                res = f"{rej} NOK" if rej else "0 NOK"
            rows.append([l["lot_code"], ref, fdate(l["production_date"], lang), _shift(l["shift"], lang),
                         fnum(good, lang), ship_txt, fnum(stock, lang), act, res])
    return rows, tot_stock


def build_one(case) -> dict:
    lang = case["lang"]
    t = L[lang]
    c = erp.complaint_for_8d(case["id"])
    part = erp.by_key("parts", "ref")[c["part_ref"]]
    cust = erp.by_key("customers", "code")[c["customer_code"]]
    lot = erp.by_key("lots", "lot_code")[c["lot_code"]]
    R = c["received_date"]
    D = lambda n: fdate(R + timedelta(days=n), lang)  # noqa: E731
    oem = case["template"] == "OEMN"
    version = case.get("version", "v2")
    closed = R + timedelta(days=case.get("close_days", 70))

    if oem:
        doc = Doc(case["id"], version, "8D Report", lang="EN", header_left="OEM Norte 8D Report v3",
                  header_right="Supplier: Componentes Arga S.L. (ARGA)",
                  accent="3A3A3A")
        doc.title("8D REPORT — OEM Norte Supplier Quality", "Form OEMN-SQ-8D rev. 3 · to be returned within 10 working days")
        doc.form([
            ("Supplier", "Componentes Arga S.L."), ("Supplier code", "ARGA"),
            ("OEM Norte complaint no.", c["complaint_id"]), ("Supplier 8D no.", case["id"]),
            ("Part number", part["ref"]), ("Part description", case["part_en"]),
            ("Special characteristic", f"{case['char_en']} ({part['char_class']})"), ("Supplier lot", c["lot_code"]),
            ("Complaint date", fdate(R, "EN")), ("Qty complained", str(c["qty_affected"])),
            ("Containment due (24 h)", fdate(R + timedelta(days=1), "EN")), ("8D due (10 WD)", fdate(R + timedelta(days=14), "EN")),
            ("Report status", "CLOSED"), ("Closure date", fdate(closed, "EN")),
        ])
    else:
        title = "INFORME 8D" if lang == "ES" else "8D REPORT"
        doc = Doc(case["id"], version, "Informe 8D" if lang == "ES" else "8D Report", lang=lang,
                  header_right="TPL-8D-ARGA v2")
        doc.title(f"{title} — {case['id']}", "Plantilla interna TPL-8D-ARGA v2" if lang == "ES" else "Internal template TPL-8D-ARGA v2 (EN)")
        if lang == "ES":
            doc.form([
                ("Cliente", cust["name"]), ("Nº reclamación cliente", c["complaint_id"]),
                ("Referencia", part["ref"]), ("Descripción", part["description"]),
                ("Característica", f"{part['special_char']} ({part['char_class']})"), ("Lote reclamado", c["lot_code"]),
                ("Fecha de recepción", fdate(R)), ("Cantidad reclamada", str(c["qty_affected"])),
                ("Línea / equipo", case["line"]), ("Estado", "CERRADO"),
                ("Fecha de cierre", fdate(closed)), ("Versión", version),
            ])
        else:
            doc.form([
                ("Customer", cust["name"]), ("Customer complaint no.", c["complaint_id"]),
                ("Part number", part["ref"]), ("Description", case["part_en"]),
                ("Characteristic", f"{case['char_en']} ({part['char_class']})"), ("Complained lot", c["lot_code"]),
                ("Date received", fdate(R, "EN")), ("Qty complained", str(c["qty_affected"])),
                ("Line / equipment", case["line"]), ("Status", "CLOSED"),
                ("Closure date", fdate(closed, "EN")), ("Version", version),
            ])

    # D1
    doc.h(t["team"])
    doc.table([t["name"], t["role"], t["dept"]], [[n, *PEOPLE[n][lang]] for n in case["team"]], font=8)
    if case.get("customer_contact"):
        doc.p(case["customer_contact"], italic=True, size=8)

    # D2
    doc.h(t["prob"])
    doc.p(t["stmt"], bold=True)
    doc.p(case["statement"])
    doc.table(["5W2H", ""], [[k, v] for k, v in case["w5h2"]], font=8)
    lot_line = (f"Lote {lot['lot_code']}: fabricado el {fdate(lot['production_date'])} (turno de {lot['shift']}), "
                f"prensa {lot['press']}{', célula ' + lot['weld_cell'] if lot['weld_cell'] else ''}, "
                f"{fnum(lot['qty_produced'])} piezas fabricadas, {lot['qty_scrap']} de chatarra. "
                f"Bobina de acero {lot['steel_lot_code']}"
                f"{', hilo ' + lot['wire_lot_code'] if lot['wire_lot_code'] else ''}"
                f"{', tuercas ' + lot['nut_lot_code'] if lot['nut_lot_code'] else ''}, química de e-coat {lot['ecoat_lot_code']}."
                ) if lang == "ES" else (
                f"Lot {lot['lot_code']}: produced {fdate(lot['production_date'], 'EN')} ({SHIFT_EN[lot['shift']]} shift), "
                f"press {lot['press']}{', cell ' + lot['weld_cell'] if lot['weld_cell'] else ''}, "
                f"{fnum(lot['qty_produced'], 'EN')} parts produced, {lot['qty_scrap']} scrapped. "
                f"Steel coil {lot['steel_lot_code']}"
                f"{', MIG wire ' + lot['wire_lot_code'] if lot['wire_lot_code'] else ''}"
                f"{', weld nuts ' + lot['nut_lot_code'] if lot['nut_lot_code'] else ''}, e-coat chemistry {lot['ecoat_lot_code']}.")
    doc.p(lot_line, italic=True, size=9)
    if case.get("d2_extra"):
        doc.p(case["d2_extra"])

    # D3
    doc.h(t["cont"])
    rows, stock = containment_rows(case, lang)
    doc.p(case["d3_intro"].format(d1=D(1), d0=D(0), d2=D(2), d3=D(3)))
    doc.table([t["lot"], t["ref"], t["prod"], t["shift"], t["good"], t["shipped"], t["stock"], t["action"], t["result"]],
              rows, font=7)
    doc.bullets([x.format(d1=D(1), d0=D(0), d2=D(2), d3=D(3), d5=D(5), stock=fnum(stock, lang)) for x in case["d3"]])

    # D4
    doc.h(t["rc"])
    if case.get("d4_intro"):
        doc.p(case["d4_intro"].format(d4=D(4), d5=D(5), d6=D(6)))
    doc.p(t["ish"], bold=True)
    doc.table([t["cat"], t["cause"], t["ver"]], [list(r) for r in case["ishikawa"]], font=8)
    doc.p(t["why_o"], bold=True)
    doc.table([t["why"], ""], [[f"{i}", w] for i, w in enumerate(case["why_occ"], 1)], font=8)
    doc.p(t["why_d"], bold=True)
    doc.table([t["why"], ""], [[f"{i}", w] for i, w in enumerate(case["why_det"], 1)], font=8)
    doc.kv(t["rco"], case["rc_occ"])
    doc.kv(t["rcd"], case["rc_det"])
    doc.kv(t["rcv"], case["rc_verif"].format(d4=D(4), d5=D(5), d6=D(6), d7=D(7)))

    # D5
    doc.h(t["pca"])
    doc.table([t["act"], t["typ"], t["owner"], t["due"]],
              [[a, ty, o, D(n)] for a, ty, o, n in case["d5"]], font=8)

    # D6
    doc.h(t["impl"])
    doc.p(case["d6"].format(**{f"d{k}": D(k) for k in (10, 14, 20, 21, 28, 30, 35, 42, 45, 56, 60)}))
    doc.p(t["res"], bold=True)
    doc.bullets(case["d6_results"])

    # D7
    doc.h(t["prev"])
    doc.table([t["act"], t["doc"], t["owner"], t["due"], t["st"]],
              [[a, dc, o, D(n), st] for a, dc, o, n, st in case["d7"]], font=8)
    if case.get("d7_note"):
        doc.p(case["d7_note"])

    # D8
    doc.h(t["close"])
    doc.p(case["d8"].format(closed=fdate(closed, lang)))
    champion = case["team"][0]
    leader = case["team"][1]
    sig = [(PEOPLE[leader][lang][0], leader, fdate(closed, lang), "firmado" if lang == "ES" else "signed"),
           (PEOPLE[champion][lang][0], champion, fdate(closed, lang), "firmado" if lang == "ES" else "signed")]
    if oem:
        sig.append(("OEM Norte SQE (acceptance)", case.get("customer_sqe", "M. Ruiz"), fdate(closed + timedelta(days=3), "EN"), "accepted"))
    doc.signatures(sig)
    folder = "calidad/8d"
    fname = f"{case['id']}_{version}.docx"
    doc.save(f"{folder}/{fname}")
    return {
        "doc_id": case["id"], "version": version,
        "title": (f"8D {c['complaint_id']} — {case['title']}"),
        "path": f"{folder}/{fname}", "folder": folder, "doc_type": "8D", "language": lang,
        "part_refs": [c["part_ref"]] + case.get("extra_refs", []),
        "pages": None, "customer": c["customer_code"], "complaint_id": c["complaint_id"],
        "lot_code": c["lot_code"], "date": R.isoformat(),
        "sections": ["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8"],
    }


def build_all() -> list[dict]:
    return [build_one(c) for c in CASES]
