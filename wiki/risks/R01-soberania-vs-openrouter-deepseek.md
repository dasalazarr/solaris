---
id: R01
type: risk
title: "Soberanía vs OpenRouter + DeepSeek"
status: validating
owner_role: security
links: ["[[F10]]", "[[H04]]", "[[P04]]"]
evidence: ["raw/research/IllariumOS.md#L131", "wiki/decisions/ADR-0003-openrouter-politica-modelos.md"]
updated: 2026-09-24
---

# R01 — Soberanía vs OpenRouter + DeepSeek

**Severidad:** high

## Riesgo
El pitch es "datos e inferencia en la UE". OpenRouter es un intermediario (EE. UU.) y DeepSeek es de origen chino; el documento advierte del recelo de TI corporativa alemana.

## Mitigación
ADR-0003: demo solo con datos sintéticos; política de proveedores con ZDR y sin entrenamiento; ficha de modelo visible; ruta UE-only (Mistral/Azure UE/vLLM local) conmutable por config antes de cualquier piloto con datos reales.
