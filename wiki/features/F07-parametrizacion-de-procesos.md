---
id: F07
type: feature
title: "Parametrización de procesos"
status: building
owner_role: product
links: ["[[P01]]", "[[L01]]", "[[H03]]", "[[ADR-0015]]"]
evidence: ["docs/plan-evolutivo.md"]
updated: 2026-11-07
---

# F07 — Parametrización de procesos

## Qué es
Un proceso se define como datos: contrato, tipos de objeto y documento, roles, reglas y acciones. Se edita en la superficie «Contrato», sin programar.

## Criterios de aceptación
- Compras migrado a plantilla da los mismos resultados.
- Alguien sin programar crea un proceso nuevo en menos de 2 horas.
- `policy_hash` real, con la versión conservada en cada decisión.

## Hito
Fase 3 de [`plan-evolutivo.md`](../../docs/plan-evolutivo.md).

## Notas / iteraciones
Sustituye la exclusión del PRD §8.1 sobre editor de reglas y relaciones.

2026-11-07: edición y publicación construidas ([[ADR-0017]]). Crear un proceso desde cero, pendiente: el criterio de las 2 horas sigue sin medir.
