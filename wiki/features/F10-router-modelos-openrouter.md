---
id: F10
type: feature
title: "Router de modelos con ficha de agente (OpenRouter)"
status: building
owner_role: dev
links: ["[[P04]]", "[[L07]]", "[[R01]]", "[[H04]]"]
evidence: ["raw/research/IllariumOS.md#L210", "raw/sessions/2026-09-25_dev_M2-T1.md"]
updated: 2026-09-25
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
- 2026-09-25 (M2-T1): `route()` + `models.yaml` operativos con mocks.
  - Primario DeepSeek, fallback Mistral (origen UE). Los ids son provisionales hasta M3-T5.
  - Una ficha con `data_collection` distinto de `deny` no carga, y `route()` no deja cambiar `model` ni `provider` por llamada.
  - Pendiente: registrar en el audit el uso del fallback (M4-T2); `zdr: true` queda sin activar hasta verificar endpoints (M3-T5).
