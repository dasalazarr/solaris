# STATUS — tablero vivo

> Se lee al **empezar** cada sesión y se actualiza al **cerrarla** (skill `session-protocol`).
> Última actualización: 2026-09-27 · wiki-maintainer · cierre de M5-T2

**Hito actual:** M5 — UI del demo (M3 ✅ cerrado: flujo 8D completo y aprobado por security) (M1 ✅; M2 con gate de calidad abierto → M2-T10) · **Demo listo el:** 17/10/2026 · **Límite duro:** 06/11/2026 (ayuda foral)

## Siguiente tarea por rol

| Rol | Siguiente tarea | Puede empezar | Notas |
|---|---|---|---|
| product | **M1-T9** verdad de `qty_not_shipped` + bloque `recommended` 0088 · **M2-T11** QA-012/015 | ✅ sí | Tareas cortas que desbloquean los gates |
| dev | **M5-T3** Inbox de reclamaciones (subir → caso 8D con progreso, aviso de inyección + nota de revisión) → **M5-T4** workspace 8D | ✅ sí | Backend: `POST /complaints/parse`, `POST /8d`, `GET /8d/{id}` (SSE opcional) |
| security | **M4-T4** suite red-team completa (6 casos + fixtures fuera del corpus + paráfrasis de PAT-012 + M-1) · M2-T12 · M4-T5 (parcial) | ✅ sí | M3 ✅ APPROVE con condiciones |
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
| M3 | ✅ cerrado (T1–T8; APPROVE con condiciones) |
| M4 | ▶ adelantado (2/5: T1 ✅ T2 ✅) |
| M5 | ▶ en curso (2/8: T1, T2 ✅) |
| M6 | ☐ (0/6) |
