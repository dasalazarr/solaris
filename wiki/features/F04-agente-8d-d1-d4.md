---
id: F04
type: feature
title: "Agente 8D D1–D4"
status: building
owner_role: dev
links: ["[[P02]]", "[[P07]]", "[[L01]]", "[[L02]]", "[[F03]]", "[[F05]]", "[[F06]]", "[[H01]]"]
evidence: ["raw/research/IllariumOS.md#L194"]
updated: 2026-09-27
---

# F04 — Agente 8D D1–D4

## Qué es
A partir de una reclamación (PDF/correo) genera borrador D1–D4: equipo, descripción, contención, causas raíz candidatas.

## Criterios de aceptación
- Borrador < 3 min.
- ≥min(3, n) 8D/incidencias similares enlazadas (n = antecedentes reales); no presentar como misma causa los de `forbidden_similar_8d` (distractor).
- ≥2 hipótesis de causa raíz ligadas a filas del AMFE cuando exista; si la pieza no tiene AMFE, hipótesis "fuera del AMFE" con el hueco declarado (esto también es valor: detectar un AMFE ausente).
- Todo editable.

## Hito
M3 — ver `plan/milestones/M3.md`.

## Notas / iteraciones
- 2026-09-26 (M3-T2): parser de reclamaciones con 100 % de campos correctos en las 5. Separa por diseño lo que ve el LLM (solo texto visible no sospechoso) de lo que se marca (oculto y metadatos). Cualquier código que devuelva el LLM tiene que aparecer literalmente en el texto visible.
- 2026-09-26 (M3-T3): primer grafo 8D de extremo a extremo. **El caso del demo (0312) pasa en las 2 pasadas**: contención exacta, 3 antecedentes y filas del AMFE correctas. Fallan el distractor (el modelo afirma misma causa contra su propia evidencia) y la clasificación de antecedentes (`no_relacionado` donde es mismo síntoma). Se resuelve con guardas deterministas en servidor (M3-T7), no con más prompt (PAT-010). Latencia: 1/5 ≤ 90 s, por el proveedor (PAT-009).
- 2026-09-27 (M3-T7): **5/5 casos PASS en ~27 s** con guardas deterministas de relación (mismo síntoma / analogía / misma causa degradada por evidencia contraria). El distractor ya no se presenta como misma causa, y los antecedentes con el mismo síntoma siempre aparecen. Queda: HITL (M3-T4) y revisión de security (M3-T6).
