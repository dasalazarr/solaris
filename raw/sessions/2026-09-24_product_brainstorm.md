# Traza de sesión — 2026-09-24 · product · M0 brainstorm + scaffolding

**Entrada:** `raw/research/IllariumOS.md` (+ PDF), paper WikiSkill (arXiv 2608.27454), petición del fundador de hacer un brainstorm y tener un repo vivo y un plan para agentes hasta un demo validable.

## Preguntas y respuestas del fundador
- ¿Qué relación hay entre Solaris e Illarium? → **Solaris es el nombre en clave interno** de Illarium.
- ¿Cuál es la cuña del demo? → **8D en automoción** (persona Iñaki, Tier 2).
- ¿Qué fidelidad técnica? → **stack objetivo reducido** (LangGraph + pgvector + MCP + Next.js, docker-compose).
- ¿Qué LLM? → **orquestación con OpenRouter**. Los modelos se evalúan por calidad-precio, sin excluir ninguno y **con preferencia por DeepSeek**.

## Razonamiento clave
- El "OS" es arquitectura, no mensaje (PRD §3.6 riesgo 1), así que el demo tiene un solo flujo: reclamación → D1–D4 con citas, ERP trazado y HITL.
- El riesgo más arriesgado es que Calidad confíe en el borrador (H01).
- La tensión soberanía vs OpenRouter/DeepSeek se documenta, no se oculta (R01, ADR-0003, PAT-002).
- Oportunidad nueva: aplicar WikiSkill **dentro** del producto (O02). Cada 8D aprobado alimenta patrones por planta y skills por OEM.
- El plazo de la ayuda foral (06/11/2026) obliga a tener el demo a mediados de octubre.

## Ideas aparcadas
Pasarela OPC UA (L08), Keycloak/OpenFGA, GraphRAG, vertical agro IFS, euskera/ALIA, autonomía L3.

## Resultado
Scaffolding M0 creado; gate `wiki_lint.py` OK; skill-impact #0 Accepted.
