# STATUS — tablero vivo

> Se lee al **empezar** cada sesión y se actualiza al **cerrarla** (skill `session-protocol`).
> Última actualización: 2026-09-27 · wiki-maintainer · cierre de M3-T4

**Hito actual:** M2 — Ingesta + RAG citado (M1 ✅ cerrado, con el menor M1-T8 pendiente) · **Demo listo el:** 17/10/2026 · **Límite duro:** 06/11/2026 (ayuda foral)

## Siguiente tarea por rol

| Rol | Siguiente tarea | Puede empezar | Notas |
|---|---|---|---|
| product | **M1-T9** verdad de `qty_not_shipped` + bloque `recommended` 0088 · **M2-T11** QA-012/015 | ✅ sí | Tareas cortas que desbloquean los gates |
| dev | **M3-T8** falso positivo de inyección en 0312 (bloquea el demo) → mejora de latencia → M2-T10 → M5-T2 (UI) | ✅ sí | — |
| security | **M3-T6** revisión de M3 + red-team preliminar (acumula los puntos de M3-T1, T2, T3, T4, T5 y ADR-0007) · M2-T12 | ✅ sí (M3-T4 hecho) | Tiene veto sobre el gate de M3 |
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
| M3 | ▶ en curso (6/8: T1–T5, T7 ✅; faltan T8 FP de inyección y T6 security) |
| M4 | ▶ adelantado (2/5: T1 ✅ T2 ✅) |
| M5 | ▶ adelantado (1/8: T1 ✅) |
| M6 | ☐ (0/6) |
