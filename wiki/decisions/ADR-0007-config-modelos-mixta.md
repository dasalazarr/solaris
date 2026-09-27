---
id: ADR-0007
type: decision
title: "Configuración de modelos mixta: Gemini en región UE para el 8D, DeepSeek para la respuesta citada"
status: accepted
owner_role: product
links: ["[[ADR-0003]]", "[[F10]]", "[[H04]]", "[[R01]]", "[[PAT-009]]"]
evidence: ["raw/sessions/2026-09-27_dev_M3-T5.md", "raw/eval-runs/2026-09-27_model_compare.json"]
updated: 2026-09-27
---

# ADR-0007 — Configuración de modelos mixta

## Contexto
Con DeepSeek, el borrador 8D tardaba 110–160 s por la latencia del proveedor asignado (PAT-009). El guion pide ≤ 90 s. La comparativa M3-T5 midió 6 combinaciones (modelo, proveedor).

## Decisión (del fundador, 2026-09-27)
| Tarea | Modelo | Proveedor | Motivo |
|---|---|---|---|
| `complaint_parse`, `8d_draft`, `translate` | google/gemini-2.5-flash (fallback mistral-medium-3.1) | **solo** `google-vertex/eu` o `mistral/eu`, `zdr: true`, sin fallback al pool | 8D en ~24 s (5 veces más rápido), calidad ≥ DeepSeek (6/10 frente a 5/10), 0,014 $/8D, **datos del 8D en región UE sin retención** |
| `rag_answer` | deepseek/deepseek-chat | pool con `data_collection: deny`, `sort: throughput` | Mejor precisión de citas (93 % frente a 77 %) |

Un test (`test_eu_route_keeps_zdr_and_closed_provider_list`) impide abrir el pool o quitar ZDR en las tareas UE sin que falle la CI.

## Consecuencias
- **Argumento ante Jon (IT/OT):** el flujo principal del demo (reclamación → 8D) se procesa en región UE con ZDR. Matiz honesto: Google es una empresa de EE. UU. (CLOUD Act, R01).
- `rag_answer` sigue en un pool que puede asignar proveedores CN (observado: StreamLake). Aceptable solo con datos sintéticos; para un piloto, variante solo UE (mistral-medium-3.1 @ mistral/eu, con iteración del prompt de D4 y qa).
- Pendiente de revisión de security: puntos M3T5-S1…S5 (M3-T6).
