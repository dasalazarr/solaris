# STATUS — tablero vivo

> Se lee al **empezar** cada sesión y se actualiza al **cerrarla** (skill `session-protocol`).
> Última actualización: 2026-09-24 · wiki-maintainer · cierre de M0

**Hito actual:** M1 — Planta sintética + golden set · **Demo listo el:** 17/10/2026 · **Límite duro:** 06/11/2026 (ayuda foral)

## Siguiente tarea por rol

| Rol | Siguiente tarea | Puede empezar | Notas |
|---|---|---|---|
| product | **M1-T1** Ficha de la planta ficticia + matriz de ACL | ✅ sí | Luego M1-T2 (corpus), que es la tarea más larga del hito: hay que priorizar la coherencia con el ERP |
| dev | **M1-T3** ERP mock + docker-compose (Postgres+pgvector) + `.env.example` | ⏳ tras M1-T1 | Mientras tanto se puede adelantar M2-T1 (esqueleto backend + `llm.route()`), que no depende de los datos |
| security | **M1-T6** Revisión de datos sintéticos | ⏳ tras M1-T5 | Mientras tanto: preparar los casos 1–6 de red-team en borrador (se ejecutan en M4-T4) |
| wiki | Consolidar al cierre de cada sesión | siempre | — |

## Bloqueos / decisiones pendientes del fundador
- Crear una cuenta de OpenRouter y poner `OPENROUTER_API_KEY` en `.env` (no se versiona). Hace falta a partir de M2-T6.
- Confirmar 5 contactos para las sesiones de validación de M6-T5 (vía ACAN o contactos propios), idealmente antes del 10/10.

## Progreso por hito

| Hito | Estado |
|---|---|
| M0 | ✅ done (2026-09-24) |
| M1 | ▶ en curso (0/6) |
| M2 | ☐ (0/8) |
| M3 | ☐ (0/6) |
| M4 | ☐ (0/5) |
| M5 | ☐ (0/8) |
| M6 | ☐ (0/6) |
