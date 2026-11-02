# Solaris — Tablero vivo

Léelo al empezar y actualízalo al cerrar. Última actualización: 2026-11-02.

## Estado
- `main` en `solaris`, `illariumcore` (producto) y `solaris_fronted` (landing). Nada desplegado.
- WikiSkill adoptada ([[ADR-0005]]). Demo 8D aparcado ([[ADR-0006]]).
- Equipo de agentes como Proceso con contrato ([[ADR-0007]]): `product` se divide en `landing-steward` y `product-steward`; contratos en `plan/contratos/`.

## Siguiente tarea por rol
| Rol | Tarea | Enlaza |
|---|---|---|
| landing-steward | Decidir cuál manda en la maqueta: menú lateral «Documentos» de la landing o pestañas «Explorar» del producto; alinear. | [[F06]], [[P04]] |
| product-steward | Ejecutar el playbook con el despacho y traer conclusiones anonimizadas al PRD §8 | [[O01]], [[H01]] |
| landing-steward | Preparar la activación de la analítica sin cookies (Plausible o Umami) para el despliegue: sin ella no hay KPI de solicitudes | [[F06]], [[ADR-0007]] |
| dev | Bajar el LCP de la landing (2,9 s móvil simulado) revisando la animación de palabras del titular | [[F06]] |
| dev | Resolver los 3 avisos de oxlint (`Footer.tsx`, `Closing.tsx`, `lib/hooks.ts`) | [[L02]] |
| security | Antes de desplegar: variables de entorno y valorar un límite de intentos global | [[R01]], [[R02]] |
| dev | Fase 1 de [[ADR-0007]]: pack `equipo` en el producto (después de configurar el despliegue de la demo) | [[O05]] |

## Bloqueos
- Dominio y logotipo definitivo (tras la búsqueda de marca).
- Revisión jurídica de la FAQ («[Respuesta pendiente de revisión jurídica.]»).

## Sin commit / local
- `~/Projects/Solaris-8D-archivo`: `marketing/accounts.*` y `.env` solo existen allí.
- `product/.env.local` (ignorado) con el espacio de demo local.
