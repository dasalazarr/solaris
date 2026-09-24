---
id: ADR-0001
type: decision
title: "WikiSkill como modelo del repositorio vivo"
status: accepted
owner_role: product
links: ["[[P05]]", "[[O02]]"]
evidence: ["raw/research/IllariumOS.md#L108-L147"]
updated: 2026-09-24
---

# ADR-0001 — WikiSkill como modelo del repositorio vivo

## Contexto
Varias sesiones y agentes (producto, dev, seguridad) trabajarán sobre Solaris. Sin memoria consolidada, cada sesión redescubre contexto y repite errores.

## Decisión
Adoptar el patrón de *WikiSkill* (arXiv 2608.27454) en tres capas:
- `raw/` evidencia inmutable (research, entrevistas, trazas de sesión, resultados de evals).
- `wiki/` conocimiento consolidado (problemas, features, lugares, oportunidades, hipótesis, riesgos, patrones, ADRs) + `index.md`, `logs.md`, `skill-impact.md`.
- `.claude/skills/` procedimientos ejecutables (`SKILL.md` + `PURPOSE.md`).

Reglas heredadas del paper: cambios atómicos por sesión; gate de validación antes de aceptar; la wiki persiste aunque el cambio se rechace; edición por parches, no reescrituras; el runtime del producto no lee la wiki de desarrollo.

## Consecuencias
+ Continuidad entre sesiones; aprendizajes acumulativos. − Disciplina de cierre de sesión obligatoria (skill `session-protocol`).
