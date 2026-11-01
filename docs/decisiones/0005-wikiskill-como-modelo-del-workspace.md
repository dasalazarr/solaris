---
id: ADR-0005
type: decision
title: "WikiSkill como modelo del espacio de trabajo"
status: accepted
owner_role: product
links: ["[[L04]]", "[[R03]]", "[[PAT-001]]"]
evidence: ["docs/decisiones/0001-estructura-submodulos.md"]
updated: 2026-11-01
---

# 0005 · WikiSkill como modelo del espacio de trabajo

- Fecha: 2026-11-01
- Estado: aceptada

## Contexto
Hay varias sesiones y agentes sobre producto y landing, y el 01/11 se perdió contexto entre nube y local ([[R03]]). El demo 8D ya usaba el patrón WikiSkill (arXiv 2608.27454) con buenos resultados de continuidad.

## Opciones
1. Seguir solo con `docs/` y `estado.md`.
2. Adoptar WikiSkill en la raíz y que cubra a `product/` y `landing/`.

## Decisión
Opción 2, en cuatro capas: `raw/` (evidencia, solo se añade), `wiki/` (conocimiento, por parches; `logs.md` y `skill-impact.md` solo se anexan), `.claude/skills/` (procedimientos con `PURPOSE.md`) y `plan/` (tablero vivo). Las decisiones siguen en `docs/decisiones/` y la wiki las indexa. `scripts/wiki_lint.py` valida enlaces y evidencia.

## Consecuencias
- Continuidad entre sesiones y entre nube y local; los aprendizajes (`PAT-*`) se acumulan.
- Coste: disciplina de cierre (skill `session-protocol`).
- La wiki es memoria de desarrollo: el runtime del producto no la lee.
