---
id: PAT-004
type: pattern
title: "La verdad de evaluación nunca en datos accesibles al agente"
status: accepted
owner_role: dev
links: ["[[O01]]", "[[F05]]", "[[F04]]", "[[R05]]"]
evidence: ["raw/sessions/2026-09-24_dev_M1-T3.md"]
updated: 2026-09-24
---

# PAT-004 — La verdad de evaluación nunca en datos accesibles al agente

## Patrón (fallo evitado)
Al fabricar datos sintéticos es tentador guardar la "respuesta correcta" (familia de recurrencia, causa raíz real, 8D similares) junto a los datos operativos. Si el agente puede leerla vía MCP o RAG, las evals miden lectura, no razonamiento, y el demo miente sobre [[O01]].

## Evidencia (trazas en raw/)
M1-T3: se retiró `erp.complaints.recurrence_family` antes del primer commit.

## Cómo aplicarlo / workaround
- La verdad del escenario vive solo en `app/data/synthetic/PLANT.md` (documentación de diseño, no ingerida) y en `app/evals/golden/`. **Ninguno de los dos se ingiere ni se expone por MCP.**
- M2-T3 (ingesta) debe **excluir explícitamente** `PLANT.md`, `acl.json`, `erp/` y `app/evals/` del corpus.
- Los documentos 8D del corpus pueden mencionar 8D anteriores **solo si** el equipo real lo habría hecho (p. ej. el 8D-2025-014 cita el 8D-2025-002). El agente debe encontrar la recurrencia por su cuenta al menos en un caso.
- Revisión de security (M1-T6): comprobar que ningún artefacto accesible contiene etiquetas de familia o de causa "verdad".
