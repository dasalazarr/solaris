---
id: ADR-0003
type: decision
title: "OpenRouter como orquestador de modelos y política de proveedores"
status: accepted
owner_role: product
links: ["[[F10]]", "[[H04]]", "[[R01]]"]
evidence: ["raw/research/IllariumOS.md#L108-L147"]
updated: 2026-09-24
---

# ADR-0003 — OpenRouter como orquestador de modelos y política de proveedores

## Decisión
- Todas las llamadas LLM pasan por una interfaz propia `llm.route(task, ...)` que usa **OpenRouter**.
- Selección por **calidad-precio** medida en el golden set; ningún proveedor excluido a priori; preferencia inicial por **DeepSeek** a validar (H04).
- Cada agente tiene una **ficha de modelo** (modelo, proveedor, región, procedencia, coste/1k tokens, score en golden set).
- Política OpenRouter: proveedores sin retención/entrenamiento (ZDR) cuando exista.
- **Demo = solo datos sintéticos.** Antes de un piloto con datos reales: ruta UE-only conmutable por config y revisión del agente de seguridad.

## Consecuencias
+ Flexibilidad y coste bajo. − Tensión con el pitch de soberanía (R01): hay que explicitarla, no esconderla.
