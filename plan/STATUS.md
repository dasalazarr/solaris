# STATUS — tablero vivo

> Se lee al **empezar** cada sesión y se actualiza al **cerrarla** (skill `session-protocol`).
> Última actualización: 2026-09-24 · wiki-maintainer · cierre de M1-T1

**Hito actual:** M1 — Planta sintética + golden set · **Demo listo el:** 17/10/2026 · **Límite duro:** 06/11/2026 (ayuda foral)

## Siguiente tarea por rol

| Rol | Siguiente tarea | Puede empezar | Notas |
|---|---|---|---|
| product | **M1-T2** Corpus documental (15 8D, 5 AMFE, 5 PC, 8 IT, 1 escaneado, 2 plantillas) + `manifest.json` | ✅ sí | Es la tarea más larga del hito; se puede partir en sesiones (8D → AMFE/PC → IT/plantillas). Respetar `PLANT.md` §5–7 y PAT-003 |
| dev | **M1-T3** ERP mock + docker-compose (Postgres+pgvector) + `.env.example` | ✅ sí (M1-T1 done) | Códigos según `PLANT.md` §3–6; los lotes de las familias A/B deben existir. Después: M2-T1 |
| security | **M1-T6** Revisión de datos sintéticos | ⏳ tras M1-T5 | Mientras tanto: preparar los casos 1–6 de red-team en borrador (se ejecutan en M4-T4) |
| wiki | Consolidar al cierre de cada sesión | siempre | — |

## Bloqueos / decisiones pendientes del fundador
- Crear una cuenta de OpenRouter y poner `OPENROUTER_API_KEY` en `.env` (no se versiona). Hace falta a partir de M2-T6.
- Confirmar 5 contactos para las sesiones de validación de M6-T5 (vía ACAN o contactos propios), idealmente antes del 10/10.

## Progreso por hito

| Hito | Estado |
|---|---|
| M0 | ✅ done (2026-09-24) |
| M1 | ▶ en curso (1/6: T1 ✅) |
| M2 | ☐ (0/8) |
| M3 | ☐ (0/6) |
| M4 | ☐ (0/5) |
| M5 | ☐ (0/8) |
| M6 | ☐ (0/6) |
