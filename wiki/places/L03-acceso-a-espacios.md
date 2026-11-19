---
id: L03
type: place
title: "Acceso a espacios (código, sesión y límite)"
status: done
owner_role: security
links: ["[[F05]]", "[[R01]]", "[[R02]]"]
evidence: ["docs/decisiones/0003-acceso-espacios.md"]
updated: 2026-11-01
---

# L03 — Acceso a espacios
`product/lib/space-auth.ts` (hash SHA-256 del código, sesión HMAC), `product/lib/space-session.ts` (cookie) y `product/lib/rate-limit.ts` (10 intentos por IP cada 15 min). Los espacios viven en `SOLARIS_SPACES`, nunca en el código.
