---
id: PAT-011
type: pattern
title: "Medir las reglas del agente con un arnés de replay sin LLM"
status: accepted
owner_role: dev
links: ["[[PAT-010]]", "[[F04]]", "[[ADR-0001]]"]
evidence: ["raw/sessions/2026-09-27_dev_M3-T7.md", "raw/eval-runs/2026-09-27_8d_m3t7_replay.json"]
updated: 2026-09-27
---

# PAT-011 — Medir las reglas del agente con un arnés de replay sin LLM

## Patrón (éxito)
Las respuestas del LLM de todas las pasadas anteriores (M3-T3 y M3-T5: 9 pasadas, 45 casos, 3 modelos) se guardan en `raw/eval-runs/`. Un arnés (`app/evals/eightd_replay.py`) re-puntúa el grafo sustituyendo la llamada al LLM por la respuesta grabada. Así, cada regla determinista nueva se mide **gratis, en segundos y sobre varios modelos a la vez**, y solo la versión final se valida con una pasada real.

## Evidencia (trazas en raw/)
M3-T7: 3 reglas medidas de una en una (24 → 27 → 32 → 36/45). Luego, 1 pasada real 5/5.

## Cómo aplicarlo
- Guardar siempre las respuestas brutas del LLM en los JSON de eval (ya lo hace el runner).
- Toda regla de post-proceso (guardas, validaciones, reclasificaciones) se mide primero en replay.
- Es el equivalente práctico del ciclo de WikiSkill (trazas raw → regla → validación) a coste casi cero.
