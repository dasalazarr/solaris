---
id: R04
type: risk
title: "Spam o abuso del formulario de solicitud de demo"
status: done
owner_role: security
links: ["[[F06]]", "[[R02]]", "[[L01]]"]
evidence: ["docs/despliegue.md", "raw/sessions/2026-11-02_orquestador_despliegue-y-correo.md"]
updated: 2026-11-02
---

# R04 — Spam del formulario de solicitud

`/api/solicitud` del producto es la única ruta pública sin sesión, por diseño: recibe el formulario de la landing y avisa por correo con Resend.

## Mitigación
Orígenes permitidos (`LANDING_ORIGINS`), validación en servidor, campo trampa (al bot se le responde «ok» sin enviar), 5 envíos por IP y hora, asunto sin saltos de línea y cuerpo en texto plano.

## Residual
CORS no autentica: un cliente fuera del navegador puede falsificar `Origin`. El límite es por instancia ([[R02]]). Si llega spam, añadir un almacén compartido para el límite o un desafío sin CAPTCHA.

## Verificado en producción (2026-11-02)
Origen ajeno 403, origen de la landing 204/400/200. El aviso llega con SPF, DKIM y DMARC en `pass`; Gmail puede enviarlo a spam hasta que se marque «No es spam» (filtro por `avisos@`). Queda el residual de CORS y del límite por instancia.
