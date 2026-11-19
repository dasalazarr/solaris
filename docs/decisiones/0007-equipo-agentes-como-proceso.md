---
id: ADR-0007
type: decision
title: "El equipo de agentes es un Proceso de Solaris"
status: accepted
owner_role: product
links: ["[[ADR-0005]]", "[[O03]]", "[[O04]]", "[[O05]]"]
evidence: ["raw/research/2026-11-02_openbot-evaluacion.md"]
updated: 2026-11-02
---

# 0007 · El equipo de agentes es un Proceso de Solaris

- Fecha: 2026-11-02
- Estado: aceptada (Diego, 02/11)

## Contexto
Diego propuso un equipo de agentes «dueños» de la landing y del producto, más adelante de comunicación y diseño, coordinado a través del repo, sobre OpenBot, y con una plataforma que muestre el estado. Hoy hay cero clientes, nada desplegado y la analítica de la landing apagada.

## Opciones
1. **OpenBot como runtime.** Licencia no comercial (Illarium necesitaría pagarla), agentes con acceso total sin confirmación, estado en SQLite fuera del repo.
2. **Repo con Claude Code.** Los agentes se definen en `.claude/agents/`, los contratos viven en git y el bucle WikiSkill ya existe.

## Decisión
Opción 2. Además, el equipo se modela con la ontología de Solaris:
- Cada rol es un **Proceso con contrato** (`plan/contratos/<rol>.md`): KPI, reglas, acciones permitidas y revisión de Diego.
- Los agentes **administran** (*stewards*): proponen y miden. La propiedad de los resultados es de Diego.
- Las reglas son código en `scripts/wiki_lint.py`, no el criterio del modelo: evidencia vigente, A/B solo con tráfico medido, insight de mercado con cita y diario en borrador hasta que Diego lo publique.
- El rol `product` se divide en `landing-steward` (solicitudes de demo, mensaje, coherencia) y `product-steward` (piloto, hipótesis, clientes).
- El tablero será un pack `equipo` dentro del producto (fase 1), alimentado por una **instantánea generada** desde el repo. El runtime sigue sin leer `wiki/` ([[ADR-0005]]); lee un fichero generado y saneado, accesible solo desde un espacio propio.

## Consecuencias
- No se instala OpenBot ([[O04]] lo reevalúa si la coordinación por repo se queda corta).
- Comunicación y LinkedIn quedan aparcados ([[O03]]): solo borradores y nunca publicación sin Revisión.
- Coste: disciplina para mantener la evidencia de cada contrato al día. El lint avisa a los 14 días.
- La fase 1 se hace después de configurar el despliegue de la demo (P0.3 del ROADMAP).
