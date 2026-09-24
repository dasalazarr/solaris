---
id: ADR-0005
type: decision
title: "Threat model inicial del demo"
status: accepted
owner_role: security
links: ["[[R03]]", "[[R01]]", "[[F05]]", "[[F08]]", "[[F09]]"]
evidence: ["raw/research/IllariumOS.md#L108-L147"]
updated: 2026-09-24
---

# ADR-0005 — Threat model inicial del demo

## Activos
Documentos de calidad (confidenciales), datos ERP, identidad del usuario, audit log, claves de API (OpenRouter).

## Amenazas principales (STRIDE resumido)
- **Tampering/Elevation:** inyección de prompts desde reclamación (L01) → el agente llama herramientas no permitidas o salta HITL.
- **Information disclosure:** RAG devuelve fragmentos de carpetas sin permiso; datos enviados a proveedor LLM no deseado.
- **Repudiation:** acciones sin trazabilidad → audit log de solo anexar.
- **Spoofing:** agente con superidentidad → on-behalf-of obligatorio.

## Controles mínimos para el demo
Allowlist MCP por rol · solo lectura ERP · HITL antes de D5/export · filtrado ACL previo a la recuperación (no post-generación) · secretos en `.env` fuera de git · audit append-only · suite red-team en `app/evals/redteam/` (M4).
