# M7-GTM — MVP de evidencia comercial ([ADR-0008](../../wiki/decisions/ADR-0008-evidencia-comercial.md))

**Fechas:** 17/10 – 06/11/2026, en paralelo a M5–M6.
**Gate de salida:**
- Landing publicada.
- Vídeo de ≤3 min.
- 3 posts.
- ≥40 cuentas contactadas.
- ≥5 demos con traza en `raw/interviews/`.
- ≥1 piloto propuesto o solicitud de ayuda.

| ID | Rol | Tarea | DoD | Gate | Depende de |
|---|---|---|---|---|---|
| M7-G1 | product | **Mensaje, oferta y tabla de claims** | `marketing/messaging.md` | Revisión de product + security (claims) | — |
| M7-G2 | product | **40 cuentas + secuencia de outbound** (sin datos personales en git) | `marketing/accounts.csv`, `marketing/outreach.md` | ≥35 cuentas con fuente | G1 |
| M7-G3 | dev | **Landing estática** con agenda y franja de "planta ficticia" | `marketing/landing/` | Navegador: 375 px, modo oscuro, sin scroll horizontal; revisión de security (RGPD, embed) | G1 |
| M7-G4 | dev | **Flujo grabable** = M5-T3..T6 + M6-T2 (sin cambios de alcance) | Ver M5/M6 | Los de M5/M6 | — |
| M7-G5 | product | **Vídeo de 2–3 min** sobre la UI real tras `make reset` | MP4 + póster en `marketing/landing/` | ≤3 min; sin consola ni datos de pruebas en pantalla | G4 |
| M7-G6 | product | **3 posts de LinkedIn** (dolor → vídeo/confianza → aprendizajes) | `marketing/posts/P1–P3.md` | Cada cifra está en la tabla de claims | G1, G5, M6-T5 |
| M7-G7 | product | **Demos = sesiones de validación** + embudo | `marketing/funnel.md`, `raw/interviews/*` | Protocolo de M6-T4 aplicado | G2, M6-T4 |
