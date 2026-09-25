# STATUS — tablero vivo

> Se lee al **empezar** cada sesión y se actualiza al **cerrarla** (skill `session-protocol`).
> Última actualización: 2026-09-25 · wiki-maintainer · cierre de M4-T1

**Hito actual:** M2 — Ingesta + RAG citado (M1 ✅ cerrado, con el menor M1-T8 pendiente) · **Demo listo el:** 17/10/2026 · **Límite duro:** 06/11/2026 (ayuda foral)

## Siguiente tarea por rol

| Rol | Siguiente tarea | Puede empezar | Notas |
|---|---|---|---|
| product | **M1-T8** menores de M1-T6 (teléfonos, metadato, check de metadatos) · después **M6-T4** protocolo de validación | ✅ sí | M5-T1 ✅ hecho. Decidido (ADR-0006): promesa de ROI + F12 en alcance |
| dev | **M2-T6** Respuesta citada `POST /ask` (necesita la clave de OpenRouter) · alternativa sin clave: **M2-T4** exactitud AMFE o **M2-T7** runner de evals (parte sin LLM: recuperación, ACL, latencia) | M2-T6 ⏳ bloqueada por la clave · M2-T4/T7 ✅ | Con la clave: M2-T6 → M2-T7 completo |
| security | **M2-T8** Revisión de M2 (incluye segunda lectura de M4-T1: `solaris/auth/` y migraciones 006/007) → después **M4-T3/M4-T5** | ✅ sí (sin necesidad de M2-T7 para la parte de código) | Puntos acumulados en el DoD de M2-T8 y en las trazas de M2-T3, M2-T5 y M4-T1 |
| wiki | Consolidar al cierre de cada sesión | siempre | — |

## Bloqueos / decisiones pendientes del fundador
- Crear una cuenta de OpenRouter y poner `OPENROUTER_API_KEY` en `.env` (no se versiona). Hace falta a partir de M2-T6.
- Confirmar 5 contactos para las sesiones de validación de M6-T5 (vía ACAN o contactos propios), idealmente antes del 10/10.

## Progreso por hito

| Hito | Estado |
|---|---|
| M0 | ✅ done (2026-09-24) |
| M1 | ✅ cerrado (T1–T7; queda el menor T8 cosmético) |
| M2 | ▶ en curso (4/8: T1–T3 ✅ T5 ✅) |
| M3 | ▶ adelantado (1/6: T1 ✅) |
| M4 | ▶ adelantado (2/5: T1 ✅ T2 ✅) |
| M5 | ▶ adelantado (1/8: T1 ✅) |
| M6 | ☐ (0/6) |
