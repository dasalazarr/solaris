---
id: O06
type: opportunity
title: "Solaris como sistema que actúa (Action Service con HITL)"
status: idea
owner_role: product
links: ["[[PAT-001]]", "[[F04]]", "[[F05]]", "[[F06]]", "[[F08]]", "[[F09]]", "[[H03]]", "[[P04]]", "[[R03]]", "[[R06]]", "[[PAT-005]]", "[[PAT-008]]", "[[PAT-012]]"]
evidence: ["raw/sessions/2026-10-16_orquestador_ocp-viabilidad.md", "raw/research/IllariumOS.md#L99-L100"]
updated: 2026-10-16
---

# O06 — Solaris como sistema que actúa (Action Service con HITL)

> **Fuera de alcance del demo** ([PAT-001](../patterns/PAT-001-demo-una-cuna.md)). No se implementa nada antes del 06/11. Se decide en M6-T6 con la evidencia de las 5 sesiones de validación.

## Oportunidad

Hoy Solaris **redacta** (D1–D4 con citas y ERP trazado) y un humano aprueba. El paso siguiente es que también **actúe**: que convierta el 8D en acciones tipadas (bloquear un lote, pedir un 8D al proveedor, crear una acción correctiva, proponer una fila de AMFE, avisar al OEM). Siempre propone el agente, aprueba un humano y ejecuta el servidor.

Origen: evaluación (16/10) de un roadmap de "Ontology Control Plane" de 18 meses, una réplica de Foundry con Cedar, OPA, OpenFGA, Iceberg, Trino, Nessie, Temporal y low-code. **Se descarta como plan** por desproporcionado para pymes. Además, su Fase 4 (Anexo III del AI Act) parte de una premisa errónea: un asistente de calidad no es de alto riesgo ([IllariumOS.md:100](../../raw/research/IllariumOS.md)). 21 CFR Part 11 es de la FDA y no aplica a automoción. **Se rescata la idea central:** una capa cinética donde el agente **solo escribe a través de Action Types**, construida sobre lo que ya existe.

## Escalera de autonomía

| Nivel | Qué hace Solaris | Toca la regla "ERP de solo lectura" | Recomendación |
|---|---|---|---|
| **N0** Redacta | Borrador 8D citado; un humano aprueba y exporta | No | **Hoy** (demo) |
| **N1** Propone y verifica | Genera acciones tipadas con sus parámetros. El humano las ejecuta en su ERP/QMS y Solaris **verifica leyendo** el ERP que se hicieron (cierra el bucle sin escribir) | No | **Primer paso** tras validar |
| **N2** Ejecuta en lo suyo | Tras la aprobación, ejecuta en sistemas **propios** de Solaris: tareas con responsable y fecha, registro de NC y de acciones, recordatorios, notificaciones internas | No | Justo después de N1 |
| **N3** Escribe en el cliente | Tras la aprobación **por acción**, escribe en el ERP/QMS del cliente mediante un conector (cuenta de servicio limitada + on-behalf-of) | **Sí → requiere un ADR** | Solo con piloto firmado y ERP conocido |
| **N4** Autónomo por política | Ejecuta sin aprobación cuando lo permite una política | Sí | **No.** Fuera del producto |

## Certeza por componente

Leyenda: **Alta** = patrón ya probado en el repo · **Media** = técnica estándar pero nueva aquí · **Baja** = depende de factores externos que no controlamos.

