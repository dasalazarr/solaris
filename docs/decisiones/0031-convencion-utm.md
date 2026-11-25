---
id: ADR-0031
type: decision
title: "Convención de UTM para los enlaces de las piezas de contenido"
status: validating
owner_role: product
links: ["[[ADR-0024]]", "[[ADR-0025]]"]
evidence: ["landing/src/lib/analytics.ts", "product/lib/solicitud.ts"]
updated: 2026-11-25
---

# ADR-0031 · Convención de UTM

- Fecha: 2026-11-25
- Estado: propuesta. Pendiente de que Diego la acepte.

## Contexto

El ADR-0024 dejó pendiente una convención de UTM. Sin ella, cada lote semanal inventa valores y la prueba A/B de mensajes (medida por `utm_content`) no se puede leer. La landing guarda los cinco parámetros estándar en `sessionStorage` y el producto los recibe con la solicitud (máx. 120 caracteres por valor). Un `utm_medium` inventado (`organico-illarium`) no entra en el canal "Organic Social" de GA4.

## Decisión

Formato: `https://www.illarium.com/solaris/demo?utm_source=…&utm_medium=…&utm_campaign=…&utm_content=…`

Reglas comunes: minúsculas, sin tildes ni espacios, guiones como separador, sin datos de personas ni prospectos.

| Parámetro | Qué lleva | Valores |
|---|---|---|
| `utm_source` | La red o el canal | `linkedin`, `x`, `email`, `directo` |
| `utm_medium` | El tipo de tráfico, no la marca | `social` (orgánico), `paid-social`, `email`, `referral` |
| `utm_campaign` | La campaña o tema | `t1-compras`, `t2-...` (tema del plan de contenido) |
| `utm_content` | La variante del mensaje | `wNN-<gancho>`, p. ej. `w48-relacion`; `wNN` es la semana ISO |
| `utm_term` | No se usa | — |

Reglas de uso:

1. **Una variante, un `utm_content`.** El A/B es de ganchos: dos ganchos para un mismo dolor llevan dos valores distintos. El formato (carrusel, texto, vídeo) no va en el nombre; si hay que medirlo, se decide aparte.
2. **Orgánico y de pago se separan por `utm_medium`**, nunca por `utm_source`.
3. **Prospección dirigida (ABM):** `utm_source=email`, `utm_medium=email`, `utm_content` con un código de lista, nunca el nombre de la empresa ni de la persona.
4. **Cada lote semanal registra** sus enlaces con UTM en `raw/` junto al resultado, para poder leer qué gancho convirtió.
5. **Ejemplo canónico:** `…/solaris/demo?utm_source=linkedin&utm_medium=social&utm_campaign=t1-compras&utm_content=w48-relacion`

## Opciones descartadas

- *Medium por marca* (`organico-illarium`): no lo agrupa GA4 y no aporta nada.
- *Formato en `utm_content`*: mezcla dos variables y complica el análisis del A/B.

## Consecuencias

- El agente `contenido` y el contrato `plan/contratos/contenido.md` usan esta tabla al generar enlaces.
- Por comprobar: que `/solaris/demo` conserve los parámetros hasta el formulario (la landing los lee de la URL en la primera carga).
- Sin cambios de código en este ADR.
