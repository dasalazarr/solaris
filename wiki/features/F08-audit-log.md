---
id: F08
type: feature
title: "Audit log de solo anexar"
status: building
owner_role: security
links: ["[[P04]]", "[[L07]]", "[[R03]]"]
evidence: ["raw/research/IllariumOS.md#L209", "raw/sessions/2026-09-25_security_M4-T2.md"]
updated: 2026-09-25
---

# F08 — Audit log de solo anexar

## Qué es
Registro inmutable de prompts, fuentes recuperadas, herramientas invocadas y aprobaciones.

## Criterios de aceptación
- Solo anexar (sin UPDATE/DELETE a nivel de BD).
- Export CSV.

## Hito
M4 — ver `plan/milestones/M4.md`.

## Notas / iteraciones
- 2026-09-25 (M4-T2): solo anexar garantizado en BD (roles + trigger + cadena de hash).
  - Queda para M4-T1: auth en `/audit`.
  - **Riesgo residual:** un superusuario puede reescribir la cadena entera o truncar el final sin que `verify_chain` lo detecte. Hace falta un **ancla externa** (hash de la cabeza publicado o guardado fuera de la BD) antes de cualquier piloto. Añadido a M6-T3 (one-pager de seguridad).
  - Patrón fail-closed en el MCP: si el audit no escribe, no hay datos.
