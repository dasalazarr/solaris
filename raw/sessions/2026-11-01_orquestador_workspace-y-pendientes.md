# Sesión 2026-11-01 · orquestador · workspace y pendientes

## Tarea
Traer a local el trabajo que Claude hizo en la nube, levantar producto y landing, cerrar los pendientes técnicos de `docs/estado.md` y adoptar WikiSkill en todo el workspace.

## Qué se hizo
- `git pull` no funcionó: `origin` solo tenía `claude/lucid-johnson-jz3tdk`, un repo sin historia común con el `master` local (demo 8D). El local no estaba en el remoto.
- El 8D se movió a `~/Projects/Solaris-8D-archivo` y se subió como `archivo/8d-automocion`. El workspace se clonó con submódulos en `~/Projects/Solaris`.
- Producto: límite de 10 intentos por IP, indicador de entorno en el onboarding, lockfile y limpieza (1115 → 573 paquetes).
- Landing: contraste AA, `next/font`, captura del hero con tamaño reservado.
- PR #1 de `illariumcore` y de `solaris_fronted` fusionados a `main`; `main` creado en `solaris`.

## Qué falló
- `next build` dejó los dos `next dev` en 500 ([[PAT-002]]).
- `npm ci` no reproducía el lockfile ([[PAT-004]]).
- Los primeros Lighthouse con `http.server` daban LCP 5,3 s por no haber compresión.
- `git add` con un fichero ya borrado abortó el commit de la landing; se repitió sin él.

## Decisiones
Ver ADR-0005 (WikiSkill) y ADR-0006 (8D aparcado).

## Evidencia
`raw/eval-runs/2026-11-01_lighthouse-landing.md`, `raw/research/2026-11-01_8d-automocion-archivo.md`.
