# Solaris — Índice de la wiki

> Catálogo generado por `python3 scripts/wiki_lint.py --write-index`. No editar a mano.
> Capa WIKI del modelo WikiSkill (ver [[ADR-0001]]). Evidencia en `raw/`, procedimientos en `.claude/skills/`.

Otros ficheros de la wiki: [logs.md](logs.md) (log cronológico) · [skill-impact.md](skill-impact.md) (auditoría de propuestas) · [_templates/](_templates/).

## Problemas (P)

| ID | Título | Estado | Rol |
|---|---|---|---|
| [P01](problems/P01-conocimiento-calidad-disperso.md) | Conocimiento de calidad disperso | validating | product |
| [P02](problems/P02-plazos-oem.md) | Plazos del OEM: contención en 24 h, 8D en 10 días | validating | product |
| [P03](problems/P03-ia-generica-sin-permisos.md) | La IA genérica no respeta permisos ni OT | validating | product |
| [P04](problems/P04-veto-it-ot.md) | Veto de IT/OT por seguridad | validating | product |
| [P05](problems/P05-trampa-consultoria.md) | Trampa de la consultoría | validating | product |
| [P06](problems/P06-corpus-baja-calidad.md) | Corpus de baja calidad (escaneados, AMFE en Excel) | idea | product |
| [P07](problems/P07-ya-tenemos-copilot.md) | «Ya tenemos Copilot» | validating | product |

## Features (F)

| ID | Título | Estado | Rol |
|---|---|---|---|
| [F01](features/F01-ingesta-acl-heredadas.md) | Ingesta con ACL heredadas | building | dev |
| [F02](features/F02-rag-citado.md) | RAG citado con "no encontrado | building | dev |
| [F03](features/F03-extraccion-amfe.md) | Extracción estructurada de AMFE | building | dev |
| [F04](features/F04-agente-8d-d1-d4.md) | Agente 8D D1–D4 | planned | dev |
| [F05](features/F05-mcp-erp-solo-lectura.md) | MCP ERP en solo lectura con consulta visible | building | dev |
| [F06](features/F06-bandeja-aprobaciones.md) | Bandeja de aprobaciones (HITL) | planned | dev |
| [F07](features/F07-export-plantilla-oem.md) | Exportación a plantilla del OEM (DOCX) | planned | dev |
| [F08](features/F08-audit-log.md) | Audit log de solo anexar | building | security |
| [F09](features/F09-rbac-on-behalf-of.md) | RBAC con on-behalf-of | building | security |
| [F10](features/F10-router-modelos-openrouter.md) | Router de modelos con ficha de agente (OpenRouter) | building | dev |
| [F11](features/F11-aviso-art50-feedback.md) | Aviso de IA (art. 50) y feedback | planned | product |
| [F12](features/F12-panel-no-conformidades.md) | Panel de no conformidades | idea | product |

## Lugares clave (L)

| ID | Título | Estado | Rol |
|---|---|---|---|
| [L01](places/L01-inbox-reclamaciones.md) | Inbox de reclamaciones | planned | product |
| [L02](places/L02-workspace-8d.md) | Workspace 8D | planned | product |
| [L03](places/L03-bandeja-aprobaciones.md) | Bandeja de aprobaciones | planned | product |
| [L04](places/L04-consulta-planta-tableta.md) | Consulta en planta (tableta/móvil) | planned | product |
| [L05](places/L05-erp.md) | ERP (lotes, envíos, proveedores) | planned | product |
| [L06](places/L06-repositorio-documental.md) | Repositorio documental (SharePoint/SMB) | planned | product |
| [L07](places/L07-consola-auditoria.md) | Consola de auditoría | planned | product |
| [L08](places/L08-borde-ot.md) | Borde OT (pasarela edge) | parked | product |

## Oportunidades (O)

| ID | Título | Estado | Rol |
|---|---|---|---|
| [O01](opportunities/O01-memoria-calidad.md) | Memoria de calidad: detección de recurrencia | idea | product |
| [O02](opportunities/O02-wikiskill-en-producto.md) | WikiSkill dentro del producto | idea | product |
| [O03](opportunities/O03-canal-naitec-iris.md) | Canal NAITEC / IRIS EDIH | idea | product |
| [O04](opportunities/O04-ayuda-foral-2026.md) | Ayuda foral fomento empresa digital (hasta 30.000 €) | validating | product |
| [O05](opportunities/O05-spri-ia-euskadi.md) | SPRI Inteligencia Artificial 2026 (País Vasco) | idea | product |

## Hipótesis (H)

