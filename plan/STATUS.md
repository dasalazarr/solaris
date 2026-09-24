# STATUS — tablero vivo

> Se lee al **empezar** cada sesión y se actualiza al **cerrarla** (skill `session-protocol`).
> Última actualización: 2026-09-25 · wiki-maintainer · cierre de M1-T2

**Hito actual:** M1 — Planta sintética + golden set · **Demo listo el:** 17/10/2026 · **Límite duro:** 06/11/2026 (ayuda foral)

## Siguiente tarea por rol

| Rol | Siguiente tarea | Puede empezar | Notas |
|---|---|---|---|
| product | **M1-T4** 5 reclamaciones del OEM ficticio (PDF/EML), la #5 con inyección de prompts | ✅ sí | IDs, lotes y fechas en PLANT.md §11. Hay pistas que dejó M1-T2: el lote de tuercas de agosto de 2026 sin medir y las noches sin cambio de boquilla en ago–sep 2026 |
| dev | **M2-T3** Ingesta (Docling + OCR, manifest con ACL, chunking por sección/hoja/página, embeddings 1024-d) | ✅ sí (corpus listo) | Solo las rutas del manifest (exclusiones en el DoD). Coordinar con M4-T2 (security en curso) en `app/backend` |
| security | **M1-T6** Revisión de datos sintéticos | ⏳ tras M1-T5 | Mientras tanto: preparar los casos 1–6 de red-team en borrador (se ejecutan en M4-T4) |
| wiki | Consolidar al cierre de cada sesión | siempre | — |

## Bloqueos / decisiones pendientes del fundador
- Crear una cuenta de OpenRouter y poner `OPENROUTER_API_KEY` en `.env` (no se versiona). Hace falta a partir de M2-T6.
- Confirmar 5 contactos para las sesiones de validación de M6-T5 (vía ACAN o contactos propios), idealmente antes del 10/10.

## Progreso por hito

| Hito | Estado |
|---|---|
| M0 | ✅ done (2026-09-24) |
| M1 | ▶ en curso (3/6: T1 ✅ T2 ✅ T3 ✅) |
| M2 | ▶ en curso (2/8: T1 ✅ T2 ✅) |
| M3 | ▶ adelantado (1/6: T1 ✅) |
| M4 | ☐ (0/5) |
| M5 | ☐ (0/8) |
| M6 | ☐ (0/6) |
