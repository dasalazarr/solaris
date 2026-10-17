# 2026-10-16 · orquestador · Evaluación del roadmap OCP y viabilidad de "Solaris que actúa"

**Rol:** orquestador (sesión con el fundador) · **Tarea:** fuera de hito (idea, PAT-001) · **Código:** sin cambios

## Entrada
El fundador pidió evaluar un roadmap de "Ontology Control Plane" (OCP) en 5 fases y 18 meses:
- **F0:** PDP con Cedar/OPA/OpenFGA, markings y OpenLineage.
- **F1:** registro LinkML sobre Iceberg/Trino/Postgres, Object Sets GraphQL, Action Service con Temporal y outbox, SDK y MCP.
- **F2:** agentes LangGraph con on-behalf-of, checkpoints de justificación y 21 CFR Part 11, evals N≥3.
- **F3:** branching global con Nessie/lakeFS y low-code.
- **F4:** expediente del Anexo III/IV del AI Act antes del 2/12/2027.

El texto traía artefactos de citas ("more_horiz", números sueltos) sin las fuentes.

## Evaluación (resumen)
- **A favor:**
  - La seguridad va antes que la escritura.
  - El agente solo escribe a través de Action Types.
  - on-behalf-of y evals N≥3 ya están alineados con el repo.
- **En contra:**
  - **F4 parte de una premisa errónea.** IllariumOS.md:100 concluye que un asistente de calidad no es Anexo III.
  - **21 CFR Part 11 es FDA/farma**, no automoción (IATF 16949 y CSR del OEM).
  - **La referencia "Digital Omnibus 2026/1744" está sin verificar** en el DOUE.
  - **El "writeback external-first síncrono"** choca con la regla de ERP de solo lectura.
  - **El stack es desproporcionado para pymes:** tres motores de políticas y un lakehouse.
  - **OpenLineage no aplica políticas.**
  - **Las dependencias se solapan** (F0 sin esquema; F2 antes de terminar F1).
  - **F3 son dos productos.**
  - **Faltan:** conectores de ERP, despliegue, equipo, métricas y gates con clientes.
- **Veredicto:** no adoptar como plan; rescatar la capa cinética como idea.

## Viabilidad de "Solaris que actúa"
El fundador confirmó que quiere estructurar Solaris también como un sistema que actúa. Se revisó la base existente:
- `agents/eight_d/hitl.py` (versión sha256, `LOCKED_KEYS`).
- Migración `011_eightd_approvals` (solo SELECT/INSERT, gana la primera decisión).
- `003_audit` (cadena de hash).
- `mcp_obo.py` (identidad solo desde el `Principal`).
- Esquema `erp` (8 tablas).

Resultado:
- **Escalera N0–N4.**
- **Certeza.** Alta para N1 y N2 (reutilizan los patrones de M3–M4 y no tocan la solo lectura). Baja para N3 (depende del ERP del cliente, H03 y P04). La mayor incertidumbre es de demanda.
- **Detalle** en `wiki/opportunities/O06-solaris-sistema-que-actua.md`.

## Decisiones del fundador
- Registrar O06 como `idea`.
- Añadir 5 preguntas al protocolo de validación (M6-T4).

`raw/interviews/_PROTOCOL.md` aún no existe (M6-T4 pendiente), así que el requisito se anota en el DoD de M6-T4 en `plan/milestones/M6.md`.

## Siguiente
- **M6-T4 (product):** incluir el bloque de preguntas.
- **M6-T6:** decidir ADR + M7 (N1+N2) o `parked`.
