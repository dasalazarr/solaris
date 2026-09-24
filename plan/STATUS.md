# STATUS — tablero vivo

> Se lee al **empezar** cada sesión y se actualiza al **cerrarla** (skill `session-protocol`).
> Última actualización: 2026-09-25 · wiki-maintainer · cierre de M2-T3

**Hito actual:** M1 — Planta sintética + golden set · **Demo listo el:** 17/10/2026 · **Límite duro:** 06/11/2026 (ayuda foral)

## Siguiente tarea por rol

| Rol | Siguiente tarea | Puede empezar | Notas |
|---|---|---|---|
| product | **M1-T5** Golden set: 50 Q&A + 5 casos 8D (JSONL en `app/evals/golden/`) | ✅ sí | Parte de `app/evals/scenario_truth.json`. Citas con locator (page/section/sheet). Los 5 casos 8D deben incluir el distractor #3 y la inyección #5 |
| dev | **M2-T4** Exactitud de la extracción de AMFE (≥85% por campo) → **M2-T5** recuperación híbrida + rerank | ✅ sí | M2-T4 necesita la verdad por fila (hay AMFE en `scenario_truth` y en el corpus). M2-T5: diversificar por documento (REG domina) |
| security | **M1-T6** Revisión de datos sintéticos (tras M1-T4/T5); después **M4-T1** RBAC + `solaris_app` + auth en `/audit` | ⏳ M1-T6 tras M1-T5; M4-T1 ✅ ya puede empezar | M4-T2 ✅ hecho. M4-T1 cierra la mayoría de los puntos heredados (ver la traza de M4-T2) |
| wiki | Consolidar al cierre de cada sesión | siempre | — |

## Bloqueos / decisiones pendientes del fundador
- Crear una cuenta de OpenRouter y poner `OPENROUTER_API_KEY` en `.env` (no se versiona). Hace falta a partir de M2-T6.
- Confirmar 5 contactos para las sesiones de validación de M6-T5 (vía ACAN o contactos propios), idealmente antes del 10/10.

## Progreso por hito

| Hito | Estado |
|---|---|
| M0 | ✅ done (2026-09-24) |
| M1 | ▶ en curso (4/6: T1–T4 ✅) |
| M2 | ▶ en curso (3/8: T1–T3 ✅) |
| M3 | ▶ adelantado (1/6: T1 ✅) |
| M4 | ▶ adelantado (1/5: T2 ✅) |
| M5 | ☐ (0/8) |
| M6 | ☐ (0/6) |
