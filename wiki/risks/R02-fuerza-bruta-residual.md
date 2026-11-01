---
id: R02
type: risk
title: "Fuerza bruta sobre el código de espacio (residual)"
status: building
owner_role: security
links: ["[[F05]]", "[[L03]]"]
evidence: ["docs/prd-producto.md#L46-L47"]
updated: 2026-11-01
---

# R02 — Fuerza bruta residual
Mitigado el 01/11 con 10 intentos por IP cada 15 min (429 + `Retry-After`). Limitación: el contador es por instancia; en serverless no es global. Si se ve abuso, cambiar el almacén tras la misma interfaz (`product/lib/rate-limit.ts`).
