# STATUS — tablero vivo

> Se lee al **empezar** cada sesión y se actualiza al **cerrarla** (skill `session-protocol`).
> Última actualización: 2026-09-25 · wiki-maintainer · cierre de M1-T6

**Hito actual:** M2 — Ingesta + RAG citado (M1 ✅ cerrado, con el menor M1-T8 pendiente) · **Demo listo el:** 17/10/2026 · **Límite duro:** 06/11/2026 (ayuda foral)

## Siguiente tarea por rol

| Rol | Siguiente tarea | Puede empezar | Notas |
|---|---|---|---|
| product | **M5-T1** Guion del demo v0 + wireframes de L01, L02, L03 y L07 | ✅ sí (adelantado; depende formalmente de M3-T3) | El guion puede escribirse ya con el escenario y los casos 8D; los wireframes validan la cuña antes de construir la UI |
| dev | **M2-T4** Exactitud de la extracción de AMFE (≥85% por campo) → **M2-T5** recuperación híbrida + rerank | ✅ sí | M2-T4 necesita la verdad por fila (hay AMFE en `scenario_truth` y en el corpus). M2-T5: diversificar por documento (REG domina) |
| security | **M4-T1** RBAC + on-behalf-of + rol `solaris_app` + auth en `/audit` | ⏳ cuando el backend quede libre (M2-T5 en curso) | Cierra la mayoría de los puntos heredados (traza de M4-T2). Luego M2-T8 (revisión de M2) |
| wiki | Consolidar al cierre de cada sesión | siempre | — |

## Bloqueos / decisiones pendientes del fundador
- Crear una cuenta de OpenRouter y poner `OPENROUTER_API_KEY` en `.env` (no se versiona). Hace falta a partir de M2-T6.
- Confirmar 5 contactos para las sesiones de validación de M6-T5 (vía ACAN o contactos propios), idealmente antes del 10/10.

## Progreso por hito

| Hito | Estado |
|---|---|
| M0 | ✅ done (2026-09-24) |
| M1 | ✅ cerrado (T1–T7; queda el menor T8 cosmético) |
| M2 | ▶ en curso (3/8: T1–T3 ✅) |
| M3 | ▶ adelantado (1/6: T1 ✅) |
| M4 | ▶ adelantado (1/5: T2 ✅) |
| M5 | ☐ (0/8) |
| M6 | ☐ (0/6) |
