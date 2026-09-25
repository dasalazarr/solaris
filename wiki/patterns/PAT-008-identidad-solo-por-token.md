---
id: PAT-008
type: pattern
title: "La identidad solo entra por el token; el rol se resuelve en el servidor"
status: accepted
owner_role: security
links: ["[[F09]]", "[[PAT-005]]", "[[R03]]"]
evidence: ["raw/sessions/2026-09-25_security_M4-T1.md"]
updated: 2026-09-25
---

# PAT-008 — La identidad solo entra por el token; el rol se resuelve en el servidor

## Patrón (éxito)
- El token solo lleva el usuario. El **rol** se resuelve en el servidor desde acl.json en cada petición, así que cambiar la ACL tiene efecto inmediato y el cliente no puede declarar un rol.
- **Ningún endpoint acepta `user` ni `role`**: un test estructural recorre el OpenAPI y falla si aparecen.
- Un único helper (`mcp_obo`) construye la identidad que viaja al MCP (`_meta`), a partir del principal autenticado. El LLM nunca la ve ni la rellena.
- Todo endpoint nuevo usa `CurrentUser` y se añade a `tests/test_access_matrix.py::MATRIX`.

## Evidencia (trazas en raw/)
M4-T1: matriz de acceso por endpoint y rol, y tests de on-behalf-of.

## Cómo aplicarlo
Al crear el orquestador 8D (M3-T3) y la UI (M5): pasar siempre el principal; nunca construir la identidad desde datos de la petición ni desde la salida del modelo.
