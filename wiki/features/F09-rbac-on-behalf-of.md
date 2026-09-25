---
id: F09
type: feature
title: "RBAC con on-behalf-of"
status: building
owner_role: security
links: ["[[P03]]", "[[P04]]", "[[L07]]"]
evidence: ["raw/research/IllariumOS.md#L207"]
updated: 2026-09-25
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
- 2026-09-25 (M4-T1): login JWT, rol en el servidor (PAT-008), `solaris_app` y ACL del ERP en BD. Riesgos residuales en R07. Falta: UI de login (M5-T2).
