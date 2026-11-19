---
id: PAT-002
type: pattern
title: "`next build` rompe un `next dev` en la misma carpeta"
status: accepted
owner_role: dev
links: ["[[L01]]", "[[L02]]"]
evidence: ["raw/sessions/2026-11-01_orquestador_workspace-y-pendientes.md"]
updated: 2026-11-01
---

# PAT-002 — `next build` rompe `next dev`
## Patrón (fallo)
Ejecutar `next build` mientras `next dev` corre sobre la misma carpeta pisa `.next` y el servidor devuelve 500.
## Cómo aplicarlo
Parar el servidor, borrar `.next` y reiniciarlo después del build. Para mediciones, servir `out/` aparte.
