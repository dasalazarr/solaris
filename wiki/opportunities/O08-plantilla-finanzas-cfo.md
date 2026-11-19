---
id: O08
type: opportunity
title: "Plantilla Finanzas: Solaris para Dirección Financiera"
status: validating
owner_role: product
links: ["[[ADR-0017]]", "[[ADR-0026]]", "[[F07]]", "[[O01]]", "[[O06]]"]
evidence: ["raw/research/2026-11-12_evaluacion-cruzada-andes.md", "raw/research/2026-11-19_cfo-pyme-procesos-ecuador.md"]
updated: 2026-11-19
---

# O08 — Plantilla Finanzas

## Oportunidad
Un «agente CFO» no es un producto aparte: es una plantilla más. Compras ya tiene a Dirección financiera como responsable. Procesos candidatos: pedido contra contrato y factura, política de gasto, vencimientos de contratos y avales, lista de cierre mensual.

Sin confirmar: demanda y disposición a pagar. Sería la sexta plantilla sin cliente.

## Condiciones para reabrir
- Una conversación comercial la pide con un proceso concreto y sus documentos.
- El piloto de [[O01]] no se retrasa por ello.

## Reabierta (18/11, [[ADR-0026]])
Se cumplió la primera condición: una propuesta de canal pide el cierre mensual de PYMES en Ecuador. Plantilla `cfo` con datos ficticios en la rama `feat/motor-linear-cfo` y puerta de decisión el 09/12.

## Auditoría del 19/11
`raw/research/2026-11-19_cfo-pyme-procesos-ecuador.md`: mapa de obligaciones mensuales (104, 103, ATS, IESS, noveno dígito), bancarización de más de 500 $ y once hallazgos sobre las cuatro reglas. Los dos más graves: R-MAR-03 cuenta préstamos y aportes como ingreso (falso conforme), y falta la regla de bancarización, la única que se traduce en dólares de impuesto.

## Siguiente paso
Diego elige qué correcciones de la sección D entran antes del 09/12. La socia lleva al contador las preguntas de la sección E.
