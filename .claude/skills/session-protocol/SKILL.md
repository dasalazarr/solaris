---
name: session-protocol
description: Protocolo de arranque y cierre de cualquier sesión en el espacio de trabajo Solaris (bucle WikiSkill). Úsalo al empezar y al terminar cada sesión, sea cual sea el rol.
---

# Protocolo de sesión (bucle WikiSkill)

## Arranque
1. `git fetch --all` en la raíz y en `product/` y `landing/`; compara con el remoto antes de tocar nada ([[PAT-001]]).
2. Lee `plan/STATUS.md` (tablero vivo), luego `wiki/index.md`, y solo las páginas enlazadas a tu tarea.
3. Revisa `wiki/skill-impact.md` por si hay propuestas rechazadas sobre el mismo objetivo.

## Ejecución
- **Una tarea atómica por sesión.** Trabajo extra descubierto → página `idea` o `parked` en la wiki, no se implementa (alcance congelado en `plan/ROADMAP.md`).
- Cumple los criterios de aceptación del PRD correspondiente (`docs/prd-producto.md`, `docs/prd-landing.md`).
- Si el cambio altera algo que la landing muestra o afirma, avísalo y propón el cambio en `landing/`.

## Gate
- Producto: `cd product && npm run lint && npm test && npm run build`. Landing: `cd landing && pnpm lint && pnpm build`. Wiki: `python3 scripts/wiki_lint.py`.
- **Pasa → Accepted.** Falla y no se arregla en la sesión → **Rejected**: revierte el código pero **conserva** la traza y lo aprendido.
- Tras `next build`, reinicia `next dev` y borra `.next` ([[PAT-002]]).

## Cierre (obligatorio, también si se rechaza)
1. Anexa una fila a `wiki/skill-impact.md`.
2. Crea `raw/sessions/YYYY-MM-DD_<rol>_<tema>.md` (tarea, qué se hizo, qué falló, decisiones, evidencia).
3. Aplica `wiki-maintainer`: patrones, páginas afectadas, `wiki/logs.md`, `plan/STATUS.md`.
4. `python3 scripts/wiki_lint.py --write-index` debe dar OK.
5. Commits: primero en el submódulo afectado (`product/` o `landing/`) y después en la raíz con el puntero y la wiki. **No** hagas push a `main`, no despliegues y no publiques sin que Diego lo confirme.
