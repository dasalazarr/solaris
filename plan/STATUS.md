# STATUS — tablero vivo

> Se lee al **empezar** cada sesión y se actualiza al **cerrarla** (skill `session-protocol`).
> Última actualización: 2026-09-26 · wiki-maintainer · cierre de M3-T2

**Hito actual:** M2 — Ingesta + RAG citado (M1 ✅ cerrado, con el menor M1-T8 pendiente) · **Demo listo el:** 17/10/2026 · **Límite duro:** 06/11/2026 (ayuda foral)

## Siguiente tarea por rol

| Rol | Siguiente tarea | Puede empezar | Notas |
|---|---|---|---|
| product | **M2-T11** revisar QA-012/QA-015 (golden set) · luego M1-T8 y M6-T4 | ✅ sí | Tarea corta |
| dev | **M3-T3** grafo LangGraph 8D D1–D4 (núcleo del demo) → M3-T4 HITL | ✅ sí | Requisitos de M5-T1 en el DoD (estados de hipótesis, `qty_not_shipped`, `injection_suspected`, idioma de la plantilla, ≤90 s) |
| security | **M2-T12** revisión del diff de M2-T6/T7 (traducción, prompts v3/v4, SQL nuevas, audit) · luego M4-T5 (parcial) | ✅ sí | Tiene veto sobre el gate de M2 |
| wiki | Consolidar al cierre de cada sesión | siempre | — |

## Bloqueos / decisiones pendientes del fundador
- **Coordinación de commits:** el fundador está haciendo commits ("first commit") con trabajo en curso de los agentes. No rompe nada, pero mezcla tareas en un mismo commit. Sugerencia: hacer push de los commits `Mx-Ty` ya cerrados en lugar de hacer commit del árbol de trabajo.
- Confirmar 5 contactos para las sesiones de validación de M6-T5 (vía ACAN o contactos propios), idealmente antes del 10/10.

## Progreso por hito

| Hito | Estado |
|---|---|
| M0 | ✅ done (2026-09-24) |
| M1 | ✅ cerrado (T1–T7; queda el menor T8 cosmético) |
| M2 | ▶ en curso (7/12: T1–T3, T5–T8 ✅; gate abierto → T10; T4, T9, T11, T12 pendientes) |
| M3 | ▶ en curso (2/6: T1 ✅ T2 ✅) |
| M4 | ▶ adelantado (2/5: T1 ✅ T2 ✅) |
| M5 | ▶ adelantado (1/8: T1 ✅) |
| M6 | ☐ (0/6) |
