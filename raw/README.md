# raw/ — Capa RAW (evidencia inmutable)

Equivale a `raw/` en WikiSkill (arXiv 2608.27454). **Nunca se editan ficheros existentes**: solo se añaden nuevos.

| Carpeta | Contenido | Quién escribe |
|---|---|---|
| `research/` | Investigación, documentos fuente y archivos de proyectos aparcados | producto |
| `interviews/` | Entrevistas y validaciones (`YYYY-MM-DD_<persona>_<empresa-anon>.md`, según `_TEMPLATE.md`). **Anonimizadas**: nada de clientes ni prospectos con nombre | producto |
| `sessions/` | Traza de cada sesión (`YYYY-MM-DD_<rol>_<tema>.md`) | todos, al cerrar la sesión |
| `eval-runs/` | Mediciones: Lighthouse, tests, red-team (`YYYY-MM-DD_<tema>.md`) | dev / security |

La wiki (`wiki/`) destila esta evidencia en patrones. Sus páginas citan rutas de `raw/` en `evidence`. Ningún documento real de un cliente entra en este repositorio.
