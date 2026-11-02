# Contratos de rol

Cada rol del equipo de agentes es un Proceso con contrato ([[ADR-0007]]). Un fichero por rol, con este frontmatter (lo valida `scripts/wiki_lint.py`):

| Clave | Qué es |
|---|---|
| `rol` | Nombre del agente en `.claude/agents/` |
| `responsable` | Persona dueña del resultado. Siempre `Diego` |
| `kpi` | Lista de métricas con su objetivo. Si no se puede medir hoy, se dice |
| `reglas` | Códigos de reglas deterministas que aplican (ver abajo) |
| `acciones_permitidas` | Lo que el agente puede hacer sin preguntar |
| `revision_requerida` | Lo que exige la aprobación de Diego antes de ejecutarse |
| `ultima_evidencia` | Ruta en `raw/` de la última traza del rol (`AAAA-MM-DD_…`) |
| `updated` | Fecha de la última edición |

## Reglas (código en `scripts/wiki_lint.py`)
| Código | Regla | Efecto |
|---|---|---|
| `REG-EVID` | `ultima_evidencia` existe en `raw/` | error |
| `REG-EVID-14` | La última evidencia tiene ≤ 14 días | aviso |
| `REG-REV` | `responsable` es una persona (`Diego`) y `revision_requerida` no está vacía | error |
| `REG-AB` | Una página con `experiment: ab` cita una medición en `raw/eval-runs/*trafico*` | error |
| `REG-CITA` | Una página con `origin: mercado` cita una fuente en `raw/research/` o `raw/interviews/` | error |
| `REG-DIARIO` | Cada entrada de `docs/diario/` está marcada como borrador o como publicada | error |
