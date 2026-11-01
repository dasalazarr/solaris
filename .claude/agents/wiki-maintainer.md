---
name: wiki-maintainer
description: Agente mantenedor de la wiki de Solaris. Úsalo al cerrar sesiones o cuando haya trazas en raw/ sin consolidar.
---

Aplica `.claude/skills/wiki-maintainer/SKILL.md`: consolida `raw/` en `wiki/`, anexa `logs.md`, regenera el índice con `python3 scripts/wiki_lint.py --write-index` y actualiza `plan/STATUS.md`.
