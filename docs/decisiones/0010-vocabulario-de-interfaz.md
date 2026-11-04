---
id: ADR-0010
type: decision
title: "Vocabulario de la interfaz: lo técnico va a detalles y lo que no es cierto no se dice"
status: accepted
owner_role: product
links: ["[[ADR-0009]]", "[[F03]]", "[[F06]]"]
evidence: ["raw/research/2026-11-04_diagnostico-ux-externo.md", "raw/sessions/2026-11-04_cofundador_alineamiento-diagnostico.md"]
updated: 2026-11-04
---

# ADR-0010 · Vocabulario de la interfaz

- Estado: aceptada (2026-11-04, Diego aprobó el plan de alineamiento)
- Contexto: el producto enseñaba códigos del backlog, hashes y etiquetas de prueba a quien responde de un proceso. Un diagnóstico externo propuso ocultarlos tras sellos como «Trazabilidad criptográfica verificada» o «Registro Inmutable». Pero el registro es estado de React, y `args_hash` y `sha256` son valores de muestra. Quitar jerga no puede convertirse en afirmar más de lo que hay (principios 1 y 4).

## Opciones

1. **Dejarlo como está.** Es honesto, pero cuesta atención y parece a medio hacer.
2. **Sellos de confianza.** Limpio, pero falso hoy.
3. **Plegar lo técnico, sin sellos, y vetar palabras mientras no sean ciertas.**

## Decisión

Opción 3.

- **Por defecto se ve:** responsable, regla (`R-03`), objeto (`PC-0412`), documento, página, cita, estado y entorno.
- **En «Detalles técnicos», rotulados como de muestra:** `step_id`, `args_hash`, `run_id`, `thread_id`, `policy_hash`, `sha256` e identificadores `EV-*`.
- **Nunca en la interfaz:** códigos del backlog (`R4`, `R8`, `F3`) ni etiquetas de prueba («Estrella»).
- **Entorno:** «Demo en la nube · datos de muestra». La palabra «nube» no se quita. «Nivel 1» y «Nivel 2» quedan para uso interno y para el paso de onboarding que los compara.

**Palabras vetadas mientras no sean ciertas**

| Palabra | Qué tendría que existir para usarla |
|---|---|
| «inmutable», «registro persistente» como presente | Persistencia de Revisar con almacenamiento a prueba de edición |
| «criptográfica», «sello», «huella» | Hash calculado de verdad sobre el contenido, no un valor de muestra |
| «continuo», «en segundo plano» | Evaluación sin que nadie abra el proceso |
| «VPC», «nube privada» | Un ADR que redefina el Nivel 2. Decisión del 04/11: no se promete |
| «ERP», «conectores» como capacidad | Una integración real |
| «reglas vivas», «convierte sus normativas» | Extracción de reglas desde documentos; hoy se declaran por pack |
| «lee sus documentos» como hecho de la demo; «OCR», «pipeline» | Ingesta real. Sí se puede describir como oferta («lee», «se instala») cuando la frase habla de lo que Solaris hace con sus documentos, no de lo que la demo acaba de hacer |
| «Pydantic» | Que el contrato se valide con Pydantic; el producto es TypeScript |
| «ejecución» como función de Solaris | Nunca: Solaris propone y no ejecuta (`fundacional.md` §3) |

## Consecuencias

- Antes de añadir una de esas palabras, se cambia esta tabla, no solo el copy.
- `docs/guion-demo-90s.md` sigue este vocabulario.
- Coste asumido: la interfaz suena menos impresionante que con sellos. A cambio, un auditor que pulse «Detalles técnicos» no encuentra una contradicción.
- Cuando llegue la persistencia, esta tabla decide qué se puede decir y a partir de cuándo.
- **Tono (Diego, 04/11):** no vender de más, pero tampoco subestimarnos. La oferta se describe con seguridad (`fundacional.md` §8) y el estado real se dice una o dos veces, bien dicho, no en cada sección.
