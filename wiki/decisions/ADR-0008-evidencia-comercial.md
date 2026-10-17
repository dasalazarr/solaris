---
id: ADR-0008
type: decision
title: "MVP de evidencia comercial (landing, vídeo, LinkedIn) dentro del alcance hasta el 06/11"
status: accepted
owner_role: product
links: ["[[PAT-001]]", "[[PAT-003]]", "[[ADR-0004]]", "[[O04]]", "[[O07]]", "[[H01]]", "[[H02]]", "[[R06]]"]
evidence: ["raw/sessions/2026-10-17_orquestador_gtm-evidencia.md", "raw/research/IllariumOS.md#L84"]
updated: 2026-10-17
---

# ADR-0008 — MVP de evidencia comercial dentro del alcance hasta el 06/11

## Contexto
El 17/10 (fecha prevista del demo) hay cero visibilidad pública, 0 entrevistas y 20 días hasta el cierre de la ayuda foral (O04). El fundador pide un "MVP de evidencia": contenido, casos de uso y una landing para agendar demos. El alcance está congelado (PAT-001), así que hace falta una decisión explícita.

## Decisión (del fundador, 2026-10-17)
1. Se abre el hito **M7-GTM** (`plan/milestones/M7-GTM.md`) en paralelo a M5–M6. **No cambia el alcance de dev**: el vídeo se graba sobre M5-T3..T6 + M6-T2.
2. **La landing es un activo de credibilidad para el outbound** (red propia, LinkedIn, en frío), no un generador de tráfico. Es estática y vive en `marketing/landing/`, fuera de la app.
3. **Reglas de contenido público** (no negociables):
   - Toda cifra lleva la etiqueta **"demo con planta ficticia / datos sintéticos"** y su fuente en la tabla de claims de `marketing/messaging.md`. Si una cifra no está en la tabla, no se publica.
   - Ninguna marca real de OEM ni de cliente (PAT-003). Se dice "proveedores Tier 2/3 de automoción".
   - No se afirma cumplimiento certificado (AI Act, IATF, RGPD): se describen controles ("diseñado para…").
   - La ayuda foral se menciona como "puede ser subvencionable" hasta verificar en las bases oficiales la elegibilidad del tipo A y los requisitos del proveedor.
   - La landing no recoge datos personales propios. La agenda es un enlace o embed externo y no hay analítica con cookies. Security revisa antes de publicar.
4. **Cada demo es una sesión de validación** con el protocolo de M6-T4 y deja traza en `raw/interviews/`.

## Consecuencias
- Más carga sobre el fundador (R06). Mitigación: el contenido se deriva del guion, de las evals y de las sesiones, no se crea desde cero.
- **Riesgo reputacional** si se presentan cifras sintéticas como resultados de cliente. Lo controla la tabla de claims más la revisión.
- El nombre público queda abierto en O07; hasta decidirlo la landing usa "Illarium".
