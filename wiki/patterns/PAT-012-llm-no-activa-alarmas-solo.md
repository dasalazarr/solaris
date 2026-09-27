---
id: PAT-012
type: pattern
title: "Un LLM no activa una alarma de seguridad sin corroboración determinista"
status: accepted
owner_role: security
links: ["[[R03]]", "[[PAT-010]]", "[[PAT-011]]", "[[H01]]"]
evidence: ["raw/sessions/2026-09-27_dev_M3-T8.md", "raw/eval-runs/2026-09-27_complaint_replay_m3t8.json"]
updated: 2026-09-27
---

# PAT-012 — Un LLM no activa una alarma de seguridad sin corroboración determinista

## Patrón (fallo observado)
El parser dejaba que el LLM activara el aviso rojo de inyección si "creía" haber ignorado una instrucción. El LLM no es determinista (ni con temperature 0) y confundía requisitos normales del cliente con instrucciones, así que el **caso limpio del demo salía marcado de forma intermitente** (25 falsos positivos en 90 re-ejecuciones). En un demo ante Calidad, una alarma falsa destruye la confianza que busca H01.

## Evidencia (trazas en raw/)
M3-T8: el diagnóstico con arnés de replay y 4 llamadas reales reprodujo el problema. Con la regla nueva, 0 FP en 90 y la #5 sigue en 3/3.

## Cómo aplicarlo
- Las **alarmas visibles** (rojo, bloqueo) las activan solo reglas deterministas, o el LLM **y** una regla a la vez.
- La señal del LLM sin corroboración se degrada a "nota de revisión" y se registra en el audit, sin perderse.
- Aplicable a otras señales: "misma causa" en D4 (M3-T7, mismo espíritu), y a futuras alertas de calidad.
