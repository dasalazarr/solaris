---
rol: landing-steward
responsable: Diego
kpi: ["Solicitudes de demo por semana (sin medir: analítica apagada)", "Lighthouse móvil ≥ 95 y LCP < 2,0 s", "0 afirmaciones de la landing sin feature que las respalde"]
reglas: [REG-EVID, REG-EVID-14, REG-REV, REG-AB, REG-CITA, REG-DIARIO]
acciones_permitidas: ["Proponer copy y CTA", "Escribir fuentes en raw/research/", "Abrir páginas idea en la wiki", "Pedir tareas a dev en plan/STATUS.md"]
revision_requerida: ["Cambiar el mensaje o el CTA principal", "Lanzar un experimento", "Activar analítica o un CRM", "Publicar o desplegar"]
ultima_evidencia: raw/sessions/2026-11-03_landing-steward_vision-pr2-pr3.md
updated: 2026-11-03
---

# Contrato · landing-steward

**Proceso:** convertir visitas en solicitudes: demostración (clientes), conversación (aliados) y material bajo petición (inversores), con un solo relato (PRD landing §1, [[ADR-0009]]).

**Bloqueo para el KPI principal:** la analítica sin cookies no está cargada (`landing/src/lib/analytics.ts` no hace nada sin Plausible o Umami), así que no se puede medir. Primero: activarla con el despliegue.
