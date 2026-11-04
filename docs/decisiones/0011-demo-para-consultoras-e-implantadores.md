---
id: ADR-0011
type: decision
title: "La demo se enseña a dueños de consultoras e implantadores de CRM"
status: accepted
owner_role: product
links: ["[[ADR-0009]]", "[[ADR-0010]]", "[[F06]]", "[[O01]]"]
evidence: []
updated: 2026-11-04
---

# ADR-0011 · La demo se enseña a consultoras e implantadores de CRM

- Estado: aceptada en su audiencia (2026-11-04, decisión de Diego). Lo que implica para el piloto del despacho y para los packs queda abierto.
- Contexto: el alcance priorizaba el pack Jurídico por el piloto del despacho. Diego presentará Solaris a dueños de consultoras y de empresas de implantación de CRM, y busca procesos más generales que enseñen el potencial, no un sector concreto. Es la audiencia «consultora o socio de canal» de [[ADR-0009]], que pasa a primer plano.

## Opciones

1. **Seguir enseñando Jurídico primero.** Coherente con el PRD, pero es un nicho para esta audiencia.
2. **Enseñar Compras como proceso general, y mostrar el motor como lo que el canal implanta.** Disponible hoy.
3. **Añadir un pack comercial cercano al CRM.** Lo más cercano a su trabajo, pero es alcance nuevo.

## Decisión

Opción 2 desde ya: Compras es un proceso que todos tienen. La opción 3 es una propuesta pendiente de Diego, y no se construye sin actualizar este ADR y `plan/ROADMAP.md`, cuyo alcance está congelado.

## Consecuencias

- La frase para esta audiencia es la de `fundacional.md` §5: «Un motor, un pack por sector: usted aporta el proceso, Illarium aporta el contrato.»
- Un implantador de CRM preguntará por la integración. Hoy no hay conectores ([[ADR-0010]]). Solaris se presenta como capa sobre el ERP y las carpetas que ya existen, y las integraciones como algo que se decide con el primer aliado, no como función actual.
- **Abierto para Diego:** si Jurídico sigue siendo el primer piloto de pago. `CLAUDE.md` y los PRD aún lo dicen, y no se han cambiado.
