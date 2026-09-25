---
id: PAT-009
type: pattern
title: "Con un agregador, la latencia es del proveedor, no del modelo"
status: accepted
owner_role: dev
links: ["[[F10]]", "[[R01]]", "[[H04]]"]
evidence: ["raw/sessions/2026-09-25_dev_M2-T6.md", "raw/eval-runs/2026-09-26_qa_deepseek-deepseek-chat_v2.json"]
updated: 2026-09-26
---

# PAT-009 — Con un agregador, la latencia es del proveedor, no del modelo

## Patrón (fallo observado)
Con OpenRouter, el mismo modelo (deepseek-chat) se sirvió desde proveedores con latencias de 1 a 20 s para respuestas de ~300 tokens. Un proveedor devolvió 429 y el tráfico pasó a otro más lento. El p95 (10,8 s) no depende del modelo, sino de la mezcla de proveedores y de su carga.

## Evidencia (trazas en raw/)
M2-T6: todas las llamadas de más de 8 s de la 1.ª pasada fueron de un mismo proveedor.

## Cómo aplicarlo / workaround
- **No arreglar la latencia fijando proveedores sin revisión de security**: el orden de proveedores cambia la jurisdicción (R01). El orquestador revirtió un `order` que priorizaba un proveedor CN.
- Medir p50/p95 **por proveedor** (OpenRouter lo devuelve) en la comparativa de M3-T5 y elegir por la tupla (modelo, proveedor), calidad, coste, latencia y jurisdicción.
- Para el demo en directo, el plan B (respuestas pregrabadas y etiquetadas, M6-T2) cubre el riesgo de un proveedor lento.
