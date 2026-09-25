# STATUS — tablero vivo

> Se lee al **empezar** cada sesión y se actualiza al **cerrarla** (skill `session-protocol`).
> Última actualización: 2026-09-25 · wiki-maintainer · cierre de M1-T5

**Hito actual:** M1 — Planta sintética + golden set · **Demo listo el:** 17/10/2026 · **Límite duro:** 06/11/2026 (ayuda foral)

## Siguiente tarea por rol

| Rol | Siguiente tarea | Puede empezar | Notas |
|---|---|---|---|
| product | **M1-T7** Correcciones de `scenario_truth` (3 errores detectados en M1-T5) → después **M5-T1** guion del demo v0 | ✅ sí | Tareas pequeñas. M1 se cierra con M1-T6 (security) |
| dev | **M2-T4** Exactitud de la extracción de AMFE (≥85% por campo) → **M2-T5** recuperación híbrida + rerank | ✅ sí | M2-T4 necesita la verdad por fila (hay AMFE en `scenario_truth` y en el corpus). M2-T5: diversificar por documento (REG domina) |
| security | **M1-T6** Revisión de datos sintéticos (corpus, reclamaciones con inyección, golden set, seed) | ✅ sí (M1-T5 done) | Incluye los puntos añadidos en el DoD (seed con etiqueta de familia, COST cita 8D). Después M4-T1 cuando el backend quede libre (M2-T5 en curso) |
| wiki | Consolidar al cierre de cada sesión | siempre | — |

## Bloqueos / decisiones pendientes del fundador
- Crear una cuenta de OpenRouter y poner `OPENROUTER_API_KEY` en `.env` (no se versiona). Hace falta a partir de M2-T6.
- Confirmar 5 contactos para las sesiones de validación de M6-T5 (vía ACAN o contactos propios), idealmente antes del 10/10.

## Progreso por hito

| Hito | Estado |
|---|---|
| M0 | ✅ done (2026-09-24) |
| M1 | ▶ en curso (5/7: T1–T5 ✅; faltan T6 security y T7 correcciones) |
| M2 | ▶ en curso (3/8: T1–T3 ✅) |
| M3 | ▶ adelantado (1/6: T1 ✅) |
| M4 | ▶ adelantado (1/5: T2 ✅) |
| M5 | ☐ (0/8) |
| M6 | ☐ (0/6) |
