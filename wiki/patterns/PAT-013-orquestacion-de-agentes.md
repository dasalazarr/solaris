---
id: PAT-013
type: pattern
title: "Orquestar agentes: un agente pesado a la vez, gate repetido y commit por rutas"
status: accepted
owner_role: wiki
links: ["[[ADR-0001]]", "[[R06]]", "[[PAT-011]]"]
evidence: ["raw/sessions/2026-09-27_orquestador_cierre-sesion.md"]
updated: 2026-09-27
---

# PAT-013 — Orquestar agentes: un agente pesado a la vez, gate repetido y commit por rutas

## Patrón (aprendido en la sesión 24–27/09)
- **Límites de sesión de la API:** con 2–3 agentes en paralelo hubo 4 cortes. Conviene un agente pesado a la vez, en paralelo solo con uno ligero que no toque las mismas rutas. Los cortados se **reanudan** con su contexto, no se relanzan.
- **Separación de roles:** los agentes no editan `wiki/`, `plan/` ni `CLAUDE.md` y no hacen commit. El orquestador **repite el gate**, consolida y hace commit **solo de las rutas de la tarea** (nunca `git add -A` con agentes activos).
- **Consolidación robusta:** encadenar `script && wiki_lint && git commit`. Un anclaje de texto que no existe (p. ej. con `**`) debe abortar el commit, no dejar la wiki a medias.
- **Trabajo interrumpido:** si el fundador detiene un agente, no se reanuda ni se hace commit sin su indicación; se documenta en STATUS qué quedó sin commit y cómo retomarlo.

## Evidencia
Traza de cierre: 4 cortes por límite, 3 consolidaciones que fallaron a medias, 2 commits del fundador con trabajo en curso.

## Cómo aplicarlo
Está incorporado en `.claude/skills/session-protocol/SKILL.md` (sección "Si orquestas varios agentes").