| ID | Título | Estado | Rol |
|---|---|---|---|
| [H01](hypotheses/H01-calidad-confia-borrador-8d.md) | Calidad confía en un borrador 8D de IA lo suficiente para usarlo ante el OEM | validating | product |
| [H02](hypotheses/H02-ahorro-tiempo-8d.md) | El borrador reduce ≥40% el tiempo de elaboración de D1–D4 | validating | product |
| [H03](hypotheses/H03-erp-pymes.md) | Las pymes objetivo usan SAP B1 / Dynamics / Sage / a3 y MES en Excel | validating | product |
| [H04](hypotheses/H04-deepseek-calidad-precio.md) | DeepSeek (vía OpenRouter) ofrece la mejor relación calidad/precio para el 8D sin penalizar la venta | validating | product |
| [H05](hypotheses/H05-wikiskill-mejora-agente.md) | Evolucionar skills del agente 8D con WikiSkill mejora el golden set del cliente | validating | product |
| [H06](hypotheses/H06-ayudas-aceleran-no-sostienen.md) | Las ayudas aceleran la decisión pero el precio es rentable sin ellas | validating | product |

## Riesgos (R)

| ID | Título | Estado | Rol |
|---|---|---|---|
| [R01](risks/R01-soberania-vs-openrouter-deepseek.md) | Soberanía vs OpenRouter + DeepSeek | validating | security |
| [R02](risks/R02-trampa-consultoria.md) | Trampa de la consultoría | validating | product |
| [R03](risks/R03-inyeccion-prompts-mcp.md) | Inyección de prompts vía reclamaciones y abuso de herramientas MCP | validating | security |
| [R04](risks/R04-empaquetado-copilot.md) | Empaquetado de Copilot | validating | product |
| [R05](risks/R05-calidad-rag-industrial.md) | Calidad del RAG industrial | validating | product |
| [R06](risks/R06-capacidad-fundador.md) | Capacidad de un fundador en solitario + plazo 06/11 | validating | product |
| [R07](risks/R07-auth-demo-no-apta-piloto.md) | Controles de acceso de demo no aptos para un piloto con datos reales | validating | security |

## Patrones aprendidos (PAT)

| ID | Título | Estado | Rol |
|---|---|---|---|
| [PAT-001](patterns/PAT-001-demo-una-cuna.md) | Un demo, una cuña: vender el flujo, no el OS | accepted | product |
| [PAT-002](patterns/PAT-002-tension-explicita.md) | Hacer explícitas las tensiones de diseño en un ADR | accepted | product |
| [PAT-003](patterns/PAT-003-nombres-ficticios-vs-marcas.md) | Comprobar los nombres ficticios contra marcas reales del sector | accepted | product |
| [PAT-004](patterns/PAT-004-verdad-fuera-del-alcance-del-agente.md) | La verdad de evaluación nunca en datos accesibles al agente | accepted | dev |
| [PAT-005](patterns/PAT-005-acl-en-sql-no-en-la-app.md) | El filtro de permisos vive en SQL, y el backend no puede saltárselo | accepted | security |
| [PAT-006](patterns/PAT-006-generadores-congelados.md) | Un generador sintético se congela cuando otro artefacto cita sus IDs | accepted | dev |
| [PAT-007](patterns/PAT-007-diversificar-antes-de-fusionar.md) | Diversificar por documento en cada rama, no solo tras fusionar | accepted | dev |
| [PAT-008](patterns/PAT-008-identidad-solo-por-token.md) | La identidad solo entra por el token; el rol se resuelve en el servidor | accepted | security |
| [PAT-009](patterns/PAT-009-latencia-depende-del-proveedor.md) | Con un agregador, la latencia es del proveedor, no del modelo | accepted | dev |
| [PAT-010](patterns/PAT-010-no-mezclar-reglas-en-un-prompt.md) | Una regla de prompt por iteración, medida aislada | accepted | dev |

## Decisiones (ADR)

| ID | Título | Estado | Rol |
|---|---|---|---|
| [ADR-0001](decisions/ADR-0001-wikiskill-como-modelo-de-repo.md) | WikiSkill como modelo del repositorio vivo | accepted | product |
| [ADR-0002](decisions/ADR-0002-stack-demo.md) | Stack del demo: objetivo reducido | accepted | product |
| [ADR-0003](decisions/ADR-0003-openrouter-politica-modelos.md) | OpenRouter como orquestador de modelos y política de proveedores | accepted | product |
| [ADR-0004](decisions/ADR-0004-demo-datos-sinteticos.md) | Demo con planta y OEM ficticios | accepted | product |
| [ADR-0005](decisions/ADR-0005-threat-model-inicial.md) | Threat model inicial del demo | accepted | security |
| [ADR-0006](decisions/ADR-0006-cierre-roi-y-panel-f12.md) | Cierre del demo con promesa de ROI y panel F12 dentro del alcance | accepted | product |
