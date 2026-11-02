# Solaris — Índice de la wiki

> Catálogo generado por `python3 scripts/wiki_lint.py --write-index`. No editar a mano.
> Capa WIKI del modelo WikiSkill (ver [[ADR-0001]]). Evidencia en `raw/`, procedimientos en `.claude/skills/`.

Otros ficheros de la wiki: [logs.md](logs.md) (log cronológico) · [skill-impact.md](skill-impact.md) (auditoría de propuestas) · [_templates/](_templates/).

## Problemas (P)

| ID | Título | Estado | Rol |
|---|---|---|---|
| [P01](problems/P01-procesos-sin-contrato.md) | Los procesos críticos no tienen contrato explícito | validating | product |
| [P02](problems/P02-respuestas-sin-cita-no-auditables.md) | Una respuesta sin cita literal no es auditable | validating | product |
| [P03](problems/P03-entorno-ambiguo-demo.md) | El prospecto no sabe si ve datos de muestra o reales | done | product |
| [P04](problems/P04-marca-incoherente.md) | Landing y producto parecían dos marcas distintas | done | product |

## Features (F)

| ID | Título | Estado | Rol |
|---|---|---|---|
| [F01](features/F01-preguntar-con-cita.md) | Preguntar: respuesta citada con visor del documento original | building | dev |
| [F02](features/F02-explorar-ontologia.md) | Explorar: objetos, atributos y evidencia | building | dev |
| [F03](features/F03-huecos-reglas-deterministas.md) | Huecos: incumplimientos por reglas deterministas | building | dev |
| [F04](features/F04-revisar-hitl.md) | Revisar: aprobaciones con borrador editable y auditoría | building | dev |
| [F05](features/F05-acceso-por-codigo-de-espacio.md) | Acceso por código de espacio con límite de intentos | done | security |
| [F06](features/F06-landing-comercial.md) | Landing comercial con demo y solicitud | building | product |

## Lugares clave (L)

| ID | Título | Estado | Rol |
|---|---|---|---|
| [L01](places/L01-producto.md) | Producto (product/ → illariumcore) | building | dev |
| [L02](places/L02-landing.md) | Landing (landing/ → solaris_fronted) | building | dev |
| [L03](places/L03-acceso-a-espacios.md) | Acceso a espacios (código, sesión y límite) | done | security |
| [L04](places/L04-docs-raiz.md) | Documentación compartida (docs/) | done | product |

## Oportunidades (O)

| ID | Título | Estado | Rol |
|---|---|---|---|
| [O01](opportunities/O01-piloto-despacho-juridico.md) | Primer piloto de pago: despacho (pack Jurídico y mercantil) | validating | product |
| [O02](opportunities/O02-solaris-8d-automocion.md) | Otro producto de Solaris: copiloto 8D para automoción | parked | product |
| [O03](opportunities/O03-agente-comunicacion-linkedin.md) | Agentes de comunicación (LinkedIn) y diseño | parked | product |
| [O04](opportunities/O04-runtime-de-agentes.md) | Runtime de agentes dedicado (OpenBot u otro) | parked | product |
| [O05](opportunities/O05-pack-equipo-para-prospectos.md) | Abrir el pack «equipo» a prospectos | idea | product |

## Hipótesis (H)

| ID | Título | Estado | Rol |
|---|---|---|---|
| [H01](hypotheses/H01-despacho-convierte-a-pago.md) | El despacho convierte el piloto a contrato de pago | validating | product |
| [H02](hypotheses/H02-citas-verificadas-95.md) | ≥ 95 % de respuestas con cita verificada por el cliente | validating | product |

## Riesgos (R)

| ID | Título | Estado | Rol |
|---|---|---|---|
| [R01](risks/R01-seguridad-demo-nivel-1.md) | Seguridad de la demo (códigos en el código, atajo sin código) | done | security |
| [R02](risks/R02-fuerza-bruta-residual.md) | Fuerza bruta sobre el código de espacio (residual) | building | security |
| [R03](risks/R03-divergencia-nube-local.md) | Trabajo en la nube y copia local divergen | building | wiki |
| [R04](risks/R04-spam-formulario-solicitud.md) | Spam o abuso del formulario de solicitud de demo | building | security |

## Patrones aprendidos (PAT)

| ID | Título | Estado | Rol |
|---|---|---|---|
| [PAT-001](patterns/PAT-001-un-repo-por-proyecto-y-fetch-al-arrancar.md) | Un repo por proyecto, y fetch al arrancar la sesión | accepted | wiki |
| [PAT-002](patterns/PAT-002-next-build-rompe-next-dev.md) | `next build` rompe un `next dev` en la misma carpeta | accepted | dev |
| [PAT-003](patterns/PAT-003-medir-antes-de-arreglar-cls.md) | Medir el origen de un CLS antes de arreglarlo | accepted | dev |
| [PAT-004](patterns/PAT-004-peer-opcional-rompe-npm-ci.md) | Un peer opcional sin usar puede romper `npm ci` | accepted | dev |

## Decisiones (ADR)

| ID | Título | Estado | Rol |
|---|---|---|---|
| [ADR-0001](../docs/decisiones/0001-estructura-submodulos.md) | Repositorio raíz con submódulos | accepted | dev |
| [ADR-0002](../docs/decisiones/0002-identidad-visual-unica.md) | Una sola identidad visual: el sol de Solaris | accepted | product |
| [ADR-0003](../docs/decisiones/0003-acceso-espacios.md) | Acceso a espacios | accepted | security |
| [ADR-0004](../docs/decisiones/0004-landing-nextjs.md) | La landing pasa de Vite a Next.js | accepted | dev |
| [ADR-0005](../docs/decisiones/0005-wikiskill-como-modelo-del-workspace.md) | WikiSkill como modelo del espacio de trabajo | accepted | product |
| [ADR-0006](../docs/decisiones/0006-8d-automocion-aparcado.md) | El copiloto 8D de automoción queda aparcado como posible otro producto | accepted | product |
| [ADR-0007](../docs/decisiones/0007-equipo-agentes-como-proceso.md) | El equipo de agentes es un Proceso de Solaris | accepted | product |
