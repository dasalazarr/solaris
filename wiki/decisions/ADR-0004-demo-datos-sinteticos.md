---
id: ADR-0004
type: decision
title: "Demo con planta y OEM ficticios"
status: accepted
owner_role: product
links: ["[[F04]]", "[[P06]]", "[[R03]]"]
evidence: ["raw/research/IllariumOS.md#L108-L147"]
updated: 2026-09-24
---

# ADR-0004 — Demo con planta y OEM ficticios

## Decisión
El demo usa una planta ficticia ("Componentes Arga S.L.", Tier 2, Orkoien) y un OEM ficticio ("OEM Norte"). **Sin marcas, logos ni plantillas reales** de VW u otros.

El dataset incluye deliberadamente: recurrencia entre 8D (O01), un AMFE "sucio" (P06), un PDF escaneado y una reclamación con inyección de prompts (R03).

## Por qué
Evita riesgos legales/de confidencialidad, permite usar OpenRouter/DeepSeek sin exponer datos reales y hace el demo reproducible.
