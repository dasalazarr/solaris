---
id: PAT-010
type: pattern
title: "Una regla de prompt por iteración, medida aislada"
status: accepted
owner_role: dev
links: ["[[F02]]", "[[ADR-0001]]"]
evidence: ["raw/sessions/2026-09-26_dev_M2-T7.md", "raw/eval-runs/2026-09-26_qa_deepseek-deepseek-chat_m2t7-1.json", "raw/eval-runs/2026-09-26_qa_deepseek-deepseek-chat_m2t7-2.json"]
updated: 2026-09-26
---

# PAT-010 — Una regla de prompt por iteración, medida aislada

## Patrón (fallo observado)
El prompt v4 añadió a la vez un check de "dato literal" (arregló "no encontrado" 5/5) y una regla de "responder parcial o negativo" (hundió la precisión del 93 % al 79 %). Al cambiar dos cosas en la misma pasada, se pierde la pasada y se tarda más en atribuir el efecto. Es la regla de cambio atómico de WikiSkill aplicada a los prompts.

## Evidencia (trazas en raw/)
M2-T7, pasadas 1 y 2.

## Cómo aplicarlo / workaround
- Cada versión de prompt cambia **una** regla. Se compara con la versión anterior en el mismo golden set.
- Los checks deterministas en servidor (p. ej. "¿aparece literalmente el dato pedido?") se prefieren a pedirle al modelo que se autoverifique: el modelo confundió "par de apriete" con "par de arrancamiento".
- Las pasadas con LLM son un recurso escaso (coste y límites): primero la suite `retrieval` sin LLM.
