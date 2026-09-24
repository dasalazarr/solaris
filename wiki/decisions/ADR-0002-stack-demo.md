---
id: ADR-0002
type: decision
title: "Stack del demo: objetivo reducido"
status: accepted
owner_role: product
links: ["[[F01]]", "[[F02]]", "[[F04]]", "[[F05]]", "[[F09]]"]
evidence: ["raw/research/IllariumOS.md#L108-L147"]
updated: 2026-09-24
---

# ADR-0002 — Stack del demo: objetivo reducido

## Decisión
Python 3.12 + FastAPI + **LangGraph** (estado e interrupts) + **PostgreSQL/pgvector** (vectores, metadatos, ACL, audit) + servidores **MCP** (erp-mock, docs) + **Next.js** para la UI. Todo en `docker-compose`.

Diferido del PRD: Keycloak/OpenFGA (→ auth simple con roles), Langfuse (opcional, trazas en BD), vLLM local, pasarela OPC UA, GraphRAG.

## Por qué
Real y extensible al stack objetivo sin triplicar el tiempo al demo (deadline O04).
