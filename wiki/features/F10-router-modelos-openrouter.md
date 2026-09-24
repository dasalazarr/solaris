---
id: F10
type: feature
title: "Router de modelos con ficha de agente (OpenRouter)"
status: planned
owner_role: dev
links: ["[[P04]]", "[[L07]]", "[[R01]]", "[[H04]]"]
evidence: ["raw/research/IllariumOS.md#L210"]
updated: 2026-09-24
---

# F10 — Router de modelos con ficha de agente (OpenRouter)

## Qué es
Capa de abstracción LLM vía OpenRouter; modelo por agente/tarea configurable sin despliegue; ficha con modelo, proveedor, región y procedencia, visible en la consola de auditoría ([[L07]]).

## Criterios de aceptación
- Cambio de modelo por config.
- Eval de regresión automática al cambiar de modelo.
- Comparativa calidad/coste (DeepSeek y alternativas) guardada en raw/eval-runs/.

## Hito
M3 — ver `plan/milestones/M3.md`.

## Notas / iteraciones
_(anexar aquí aprendizajes; las propuestas de cambio van a `wiki/skill-impact.md`)_
