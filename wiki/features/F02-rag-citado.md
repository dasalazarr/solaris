---
id: F02
type: feature
title: "RAG citado con "no encontrado""
status: building
owner_role: dev
links: ["[[P01]]", "[[L02]]", "[[L04]]"]
evidence: ["raw/research/IllariumOS.md#L183", "raw/eval-runs/2026-09-26_qa_deepseek-deepseek-chat_v2.json"]
updated: 2026-09-26
---

# F02 — RAG citado con "no encontrado"

## Qué es
Respuestas en ES/EN con cita a documento, versión y página. Si no hay evidencia, responde "no encontrado".

## Criterios de aceptación
- 100% de respuestas con ≥1 cita navegable.
- Precisión de citas ≥90% en golden set.
- p95 < 8 s.

## Hito
M2 — ver `plan/milestones/M2.md`.

## Notas / iteraciones
- 2026-09-25 (M1-T2): el corpus tiene 3 unidades de cita. Los PDF citan `page`, los DOCX 8D citan `section` (D1–D8) y los XLSX citan hoja y fila. La cita `{doc_id, version, page}` se generaliza a `{doc_id, version, locator}`.
- 2026-09-26 (M2-T6): primera medición con el LLM real (deepseek-chat). Precisión de citas 77,1 % (factual 86,5 %, multilingüe 100 % cuando responde, recurrencia 25 %), "no encontrado" 4/5, ACL 0 fugas, p95 10,8 s. **El cuello de botella es la recuperación** (no trae la D4 de los 8D; poca cobertura EN↔ES) y **la latencia depende del proveedor** que OpenRouter asigna. Coste ~0,07 $ por 50 preguntas.
