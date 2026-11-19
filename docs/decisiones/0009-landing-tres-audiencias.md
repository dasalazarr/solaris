---
id: ADR-0009
type: decision
title: "La landing sirve a clientes, aliados e inversores"
status: accepted
owner_role: product
links: ["[[ADR-0004]]", "[[ADR-0007]]", "[[F06]]"]
evidence: ["docs/fundacional.md", "docs/sinergia-landing-producto.md"]
updated: 2026-11-03
---

# ADR-0009 · La landing sirve a clientes, aliados e inversores

- Estado: aceptada (2026-11-03, decisión de Diego)
- Contexto: el PRD de la landing (§1) le daba un único objetivo: que un responsable de proceso pida una demostración. Diego quiere que la misma página también explique la visión del proyecto (la ontología de procesos), enseñe la demo y sirva a aliados estratégicos (consultoras, canal) y a inversores. Hoy esas dos audiencias no tienen ni mensaje ni salida, y la sección que más se acercaba a la visión («Una base, muchas vistas») prometía la Visión v2 como si existiera (auditoría del 02/11, C3).

## Opciones

1. **Mantener un único objetivo.** Aliados e inversores llegan por contacto directo. Es lo más simple, pero la página no cuenta la visión y obliga a explicarla de palabra cada vez.
2. **Tres páginas** (`/clientes`, `/aliados`, `/inversores`). Mensajes a medida, pero son tres relatos que mantener coherentes con el producto, con un equipo de una persona y sin tráfico medido que lo justifique.
3. **Un solo relato con tres salidas.** La misma página explica qué es la ontología de procesos, la enseña en la demo y separa lo que existe hoy de lo que viene después. Al final, cada audiencia tiene su salida; la llamada principal sigue siendo «Solicitar demostración».

## Decisión

Opción 3. Un relato, tres salidas:

- **Clientes:** «Solicitar demostración» (sin cambios; sigue siendo la acción principal).
- **Aliados:** «Cómo trabajamos» (método con Illarium y packs por sector).
- **Inversores:** «Material para inversores», solo bajo petición mediante el mismo formulario.

El formulario añade un campo «Perfil» (cliente, aliado o inversor) que viaja a `/api/solicitud` del producto y como propiedad del evento de Umami, para medir qué audiencia llega.

La visión se cuenta con tres etiquetas tomadas de la tabla §6 de `fundacional.md`: **Hoy** (existe en el producto), **Siguiente** (comprometido para el piloto) y **Visión** (hipótesis de la Visión v2, siempre rotulada como tal).

## Consecuencias

- Regla de copy reforzada: lo que está en presente existe en el producto; lo demás va en futuro y con etiqueta. Hablar a inversores no permite cifras, clientes, pilotos, valoración ni precios no publicados.
- El material para inversores no se publica en la página: se envía a quien lo pide. Hasta que exista, la salida promete solo una conversación.
- `/api/solicitud` del producto debe aceptar `perfil` antes de publicar el campo en la landing. Ese cambio es de product-steward/dev.
- El PRD de la landing cambia §1 (propósito) y §3 (audiencias); la estructura de secciones (§5) cambia en el PR `feat/vision-y-audiencias`, tras el visto bueno de Diego a la propuesta.
- Riesgo: diluir el mensaje principal. Mitigación: el hero y la demo siguen hablando al responsable de proceso, y las salidas de aliado e inversor viven al final. Con Umami se podrá comprobar que las solicitudes de clientes no bajan (línea base de 2 semanas antes de cualquier experimento).
