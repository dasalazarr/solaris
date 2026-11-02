---
id: O04
type: opportunity
title: "Runtime de agentes dedicado (OpenBot u otro)"
status: parked
owner_role: product
links: ["[[ADR-0007]]", "[[ADR-0005]]"]
evidence: ["raw/research/2026-11-02_openbot-evaluacion.md"]
updated: 2026-11-02
---

# O04 — Runtime de agentes dedicado

## Oportunidad
Agentes persistentes con colas y mensajería entre ellos, en lugar de sesiones de Claude Code coordinadas por el repo.

## Condiciones para reabrir
- La coordinación por repo falla de forma repetida (traza en `raw/sessions/`).
- Licencia comercial presupuestada y permisos por acción configurables (principio 3).
- El estado de los agentes se puede volcar a git.

## Siguiente paso
Ninguno.
