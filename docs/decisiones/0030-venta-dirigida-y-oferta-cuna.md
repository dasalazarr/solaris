---
id: ADR-0030
type: decision
title: "Venta dirigida a despachos con una oferta cuña de 21 días; PMM-OS aparcado"
status: validating
owner_role: product
links: ["[[ADR-0024]]", "[[ADR-0019]]", "[[ADR-0026]]", "[[ADR-0018]]", "[[ADR-0010]]", "[[O01]]", "[[H01]]"]
evidence: ["raw/research/2026-11-21_mercado-abogados-pamplona-logrono.md", "docs/playbook-evaluacion-piloto.md"]
updated: 2026-11-25
---

# ADR-0030 · Venta dirigida y oferta cuña

- Fecha: 2026-11-25
- Estado: propuesta. Diego eligió el nicho (despachos) el 25/11; falta que acepte o corrija el resto.

## Contexto

Diego planteó dos cosas el mismo día:

1. **PMM-OS**, un PRD de orquestador de marketing multiagente (FastAPI, LangGraph, n8n, Qdrant, servidores MCP, aprobaciones en Slack y Telegram, publicación automática) para que el contenido salga de lo que el código hace.
2. **Un giro comercial:** pasar de visibilidad pasiva a prospección dirigida a 15–20 cuentas (ABM), vender el resultado y no el stack, y abrir con una oferta pequeña de 21 días en vez de una implantación.

A 25/11 no hay ninguna entrevista hecha, la lista de cuentas objetivo está vacía y el contenido sale cada semana. El cuello de botella son las conversaciones con compradores, no la producción de piezas.

## Opciones

1. **Construir PMM-OS.** Tres a cinco semanas y cinco piezas de infraestructura nuevas. El 70 % ya existe en [[ADR-0024]] (mensajes permitidos con su referencia, gate de vocabulario, lote en borrador que Diego aprueba). Supone un equipo (PMM, desarrolladores, CEO) que hoy es una persona. Su fase 4, publicar sola, contradice [[ADR-0024]]. LangGraph sigue aparcado ([[ADR-0019]]).
2. **Seguir solo con contenido.** No cambia el número de conversaciones.
3. **Venta dirigida con oferta cuña**, sobre lo que el producto hace hoy y con el nicho del primer piloto.

## Decisión

Opción 3. PMM-OS queda aparcado; su única idea que falta (descubrir mensajes candidatos desde los PR fusionados) se puede añadir como script al lote semanal cuando el contenido vuelva a ser el cuello de botella.

1. **Nicho: despachos de empresa o mercantil de 2 a 19 personas en Pamplona y Logroño.** Es el P0 del PRD y el segmento de encaje alto del estudio del 21/11 (unos 100–150 despachos). La venta dirigida **es** la Fase A de ese estudio, con 15–20 despachos con nombre en vez de un muestreo.
2. **Dónde vive la lista.** Despachos y personas, solo en el repositorio privado de contenido. Las personas las escribe Diego. En esta raíz no entra ningún nombre.
3. **Canal.** Mensaje directo en LinkedIn, teléfono, presentación por un tercero o el colegio. **No hay correo comercial en frío**: la LSSI (art. 21) restringe el correo no solicitado. Sin comprobar: si alguna excepción cubre el contacto entre profesionales; lo confirma quien valide Privacidad.
4. **Mensaje por resultado y sin cifras sin medir.** El titular nombra la consecuencia (un aval que vence sin aviso, un anexo sin firmar que aparece en una operación). Ningún porcentaje de ahorro: el tiempo antes y después se mide en la oferta cuña y solo entonces se puede contar ([[ADR-0010]], [[ADR-0026]]).
5. **Oferta cuña: «Primer contrato · despachos», 21 días, un despacho.**
   - Semana 1: con el socio, un tipo de asunto y 3–5 criterios del despacho escritos como reglas (vencimientos, anexos, apoderamientos, hoja de encargo).
   - Semana 2: revisión de hasta 20 expedientes contra esas reglas, a mano y en el despacho, o sobre copias anonimizadas. Cada hallazgo con su cita. Se cronometra.
   - Semana 3: entrega del dictamen, la medida antes y después, y la demo de Solaris con esas reglas sobre datos de muestra. Al final, orden firmada para un piloto de Nivel 2 con precio de fundador, o despedida sin coste.
   - **Ningún documento del despacho entra en Solaris ni en un sistema nuestro** hasta que existan la Fase 4, un modelo local o europeo con contrato de encargo, el acuerdo de confidencialidad y el encargo de tratamiento, y el veto de `security` levantado. El secreto profesional lo exige.
6. **Prototipo visual.** Un vídeo corto grabado por Diego sobre la demo actual, con el guion de 90 s adaptado a Jurídico. Rótulo de datos de muestra visible.

## Puerta

La del estudio del 21/11: con ≥ 8 conversaciones, si ≥ 3 despachos reconocen el dolor como semanal y ≥ 1 acepta la prueba con 20 expedientes, **la Fase 4 y el `LLMProvider` local pasan a P0 de dev**, por delante del pulido de la interfaz. Si no, Jurídico queda como muestra y el piloto se busca en la industria ([[ADR-0015]]).

## Consecuencias

- **Coste:** uno o dos días de documentos y mensaje. El trabajo de venta (contactar, llamar, visitar) es de Diego y compite con el sprint CFO hasta el 09/12; el sprint no se mueve.
- **Producto:** si la puerta se abre, la Fase 4 desplaza la auditoría de interfaz del 14/11 y el trabajo en móvil. Antes de enseñar reglas nuevas (apoderamiento, hoja de encargo, MASC), un abogado colegiado las revisa.
- **Landing:** no cambia. No promete el sprint ni el Nivel 2 en presente.
- **Contenido:** el tramo de despachos se adelanta. Las piezas apoyan los mensajes directos, no al revés.
- **Fuera:** PMM-OS, Slack, Telegram, n8n, publicación automática, correo masivo, extracción de facturas como oferta (mercado de commodity, no es la tesis).

## Abierto para Diego

1. ¿Hay un contacto o despacho candidato en Pamplona o Logroño? Si lo hay, se empieza por ahí.
2. ¿Quién va al despacho en la semana 2?
3. ¿Qué abogado colegiado revisa las reglas nuevas?
4. Precio de fundador del piloto: lo fija Diego y no se escribe en esta raíz.
