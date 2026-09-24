# raw/ — Capa RAW (evidencia inmutable)

Equivale a `raw/` en WikiSkill (arXiv 2608.27454). **Nunca se editan ficheros existentes**: solo se añaden nuevos.

| Carpeta | Contenido | Quién escribe |
|---|---|---|
| `research/` | Investigación de mercado, PRD y documentos fuente | producto (solo se añaden versiones nuevas) |
| `interviews/` | Notas de entrevistas y sesiones de validación (`YYYY-MM-DD_<persona>_<empresa-anon>.md`, según `_TEMPLATE.md`) | producto |
| `sessions/` | Traza de cada sesión de agente (`YYYY-MM-DD_<rol>_<tema>.md`) | todos los agentes, al cerrar la sesión |
| `eval-runs/` | Resultados de golden set, red-team y comparativas de modelos (`YYYY-MM-DD_<suite>_<modelo>.json`) | dev / seguridad |

La wiki (`wiki/`) destila esta evidencia en patrones. Las páginas de la wiki citan rutas de `raw/` en su campo `evidence`.
