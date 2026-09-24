---
name: wiki-maintainer
description: Consolida la evidencia de raw/ (trazas de sesión, entrevistas, eval-runs) en la wiki de Solaris. Crea o edita patrones, actualiza páginas afectadas, logs, index y STATUS. Úsalo al cerrar cada sesión o cuando se acumulen trazas sin consolidar.
---

# Wiki maintainer

Equivale al *Wiki Maintainer* de WikiSkill: analiza trazas y las destila en conocimiento reutilizable.

## Entrada
- Trazas nuevas en `raw/sessions/`, `raw/interviews/` y `raw/eval-runs/` desde la última entrada de `wiki/logs.md`.
- Estado actual de `wiki/`.

## Procedimiento
1. **Análisis de causa raíz** de lo que falló (tests rojos, evals bajo umbral, objeciones de clientes) y **extracción de lo que funcionó**.
2. **Patrones** (`wiki/patterns/PAT-NNN-*.md`, según `wiki/_templates/pattern.md`):
   - Si ya existe un patrón parecido, **edítalo por parches** añadiendo evidencia o un workaround. No lo dupliques.
   - Crea uno nuevo solo si el aprendizaje se reutiliza en otra sesión o rol.
3. **Páginas afectadas:**
   - Cambia el `status` de las features (planned → building → done).
   - Rellena la sección "Resultado" de las hipótesis con evidencia.
   - Sube o baja la severidad de los riesgos.
   - Actualiza siempre `updated:` y `evidence:`.
4. **logs.md:** anexa `## YYYY-MM-DD · <rol> · Mx-Ty` con hecho, aprendido, gate y traza.
5. **STATUS:** marca la tarea y escribe la **siguiente tarea de cada rol** y los bloqueos.
6. `python3 scripts/wiki_lint.py --write-index`, que debe dar OK.

## Reglas
- Nunca edites ni borres ficheros de `raw/`.
- Nunca reescribas una página entera: edita por parches y conserva la historia.
- `logs.md` y `skill-impact.md` son de solo anexar.
- Una hipótesis solo pasa a `done`/`rejected` con evidencia en `raw/`.
