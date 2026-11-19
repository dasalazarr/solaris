---
id: PAT-004
type: pattern
title: "Un peer opcional sin usar puede romper `npm ci`"
status: accepted
owner_role: dev
links: ["[[L01]]"]
evidence: ["raw/sessions/2026-11-01_orquestador_workspace-y-pendientes.md"]
updated: 2026-11-01
---

# PAT-004 — Peer opcional sin usar
## Patrón (fallo)
`@hookform/resolvers` declara `ajv@8` como peer opcional y chocaba con `ajv@6`: `npm ci` fallaba con el lockfile recién creado.
## Cómo aplicarlo
Antes de pelear con el lockfile, comprobar con `grep` qué dependencias se importan. Quitar las que no se usan (aquí 5, de 1115 a 573 paquetes).
