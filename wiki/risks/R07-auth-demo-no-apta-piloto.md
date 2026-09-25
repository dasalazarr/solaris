---
id: R07
type: risk
title: "Controles de acceso de demo no aptos para un piloto con datos reales"
status: validating
owner_role: security
links: ["[[F09]]", "[[F02]]", "[[PAT-005]]", "[[P04]]"]
evidence: ["raw/sessions/2026-09-25_security_M4-T1.md", "raw/sessions/2026-09-25_security_M2-T8.md"]
updated: 2026-09-25
---

# R07 — Controles de acceso de demo no aptos para un piloto con datos reales

**Severidad:** high (antes de un piloto) · low (demo con datos sintéticos)

## Riesgo
Riesgos residuales que M4-T1 acepta para el demo:
1. Contraseñas de demo en `.env`, sesiones en memoria (1 worker) y sin TLS.
2. `/docs` (OpenAPI) público.
3. El rol de negocio sigue siendo un parámetro de las funciones `rag.visible_*`, así que la garantía depende de que solo `solaris_app` las llame con el rol resuelto.
4. Con SECURITY DEFINER, la búsqueda vectorial no usa HNSW: escala hasta ~50k chunks. Suficiente para el demo (340), no para clientes grandes.
5. (M2-T8 S3) El bloqueo de login es por usuario: rotando 1.000 usuarios inexistentes se esquiva y se inunda el audit. Hace falta limitar por IP o globalmente.
6. (M2-T8 S5) La política de proveedor LLM es la misma para el primario y el fallback. En piloto, la ruta solo UE necesita políticas por modelo.
7. (M2-T8 S6) Un xlsx pequeño con una celda combinada gigante bloquea la ingesta: limitar celdas, filas y tiempo por documento.
8. (M2-T8 L1) El reranker Jina (CC-BY-NC) se puede activar por configuración: bloquearlo en entornos comerciales.

## Mitigación
Antes de cualquier piloto: Keycloak/Entra (ADR-0002, diferido), TLS, `/docs` protegido, identidad propagada a la BD (p. ej. `SET LOCAL` + RLS en lugar del parámetro) y revisión del índice vectorial. Se incluye en el one-pager de M6-T3 como lista de "qué cambia del demo al piloto".
