# Solaris — Log de evolución

> Log cronológico, **solo se anexa** (equivale a `logs.md` en WikiSkill). Una entrada por sesión o iteración, con la más reciente al final.
> Formato: `## YYYY-MM-DD · <rol> · <hito>/<tarea>`, seguido de lo hecho, lo aprendido (patrones creados o editados), el resultado del gate y la traza en `raw/sessions/`.

## 2026-09-24 · product · M0/brainstorm + scaffolding
- **Hecho:** brainstorm de problemas, features y oportunidades sobre `raw/research/IllariumOS.md`. Se adopta WikiSkill (ADR-0001) y se siembran 7 P, 12 F, 8 L, 5 O, 6 H, 6 R, 5 ADR y 2 PAT. Se crean las skills, los agentes y `plan/`.
- **Decisiones:**
  - Cuña del demo: 8D en automoción.
  - Stack objetivo reducido (ADR-0002).
  - OpenRouter con evaluación de calidad-precio y preferencia por DeepSeek (ADR-0003), con la tensión de soberanía explícita en R01.
  - Datos sintéticos (ADR-0004).
- **Aprendido:** PAT-001 (un demo, una cuña), PAT-002 (tensiones explícitas en ADR).
- **Calendario crítico:** la ayuda foral cierra el 06/11/2026 (O04), así que el demo debe estar listo a mediados de octubre.
- **Gate:** `wiki_lint.py` OK.
- **Traza:** `raw/sessions/2026-09-24_product_brainstorm.md`.
