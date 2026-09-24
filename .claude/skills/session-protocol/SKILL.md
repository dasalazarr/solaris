---
name: session-protocol
description: Protocolo de arranque y cierre de cualquier sesión de agente en Solaris (bucle WikiSkill). Úsalo al empezar y al terminar cada sesión de trabajo, sea cual sea el rol.
---

# Protocolo de sesión (bucle WikiSkill)

## Arranque (≤5 min de contexto)
1. `cat plan/STATUS.md`: identifica el hito actual y **la siguiente tarea de tu rol**.
2. `cat wiki/index.md`, y después abre solo las páginas enlazadas a esa tarea en `plan/milestones/Mx.md`.
3. Si la tarea depende de otra que no está `done`, no la empieces. Elige la siguiente de tu rol o anota el bloqueo en STATUS.
4. Revisa `wiki/skill-impact.md` por si hay propuestas rechazadas sobre el mismo objetivo, para no repetirlas.

## Ejecución
- **Una tarea atómica por sesión.** Si descubres trabajo extra, créalo como tarea nueva en el hito o como página `idea` en la wiki; no lo hagas ahora.
- Cumple la definición de hecho (DoD) literal de la tarea. No añadas alcance.

## Gate
- Ejecuta el gate indicado en la tarea: tests, evals, `python3 scripts/wiki_lint.py` o revisión de seguridad.
- **Si pasa → Accepted.** Si falla y no se arregla en la sesión → **Rejected**: revierte el código (`git restore`/`git revert`), pero **conserva** la traza y lo aprendido.

## Cierre (obligatorio, también si se rechaza)
1. Anexa una fila a `wiki/skill-impact.md`: `| n | fecha | rol | objetivo | cambio | gate | resultado | Accepted/Rejected |`.
2. Crea `raw/sessions/YYYY-MM-DD_<rol>_<tarea>.md` con: tarea, qué se hizo, qué falló, decisiones y evidencia (rutas de raw/eval-runs).
3. Aplica la skill `wiki-maintainer` para consolidar patrones, logs, index y STATUS.
4. `python3 scripts/wiki_lint.py --write-index`, que debe dar OK.
5. Commit: `Mx-Ty: <resumen>`.
