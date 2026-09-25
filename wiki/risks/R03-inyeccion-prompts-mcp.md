---
id: R03
type: risk
title: "Inyección de prompts vía reclamaciones y abuso de herramientas MCP"
status: validating
owner_role: security
links: ["[[L01]]", "[[F05]]", "[[F08]]", "[[P04]]"]
evidence: ["raw/research/IllariumOS.md#L273", "raw/sessions/2026-09-25_security_M1-T6.md"]
updated: 2026-09-25
---

# R03 — Inyección de prompts vía reclamaciones y abuso de herramientas MCP

**Severidad:** high

## Riesgo
La reclamación es un documento externo controlado por un tercero; puede intentar que el agente consulte/exfiltre datos o salte aprobaciones.

## Mitigación
Contenido externo tratado como datos; allowlist de herramientas MCP por rol; solo lectura; HITL; caso de inyección en golden set (M1) y suite red-team (M4).

## Evolución
- 2026-09-25 (M1-T4/M1-T6): la reclamación C-OEMN-2026-0331 lleva 3 variantes de inyección (nota visible, texto blanco y metadatos del PDF), cada una con código testigo (`app/evals/redteam/injection_cases.md`). Security lo validó: sin cargas activas ni inyección accidental en el resto del corpus.
  - Pendiente para M4-T4: fixtures de inyección indirecta en el corpus, por el canal EML y de exfiltración por URL, **fuera del corpus del demo**.
- Ya mitigado en código: la identidad llega por `_meta` fuera del alcance del LLM (M3-T1), el ERP es de solo lectura por rol de BD (M3-T1) y el audit es fail-closed en el MCP (M4-T2).
