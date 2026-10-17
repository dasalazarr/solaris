# 2026-10-17 · orquestador (cofundador comercial) · MVP de evidencia comercial

**Tarea:** M7-GTM (Paso 0, G1, G3 v1, G6-P1, plantillas de G2 y G7) · **Decisión:** ADR-0008

## Entrada
El fundador pide un "MVP que sirva de evidencia" (publicaciones, artículos, landing para agendar demo), con un enfoque en visibilizar features, casos de uso y mejoras, y que se evalúe como cofundador comercial.

## Crítica (aceptada por el fundador al aprobar el plan)
1. Los resultados son sintéticos: publicarlos como "resultados" quema la credibilidad en un mercado pequeño (~120 empresas de automoción en Navarra). Hay que etiquetarlos.
2. La landing no genera leads en este mercado: es un activo de credibilidad para el outbound.
3. Se abre con el dolor (P02), no con las features.
4. El contenido sale de las sesiones de validación; no las sustituye.
5. "Industrial OS" choca con la tesis del copiloto de calidad → O07.

**Respuestas del fundador:** canal = red propia/LinkedIn + en frío; landing estática en el repo; marca y dominio por decidir.

## Hecho
- `wiki/decisions/ADR-0008-evidencia-comercial.md`, `wiki/opportunities/O07-mensaje-y-marca.md`, `plan/milestones/M7-GTM.md` y la fila en `plan/ROADMAP.md`.
- `marketing/messaging.md`: mensaje por persona, oferta de piloto, tabla de claims C1–C9 con fuente y claims prohibidos.
- `marketing/landing/`: página estática con la franja de "planta ficticia", una maqueta del caso 0312 alineada con `app/evals/scenario_truth.json` y el CTA de agenda como placeholder. Config `landing` en `.claude/launch.json`.
- `marketing/posts/P1-dolor-8d-24h.md`, `marketing/outreach.md`, `marketing/funnel.md`.

## Verificación
Landing en el navegador interno:
- Escritorio en modo oscuro y móvil 375 px en modo claro.
- `scrollWidth = 375` (sin scroll horizontal).
- Sin errores de consola.

## Ayuda foral
Búsqueda web (17/10): solo fuentes de terceros (tecnociminnova, catálogo de AIN).
- Las fuentes dan 30.000 € como máximo, una intensidad del 35–90 %, una inversión mínima discrepante (600 € frente a 5.000 €) y minimis.
- **No se encontraron las bases oficiales** ni los requisitos del proveedor del tipo A → en público se dice "puede ser subvencionable".

## Pendiente
- Fundador: nombre y dominio (O07), enlace de la agenda, verificar las bases de la ayuda, publicar P1.
- Security: revisión de la landing (RGPD, agenda).
- Propuestas de sesión en paralelo: G4 (flujo grabable M5-T3→T4) y G2 (lista de 40 cuentas).
