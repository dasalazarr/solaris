---
name: wiki-maintainer
description: Consolida la evidencia de raw/ (sesiones, entrevistas, eval-runs) en la wiki de Solaris. Crea o edita patrones, actualiza páginas, logs, index y STATUS. Úsalo al cerrar cada sesión.
---

# Wiki maintainer

## Entrada
Trazas nuevas en `raw/` desde la última entrada de `wiki/logs.md`, y el estado actual de `wiki/` y `docs/decisiones/`.

## Procedimiento
1. **Causa raíz** de lo que falló y **extracción** de lo que funcionó.
2. **Patrones** (`wiki/patterns/PAT-NNN-*.md`, según `wiki/_templates/pattern.md`): si ya existe uno parecido, edítalo por parches; crea uno nuevo solo si se reutiliza.
3. **Páginas afectadas:** cambia `status` de features, rellena "Resultado" de hipótesis con evidencia, ajusta riesgos. Actualiza siempre `updated:` y `evidence:`.
4. **Decisiones:** una decisión con consecuencias va como nota en `docs/decisiones/NNNN-*.md` con frontmatter (`ADR-NNNN`); la wiki la indexa.
5. **logs.md:** anexa `## YYYY-MM-DD · <rol> · <tarea>` con hecho, aprendido, gate y traza.
6. **plan/STATUS.md:** marca la tarea y deja la siguiente por rol y los bloqueos.
7. `python3 scripts/wiki_lint.py --write-index` debe dar OK.

## Reglas
- Nunca edites ni borres ficheros de `raw/`. `logs.md` y `skill-impact.md` son de solo anexar.
- Nada de datos reales, clientes ni prospectos con nombre en wiki ni raw.
- Una hipótesis solo pasa a `done`/`rejected` con evidencia en `raw/`.
