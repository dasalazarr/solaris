---
id: R03
type: risk
title: "Inyección de prompts vía reclamaciones y abuso de herramientas MCP"
status: validating
owner_role: security
links: ["[[L01]]", "[[F05]]", "[[F08]]", "[[P04]]"]
evidence: ["raw/research/IllariumOS.md#L273"]
updated: 2026-09-24
---

# R03 — Inyección de prompts vía reclamaciones y abuso de herramientas MCP

**Severidad:** high

## Riesgo
La reclamación es un documento externo controlado por un tercero; puede intentar que el agente consulte/exfiltre datos o salte aprobaciones.

## Mitigación
Contenido externo tratado como datos; allowlist de herramientas MCP por rol; solo lectura; HITL; caso de inyección en golden set (M1) y suite red-team (M4).
