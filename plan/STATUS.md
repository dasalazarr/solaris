# STATUS — tablero vivo

> Se lee al **empezar** cada sesión y se actualiza al **cerrarla** (skill `session-protocol`).
> Última actualización: 2026-09-26 · wiki-maintainer · cierre de M2-T6

**Hito actual:** M2 — Ingesta + RAG citado (M1 ✅ cerrado, con el menor M1-T8 pendiente) · **Demo listo el:** 17/10/2026 · **Límite duro:** 06/11/2026 (ayuda foral)

## Siguiente tarea por rol

| Rol | Siguiente tarea | Puede empezar | Notas |
|---|---|---|---|
| product | **M1-T8** menores de M1-T6 (teléfonos, metadato, check de metadatos) · después **M6-T4** protocolo de validación | ✅ sí | M5-T1 ✅ hecho. Decidido (ADR-0006): promesa de ROI + F12 en alcance |
| dev | **M2-T7** Cerrar el gate de calidad de M2 (citas ≥90 %, "no encontrado" 5/5, p95 <8 s) **y en paralelo M3-T2** parser de reclamaciones | ✅ sí | Estado actual: 77,1 % / 4/5 / 10,8 s. Runner parcial en `app/evals/` (commit `ededb35`) |
| security | **Revisar el diff de M2-T6** (tabla de cumplimiento en su traza) · **M4-T5** pack de cumplimiento (parcial en `docs-compliance/`, detenido por el fundador) | ✅ sí | M2-T8 ✅ APPROVE. Luego M4-T4 red-team (necesita M3-T4) |
| wiki | Consolidar al cierre de cada sesión | siempre | — |

## Bloqueos / decisiones pendientes del fundador
- Confirmar 5 contactos para las sesiones de validación de M6-T5 (vía ACAN o contactos propios), idealmente antes del 10/10.

## Progreso por hito

| Hito | Estado |
|---|---|
| M0 | ✅ done (2026-09-24) |
| M1 | ✅ cerrado (T1–T7; queda el menor T8 cosmético) |
| M2 | ▶ en curso (6/9: T1–T3, T5, T6, T8 ✅; T7 = gate de calidad abierto; T4 y T9 pendientes) |
| M3 | ▶ adelantado (1/6: T1 ✅) |
| M4 | ▶ adelantado (2/5: T1 ✅ T2 ✅) |
| M5 | ▶ adelantado (1/8: T1 ✅) |
| M6 | ☐ (0/6) |
