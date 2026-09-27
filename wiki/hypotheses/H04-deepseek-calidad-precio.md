---
id: H04
type: hypothesis
title: "DeepSeek (vía OpenRouter) ofrece la mejor relación calidad/precio para el 8D sin penalizar la venta"
status: validating
owner_role: product
links: ["[[F10]]", "[[R01]]"]
evidence: ["raw/research/IllariumOS.md#L156-L162"]
updated: 2026-09-27
---

# H04 — DeepSeek (vía OpenRouter) ofrece la mejor relación calidad/precio para el 8D sin penalizar la venta

## Por qué importa
Preferencia del fundador. Dos partes: (a) técnica — calidad en golden set; (b) comercial — aceptación por IT/OT de un modelo de origen chino.

## Cómo se valida
(a) Comparativa en M3 sobre golden set (≥3 modelos). (b) Preguntar explícitamente a Jon-personas en M6.

## Resultado
**Evidencia parcial (2026-09-26):**
- **Coste:** muy bajo. ~0,07 $ por 50 Q&A y 0,037 $ por 5 borradores 8D.
- **Calidad:** 93 % de citas y el caso principal del 8D correcto, pero falla en matices (distractor).
- **Latencia inaceptable para el demo en vivo según el proveedor:** StreamLake (jurisdicción CN) tarda 10–17 s por llamada y DeepInfra 50–123 s.
- La parte (b), la aceptación comercial, sigue sin validar.
- Decisión en M3-T5 (ver PAT-009, R01).

**Resultado parcial (M3-T5, 2026-09-27):** H04 **se refuta en parte**. DeepSeek es el mejor en respuesta citada (93 %), pero no en el borrador 8D: Gemini 2.5 Flash @ Vertex UE da más calidad (6/10 frente a 5/10) y es 5 veces más rápido a un coste parecido. La preferencia por DeepSeek se mantiene solo para `rag_answer` (ADR-0007).