| Componente | Base existente | Certeza | Nota |
|---|---|---|---|
| Ontología mínima (Reclamación, Pieza, Lote, Lote de material, OF, Envío, AMFE, 8D) | `erp` (8 tablas), `agents/eight_d/domain.py` | **Alta** | Registro de tipos en Postgres o Pydantic; LinkML y lakehouse innecesarios |
| Action Types tipados: propuesta → aprobación → ejecución | `eightd.approvals` (versión sha256, gana la primera decisión, rol solo INSERT), `hitl.py` (`LOCKED_KEYS`) | **Alta** | Generalizar el HITL ligado a versión: el hash cubre el tipo de acción y sus parámetros |
| PDP por acción | `acl.json → hitl_approvers`, RLS ([PAT-005](../patterns/PAT-005-acl-en-sql-no-en-la-app.md)), `CurrentUser` ([PAT-008](../patterns/PAT-008-identidad-solo-por-token.md)), `test_access_matrix` | **Alta** | Un solo motor; Cedar solo si las reglas crecen. Se descartan OPA y OpenFGA a la vez |
| Ejecución: precondiciones reevaluadas, idempotencia, outbox | — | **Media-alta** | Outbox en Postgres en vez de Temporal. Riesgo: que el estado haya cambiado entre la aprobación y la ejecución (lote ya enviado) → 409, igual que la versión del borrador |
| Verificación por lectura (N1) | MCP erp-mock de solo lectura y `mcp_obo.py` | **Alta** | Consultar que el lote quedó bloqueado y registrarlo en el audit |
| Efectos en sistemas propios (N2) | Backend, BD, frontend | **Alta** | |
| Writeback al ERP del cliente (N3) | — | **Baja / desconocida** | Depende de [H03](../hypotheses/H03-erp-pymes.md): muchos ERP de pyme no tienen API o los gestiona un integrador. Hay que hacer un conector por ERP, y la confianza de IT/OT está en juego ([P04](../problems/P04-veto-it-ot.md)) |
| Comunicación al OEM (correo o portal) | Export DOCX (F07) | Técnica alta, **aceptación baja-media** | Los portales de OEM rara vez tienen API. Es comunicación contractual: siempre la envía un humano |
| Seguridad del agente cuando puede actuar | R03, PAT-012, `prompts/untrusted.py`, red-team M3-T6 | **Media** | Con solo lectura, lo peor que puede pasar es un mal borrador; con acciones, una acción mal parametrizada. Reglas: el LLM solo **propone**, el contenido externo no puede originar una acción de alto impacto sin corroboración determinista (análogo a PAT-012), los parámetros sensibles quedan bloqueados como `LOCKED_KEYS`. **Veto de security** |
| Audit ligado a cada acción | `003_audit` (cadena de hash), `verify_chain()` | **Alta** | Falta el ancla externa (ya es requisito de piloto, M6-T3) |
| Reversibilidad | — | **Media** | Cada Action Type declara su compensación o se marca irreversible (en ese caso, doble aprobación) |
| Regulatorio | Pack art. 50 (M4-T5) | **Media** | Sigue fuera del Anexo III mientras no toque OT ni funciones de seguridad (Anexo I, 2028). Riesgo contractual o IATF si se libera un lote por error → la acción la firma el humano |

**Conclusión de certeza:**
- **Técnica.** N1 y N2 tienen certeza **alta**: reutilizan los patrones de M3–M4 y no tocan la regla de solo lectura. N3 es **incierta** hasta conocer el ERP del primer piloto.
- **De negocio.** Es la mayor incertidumbre: no sabemos si las pymes quieren que Solaris actúe, ni hasta qué nivel. Por eso se pregunta en M6.
- **Capacidad.** [R06](../risks/R06-capacidad-fundador.md): un fundador solo; N3 multiplica el trabajo por cada ERP.

## Primeros Action Types candidatos (8D)

1. **Bloquear un lote / poner en cuarentena** (contención en D3): el de más valor y el de más riesgo.
2. **Pedir un 8D al proveedor** del lote de material implicado.
3. **Crear una acción correctiva** con responsable y fecha (anticipa D5–D7).
4. **Proponer una fila o un cambio de AMFE** (propuesta para revisión, nunca una edición directa).
5. **Preparar el aviso de contención al OEM** (lo envía siempre un humano).

## Preguntas para la validación (→ M6-T4)

1. **Acciones de valor.** "Después del borrador, ¿qué acciones del 8D le gustaría que Solaris dejara preparadas o hiciera?" Enseñar la lista de los 5 candidatos y pedir que los ordene.
2. **Nivel de autonomía.** "¿Hasta dónde lo dejaría llegar?" Mostrar N1/N2/N3. "¿Qué acción no dejaría nunca en manos del sistema?"
3. **Dueño y vía de escritura** (→ H03). "¿Qué ERP/QMS usan y en qué versión? ¿Quién lo administra (IT interno o integrador)? Hoy, ¿cómo se bloquea un lote: con API, con pantalla o en Excel?"
4. **Condiciones de IT/OT** (→ P04). "¿Qué exigiría para dar a Solaris una cuenta de escritura (aprobación por acción, cuenta limitada, log, posibilidad de deshacer)? ¿Qué lo haría inaceptable?"
5. **Disposición a pagar.** "¿Pagaría más porque Solaris ejecute acciones y no solo redacte? ¿Qué acción concreta justificaría ese precio?"

## Siguiente paso

- **M6-T4:** incluir las 5 preguntas en `raw/interviews/_PROTOCOL.md`.
- **M6-T6:** con la evidencia, decidir:
  - **Si hay señal:** escribir un ADR "Solaris actúa: niveles de autonomía" (N1+N2) y un hito M7.
  - **Para N3:** solo con un piloto firmado y un ADR que modifique la regla de solo lectura.
  - **Si no hay señal:** pasar a `parked`.
