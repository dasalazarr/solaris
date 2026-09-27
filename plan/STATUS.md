# STATUS — tablero vivo

> Se lee al **empezar** cada sesión y se actualiza al **cerrarla** (skill `session-protocol`).
> Última actualización: 2026-09-27 · orquestador · **cierre de la sesión de trabajo 24–27/09** (traza: `raw/sessions/2026-09-27_orquestador_cierre-sesion.md`)

**Hito actual:** M5 — UI del demo. M1 ✅ y M3 ✅ cerrados; el flujo 8D del backend está completo y aprobado por security. M2 tiene el gate de calidad abierto (→ M2-T10).
**Demo listo el:** 17/10/2026 · **Límite duro:** 06/11/2026 (ayuda foral, O04)

## ⚠️ Trabajo sin commit al cerrar (léelo antes de empezar)

**M5-T3 (inbox) quedó a medias:** el fundador detuvo el agente mientras actualizaba los tests del BFF. Los cambios están **en el árbol de trabajo, sin commit y sin validar**:

- **Backend:** `solaris/agents/complaint.py`, `agents/eight_d/api.py` y `store.py` (endpoint de listado y ajustes) + los tests `test_access_matrix`, `test_complaint`, `test_eightd_hitl` y `test_eightd_store`.
- **Frontend:** `(app)/inbox/page.tsx`, `components/inbox/`, `lib/inbox.ts`, `lib/case-watch.ts`, `(app)/casos/[id]/`, `api/backend/[...path]/route.ts`, `lib/bff.ts`, `lib/api-client.ts`, `globals.css`, `vitest.config.mts`, `public/` y los tests `bff.test.ts` y `api-client.test.ts`.

**Quien retome M5-T3:**
1. `git status` y `git diff` para revisar lo hecho.
2. Termina los tests del BFF.
3. Pasa el gate completo: backend `pytest` + `ruff`; frontend `pnpm lint`, `typecheck`, `test` y `build`.
4. Haz la prueba en el navegador descrita en `plan/milestones/M5.md`.
5. **Commit con el mensaje `M5-T3: …`.**

Si prefieres empezar de cero: `git stash` (no `git checkout .`, para no perderlo).

## Siguiente tarea por rol

| Rol | Siguiente tarea | Puede empezar | Notas |
|---|---|---|---|
| dev | **M5-T3** terminar el inbox (ver arriba) → **M5-T4** workspace 8D → M5-T5/T6 (aprobaciones y auditoría, export DOCX) → M5-T7 (panel F12, en alcance por ADR-0006) | ✅ sí | Backend en 127.0.0.1:8011, frontend en localhost:3000 (`.claude/launch.json`). Requisitos de UI en `plan/demo-script.md` §Requisitos |
| product | **M1-T9** verdad de `qty_not_shipped` + bloque `recommended` del caso 0088 · **M2-T11** revisar QA-012/015 · después **M6-T4** protocolo de validación | ✅ sí | Tareas cortas que desbloquean gates |
| security | **M4-T4** suite red-team completa (6 casos + fixtures fuera del corpus + paráfrasis de PAT-012 + M-1) · **M2-T12** revisión de traducción y prompts v3/v4 · **M4-T5** pack de cumplimiento (parcial: 3/7 documentos en `docs-compliance/`, commit `ededb35`) | ✅ sí | M3 ✅ APPROVE con condiciones; M-2/M-3 bloquean piloto, no demo |
| dev (cuando haya hueco) | **M2-T10** prompt v5 (cierra el gate de M2) · mejora de latencia del 8D (rama paralela `qproc`/`fmea_rows`, −4–7 s) · M2-T4, M2-T9 | ✅ sí | Una regla por iteración (PAT-010); medir primero con replay (PAT-011) |
| wiki | Consolidar al cierre de cada sesión | siempre | — |

## Bloqueos y decisiones pendientes del fundador
- **Contactos para validación:** confirmar 5 responsables de calidad (y 1–2 de IT/OT) para M6-T5, idealmente antes del 10/10.
- **Coordinación de commits:** en esta sesión hubo commits "first commit" con trabajo en curso de agentes (`ededb35`, `5bdc685`). Recomendación: hacer push solo de los commits `Mx-Ty` ya cerrados y no hacer commit del árbol de trabajo mientras un agente trabaja.
- **Antes de cualquier piloto con datos reales** (no bloquea el demo): R07 (auth de demo, M-2 retención/RGPD, M-3 jurisdicción de Vertex UE y pool de `rag_answer`) y el ancla externa del audit.

## Estado técnico en una línea
Parser (100 % campos, inyección 3/3 sin FP) → 8D D1–D4 (5/5 casos, ~27 s, Gemini 2.5 Flash en Vertex UE con ZDR) → HITL ligado a versión → export bloqueado sin aprobación · RAG citado 93 % (DeepSeek) · 366 tests backend, 38 MCP, 68 evals, 27 frontend · coste LLM acumulado de desarrollo ≈ 2 $.

## Progreso por hito

| Hito | Estado |
|---|---|
| M0 | ✅ done (2026-09-24) |
| M1 | ✅ cerrado (T1–T7; pendientes menores T8 cosmético y T9 verdad `qty_not_shipped`) |
| M2 | ▶ en curso (7/12: T1–T3, T5–T8 ✅; gate de calidad abierto → T10; T4, T9, T11, T12 pendientes) |
| M3 | ✅ cerrado (T1–T8; APPROVE con condiciones) |
| M4 | ▶ adelantado (2/5: T1 ✅ T2 ✅; T5 parcial) |
| M5 | ▶ en curso (2/8: T1, T2 ✅; **T3 a medias sin commit**) |
| M6 | ☐ (0/6) |
