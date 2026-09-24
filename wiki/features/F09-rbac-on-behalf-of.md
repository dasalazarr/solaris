---
id: F09
type: feature
title: "RBAC con on-behalf-of"
status: planned
owner_role: security
links: ["[[P03]]", "[[P04]]", "[[L07]]"]
evidence: ["raw/research/IllariumOS.md#L207"]
updated: 2026-09-24
---

# F09 — RBAC con on-behalf-of

## Qué es
Roles Calidad, Planta, Auditor, Admin. El agente actúa siempre con la identidad y permisos del usuario.

## Criterios de aceptación
- Test negativo de escalado de privilegios.
- Demo: auth simple (sin Keycloak, ver ADR-0002).

## Hito
M4 — ver `plan/milestones/M4.md`.

## Notas / iteraciones
_(anexar aquí aprendizajes; las propuestas de cambio van a `wiki/skill-impact.md`)_
