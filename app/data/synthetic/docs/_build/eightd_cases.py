"""Contenido técnico de los 15 8D históricos (PLANT.md §11). DATOS SINTÉTICOS (ADR-0004).

Reglas del escenario (no se escriben en los documentos):
- Las causas raíz de los casos recurrentes son coherentes con PLANT.md §5 pero INCOMPLETAS.
- Solo 8D-ARGA-2025-014 cita un 8D anterior (PAT-004).
Lotes y cantidades salen del ERP (build_8d.containment_rows); aquí solo se citan códigos que existen en el seed.
"""
from __future__ import annotations

from datetime import date

import maint

# Personas ficticias: nombre -> {idioma: (función, área)}
PEOPLE = {
    "Iñaki Etxeberria": {"ES": ("Responsable de Calidad (champion)", "Calidad"), "EN": ("Quality Manager (champion)", "Quality")},
    "Maialen Irigoyen": {"ES": ("Ingeniera de calidad cliente (líder 8D)", "Calidad"), "EN": ("Customer Quality Engineer (8D leader)", "Quality")},
    "Oihana Zabaleta": {"ES": ("Ingeniera de procesos de soldadura", "Ingeniería L2"), "EN": ("Welding Process Engineer", "Engineering L2")},
    "Xabier Urrutia": {"ES": ("Responsable de producción L2", "Producción"), "EN": ("Production Manager L2", "Production")},
    "Ander Goñi": {"ES": ("Jefe de turno de noche L2", "Producción"), "EN": ("Night Shift Leader L2", "Production")},
    "Josu Elizalde": {"ES": ("Jefe de turno de tarde L1/L3", "Producción"), "EN": ("Afternoon Shift Leader L1/L3", "Production")},
    "Koldo Arbizu": {"ES": ("Responsable de mantenimiento", "Mantenimiento"), "EN": ("Maintenance Manager", "Maintenance")},
    "Unai Ezkurra": {"ES": ("Responsable de matricería L1", "Matricería"), "EN": ("Toolroom Lead L1", "Toolroom")},
    "Leire Sarasola": {"ES": ("Técnica de calidad de proveedores", "Compras"), "EN": ("Supplier Quality Engineer", "Purchasing")},
    "Mikel Aranburu": {"ES": ("Técnico de metrología y laboratorio", "Calidad"), "EN": ("Metrology & Lab Technician", "Quality")},
    "Garazi Lizarraga": {"ES": ("Ingeniera de procesos L3 (e-coat)", "Ingeniería L3"), "EN": ("Process Engineer L3 (e-coat)", "Engineering L3")},
    "Amaia Olaberri": {"ES": ("Responsable de logística y expediciones", "Logística"), "EN": ("Logistics Manager", "Logistics")},
}

_n25_a, _n25_t = maint.night_stats(date(2025, 9, 1), date(2025, 10, 31))
_d25_a, _d25_t = maint.day_stats(date(2025, 9, 1), date(2025, 10, 31))
_n25b_a, _n25b_t = maint.night_stats(date(2025, 11, 21), date(2025, 12, 31))
_mt07_24 = maint.mt07_counter("L24268-AR1007-01")
_mt07_25 = maint.mt07_counter("L25196-AR1007-01")


def _es(n: int) -> str:
    return f"{n:,}".replace(",", ".")


