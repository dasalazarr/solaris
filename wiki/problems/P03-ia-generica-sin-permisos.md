---
id: P03
type: problem
title: "La IA genérica no respeta permisos ni OT"
status: validating
owner_role: product
links: ["[[F01]]", "[[F09]]", "[[F05]]", "[[L06]]", "[[L05]]"]
evidence: ["raw/research/IllariumOS.md#L154", "raw/research/IllariumOS.md#L61"]
updated: 2026-09-24
---

# P03 — La IA genérica no respeta permisos ni OT

## Problema
Copilot/ChatGPT no heredan ACL de forma fiable sobre carpetas caóticas, no llegan a ERP local ni a OT y no generan entregables con formato del sistema de calidad.

## Consecuencia
La IA se queda en la oficina; Calidad copia y pega a mano. Saneamiento de permisos: 20–80 h (Summum IA).
