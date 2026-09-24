---
id: PAT-003
type: pattern
title: "Comprobar los nombres ficticios contra marcas reales del sector"
status: accepted
owner_role: product
links: ["[[ADR-0004]]", "[[R03]]"]
evidence: ["raw/sessions/2026-09-24_product_M1-T1.md"]
updated: 2026-09-24
---

# PAT-003 — Comprobar los nombres ficticios contra marcas reales del sector

## Patrón (fallo evitado)
Los nombres geográficos navarros o vascos (ríos, valles, comarcas) son buena materia prima para empresas ficticias, pero algunos ya son **marcas reales** del sector (p. ej. "Ebro" es una marca de vehículos). Usarlos incumple [[ADR-0004]] y puede parecer suplantación en un demo comercial.

## Evidencia (trazas en raw/)
M1-T1: "Ebro Chassis Systems" se renombró a "Ribera Chassis Systems".

## Cómo aplicarlo / workaround
- Antes de fijar un nombre de empresa, cliente, proveedor o producto ficticio: comprobar que no es una marca conocida de automoción, industria o alimentación. Preferir combinaciones como topónimo + sector genérico.
- Aplicar en M1-T2 (cabeceras de documentos), M1-T4 (reclamaciones) y en la plantilla del OEM ficticio.
- Seguridad lo verifica en M1-T6.