CASES = [
    # ------------------------------------------------------------------ 2024-004 · AR-1003 · OEM Norte
    dict(
        id="8D-ARGA-2024-004", lang="EN", template="OEMN", close_days=104,
        title="Crack in MIG weld seam, battery tray bracket LH (AR-1003)",
        part_en="Battery tray bracket LH", char_en="MIG weld strength", line="L2 — CR-01",
        team=["Iñaki Etxeberria", "Maialen Irigoyen", "Oihana Zabaleta", "Xabier Urrutia", "Ander Goñi", "Mikel Aranburu", "Koldo Arbizu"],
        customer_contact="Customer contact: M. Ruiz, Supplier Quality Engineer, OEM Norte battery module assembly.",
        statement=("OEM Norte reported 38 battery tray brackets LH (AR-1003) with a crack along MIG weld seam W2 "
                   "(bracket-to-gusset fillet weld, 45 mm long). The parts failed the pull-out test at the battery tray "
                   "sub-assembly station (requirement ≥ 18 kN); cracked parts broke between 9 and 12 kN. All complained "
                   "parts are traceable to lot L24094-AR1003-01."),
        w5h2=[
            ("What", "Crack / lack of fusion at the root of seam W2 (fillet a = 3.0 mm). Characteristic 'MIG weld strength' is classified CC."),
            ("Where", "Detected at OEM Norte, pull-out test station of the battery tray sub-assembly. Origin: Arga L2, robot cell CR-01, program P12."),
            ("When", "Lot produced 03/04/2024 on the night shift, delivered 09–10/04/2024, detected by the customer on 13/05/2024."),
            ("Who", "Detected by an OEM Norte line operator; reported by the OEM Norte SQE."),
            ("Which", "AR-1003 only. AR-1004 (RH, same cell and wire) was checked at the customer: no failures."),
            ("How", "Fracture along the weld root; macro-section shows root penetration of 0.4–0.6 mm (requirement ≥ 1.0 mm)."),
            ("How many", "38 parts NOK out of 1,189 delivered from the lot (3.2 %)."),
        ],
        rejects={"L24094-AR1003-01": 41, "L24108-AR1003-01": 3},
        d3_intro=("Containment started on {d0}, within 24 h of notification. Scope: every AR-1003 lot welded on CR-01 "
                  "from the complained lot up to the notification date (ERP lots, delivery notes and finished-goods stock)."),
        d3=[
            "Finished-goods stock at Arga ({stock} parts) blocked in the ERP on {d0} and 100 % re-inspected: visual inspection of seam W2 with 10x loupe + chisel test 1 part in 50.",
            "Customer stock and parts in transit sorted by the Arga resident team at OEM Norte on {d1}–{d3} (visual + dye penetrant on seam W2).",
            "Destructive pull-out test, 5 parts per suspect lot: all ≥ 21 kN except lot L24094-AR1003-01 (2 of 5 below 18 kN).",
            "Certified parts identified with a green dot label 'CP 8D-ARGA-2024-004' until the effectiveness check is closed.",
        ],
        d4_intro="Root cause workshop on {d4} (Ishikawa + 5 Whys) with the three L2 shift leaders; weld trials on {d5}.",
        ishikawa=[
            ("Man", "Operator adjusted welding parameters on the teach pendant without authorisation", "CONFIRMED – wire feed speed override −8 % found active on P12"),
            ("Machine", "Wire feeder / drive rolls of CR-01", "Ruled out – feed speed stable within ±1 % (measured 16/05/2024)"),
            ("Machine", "Contact tip and gas nozzle wear", "Ruled out – spatter build-up observed, tip replaced on 16/05/2024; trial welds with the removed tip at nominal parameters passed macro-section (n = 3)"),
            ("Method", "No start-of-shift verification of welding parameters in IT-L2-CR01-03 v1", "CONFIRMED"),
            ("Material", "MIG wire lot S-GOIE-240126 (G3Si1 Ø1.0 mm), in use since 20/03/2024", "Ruled out – 3.1 certificate conform, Si/Mn within specification"),
            ("Material", "Steel coil S-ULTZ-240183 (HSLA 420, 3.0 mm)", "Ruled out – certificate conform, CEV 0.38"),
            ("Measurement", "In-process weld check: visual + chisel test 1 part per shift", "CONFIRMED (non-detection) – cannot reveal root lack of fusion"),
            ("Environment", "Shielding gas flow M21 (Ar 82 / CO2 18)", "Ruled out – 15 l/min measured at the nozzle"),
        ],
        why_occ=[
            "Why did seam W2 crack in the pull-out test? — Insufficient root penetration (0.4–0.6 mm).",
            "Why was penetration insufficient? — Heat input about 15 % below the window qualified in WPS-CR01-03.",
            "Why was heat input low? — Wire feed speed override of −8 % (8.6 m/min vs 9.4 ± 0.3 m/min) and arc voltage at the lower limit on program P12.",
            "Why was the override active? — It was set on the teach pendant during the night shift of 03/04/2024 to reduce spatter and was neither reset nor recorded.",
            "Why was this possible? — Parameter screens were not password-protected and IT-L2-CR01-03 v1 did not require a start-of-shift parameter check.",
        ],
        why_det=[
            "Why was the defect not detected at Arga? — Visual inspection and the chisel test (1 part/shift) do not reveal lack of fusion at the root.",
            "Why is there no more sensitive test? — Macro-sections were only required for PPAP and requalification, not in series production.",
            "Why? — The PFMEA rated detection D = 4 assuming the chisel test was effective; its effectiveness had not been validated.",
        ],
        rc_occ=("Welding parameters of program P12 on CR-01 were outside the WPS window (wire feed speed override −8 % set "
                "manually and not reset), resulting in insufficient heat input and lack of fusion at the root of seam W2."),
        rc_det=("The control plan relied on visual inspection and a chisel test once per shift, which cannot detect root lack "
                "of fusion; no periodic macro-section or pull-out test at Arga."),
        rc_verif=("Defect reproduced on {d5}: 10 parts welded with WFS −8 % → 4/10 below 18 kN, penetration 0.5 mm. "
                  "10 parts at nominal parameters → 10/10 ≥ 22 kN, penetration 1.3–1.6 mm."),
        d5=[
            ("Password protection of welding parameters on the CR-01 and CR-02 teach pendants (level 2 = process engineer)", "Corrective – occurrence", "Koldo Arbizu", 9),
            ("Start-of-shift parameter check (WFS, voltage, gas flow) recorded on the cell checklist, included in IT-L2-CR01-03 v2", "Corrective – occurrence", "Oihana Zabaleta", 12),
            ("Macro-section 1 part per week and per program + chisel test 1 part per shift", "Corrective – detection", "Mikel Aranburu", 12),
            ("Pull-out test at Arga lab, 3 parts per lot (≥ 18 kN)", "Corrective – detection", "Mikel Aranburu", 14),
        ],
        d6=("Actions implemented between {d10} and {d20}. Parameter lock active since {d10}. IT-L2-CR01-03 v2 released on "
            "{d14} with the start-of-shift checklist; operators of the three shifts trained (attendance sheet TR-L2-2024-019). "
            "Macro-section and lot pull-out test added to PC-AR1003-01 v2."),
        d6_results=[
            "Pull-out tests weeks 21–29/2024: 42 lots × 3 parts, minimum 20.4 kN, Cpk 1.71.",
            "Macro-sections: 12/12 with root penetration ≥ 1.1 mm.",
            "No further complaints from OEM Norte on AR-1003/AR-1004 in the 90 days after implementation.",
        ],
        d7=[
            ("PFMEA: new cause 'parameter change on the pendant', O 5→3, D 6→4", "AMFE-AR1003-01 v2", "Oihana Zabaleta", 30, "Done"),
            ("Control plan: macro-section and lot pull-out test", "PC-AR1003-01 v2", "Maialen Irigoyen", 30, "Done"),
            ("Read-across: parameter lock on CR-02 programs (AR-1005, AR-1009, AR-1010)", "CR-02 robot controller", "Koldo Arbizu", 35, "Done"),
            ("Lessons learned presented at the monthly quality meeting", "LL-2024-06", "Maialen Irigoyen", 40, "Done"),
        ],
        d8="8D closed on {closed} after the 90-day effectiveness check; closure accepted by the OEM Norte SQE. Management thanked the team at the monthly quality review.",
    ),
    # ------------------------------------------------------------------ 2024-007 · AR-1002 · Ribera
    dict(
        id="8D-ARGA-2024-007", lang="ES", template="ARGA", close_days=68,
        title="Escuadras deformadas por embalaje (AR-1002)", line="L1 — PR-400 / L3 embalaje",
        team=["Iñaki Etxeberria", "Maialen Irigoyen", "Amaia Olaberri", "Leire Sarasola", "Josu Elizalde"],
        customer_contact="Contacto del cliente: C. Jiménez, Calidad de Proveedores, Ribera Chassis Systems.",
        statement=("Ribera Chassis Systems rechaza en recepción 120 escuadras de fijación del parachoques trasero (AR-1002) "
                   "deformadas en el ala de fijación, con cajas retornables y separadores dañados. Lote L24128-AR1002-01."),
        w5h2=[
            ("Qué", "Ala de fijación doblada 3–6 mm; planitud muy fuera de tolerancia (SC, 0,5 mm). Separadores de cartón aplastados."),
            ("Dónde", "Detectado en la recepción de Ribera (muelle 3). Las piezas salieron de Arga conformes (registro de inspección final VI-01)."),
            ("Cuándo", "Lote fabricado el 07/05/2024 (turno de noche), expedido el 12/05/2024, detectado el 19/06/2024 al abrir las cajas."),
            ("Quién", "Operario de recepción de Ribera; comunicado por C. Jiménez."),
            ("Cuál", "Solo las cajas de las dos filas inferiores del camión del albarán AL-24-00259."),
            ("Cómo", "Deformación por aplastamiento: los separadores cedieron y las piezas quedaron apoyadas unas sobre otras."),
            ("Cuántas", "120 piezas NOK de 2.165 expedidas."),
        ],
        rejects={"L24128-AR1002-01": 132},
        d3_intro="Contención iniciada el {d0} (plazo del cliente: 48 h). Alcance: lotes de AR-1002 fabricados desde el lote reclamado hasta la fecha de la reclamación.",
        d3=[
            "Stock de producto terminado en Arga ({stock} piezas) revisado el {d1}: sin deformaciones; se reembala con separadores de 5 mm del stock antiguo.",
            "Selección en Ribera por el equipo de Arga el {d1}: 132 piezas NOK (120 reclamadas + 12 adicionales), achatarradas.",
            "Apilado en camión limitado a 4 alturas de caja desde el {d2} (comunicado a transportista y a expediciones).",
        ],
        d4_intro="Análisis realizado el {d4} con Logística, Compras y el proveedor de embalaje S-ERRO (Embalajes Erro S.L.).",
        ishikawa=[
            ("Material", "Separador de cartón nuevo de S-ERRO (3 mm en lugar de 5 mm) introducido en 04/2024", "CONFIRMADO – cambio no notificado a Calidad"),
            ("Método", "Apilado de 5 alturas en camión sin ensayo de transporte", "CONFIRMADO (contribuyente)"),
            ("Máquina", "Estampación PR-400 / matriz MT-02", "Descartado – piezas de retención conformes en planitud"),
            ("Mano de obra", "Carga incorrecta del camión", "Descartado – plan de carga respetado"),
            ("Medición", "Inspección final sin control del estado del embalaje", "CONFIRMADO (no detección)"),
            ("Medio ambiente", "Humedad en el almacén del cliente", "Contribuyente posible – cartón con 14 % de humedad"),
        ],
        why_occ=[
            "¿Por qué se deformaron las escuadras? — Porque los separadores cedieron y las piezas soportaron el peso de las cajas superiores.",
            "¿Por qué cedieron los separadores? — Porque eran de cartón de 3 mm, con menor resistencia a compresión que el de 5 mm validado.",
            "¿Por qué se usó un separador de 3 mm? — S-ERRO cambió el diseño para reducir costes y lo suministró sin aviso de cambio.",
            "¿Por qué no se detectó el cambio? — El embalaje no estaba sujeto a control de cambios ni a inspección de recepción en Arga.",
        ],
        why_det=[
            "¿Por qué no se detectó en la expedición? — La IT de embalaje no incluía la comprobación del estado de los separadores.",
            "¿Por qué? — El embalaje se consideraba un elemento logístico y no formaba parte del plan de control.",
        ],
        rc_occ="Separadores de cartón de menor espesor (3 mm) suministrados por S-ERRO sin notificación de cambio, combinados con un apilado de 5 alturas en transporte.",
        rc_det="El embalaje no estaba incluido en el control de cambios de proveedores ni en la inspección final de expedición.",
        rc_verif="Ensayo de compresión el {d6}: separador de 3 mm colapsa a 1,9 kN; separador de 5 mm soporta 4,6 kN. La carga estimada en la fila inferior con 5 alturas es de 2,4 kN.",
        d5=[
            ("Volver al separador de 5 mm validado; S-ERRO emite aviso de cambio y su propio 8D", "Correctiva – ocurrencia", "Leire Sarasola", 7),
            ("Apilado máximo de 4 alturas en camión; plan de carga actualizado", "Correctiva – ocurrencia", "Amaia Olaberri", 5),
            ("Inspección visual del estado del separador y de la caja en expedición", "Correctiva – detección", "Josu Elizalde", 10),
        ],
        d6="Separador de 5 mm en uso desde el {d10}. IT-L3-VI01-01 actualizada (v2) el {d14} con el control del embalaje. Ensayo de transporte real (ida y vuelta Orkoien–cliente) el {d21} sin daños.",
        d6_results=["6 expediciones monitorizadas sin incidencias.", "Sin nuevas reclamaciones de Ribera por deformación en los 60 días siguientes."],
        d7=[
            ("Incluir el embalaje de S-ERRO en el procedimiento de gestión de cambios de proveedor", "PROC-COMP-02 v3", "Leire Sarasola", 30, "Hecho"),
            ("Evaluación de S-ERRO: penalización por cambio no notificado", "EVAL anual de proveedores", "Leire Sarasola", 45, "Hecho"),
            ("Actualizar AMFE: modo de fallo 'deformación en transporte'", "AMFE-AR1002-01 v2", "Maialen Irigoyen", 30, "Hecho"),
        ],
        d8="8D cerrado el {closed}. Ribera acepta el cierre por correo. Se reconoce la rapidez del equipo de Logística en la contención.",
    ),
    # ------------------------------------------------------------------ 2024-009 · AR-1009 · OEM Norte
    dict(
        id="8D-ARGA-2024-009", lang="EN", template="OEMN", close_days=84,
        title="Pores and craters in e-coat, LT radiator bracket (AR-1009)",
        part_en="Low-temperature radiator bracket", char_en="E-coat thickness", line="L3 — EC-01 / HC-01",
        team=["Iñaki Etxeberria", "Maialen Irigoyen", "Garazi Lizarraga", "Leire Sarasola", "Mikel Aranburu"],
        customer_contact="Customer contact: M. Ruiz, Supplier Quality Engineer, OEM Norte.",
        statement=("OEM Norte reported pores and craters in the e-coat of 260 low-temperature radiator brackets (AR-1009) and red "
                   "rust after 240 h in the neutral salt spray test (requirement: no red rust at 480 h). Lot L24151-AR1009-01."),
        w5h2=[
            ("What", "Pinholes and craters Ø0.2–0.8 mm, mainly on the flat face; e-coat thickness 14–17 µm locally (spec 18–25 µm)."),
            ("Where", "Detected at OEM Norte incoming audit and confirmed in their lab. Origin: Arga L3, e-coat line EC-01."),
            ("When", "Lot produced 30/05/2024 (night shift), e-coated on 31/05/2024, delivered 05 and 07/06/2024."),
            ("Who", "OEM Norte incoming quality lab."),
            ("Which", "AR-1009 lots coated with bath make-up chemistry lot S-ARAK-240132."),
            ("How", "Craters with contamination at the centre (EDX: phosphorus and zinc)."),
            ("How many", "260 NOK reported out of 1,393 delivered."),
        ],
        rejects={"L24151-AR1009-01": 290, "L24158-AR1009-01": 34, "L24165-AR1009-01": 21, "L24172-AR1009-01": 9},
        d3_intro="Containment launched on {d0}. Scope: all AR-1009 lots e-coated since the complained lot until the notification date.",
        d3=[
            "Arga stock ({stock} parts) blocked on {d0}; 100 % visual inspection under 1,000 lux + thickness check (5 points per part, 1 part in 20).",
            "Parts at OEM Norte sorted by the Arga resident team on {d1}–{d2}; NOK parts returned for re-coating and scrapped (re-coat not approved by the customer).",
            "EC-01 bath: filtration bags replaced and ultrafiltrate partially dumped (2,000 l) on {d1}.",
        ],
        d4_intro="Investigation on {d4}–{d6} with the chemistry supplier S-ARAK (Química Araxes S.A.).",
        ishikawa=[
            ("Material", "Make-up chemistry lot S-ARAK-240132 with phosphate content above target", "CONFIRMED – bath phosphate 42 ppm (target < 20 ppm) after make-up of 27/05/2024"),
            ("Method", "DI rinse before the e-coat tank: conductivity > 30 µS/cm", "CONFIRMED (contributing) – 38 µS/cm recorded on 30–31/05/2024"),
            ("Machine", "Filtration bags overdue (changed every 2 weeks, last change 12 days before)", "Contributing"),
            ("Man", "Bath titration by night-shift operator", "Ruled out – titrations performed per plan"),
            ("Measurement", "Final inspection checks thickness only, no pore check", "CONFIRMED (non-detection)"),
            ("Environment", "Oven HC-01 curing profile", "Ruled out – 180 °C / 20 min verified with data logger"),
        ],
        why_occ=[
            "Why pores/craters? — Contaminant particles and phosphate carry-over in the e-coat bath.",
            "Why contamination? — Bath make-up with chemistry lot S-ARAK-240132 raised phosphate to 42 ppm, and the DI rinse was above 30 µS/cm.",
            "Why was the chemistry lot accepted? — Incoming inspection of chemistry relied on the supplier certificate only.",
            "Why was the high rinse conductivity not acted on? — No alarm limit on the DI rinse; the value was logged but not reviewed on the night shift.",
        ],
        why_det=[
            "Why was the defect not detected at Arga? — Final inspection (VI-01) checks thickness on 1 part in 20; no porosity or salt spray test in series.",
        ],
        rc_occ="Bath contamination from chemistry lot S-ARAK-240132 (phosphate above target) combined with insufficient DI rinsing before the e-coat tank.",
        rc_det="No porosity check and no periodic corrosion test in the control plan; thickness measurement alone does not detect pinholes.",
        rc_verif="Lab panels coated on {d5} with contaminated bath sample → 11 craters/dm²; with fresh bath + DI rinse < 10 µS/cm → 0 craters/dm².",
        d5=[
            ("Incoming check of each S-ARAK chemistry lot (phosphate + conductivity) before bath addition", "Corrective – occurrence", "Garazi Lizarraga", 10),
            ("DI rinse conductivity alarm at 20 µS/cm with line stop", "Corrective – occurrence", "Koldo Arbizu", 12),
            ("Filtration bag change weekly", "Corrective – occurrence", "Garazi Lizarraga", 7),
            ("Porosity check (visual 1,000 lux) 5 parts per rack + monthly salt spray test", "Corrective – detection", "Mikel Aranburu", 14),
        ],
        d6="Actions effective from {d14}. IT-L3-EC01-02 updated to v2 on {d20}. S-ARAK issued its own 8D (supplier ref. SA-24-117) and quarantined the batch.",
        d6_results=["Bath phosphate < 15 ppm since {d14} (daily titration).".replace("{d14}", "mid-July 2024"),
                    "Salt spray 480 h: 3 of 3 monthly samples without red rust.", "No further OEM Norte complaints on e-coat in 90 days."],
        d7=[
            ("PFMEA e-coat: causes 'chemistry contamination' and 'rinse conductivity'", "AMFE-L3-EC01-01 v2", "Garazi Lizarraga", 30, "Done"),
            ("Control plan e-coat: incoming chemistry check, rinse alarm, porosity check", "PC-L3-EC01-01 v2", "Garazi Lizarraga", 30, "Done"),
            ("Supplier evaluation S-ARAK: quality incident recorded", "Supplier evaluation 2024", "Leire Sarasola", 45, "Done"),
        ],
        d8="8D closed on {closed}; accepted by OEM Norte SQE.",
    ),
    # ------------------------------------------------------------------ 2024-012 · AR-1007 · Leitzaran
    dict(
        id="8D-ARGA-2024-012", lang="EN", template="ARGA", close_days=77,
        title="Burr in seat belt anchor hole (AR-1007)",
        part_en="Belt anchor flange (seat structure)", char_en="Hole diameter and burr", line="L1 — PR-250 / die MT-07",
        team=["Iñaki Etxeberria", "Maialen Irigoyen", "Unai Ezkurra", "Koldo Arbizu", "Josu Elizalde", "Mikel Aranburu", "Leire Sarasola"],
        customer_contact="Customer contact: A. Bengoetxea, Supplier Quality, Leitzaran Seating.",
        statement=("Leitzaran Seating reported 410 seat belt anchor flanges (AR-1007) with burr > 0.2 mm on the exit side of the "
                   "anchor hole; the anchor bolt shoulder does not seat and the belt cannot be assembled. Lot L24268-AR1007-01."),
        w5h2=[
            ("What", "Burr 0.25–0.40 mm on the anchor hole (requirement ≤ 0.2 mm); hole Ø11.20–11.24 (spec Ø11.20 +0.15/0). CC characteristic."),
            ("Where", "Leitzaran seat frame line, belt anchor bolting station. Origin: Arga L1, press PR-250, progressive die MT-07, piercing station P3."),
            ("When", "Lot produced 24/09/2024 (afternoon shift), delivered 30/09/2024, detected 04/11/2024."),
            ("Who", "Leitzaran assembly operator; notified by A. Bengoetxea."),
            ("Which", "AR-1007 only (MT-07 is dedicated)."),
            ("How", "Rolled burr on the die side, consistent with a worn punch cutting edge."),
            ("How many", "410 NOK out of 2,572 delivered."),
        ],
        rejects={"L24268-AR1007-01": 446},
        d3_intro="Containment started on {d0}. Scope: AR-1007 lots stamped with MT-07 from the complained lot up to the notification date.",
        d3=[
            "Arga stock ({stock} parts) blocked on {d0} and 100 % checked with burr gauge (0.2 mm) and plug gauge Ø11.20 go/no-go.",
            "Leitzaran stock sorted by Arga on {d1}–{d2}: 446 NOK, all from lot L24268-AR1007-01. Lots stamped after the punch sharpening of 28/09/2024 were 100 % OK.",
            "NOK parts deburred? — Not allowed for CC characteristic; all NOK parts scrapped.",
        ],
        d4_intro="Analysis on {d4} with toolroom and the die sharpening subcontractor S-ZIDA (Tratamientos Zidacos S.L.).",
        ishikawa=[
            ("Machine", "Piercing punch P3 of MT-07 worn (cutting edge radius 0.18 mm, wear land 0.25 mm)", "CONFIRMED"),
            ("Method", f"Sharpening interval 40,000 strokes exceeded: counter at {_mt07_24:,} strokes when the lot was stamped", "CONFIRMED – die kept in production waiting for an S-ZIDA slot"),
            ("Method", "No spare punch set for MT-07", "CONFIRMED (contributing)"),
            ("Material", "Coil S-ULTZ-240223 (HSLA 500, 3.5 mm)", "Ruled out – mechanical properties mid-range"),
            ("Man", "Die setting by afternoon shift", "Ruled out – setup sheet complete"),
            ("Measurement", "Burr and hole checked at first and last part only", "CONFIRMED (non-detection)"),
        ],
        why_occ=[
            "Why was there burr > 0.2 mm? — The cutting edge of punch P3 was worn and the effective clearance had increased.",
            f"Why was the punch worn? — It had reached {_mt07_24:,} strokes, above the 40,000-stroke sharpening interval.",
            "Why was the interval exceeded? — S-ZIDA had no slot for 10 days and the die was kept running to meet deliveries.",
            "Why could it keep running? — There was no spare punch set and no interlock on the stroke counter of PR-250.",
        ],
        why_det=[
            "Why was the burr not detected? — Burr and hole diameter were checked only on the first and last part of the lot (PC-AR1007-01 v1).",
            "Why? — Wear was considered slow and predictable; the control plan did not foresee a check during the run.",
        ],
        rc_occ="Worn piercing punch P3 on die MT-07: sharpening overdue (above 40,000 strokes) because of subcontractor lead time and no spare punch.",
        rc_det="Burr and hole diameter were only checked at first and last part; progressive wear during the run was not detected.",
        rc_verif=f"S-ZIDA measurement of the removed punch (OT-MT-24-002): edge radius 0.18 mm. Trial on {{d6}} with the sharpened punch: burr 0.04–0.08 mm, Ø11.26 mm.",
        d5=[
            ("Spare punch set for MT-07 (P3) held at Arga; die no longer waits for the subcontractor", "Corrective – occurrence", "Unai Ezkurra", 21),
            ("Stroke counter alarm on PR-250 at 38,000 strokes for MT-07", "Corrective – occurrence", "Koldo Arbizu", 14),
            ("S-ZIDA contract: sharpening lead time ≤ 5 working days", "Corrective – occurrence", "Leire Sarasola", 30),
            ("Burr gauge + plug gauge check every 2 h during the run", "Corrective – detection", "Josu Elizalde", 7),
        ],
        d6="Checks every 2 h in place since {d10}; stroke alarm active since {d14}; spare punch delivered on {d21}. Operators of the three shifts trained on the new checks.",
        d6_results=["Burr ≤ 0.10 mm in all 2-hourly checks for 8 weeks.", "No further complaints from Leitzaran in the 60 days after implementation."],
        d7=[
            ("PFMEA: cause 'sharpening overdue', prevention = stroke alarm + spare punch", "AMFE-AR1007-01 v2", "Unai Ezkurra", 30, "Done"),
            ("Control plan: 2-hourly burr and hole checks", "PC-AR1007-01 v2", "Maialen Irigoyen", 30, "Done"),
            ("Die sharpening plan: lead time and spare punch requirement", "PROC-L1-AFILADO-01 v2", "Koldo Arbizu", 20, "Done"),
        ],
        d8="8D closed on {closed}. Leitzaran accepted the closure at the quarterly supplier review.",
    ),
    # ------------------------------------------------------------------ 2024-013 · AR-1006 · OEM Norte
    dict(
        id="8D-ARGA-2024-013", lang="EN", template="OEMN", close_days=72,
        title="Low torque-out of weld nut, A/C compressor bracket (AR-1006)",
        part_en="A/C compressor bracket", char_en="Weld nut torque", line="L2 — SP-01 / AT-01",
        team=["Iñaki Etxeberria", "Maialen Irigoyen", "Oihana Zabaleta", "Koldo Arbizu", "Xabier Urrutia", "Mikel Aranburu"],
        customer_contact="Customer contact: M. Ruiz, Supplier Quality Engineer, OEM Norte.",
        statement=("OEM Norte reported 75 A/C compressor brackets (AR-1006) whose M8 weld nut detached or turned below the "
                   "torque-out requirement (≥ 40 Nm) when tightening the compressor bolts. Lot L24295-AR1006-01."),
        w5h2=[
            ("What", "Weld nut M8 torque-out 12–30 Nm (spec ≥ 40 Nm); 1 or 2 of the 3 projections not fused."),
            ("Where", "OEM Norte front-end module line. Origin: Arga L2, projection welding with SP-01 and nut feeder AT-01."),
            ("When", "Lot produced 21/10/2024 (night shift), delivered 26–27/10/2024, detected 02/12/2024."),
            ("Who", "OEM Norte assembly operator (nut spinning with the DC nutrunner)."),
            ("Which", "AR-1006 only."),
            ("How", "Off-centre weld: projections on one side not fused, witness marks show nut offset 0.8 mm."),
            ("How many", "75 NOK out of 2,965 delivered."),
        ],
        rejects={"L24295-AR1006-01": 81, "L24302-AR1006-01": 6},
        d3_intro="Containment started on {d0}. Scope: AR-1006 lots welded on SP-01 from the complained lot up to notification.",
        d3=[
            "Arga stock ({stock} parts) blocked on {d0}; torque-out test on 5 parts per box, 100 % sorting of boxes with any NOK.",
            "OEM Norte stock sorted by Arga on {d1}–{d2} with a torque wrench at 40 Nm (non-destructive proof torque).",
        ],
        d4_intro="Root cause workshop on {d4} with maintenance and welding engineering.",
        ishikawa=[
            ("Machine", "Upper electrode of SP-01 misaligned after replacement of the lower electrode insulating sleeve on 18/10/2024", "CONFIRMED – offset 0.8 mm measured"),
            ("Method", "No first-part torque test after maintenance on SP-01", "CONFIRMED"),
            ("Material", "Weld nut lot S-BIDA-240140 (M8 Zn-Ni)", "Ruled out – coating thickness 9–10 µm, projection height conform"),
            ("Man", "Operator loading nuts manually when AT-01 jams", "Ruled out – no jams recorded on 21/10/2024"),
            ("Measurement", "Torque-out test only 1 part at start of shift", "CONFIRMED (non-detection)"),
            ("Environment", "Cooling water temperature of SP-01", "Ruled out"),
        ],
        why_occ=[
            "Why low torque-out? — Only 1–2 of 3 projections fused.",
            "Why? — The nut was welded off-centre (0.8 mm) relative to the electrode.",
            "Why? — The upper electrode was misaligned after the lower electrode sleeve was replaced on 18/10/2024.",
            "Why was it not corrected? — Maintenance released the machine without an alignment check or a torque test on the first part.",
        ],
        why_det=["Why not detected? — Torque-out test was performed only once per shift, at the start; the night shift of 21/10/2024 started before the maintenance was completed."],
        rc_occ="Electrode misalignment on SP-01 after maintenance, causing off-centre projection welds.",
        rc_det="No release test after maintenance and insufficient torque-out test frequency.",
        rc_verif="Trial on {d5}: 0.8 mm offset → 7/10 parts below 40 Nm; aligned electrode → 10/10 above 62 Nm.",
        d5=[
            ("Electrode alignment gauge and check after every electrode intervention", "Corrective – occurrence", "Koldo Arbizu", 10),
            ("First-part torque test mandatory for machine release after maintenance", "Corrective – occurrence", "Oihana Zabaleta", 10),
            ("Torque-out test 3 parts every 2 h", "Corrective – detection", "Xabier Urrutia", 7),
        ],
        d6="All actions implemented by {d14}. IT-L2-SP01-02 updated (v3) with the alignment check and release test.",
        d6_results=["Torque-out ≥ 55 Nm in all checks during 8 weeks.", "No recurrence at OEM Norte in 90 days."],
        d7=[
            ("PFMEA SP-01: cause 'electrode misalignment after maintenance'", "AMFE-AR1006-01 v2", "Oihana Zabaleta", 35, "Done"),
            ("Control plan: torque-out every 2 h", "PC-AR1006-01 v2", "Maialen Irigoyen", 35, "Done"),
            ("Maintenance release checklist for all welding equipment", "Maintenance system", "Koldo Arbizu", 45, "Done"),
        ],
        d8="8D closed on {closed}; accepted by OEM Norte.",
    ),
    # ------------------------------------------------------------------ 2025-002 · AR-1003 · OEM Norte
    dict(
        id="8D-ARGA-2025-002", lang="EN", template="OEMN", close_days=78,
        title="Lack of fusion in MIG weld seam, battery tray bracket LH (AR-1003)",
        part_en="Battery tray bracket LH", char_en="MIG weld strength", line="L2 — CR-01",
        team=["Iñaki Etxeberria", "Maialen Irigoyen", "Oihana Zabaleta", "Xabier Urrutia", "Mikel Aranburu", "Koldo Arbizu"],
        customer_contact="Customer contact: M. Ruiz, Supplier Quality Engineer, OEM Norte battery module assembly.",
        statement=("OEM Norte reported 22 battery tray brackets LH (AR-1003) broken at the MIG weld seam W2 during battery tray "
                   "assembly (bolting and handling). Lack of fusion visible on the fracture surface. Lot L25001-AR1003-01."),
        w5h2=[
            ("What", "Lack of fusion along 15–30 mm of seam W2; fracture surface smooth with unfused areas. CC characteristic."),
            ("Where", "OEM Norte battery tray assembly line. Origin: Arga L2, robot cell CR-01."),
            ("When", "Lot produced 01/01/2025 (night shift, holiday with reduced crew), delivered 07/01/2025, detected 10/02/2025."),
            ("Who", "OEM Norte assembly operators; notified by the OEM Norte SQE."),
            ("Which", "AR-1003. AR-1004 lots of the same period sorted at the customer: no NOK."),
            ("How", "Irregular bead, spatter on the part, porosity at bead start/stop; typical of an unstable arc."),
            ("How many", "22 NOK out of 1,679 delivered."),
        ],
        rejects={"L25001-AR1003-01": 27, "L25015-AR1003-01": 4, "L25036-AR1003-01": 2},
        d3_intro="Containment started on {d0}, within 24 h. Scope: all AR-1003 lots welded on CR-01 from the complained lot to the notification date.",
        d3=[
            "Arga stock ({stock} parts) blocked on {d0}; 100 % visual inspection of seam W2 + pull-out test 5 parts per lot.",
            "OEM Norte stock and parts in transit sorted by the Arga resident team on {d1}–{d3}.",
            "Rejects found in sorting were concentrated in night-shift lots; the holiday night shift of 01/01/2025 ran with 2 operators and no L2 technician.",
            "Immediate action on CR-01 from 24/02/2025: gas nozzle and contact tip replaced every 8 h, recorded in the change log REG-L2-CR01-01.",
        ],
        d4_intro="Root cause analysis on {d4}–{d6}. Welding parameters were checked first: all within the WPS window (parameter lock and start-of-shift check in place).",
        ishikawa=[
            ("Machine", "Contact tip worn (bore ovalised to 1.45 mm, nominal 1.20 mm) and gas nozzle ~40 % obstructed by spatter", "CONFIRMED"),
            ("Method", "No defined frequency for nozzle / contact tip change ('when needed', operator judgement)", "CONFIRMED"),
            ("Man", "Reduced crew on the holiday night shift of 01/01/2025", "CONFIRMED (contributing)"),
            ("Method", "Welding parameters of program P12", "Ruled out – within WPS-CR01-03, pendant locked"),
            ("Material", "MIG wire lot S-GOIE-240136, in use since 04/12/2024", "Ruled out – 3.1 certificate conform; no wire lot change during the affected lot"),
            ("Material", "Steel coil S-ULTZ-240204 (HSLA 420)", "Ruled out"),
            ("Measurement", "Pull-out test 3 parts per lot passed (19.8 / 21.5 / 23.0 kN)", "Sampling did not capture intermittent defect"),
            ("Environment", "Draught near CR-01 door (winter)", "Ruled out – curtain closed"),
        ],
        why_occ=[
            "Why did seam W2 break? — Lack of fusion over part of the seam.",
            "Why lack of fusion? — Unstable arc and poor gas shielding.",
            "Why unstable arc? — Contact tip bore worn (1.45 mm) and nozzle obstructed by spatter, causing erratic current transfer and wire position.",
            "Why were tip and nozzle worn? — No change frequency was defined; they were changed 'when needed' by operator judgement.",
            "Why no frequency? — Consumable wear was not identified as a cause in the PFMEA or in IT-L2-CR01-03.",
        ],
        why_det=[
            "Why not detected at Arga? — The defect is intermittent; 3 pull-out tests per lot passed and visual inspection did not flag the irregular bead on the night shift.",
        ],
        rc_occ=("Worn contact tip and spatter-obstructed gas nozzle on CR-01, because no replacement frequency was defined for these "
                "consumables (changed by operator judgement)."),
        rc_det="Intermittent defect not captured by the 3-part pull-out sample per lot; no requirement to inspect consumables.",
        rc_verif=("Trial on {d6}: 20 parts welded with the worn tip/nozzle removed from CR-01 → 5/20 with lack of fusion in macro-section; "
                  "20 parts with new tip/nozzle → 0/20. Tip wear measured after 8 h of production: bore 1.26–1.29 mm (acceptable)."),
        d5=[
            ("Change gas nozzle and contact tip every 8 h, recorded in REG-L2-CR01-01", "Corrective – occurrence", "Xabier Urrutia", 13),
            ("Spare consumable kits stored at the cell; nozzle reamer cycle every 20 parts", "Corrective – occurrence", "Koldo Arbizu", 14),
            ("Update IT-L2-CR01-03 with the 8 h change and a visual check of the nozzle", "Corrective – occurrence", "Oihana Zabaleta", 20),
            ("Arc stability monitoring (weld data logger) — feasibility study", "Corrective – detection", "Oihana Zabaleta", 60),
        ],
        d6=("Change log REG-L2-CR01-01 started on 24/02/2025. IT-L2-CR01-03 v3 released on 03/03/2025 with the nozzle and contact tip "
            "change. Layered process audits on 12/03/2025 and 19/03/2025 (morning and afternoon shifts) confirmed compliance; "
            "the log was reviewed weekly by the L2 production manager for 4 weeks."),
        d6_results=[
            "Macro-sections weeks 10–17/2025: 16/16 with root penetration ≥ 1.2 mm.",
            "Pull-out tests: minimum 20.9 kN, no value below 20 kN.",
            "No complaints from OEM Norte on AR-1003/AR-1004 in the 60 days after implementation.",
        ],
        d7=[
            ("PFMEA: new cause 'contact tip / nozzle wear', prevention = change every 8 h, O 6→3", "AMFE-AR1003-01 v3", "Oihana Zabaleta", 25, "Done"),
            ("Control plan: consumable change frequency and log", "PC-AR1003-01 v3", "Maialen Irigoyen", 25, "Done"),
            ("Work instruction: nozzle and contact tip change", "IT-L2-CR01-03 v3", "Oihana Zabaleta", 20, "Done"),
            ("Read-across to CR-02: same consumable change frequency", "IT-L2-CR02-02 v2", "Oihana Zabaleta", 35, "Done"),
        ],
        d8="8D closed on {closed}; OEM Norte accepted the closure. The team presented the consumable change log at the plant quality meeting.",
    ),
    # ------------------------------------------------------------------ 2025-005 · AR-1005 · Ribera
    dict(
        id="8D-ARGA-2025-005", lang="ES", template="ARGA", close_days=90,
        title="Refuerzo deformado bajo carga; material en el límite (AR-1005)", line="L1 — PR-400 / L2 — CR-02",
        team=["Iñaki Etxeberria", "Maialen Irigoyen", "Leire Sarasola", "Mikel Aranburu", "Unai Ezkurra", "Oihana Zabaleta"],
        customer_contact="Contacto del cliente: C. Jiménez, Calidad de Proveedores, Ribera Chassis Systems.",
        statement=("Ribera Chassis Systems informa de 64 refuerzos del travesaño del subchasis (AR-1005) con deformación "
                   "permanente > 0,5 mm en su ensayo de validación de carga estática (12 kN). Lote L25059-AR1005-01."),
        w5h2=[
            ("Qué", "Deformación permanente de 0,6–1,1 mm en el ala del refuerzo tras la carga de 12 kN (requisito ≤ 0,5 mm)."),
            ("Dónde", "Laboratorio de validación de Ribera (ensayo de recualificación anual). Origen: Arga L1 PR-400 + L2 CR-02."),
            ("Cuándo", "Lote fabricado el 28/02/2025 (turno de noche), expedido el 05/03/2025, ensayado por el cliente el 04/04/2025."),
            ("Quién", "Laboratorio de Ribera; comunicado por C. Jiménez."),
            ("Cuál", "Piezas fabricadas con la bobina S-ULTZ-250150 (HSLA 340, 2,5 mm)."),
            ("Cómo", "Pandeo del ala sin rotura; la soldadura MIG está intacta (penetración conforme en macrografía)."),
            ("Cuántas", "64 piezas NOK de la muestra de validación y del stock revisado por el cliente."),
        ],
        rejects={"L25059-AR1005-01": 64},
        d3_intro="Contención iniciada el {d0}. Alcance: lotes de AR-1005 fabricados con la bobina S-ULTZ-250150 y posteriores hasta la fecha de la reclamación.",
        d3=[
            "Stock en Arga ({stock} piezas) bloqueado el {d0}. Ensayo de tracción de probetas de cada bobina en uso.",
            "Piezas con bobina S-ULTZ-250150 sustituidas en Ribera por piezas de bobina con Re ≥ 370 MPa el {d2}.",
            "Resto de lotes liberados tras ensayo de carga 3 piezas/lote en el laboratorio de Arga (todas ≤ 0,3 mm).",
        ],
        d4_intro="Análisis del {d4} al {d6} con Compras y el proveedor de acero S-ULTZ (Aceros Ultzama S.A.).",
        ishikawa=[
            ("Material", "Bobina S-ULTZ-250150 con límite elástico en el mínimo de especificación (Re 342 MPa; mín. 340 MPa)", "CONFIRMADO – anotado en la recepción, sin reacción"),
            ("Método", "Recepción de acero basada solo en el certificado 3.1, sin ensayo propio para piezas CC", "CONFIRMADO"),
            ("Máquina", "Estampación PR-400 / matriz MT-05: espesor y radios", "Descartado – espesor 2,48 mm, radios conformes"),
            ("Máquina", "Soldadura CR-02: penetración (CC)", "Descartado – macrografías conformes"),
            ("Mano de obra", "—", "Sin relación"),
            ("Medición", "Ensayo de carga solo en la validación anual del cliente", "CONFIRMADO (no detección)"),
        ],
        why_occ=[
            "¿Por qué se deformó el refuerzo? — Porque el material cedió por debajo de 12 kN.",
            "¿Por qué cedió? — Porque el límite elástico de la bobina estaba en el mínimo de la especificación (342 MPa) y el diseño tiene poco margen con material en el mínimo.",
            "¿Por qué se usó esa bobina? — Porque cumplía la especificación y la recepción se basaba en el certificado del proveedor.",
            "¿Por qué no se reaccionó a la nota de recepción? — No había una regla que exigiera acción para valores en el límite en piezas CC.",
        ],
        why_det=["¿Por qué no se detectó? — Arga no hacía ensayos de carga en serie; solo el cliente en la validación anual."],
        rc_occ="Material HSLA 340 con límite elástico en el mínimo de especificación, sin margen suficiente para la carga de validación del cliente.",
        rc_det="Sin ensayo de tracción propio ni ensayo de carga periódico en Arga para una característica CC.",
        rc_verif="Ensayo del {d6}: 10 piezas de la bobina S-ULTZ-250150 → 7/10 con deformación > 0,5 mm; 10 piezas de bobina con Re 378 MPa → 10/10 ≤ 0,25 mm.",
        d5=[
            ("Acuerdo con S-ULTZ: HSLA 340 para AR-1005 con Re ≥ 360 MPa (ventana restringida)", "Correctiva – ocurrencia", "Leire Sarasola", 21),
            ("Ensayo de tracción en recepción de cada bobina para piezas CC", "Correctiva – ocurrencia", "Mikel Aranburu", 14),
            ("Ensayo de carga 3 piezas por lote en el laboratorio de Arga", "Correctiva – detección", "Mikel Aranburu", 14),
        ],
        d6="Acuerdo técnico con S-ULTZ firmado el {d21}. Ensayo de tracción en recepción desde el {d14}.",
        d6_results=["12 bobinas recibidas con Re entre 368 y 395 MPa.", "Ensayos de carga en Arga: máximo 0,28 mm de deformación.", "Ribera repite la validación con resultado OK."],
        d7=[
            ("AMFE: causa 'material en el límite de especificación'", "AMFE-AR1002-01 v3 (AR-1005)", "Maialen Irigoyen", 35, "Hecho"),
            ("Evaluación de S-ULTZ: incidente de calidad", "EVAL anual", "Leire Sarasola", 45, "Hecho"),
            ("Propuesta a Ribera de revisar el margen de diseño (cambio a HSLA 420)", "Solicitud de cambio de ingeniería", "Iñaki Etxeberria", 60, "En curso (decisión del cliente)"),
        ],
        d8="8D cerrado el {closed}. Ribera acepta el cierre con la acción de diseño pendiente de su lado.",
    ),
    # ------------------------------------------------------------------ 2025-006 · AR-1002 · Ribera
    dict(
        id="8D-ARGA-2025-006", lang="ES", template="ARGA", close_days=64,
        title="Planitud fuera de tolerancia (AR-1002)", line="L1 — PR-400 / matriz MT-02",
        team=["Iñaki Etxeberria", "Maialen Irigoyen", "Unai Ezkurra", "Josu Elizalde", "Mikel Aranburu"],
        customer_contact="Contacto del cliente: C. Jiménez, Calidad de Proveedores, Ribera Chassis Systems.",
        statement=("Ribera Chassis Systems reclama 300 escuadras de fijación del parachoques trasero (AR-1002) con planitud de "
                   "0,8 mm frente a 0,5 mm especificados; las escuadras no apoyan en el travesaño. Lote L25091-AR1002-01."),
        w5h2=[
            ("Qué", "Planitud de la cara de apoyo 0,7–0,9 mm (tolerancia 0,5 mm, SC)."),
            ("Dónde", "Línea de montaje de Ribera. Origen: Arga L1, prensa PR-400, matriz MT-02, estación de calibrado (E5)."),
            ("Cuándo", "Lote fabricado el 01/04/2025 (turno de tarde), expedido el 07/04/2025, detectado el 12/05/2025."),
            ("Quién", "Operario de montaje de Ribera."),
            ("Cuál", "Lotes estampados tras la reparación de MT-02 del 27/03/2025."),
            ("Cómo", "Recuperación elástica: el inserto de calibrado no aplana la cara de apoyo."),
            ("Cuántas", "300 piezas NOK de 2.363 expedidas."),
        ],
        rejects={"L25091-AR1002-01": 318, "L25098-AR1002-01": 41},
        d3_intro="Contención iniciada el {d0}. Alcance: lotes de AR-1002 estampados desde el lote reclamado hasta la fecha de la reclamación.",
        d3=[
            "Stock en Arga ({stock} piezas) bloqueado y medido al 100 % en mármol con galga de espesores el {d1}.",
            "Selección en Ribera el {d1}–{d2}: NOK devueltas y achatarradas.",
            "Lotes posteriores a la corrección del inserto (suplemento de 0,15 mm) conformes.",
        ],
        d4_intro="Análisis del {d4} con matricería.",
        ishikawa=[
            ("Máquina", "Inserto de calibrado de E5 sustituido el 27/03/2025 con altura 0,15 mm inferior a la nominal", "CONFIRMADO"),
            ("Método", "Liberación de la matriz tras reparación sin medición completa de primera pieza (solo visual)", "CONFIRMADO"),
            ("Material", "Bobina S-ULTZ-250125 (DC04 2,0 mm)", "Descartado – propiedades medias"),
            ("Mano de obra", "Montaje de la matriz en PR-400", "Descartado"),
            ("Medición", "Control de planitud 1 pieza por turno", "CONFIRMADO (no detección) – el registro del turno de noche del 01/04 falta"),
            ("Medio ambiente", "—", "Sin relación"),
        ],
        why_occ=[
            "¿Por qué la planitud es de 0,8 mm? — Porque la estación de calibrado no aplana la cara de apoyo.",
            "¿Por qué? — El inserto nuevo es 0,15 mm más bajo que el nominal.",
            "¿Por qué se montó así? — El inserto se fabricó según un plano sin la última revisión (suplemento incluido en la cota).",
            "¿Por qué no se detectó al liberar la matriz? — La liberación tras reparación solo exigía inspección visual.",
        ],
        why_det=["¿Por qué no se detectó en producción? — Control de planitud 1 pieza/turno; el registro de un turno faltaba y no se reaccionó a 0,55 mm registrado el 02/04/2025."],
        rc_occ="Inserto de calibrado de MT-02 fabricado con plano desactualizado (0,15 mm bajo), montado sin medición de primera pieza.",
        rc_det="Liberación de matriz tras reparación sin medición dimensional; frecuencia de control de planitud insuficiente.",
        rc_verif="Prueba del {d5}: con suplemento de 0,15 mm, planitud 0,18–0,26 mm en 20 piezas.",
        d5=[
            ("Rectificar/suplementar el inserto E5 y actualizar el plano en matricería", "Correctiva – ocurrencia", "Unai Ezkurra", 5),
            ("Liberación de matriz tras reparación con medición de primera pieza (planitud y cotas SC)", "Correctiva – ocurrencia", "Unai Ezkurra", 14),
            ("Control de planitud 1 pieza cada 2 h", "Correctiva – detección", "Josu Elizalde", 7),
        ],
        d6="Acciones implantadas antes del {d14}. IT-L1-PR400-03 actualizada a v2 con la liberación tras reparación.",
        d6_results=["Planitud máxima 0,31 mm en 6 semanas de seguimiento.", "Sin nuevas reclamaciones de Ribera."],
        d7=[
            ("AMFE: causa 'herramienta reparada sin liberación dimensional'", "AMFE-AR1002-01 v4", "Maialen Irigoyen", 30, "Hecho"),
            ("Plan de control: planitud cada 2 h", "PC-AR1002-01 v3", "Maialen Irigoyen", 30, "Hecho"),
            ("Control de planos de matricería (revisión vigente en el taller)", "Sistema documental matricería", "Unai Ezkurra", 45, "Hecho"),
        ],
        d8="8D cerrado el {closed}. Aceptado por Ribera.",
    ),
    # ------------------------------------------------------------------ 2025-008 · AR-1010 · OEM Norte
    dict(
        id="8D-ARGA-2025-008", lang="EN", template="OEMN", close_days=80,
        title="Weld nut spins at torque, power inverter bracket (AR-1010)",
        part_en="Power inverter bracket", char_en="Weld nut torque", line="L2 — CR-02 nut station / AT-01",
        team=["Iñaki Etxeberria", "Maialen Irigoyen", "Oihana Zabaleta", "Leire Sarasola", "Mikel Aranburu", "Xabier Urrutia"],
        customer_contact="Customer contact: M. Ruiz, Supplier Quality Engineer, OEM Norte.",
        statement=("OEM Norte reported 48 power inverter brackets (AR-1010) whose M8 weld nut spins when tightening the inverter "
                   "fixing bolt (torque 25 Nm). Lot L25129-AR1010-01."),
        w5h2=[
            ("What", "Weld nut rotates at 18–30 Nm (torque-out requirement ≥ 40 Nm); cold projection welds."),
            ("Where", "OEM Norte e-drive module line. Origin: Arga L2, projection nut welding station of cell CR-02 (feeder AT-01)."),
            ("When", "Lot produced 09/05/2025 (morning shift), delivered 14 and 16/05/2025, detected 16/06/2025."),
            ("Who", "OEM Norte assembly operator."),
            ("Which", "Parts welded with weld nut lot S-BIDA-250129."),
            ("How", "Projections flattened but not fused; bright zinc-nickel residue in the weld interface."),
            ("How many", "48 NOK out of 1,886 delivered."),
        ],
        rejects={"L25129-AR1010-01": 52, "L25136-AR1010-01": 9},
        d3_intro="Containment started on {d0}, within 24 h. Scope: AR-1010 lots from the complained lot until the notification date.",
        d3=[
            "Arga stock ({stock} parts) blocked on {d0}; proof torque 40 Nm on 100 % of parts with nut lot S-BIDA-250129.",
            "OEM Norte stock sorted on {d1}–{d2} by the Arga resident team (proof torque 40 Nm).",
            "Remaining nuts of lot S-BIDA-250129 quarantined and returned to the supplier on {d3}.",
        ],
        d4_intro="Investigation on {d4}–{d6} with the nut supplier S-BIDA (Fijaciones Bidasoa S.L.).",
        ishikawa=[
            ("Material", "Zn-Ni coating thickness of nut lot S-BIDA-250129 at the upper limit (11.5–12.0 µm, spec 8–12 µm)", "CONFIRMED – noted at incoming inspection"),
            ("Method", "Weld schedule validated only with mid-range coating (9–10 µm)", "CONFIRMED"),
            ("Machine", "Electrode wear / alignment of the nut station", "Ruled out – within limits"),
            ("Man", "—", "Not related"),
            ("Measurement", "Torque-out test 1 part per shift", "CONFIRMED (non-detection)"),
            ("Environment", "—", "Not related"),
        ],
        why_occ=[
            "Why does the nut spin? — The projections are not fused.",
            "Why? — Energy at the interface was insufficient: the thicker Zn-Ni coating increases contact resistance and zinc vapour.",
            "Why was energy insufficient? — The weld schedule was validated only with coating in the middle of the range.",
            "Why was the lot used? — Coating was within specification; no rule to adjust or segregate lots at the limit.",
        ],
        why_det=["Why not detected? — Torque-out test was performed only once per shift."],
        rc_occ="Weld nuts with Zn-Ni coating at the upper tolerance combined with a weld schedule not validated for that condition.",
        rc_det="Insufficient torque-out test frequency.",
        rc_verif="Trial on {d6}: nuts with 11.8 µm coating → 6/10 below 40 Nm; with +8 % weld current → 10/10 ≥ 58 Nm; nuts with 9.5 µm → 10/10 ≥ 60 Nm.",
        d5=[
            ("S-BIDA: coating window for Arga restricted to 8–11 µm (drawing note + PCN)", "Corrective – occurrence", "Leire Sarasola", 30),
            ("Incoming XRF coating measurement per nut lot", "Corrective – occurrence", "Mikel Aranburu", 14),
            ("Weld schedule revalidated across the full coating range", "Corrective – occurrence", "Oihana Zabaleta", 21),
            ("Torque-out 3 parts every 2 h", "Corrective – detection", "Xabier Urrutia", 7),
        ],
        d6="Implemented by {d30}. S-BIDA confirmed the restricted window from its lot of July 2025.",
        d6_results=["Torque-out ≥ 52 Nm in all checks over 10 weeks.", "No recurrence at OEM Norte in 90 days."],
        d7=[
            ("PFMEA nut welding: cause 'coating at upper limit'", "AMFE-AR1006-01 v3 (AR-1006/AR-1010)", "Oihana Zabaleta", 35, "Done"),
            ("Control plan: XRF at incoming + torque-out every 2 h", "PC-AR1006-01 v3", "Maialen Irigoyen", 35, "Done"),
            ("Read-across to AR-1006 on SP-01", "IT-L2-SP01-02 v4", "Oihana Zabaleta", 40, "Done"),
        ],
        d8="8D closed on {closed}; accepted by OEM Norte.",
    ),
    # ------------------------------------------------------------------ 2025-010 · AR-1007 · Leitzaran
    dict(
        id="8D-ARGA-2025-010", lang="EN", template="ARGA", close_days=84,
        title="Undersized anchor hole and burr (AR-1007)",
        part_en="Belt anchor flange (seat structure)", char_en="Hole diameter and burr", line="L1 — PR-250 / die MT-07",
        team=["Iñaki Etxeberria", "Maialen Irigoyen", "Unai Ezkurra", "Mikel Aranburu", "Leire Sarasola", "Josu Elizalde"],
        customer_contact="Customer contact: A. Bengoetxea, Supplier Quality, Leitzaran Seating.",
        statement=("Leitzaran Seating reported 520 seat belt anchor flanges (AR-1007) with anchor hole diameter below tolerance "
                   "and burr on the exit side; the anchor bolt does not enter. Lot L25196-AR1007-01."),
        w5h2=[
            ("What", "Hole Ø11.12–11.18 mm (spec Ø11.20 +0.15/0) and burr 0.22–0.34 mm (≤ 0.2 mm). CC characteristic."),
            ("Where", "Leitzaran seat frame line. Origin: Arga L1, PR-250, progressive die MT-07, piercing station P3."),
            ("When", "Lot produced 15/07/2025 (afternoon shift), delivered 19/07/2025, detected 25/08/2025."),
            ("Who", "Leitzaran assembly operator."),
            ("Which", "AR-1007 only."),
            ("How", "Worn and micro-chipped punch edge; hole shrinks after springback in HSLA 500."),
            ("How many", "520 NOK out of 2,065 delivered."),
        ],
        rejects={"L25196-AR1007-01": 537},
        d3_intro="Containment started on {d0}. Scope: AR-1007 lots stamped with MT-07 from the complained lot to the notification date.",
        d3=[
            "Arga stock ({stock} parts) blocked on {d0} and 100 % checked with a new calibrated plug gauge and a dial burr gauge.",
            "Leitzaran stock sorted on {d1}–{d2}: 537 NOK, all from lot L25196-AR1007-01.",
            "Lots stamped after the planned sharpening of 19/07/2025 (OT-MT-25-004) were 100 % conform.",
        ],
        d4_intro="Analysis on {d4} with toolroom, S-ZIDA and the steel supplier S-ULTZ.",
        ishikawa=[
            ("Machine", "Punch P3 cutting edge wear and micro-chipping", "CONFIRMED – edge radius 0.20 mm, two chips of 0.1 mm"),
            ("Method", f"Sharpening per plan PROC-L1-AFILADO-01 (60,000 strokes); counter at {_mt07_25:,} strokes when the lot was stamped", "Within plan – not retained as cause"),
            ("Material", "Coil S-ULTZ-250205 (HSLA 500) with tensile strength at the upper range (Rm 668 MPa, spec 560–700 MPa)", "CONFIRMED (contributing) – accelerates punch wear"),
            ("Measurement", "Plug gauge Ø11.20 worn to Ø11.17 (calibration overdue by 2 months)", "CONFIRMED (non-detection)"),
            ("Man", "2-hourly checks performed and recorded", "Ruled out – records complete"),
            ("Environment", "—", "Not related"),
        ],
        why_occ=[
            "Why undersized hole and burr? — The punch cutting edge was worn and chipped.",
            "Why was it worn and chipped? — High-strength coil at the upper end of the range increased edge loading near the end of the sharpening interval.",
            "Why at the upper end? — HSLA 500 specification allows 560–700 MPa; no restriction for AR-1007.",
            "Why did the punch chip? — Standard HSS punch without coating; not designed for Rm close to 700 MPa.",
        ],
        why_det=[
            "Why not detected at Arga? — The 2-hourly plug gauge check passed because the gauge itself was worn (Ø11.17).",
            "Why was the gauge worn? — Calibration interval of 6 months not respected (overdue 2 months).",
        ],
        rc_occ="Punch P3 edge wear and chipping, accelerated by a coil with tensile strength at the upper specification range.",
        rc_det="Worn, out-of-calibration plug gauge accepted undersized holes during in-process checks.",
        rc_verif="Trial on {d6}: sharpened punch with coil S-ULTZ-250205 → Ø11.24–11.27, burr ≤ 0.08 mm. Worn plug gauge accepts Ø11.17 holes.",
        d5=[
            ("Coated punch P3 (PM steel + TiCN) for MT-07 — order and trial", "Corrective – occurrence", "Unai Ezkurra", 60),
            ("HSLA 500 for AR-1007: Rm ≤ 650 MPa agreed with S-ULTZ", "Corrective – occurrence", "Leire Sarasola", 30),
            ("New plug gauge; calibration interval 3 months; gauge wear check weekly", "Corrective – detection", "Mikel Aranburu", 7),
            ("Burr measured with dial gauge at 4 positions every 2 h", "Corrective – detection", "Josu Elizalde", 7),
        ],
        d6=("New gauge in use since {d10}; burr measurement at 4 positions since {d10}. The sharpening interval of 60,000 strokes "
            "defined in PROC-L1-AFILADO-01 v3 is maintained; the coated punch is expected to extend punch life further."),
        d6_results=["Hole Ø11.23–11.29 mm and burr ≤ 0.12 mm in all checks for 8 weeks.", "No further complaints from Leitzaran in 60 days."],
        d7=[
            ("PFMEA: causes 'material at upper strength range' and 'gauge wear'", "AMFE-AR1007-01 v3", "Unai Ezkurra", 35, "Done"),
            ("Control plan: burr at 4 positions, gauge calibration 3 months", "PC-AR1007-01 v3", "Maialen Irigoyen", 35, "Done"),
            ("Coated punch trial on MT-07", "Toolroom project TR-25-07", "Unai Ezkurra", 90, "Open – supplier delivery delayed"),
        ],
        d8="8D closed on {closed} with the coated punch trial carried in the toolroom action plan. Leitzaran accepted the closure.",
    ),
    # ------------------------------------------------------------------ 2025-011 · AR-1001 · OEM Norte
    dict(
        id="8D-ARGA-2025-011", lang="EN", template="OEMN", close_days=70,
        title="Hole position shifted, engine bay harness bracket (AR-1001)",
        part_en="Engine bay harness bracket", char_en="Hole position", line="L1 — PR-250 / die MT-01",
        team=["Iñaki Etxeberria", "Maialen Irigoyen", "Unai Ezkurra", "Koldo Arbizu", "Josu Elizalde"],
        customer_contact="Customer contact: M. Ruiz, Supplier Quality Engineer, OEM Norte.",
        statement=("OEM Norte reported 180 engine bay harness brackets (AR-1001) with the two clip holes shifted 1.2 mm in X; the "
                   "harness clip cannot be installed. Lot L25216-AR1001-01."),
        w5h2=[
            ("What", "Position of holes H1/H2 shifted +1.1 to +1.3 mm in X (tolerance ±0.3 mm, SC)."),
            ("Where", "OEM Norte front-end harness station. Origin: Arga L1, PR-250, progressive die MT-01."),
            ("When", "Lot produced 04/08/2025 (afternoon shift), delivered 09 and 11/08/2025, detected 15/09/2025."),
            ("Who", "OEM Norte assembly operator."),
            ("Which", "Only parts stamped after a strip misfeed at the coil end."),
            ("How", "Strip mis-registration: the pilot of station 2 was broken, so the strip was not re-centred."),
            ("How many", "180 NOK out of 2,586 delivered."),
        ],
        rejects={"L25216-AR1001-01": 196},
        d3_intro="Containment started on {d0}, within 24 h. Scope: AR-1001 lots from the complained lot to the notification date.",
        d3=[
            "Arga stock ({stock} parts) blocked on {d0} and 100 % checked on the checking fixture CF-AR1001.",
            "OEM Norte stock sorted on {d1}–{d2}.",
        ],
        d4_intro="Analysis on {d4} with toolroom and maintenance.",
        ishikawa=[
            ("Machine", "Pilot pin of station 2 of MT-01 broken after a misfeed at the coil end", "CONFIRMED"),
            ("Machine", "Die protection sensor (misfeed) not connected after the last die change", "CONFIRMED"),
            ("Method", "Die setup checklist without a check of the die protection sensors", "CONFIRMED"),
            ("Material", "Coil S-ULTZ-250133 (DC04 1.5 mm): camber", "Ruled out"),
            ("Measurement", "Checking fixture control once per shift", "CONFIRMED (non-detection)"),
            ("Man", "—", "Not related"),
        ],
        why_occ=[
            "Why were holes shifted? — The strip was not re-centred at station 2.",
            "Why? — The pilot pin of station 2 was broken.",
            "Why did it break? — A misfeed at the coil end was not stopped by the press.",
            "Why was it not stopped? — The misfeed sensor cable was not connected after the last die change.",
            "Why? — The die setup checklist (IT-L1-PR250-04 v1) did not require checking die protection sensors.",
        ],
        why_det=["Why not detected at Arga? — Checking fixture control once per shift; the misfeed happened mid-shift."],
        rc_occ="Broken pilot in MT-01 after an undetected misfeed, because the die protection sensor was not connected at die setup.",
        rc_det="Checking fixture control frequency too low to detect a mid-shift event.",
        rc_verif="Reproduced on {d5} with the pilot removed: holes shifted 1.1–1.3 mm.",
        d5=[
            ("Replace pilot pins of MT-01; sensor connection with press interlock (no stroke without sensor signal)", "Corrective – occurrence", "Koldo Arbizu", 10),
            ("Die setup checklist: die protection sensors connected and tested", "Corrective – occurrence", "Unai Ezkurra", 14),
            ("Checking fixture control every 2 h and after every coil change", "Corrective – detection", "Josu Elizalde", 7),
        ],
        d6="Implemented by {d14}. IT-L1-PR250-04 updated to v2 with the sensor check.",
        d6_results=["Hole position within ±0.15 mm in all checks during 8 weeks.", "No recurrence at OEM Norte."],
        d7=[
            ("Read-across: sensor interlock on all progressive dies of PR-250", "PR-250 controller", "Koldo Arbizu", 45, "Done"),
            ("Die setup instruction updated", "IT-L1-PR250-04 v2", "Unai Ezkurra", 14, "Done"),
        ],
        d8="8D closed on {closed}; accepted by OEM Norte.",
    ),
    # ------------------------------------------------------------------ 2025-014 · AR-1003 · OEM Norte
    dict(
        id="8D-ARGA-2025-014", lang="EN", template="OEMN", close_days=70, extra_refs=["AR-1004"],
        title="Crack at root of MIG weld seam, battery tray bracket LH (AR-1003)",
        part_en="Battery tray bracket LH", char_en="MIG weld strength", line="L2 — CR-01",
        team=["Iñaki Etxeberria", "Maialen Irigoyen", "Oihana Zabaleta", "Xabier Urrutia", "Ander Goñi", "Mikel Aranburu"],
        customer_contact="Customer contact: M. Ruiz, Supplier Quality Engineer, OEM Norte battery module assembly.",
        statement=("During its product audit (cross-sections), OEM Norte found 16 battery tray brackets LH (AR-1003) with a crack "
                   "at the root of MIG weld seam W2. Lot L25281-AR1003-01. OEM Norte requested reference to previous 8D "
                   "reports on the same part."),
        w5h2=[
            ("What", "Crack at the weld root of seam W2, length 3–8 mm, lack of fusion at the root. CC characteristic."),
            ("Where", "OEM Norte product audit lab. Origin: Arga L2, robot cell CR-01."),
            ("When", "Lot produced 08/10/2025 (night shift), delivered 11/10/2025, detected 17/11/2025."),
            ("Who", "OEM Norte product audit team."),
            ("Which", "AR-1003; AR-1004 (same cell) included in containment as read-across."),
            ("How", "Macro-section: root penetration 0.3–0.7 mm; spatter inclusions at the root."),
            ("How many", "16 NOK out of 788 delivered."),
        ],
        d2_extra=("History: this part/defect was already addressed in 8D-ARGA-2025-002 (lack of fusion, lot L25001-AR1003-01), "
                  "which introduced the change of gas nozzle and contact tip every 8 h. This report checks whether that "
                  "action was effective."),
        rejects={"L25281-AR1003-01": 19, "L25288-AR1003-01": 4, "L25309-AR1003-01": 2},
        d3_intro=("Containment started on {d0}, within 24 h. Scope: AR-1003 and AR-1004 lots welded on CR-01 from the complained lot "
                  "to the notification date."),
        d3=[
            "Arga stock ({stock} parts) blocked on {d0}; 100 % visual of seam W2 + pull-out test 5 parts per lot + 1 macro-section per lot.",
            "OEM Norte stock and parts in transit sorted by the Arga resident team on {d1}–{d3} (visual + dye penetrant).",
            "All NOK parts found in sorting came from lots welded on the night shift.",
            "Interim action from 21/11/2025: toolbox talk to the night shift of L2 and handwritten addendum at CR-01: nozzle and contact tip change at 22:00.",
        ],
        d4_intro=("Review of 8D-ARGA-2025-002 and of its actions on {d4}. The change log REG-L2-CR01-01 was analysed for "
                  "September and October 2025."),
        ishikawa=[
            ("Method", f"Nozzle/contact tip change not performed on the night shift: log REG-L2-CR01-01 shows the preventive change on {_d25_a} of {_d25_t} morning/afternoon shifts but only on {_n25_a} of {_n25_t} nights (Sep–Oct 2025)", "CONFIRMED"),
            ("Method", "IT-L2-CR01-03 v3 §5.2 defines the change at the start of the morning (06:00) and afternoon (14:00) shifts only", "CONFIRMED"),
            ("Man", "Night crew not trained on the 8 h rule; no shift-start meeting at 22:00", "CONFIRMED (contributing)"),
            ("Machine", "Contact tip in use up to 16 h at the end of the night shift (last change 14:00)", "CONFIRMED"),
            ("Material", "MIG wire lot S-GOIE-250130, in use on CR-01 since 24/09/2025", "Ruled out – 3.1 certificate conform; program P12 unchanged at spool change"),
            ("Material", "Steel coil S-ULTZ-250183 (HSLA 420)", "Ruled out"),
            ("Measurement", "Pull-out test 3 parts per lot passed (18.6 / 19.1 / 22.0 kN) — values close to the limit without reaction", "CONFIRMED (non-detection)"),
            ("Environment", "—", "Not related"),
        ],
        why_occ=[
            "Why did seam W2 crack at the root? — Lack of fusion at the root with spatter inclusions.",
            "Why lack of fusion? — Unstable arc and poor gas shielding from a worn contact tip and an obstructed nozzle.",
            "Why were they worn on 08/10/2025? — No change was made at the start of the night shift; the tip had been in use since 14:00.",
            "Why no change on the night shift? — IT-L2-CR01-03 v3 lists the change only for the morning and afternoon shifts; the 8 h rule of 8D-ARGA-2025-002 was written into the instruction as 'start of shift' for the two day shifts.",
            "Why was the gap not found earlier? — The effectiveness check of 8D-ARGA-2025-002 (layered audits of 12 and 19/03/2025) covered the morning and afternoon shifts only.",
        ],
        why_det=[
            "Why not detected at Arga? — Pull-out tests passed with values close to the 18 kN limit; the control plan has no reaction rule for results near the limit.",
            "Why? — Only a lower specification limit was defined; no warning limit.",
        ],
        rc_occ=("The corrective action of 8D-ARGA-2025-002 (nozzle and contact tip change every 8 h) was not standardised for the night "
                "shift: IT-L2-CR01-03 v3 only defines it for the morning and afternoon shifts, so on the night shift the consumables "
                "stayed in use up to 16 h."),
        rc_det="No warning limit or reaction rule for pull-out results close to the specification limit.",
        rc_verif=("Trial on {d6}: tip after 16 h → bore 1.38–1.42 mm and 3/10 parts with root penetration < 1.0 mm; tip after 8 h → "
                  "1.25–1.28 mm and 10/10 conform."),
        d5=[
            ("Include the 22:00 change (night shift) in IT-L2-CR01-03 and in the cell checklist", "Corrective – occurrence", "Oihana Zabaleta", 73),
            ("Night shift leader signs the change log every night; weekly review by L2 production manager", "Corrective – occurrence", "Ander Goñi", 5),
            ("Pull-out warning limit 20 kN: below it, 5 extra parts + macro-section", "Corrective – detection", "Mikel Aranburu", 14),
            ("Layered process audits on all three shifts (including night) for 3 months", "Verification", "Maialen Irigoyen", 90),
        ],
        d6=("Night-shift change applied from 21/11/2025 (toolbox talk + handwritten addendum at the cell). Warning limit for "
            "pull-out test in PC-AR1003-01 from {d14}."),
        d6_results=[
            f"Change log REG-L2-CR01-01, 21/11–31/12/2025: night-shift preventive change recorded on {_n25b_a} of {_n25b_t} nights.",
            "Pull-out tests: minimum 20.2 kN, 2 warning-limit reactions, both conform after macro-section.",
            "No further complaints from OEM Norte in the 60 days after implementation.",
        ],
        d7=[
            ("Work instruction: night-shift change at 22:00", "IT-L2-CR01-03 v4", "Oihana Zabaleta", 73, "Open – draft v4 under review (action plan AP-2025-031)"),
            ("PFMEA: detection rating of pull-out test reviewed (warning limit)", "AMFE-AR1003-01 v4", "Oihana Zabaleta", 30, "Done"),
            ("Control plan: pull-out warning limit", "PC-AR1003-01 v4", "Maialen Irigoyen", 30, "Done"),
            ("Lessons learned: verify 8D effectiveness on every shift", "LL-2025-11", "Maialen Irigoyen", 40, "Done"),
        ],
        d7_note="Open D7 actions are tracked in the plant action plan (AP-2025-031) and reviewed at the monthly quality meeting.",
        d8="8D closed on {closed} with the work instruction update carried in the action plan. OEM Norte accepted the closure.",
    ),
    # ------------------------------------------------------------------ 2025-015 · AR-1012 · Ribera
    dict(
        id="8D-ARGA-2025-015", lang="ES", template="ARGA", close_days=66,
        title="Fuerza de retención del clip baja (AR-1012)", line="L1 — PR-250 / matriz MT-12",
        team=["Iñaki Etxeberria", "Maialen Irigoyen", "Unai Ezkurra", "Mikel Aranburu", "Josu Elizalde"],
        customer_contact="Contacto del cliente: C. Jiménez, Calidad de Proveedores, Ribera Chassis Systems.",
        statement=("Ribera Chassis Systems reclama 900 clips de sujeción del tubo de freno (AR-1012) con fuerza de retención baja: "
                   "el tubo se suelta en su ensayo de extracción. Lote L25301-AR1012-01."),
        w5h2=[
            ("Qué", "Fuerza de retención 28–41 N (requisito ≥ 45 N, SC)."),
            ("Dónde", "Laboratorio y línea de montaje de Ribera. Origen: Arga L1, PR-250, matriz MT-12, estación de doblado E4."),
            ("Cuándo", "Lote fabricado el 28/10/2025 (turno de tarde), expedido el 04–05/11/2025, detectado el 08/12/2025."),
            ("Quién", "Laboratorio de Ribera."),
            ("Cuál", "Lotes estampados tras el cambio de inserto de doblado del 20/10/2025."),
            ("Cómo", "Ángulo de la lengüeta de retención 86–87° (nominal 90 ± 1°): menor precarga sobre el tubo."),
            ("Cuántas", "900 piezas NOK de 1.196 expedidas."),
        ],
        rejects={"L25301-AR1012-01": 930, "L25308-AR1012-01": 120},
        d3_intro="Contención iniciada el {d0}. Alcance: lotes de AR-1012 desde el lote reclamado hasta la fecha de la reclamación.",
        d3=[
            "Stock en Arga ({stock} piezas) bloqueado el {d0}; ensayo de retención 5 piezas por caja y medición de ángulo en proyector de perfiles.",
            "Selección en Ribera el {d1}–{d2}.",
        ],
        d4_intro="Análisis del {d4} con matricería.",
        ishikawa=[
            ("Máquina", "Inserto de doblado E4 de MT-12 desgastado (radio 0,6 mm frente a 0,3 mm)", "CONFIRMADO"),
            ("Máquina", "Falta de la calza de 0,2 mm tras el cambio de inserto del 20/10/2025", "CONFIRMADO"),
            ("Material", "Bobina S-ULTZ-250234 (acero para muelles 1,0 mm)", "Descartado – dureza conforme"),
            ("Método", "Ensayo de retención solo en la primera pieza", "CONFIRMADO (no detección)"),
            ("Mano de obra", "—", "Sin relación"),
            ("Medio ambiente", "—", "Sin relación"),
        ],
        why_occ=[
            "¿Por qué la retención es baja? — La lengüeta queda a 86–87°.",
            "¿Por qué? — El inserto de doblado E4 estaba desgastado y faltaba la calza de 0,2 mm.",
            "¿Por qué faltaba la calza? — No figuraba en la hoja de montaje del inserto.",
        ],
        why_det=["¿Por qué no se detectó? — El ensayo de retención solo se hacía en la primera pieza del lote."],
        rc_occ="Inserto de doblado desgastado y montado sin la calza requerida tras su cambio.",
        rc_det="Ensayo de retención solo en primera pieza.",
        rc_verif="Prueba del {d5}: con inserto nuevo y calza, ángulo 89,6–90,4° y retención 52–58 N.",
        d5=[
            ("Nuevo inserto E4 y calza incluida en la hoja de montaje", "Correctiva – ocurrencia", "Unai Ezkurra", 7),
            ("Ensayo de retención 5 piezas cada 2 h", "Correctiva – detección", "Josu Elizalde", 7),
        ],
        d6="Implantado el {d10}.",
        d6_results=["Retención mínima 49 N durante 8 semanas.", "Sin nuevas reclamaciones en 60 días."],
        d7=[
            ("Plan de control AR-1012: retención cada 2 h", "Plan de control AR-1012", "Maialen Irigoyen", 30, "Hecho"),
            ("Hojas de montaje de insertos con calzas", "Matricería", "Unai Ezkurra", 30, "Hecho"),
        ],
        d8="8D cerrado el {closed}; aceptado por Ribera.",
    ),
    # ------------------------------------------------------------------ 2026-001 · AR-1011 · Leitzaran
    dict(
        id="8D-ARGA-2026-001", lang="EN", template="ARGA", close_days=70,
        title="Stuck spot weld, bracket for seat frame (AR-1011)",
        part_en="Bracket for seat frame", char_en="Spot weld strength", line="L2 — SP-01",
        team=["Iñaki Etxeberria", "Maialen Irigoyen", "Oihana Zabaleta", "Koldo Arbizu", "Xabier Urrutia"],
        customer_contact="Customer contact: A. Bengoetxea, Supplier Quality, Leitzaran Seating.",
        statement=("Leitzaran Seating reported 35 seat frame brackets (AR-1011) with a stuck (unfused) spot weld that separated "
                   "during assembly. Lot L25363-AR1011-01."),
        w5h2=[
            ("What", "Spot weld S3 separated without nugget (stuck weld). CC characteristic."),
            ("Where", "Leitzaran seat frame line. Origin: Arga L2, spot welding gun SP-01."),
            ("When", "Lot produced 29/12/2025 (afternoon shift), delivered 02/01/2026, detected 09/02/2026."),
            ("Who", "Leitzaran assembly operator."),
            ("Which", "AR-1011."),
            ("How", "Electrode cap face grown to 8.5 mm (nominal 6.0 mm) → current density too low."),
            ("How many", "35 NOK out of 1,080 delivered."),
        ],
        rejects={"L25363-AR1011-01": 41},
        d3_intro="Containment started on {d0}. Scope: AR-1011 lots from the complained lot until notification.",
        d3=["Arga stock ({stock} parts) blocked on {d0}; chisel test 100 % on spot S3.", "Leitzaran stock sorted on {d1}–{d2}."],
        d4_intro="Analysis on {d4}.",
        ishikawa=[
            ("Machine", "Tip dresser of SP-01 cutter broken; fault alarm bypassed during the holiday period", "CONFIRMED"),
            ("Method", "No check of the electrode face diameter", "CONFIRMED"),
            ("Material", "Coil S-ULTZ-250164 (HSLA 340)", "Ruled out"),
            ("Measurement", "Chisel test only at start of shift", "CONFIRMED (non-detection)"),
            ("Man", "Reduced crew during holiday period", "Contributing"),
            ("Environment", "—", "Not related"),
        ],
        why_occ=[
            "Why stuck weld? — Current density too low to form a nugget.",
            "Why? — Electrode face grew to 8.5 mm.",
            "Why? — Tip dressing did not take place: the dresser cutter was broken.",
            "Why was welding not stopped? — The dresser fault alarm had been bypassed.",
        ],
        why_det=["Why not detected? — Chisel test only at the start of each shift."],
        rc_occ="Electrode caps not dressed because of a broken tip dresser whose alarm was bypassed.",
        rc_det="Low chisel test frequency and no face diameter check.",
        rc_verif="Trial on {d5}: 8.5 mm face → 6/10 stuck welds; dressed 6.0 mm face → 10/10 nugget ≥ 5.2 mm.",
        d5=[
            ("Tip dresser fault interlocked with welding (bypass requires maintenance key)", "Corrective – occurrence", "Koldo Arbizu", 10),
            ("Face diameter check with template every 2 h", "Corrective – occurrence", "Xabier Urrutia", 7),
            ("Chisel test 1 part every 2 h", "Corrective – detection", "Xabier Urrutia", 7),
        ],
        d6="Implemented by {d14}. IT-L2-SP01-02 updated to v5.",
        d6_results=["All chisel tests conform for 8 weeks.", "No recurrence at Leitzaran."],
        d7=[("Bypass control of safety/quality alarms", "Maintenance procedure", "Koldo Arbizu", 45, "Done")],
        d8="8D closed on {closed}; accepted by Leitzaran.",
    ),
    # ------------------------------------------------------------------ 2026-003 · AR-1008 · OEM Norte
    dict(
        id="8D-ARGA-2026-003", lang="EN", template="OEMN", close_days=68,
        title="Hole position out of tolerance, tailgate hinge reinforcement (AR-1008)",
        part_en="Tailgate hinge reinforcement plate", char_en="Hole position", line="L1 — PR-250 / die MT-08",
        team=["Iñaki Etxeberria", "Maialen Irigoyen", "Unai Ezkurra", "Josu Elizalde", "Mikel Aranburu"],
        customer_contact="Customer contact: M. Ruiz, Supplier Quality Engineer, OEM Norte.",
        statement=("OEM Norte reported 90 tailgate hinge reinforcement plates (AR-1008) with hole position out of tolerance; the "
                   "hinge does not align. Lot L26070-AR1008-01."),
        w5h2=[
            ("What", "Hole position shifted 0.6–0.9 mm in Y (tolerance ±0.3 mm, SC)."),
            ("Where", "OEM Norte body shop, tailgate line. Origin: Arga L1, PR-250, die MT-08."),
            ("When", "Lot produced 11/03/2026 (night shift, die changed at 23:30), delivered 18/03/2026, detected 20/04/2026."),
            ("Who", "OEM Norte body shop."),
            ("Which", "AR-1008, parts stamped after the night-shift die change."),
            ("How", "Die MT-08 positioned against the wrong stop block on the bolster."),
            ("How many", "90 NOK out of 983 delivered."),
        ],
        rejects={"L26070-AR1008-01": 98},
        d3_intro="Containment started on {d0}, within 24 h. Scope: AR-1008 lots from the complained lot until notification.",
        d3=["Arga stock ({stock} parts) blocked on {d0}; 100 % check on checking fixture CF-AR1008.", "OEM Norte stock sorted on {d1}–{d2}."],
        d4_intro="Analysis on {d4}.",
        ishikawa=[
            ("Method", "Die change on the night shift without first-off approval (no quality technician on nights)", "CONFIRMED"),
            ("Machine", "Die locating: two stop blocks on PR-250 bolster, no poka-yoke", "CONFIRMED"),
            ("Man", "Die setter from L3 covering the night shift", "Contributing"),
            ("Material", "Coil S-ULTZ-260123 (DC04)", "Ruled out"),
            ("Measurement", "Checking fixture control at 06:00 found the deviation but the lot had been partially packed", "CONFIRMED (non-detection)"),
            ("Environment", "—", "Not related"),
        ],
        why_occ=[
            "Why hole position shifted? — Die MT-08 set against the wrong stop block.",
            "Why? — Two stop blocks exist on the bolster and no locating pin prevents the wrong position.",
            "Why was it not detected at setup? — First-off approval by quality is not available on the night shift and was skipped.",
        ],
        why_det=["Why not detected earlier? — Checking fixture control once per shift; parts packed before the 06:00 check were not segregated."],
        rc_occ="Die mis-location on PR-250 during a night-shift die change, without poka-yoke and without first-off approval.",
        rc_det="First-off approval skipped on nights; low checking fixture frequency.",
        rc_verif="Reproduced on {d5}: die on the second stop block → +0.8 mm in Y.",
        d5=[
            ("Locating pins on the PR-250 bolster for MT-08 (poka-yoke)", "Corrective – occurrence", "Unai Ezkurra", 21),
            ("Night-shift first-off approval by the shift leader with checking fixture + photo in the setup log", "Corrective – occurrence", "Josu Elizalde", 7),
            ("Checking fixture control every 2 h; packing only after first-off approval", "Corrective – detection", "Mikel Aranburu", 7),
        ],
        d6="Implemented by {d21}. IT-L1-PR250-04 updated to v3.",
        d6_results=["Hole position within ±0.12 mm for 8 weeks.", "No recurrence at OEM Norte."],
        d7=[("Die setup instruction: night-shift first-off approval", "IT-L1-PR250-04 v3", "Unai Ezkurra", 21, "Done"),
            ("Read-across: locating pins for all dies on PR-250", "Toolroom", "Unai Ezkurra", 60, "Done")],
        d8="8D closed on {closed}; accepted by OEM Norte.",
    ),
]
