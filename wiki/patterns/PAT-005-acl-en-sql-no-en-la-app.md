---
id: PAT-005
type: pattern
title: "El filtro de permisos vive en SQL, y el backend no puede saltárselo"
status: accepted
owner_role: security
links: ["[[F01]]", "[[F09]]", "[[P03]]", "[[R03]]"]
evidence: ["raw/sessions/2026-09-25_dev_M2-T2.md"]
updated: 2026-09-25
---

# PAT-005 — El filtro de permisos vive en SQL, y el backend no puede saltárselo

## Patrón (éxito + deuda detectada)
- **Éxito:** `rag.visible_chunks(role)` aplica el ACL por carpeta *antes* del ranking vectorial y léxico (EXPLAIN lo confirma). Una carpeta sin fila de ACL no es visible para nadie (denegación por defecto). Un rol desconocido, NULL o con inyección ve 0 filas.
- **Deuda:** el backend conecta como superusuario, así que un `SELECT FROM rag.chunks` directo se salta el filtro. La garantía es de convención, no de sistema.

## Evidencia (trazas en raw/)
M2-T2, puntos para security 1–3.

## Cómo aplicarlo / workaround
- El `role` se deriva **siempre** del usuario autenticado ([[F09]]), nunca de parámetros de la petición ni de la salida del LLM.
- M4-T1 crea el rol de BD `solaris_app` con EXECUTE solo sobre las funciones `visible_*` y sin SELECT directo sobre `rag.chunks`/`rag.fmea_rows`, y el rol `erp_reader` solo lectura para el MCP (M3-T1).
- Tests de ACL negativos en cada cambio que toque la recuperación.
