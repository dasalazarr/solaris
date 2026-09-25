---
id: R07
type: risk
title: "Controles de acceso de demo no aptos para un piloto con datos reales"
status: validating
owner_role: security
links: ["[[F09]]", "[[F02]]", "[[PAT-005]]", "[[P04]]"]
evidence: ["raw/sessions/2026-09-25_security_M4-T1.md"]
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

## Mitigación
Antes de cualquier piloto: Keycloak/Entra (ADR-0002, diferido), TLS, `/docs` protegido, identidad propagada a la BD (p. ej. `SET LOCAL` + RLS en lugar del parámetro) y revisión del índice vectorial. Se incluye en el one-pager de M6-T3 como lista de "qué cambia del demo al piloto".
