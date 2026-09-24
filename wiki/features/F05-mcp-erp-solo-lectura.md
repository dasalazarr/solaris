---
id: F05
type: feature
title: "MCP ERP en solo lectura con consulta visible"
status: building
owner_role: dev
links: ["[[P03]]", "[[P07]]", "[[L05]]", "[[R03]]"]
evidence: ["raw/research/IllariumOS.md#L195"]
updated: 2026-09-25
---

# F05 — MCP ERP en solo lectura con consulta visible

## Qué es
Servidor MCP sobre ERP mock (lotes, envíos, proveedores, líneas). Cada dato se muestra con la consulta ejecutada.

## Criterios de aceptación
- Solo lectura (escritura rechazada y registrada).
- Si el conector falla, el agente lo dice y no inventa.

## Hito
M3 — ver `plan/milestones/M3.md`.

## Notas / iteraciones
- 2026-09-25 (M3-T1): servidor en `app/mcp/erp_mock` con 7 herramientas; `containment_scope` reproduce el alcance de referencia de la familia A.
  - Con la matriz actual, el rol planta solo puede usar `find_lots`.
  - `query` es una lista `{sql, params}` porque algunas herramientas hacen 2 consultas; la UI (M5-T4) debe mostrarlas todas.
