---
id: PAT-007
type: pattern
title: "Diversificar por documento en cada rama, no solo tras fusionar"
status: accepted
owner_role: dev
links: ["[[F02]]", "[[R05]]"]
evidence: ["raw/sessions/2026-09-25_dev_M2-T5.md", "raw/sessions/2026-09-25_dev_M2-T3.md"]
updated: 2026-09-25
---

# PAT-007 — Diversificar por documento en cada rama, no solo tras fusionar

## Patrón (fallo evitado)
Los documentos tipo registro (REG de cambios de boquilla: 94 de 340 chunks) son muy parecidos entre sí y a cualquier consulta sobre el equipo. Si cada rama (léxica y vectorial) devuelve sus N mejores sin límite por documento, el registro copa el pool de candidatos (77 de 77) y limitar después de la fusión deja un top-k de 2 resultados. La IT, que es la respuesta correcta, ni siquiera entra al pool.

## Evidencia (trazas en raw/)
M2-T5: la consulta "boquilla CR-01" antes y después de limitar por documento en el SQL de cada rama.

## Cómo aplicarlo / workaround
- Límite por documento **en cada rama** (SQL), otra vez en el pool del rerank y otra vez en el top-k. Todos configurables.
- Al diseñar el chunking de documentos tipo registro o log, valorar agrupar filas por periodo (mes) en lugar de chunks pequeños.
- En M2-T7, medir con el golden set el efecto de los límites y del rerank.
