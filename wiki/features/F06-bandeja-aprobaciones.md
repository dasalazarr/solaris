---
id: F06
type: feature
title: "Bandeja de aprobaciones (HITL)"
status: building
owner_role: dev
links: ["[[P02]]", "[[P04]]", "[[L03]]", "[[H01]]"]
evidence: ["raw/research/IllariumOS.md#L196", "raw/research/IllariumOS.md#L145"]
updated: 2026-09-27
---

# F06 — Bandeja de aprobaciones (HITL)

## Qué es
Interrupts de LangGraph: el 8D no avanza a D5+ ni se exporta sin aprobación de un rol designado.

## Criterios de aceptación
- Sin aprobación no hay acción (test).
- Audit guarda quién, cuándo y qué versión.

## Hito
M3 — ver `plan/milestones/M3.md`.

## Notas / iteraciones
- 2026-09-27 (M3-T4): HITL operativo. La aprobación va ligada al hash exacto de D1–D4 y el servidor la revalida al reanudar (no se fía del valor que llega). El borrador aprobado queda congelado en BD, se calcula el % editado (H01) y el export se bloquea sin aprobación. Falta la UI (M5-T5) y el DOCX (M5-T6).
