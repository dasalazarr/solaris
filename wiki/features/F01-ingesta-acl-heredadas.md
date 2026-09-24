---
id: F01
type: feature
title: "Ingesta con ACL heredadas"
status: building
owner_role: dev
links: ["[[P01]]", "[[P03]]", "[[L06]]"]
evidence: ["raw/research/IllariumOS.md#L182"]
updated: 2026-09-25
---

# F01 — Ingesta con ACL heredadas

## Qué es
Indexar SharePoint/SMB (demo: carpeta local con ACL simuladas) heredando permisos del origen.

## Criterios de aceptación
- Usuario sin acceso a una carpeta recibe 0 fragmentos de ella (test automatizado).
- Cambio de permisos reflejado en re-sync.

## Hito
M2 — ver `plan/milestones/M2.md`.

## Notas / iteraciones
_(anexar aquí aprendizajes; las propuestas de cambio van a `wiki/skill-impact.md`)_
