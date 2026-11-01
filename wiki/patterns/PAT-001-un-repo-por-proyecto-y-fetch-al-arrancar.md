---
id: PAT-001
type: pattern
title: "Un repo por proyecto, y fetch al arrancar la sesión"
status: accepted
owner_role: wiki
links: ["[[R03]]"]
evidence: ["raw/sessions/2026-11-01_orquestador_workspace-y-pendientes.md"]
updated: 2026-11-01
---

# PAT-001 — Un repo por proyecto, y fetch al arrancar
## Patrón (fallo)
Dos proyectos distintos compartían el nombre y la URL `solaris.git`; `git pull` falló por historias sin punto en común y el `master` local nunca se había subido.
## Cómo aplicarlo
- Al arrancar: `git fetch --all` en la raíz y en cada submódulo, y comparar con el remoto antes de trabajar.
- Un proyecto, un repo. El 8D vive en la rama `archivo/8d-automocion` y, si se retoma, en su propio repo.
- Subir pronto cualquier rama local nueva.
