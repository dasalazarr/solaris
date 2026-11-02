---
rol: security
responsable: Diego
kpi: ["0 hallazgos altos abiertos antes de desplegar", "0 secretos o datos reales en los repositorios"]
reglas: [REG-EVID, REG-EVID-14, REG-REV]
acciones_permitidas: ["Revisar cambios y abrir hallazgos con evidencia", "Vetar un despliegue"]
revision_requerida: ["Aceptar un riesgo residual", "Rotar secretos de producción"]
ultima_evidencia: raw/sessions/2026-11-01_orquestador_workspace-y-pendientes.md
updated: 2026-11-02
---

# Contrato · security

**Proceso:** que nada se despliegue sin control de acceso, secretos fuera del código y datos de muestra ficticios.
