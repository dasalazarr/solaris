---
id: ADR-0022
type: decision
title: "Inicio con estado vivo y pantallas compuestas con piezas comunes"
status: validating
owner_role: product
links: ["[[ADR-0015]]", "[[ADR-0021]]", "[[F06]]"]
evidence: ["raw/sessions/2026-11-14_cofundador_inicio-vivo.md"]
updated: 2026-11-14
---

# ADR-0022 · Inicio y piezas comunes

- Estado: propuesta. Construida y fusionada en illariumcore#30 el 14/11; Vercel completó el despliegue. Falta que Diego la acepte o la corrija.
- Contexto: tras la bienvenida, el espacio abría en Preguntar con una respuesta ya escrita. Cada pantalla tenía su título, su ancho y sus controles, y ninguna resumía el estado. Diego pide, con ElevenLabs como referencia, un inicio que resuma el estado, enseñe los procesos habilitados, ponga la pregunta en primer plano y dé sensación de sistema vivo.

## Opciones

- **A. Retocar Preguntar** para que haga de portada. Poco código, pero mezcla preguntar con resumir y no resuelve la disparidad entre pantallas.
- **B. Pantalla Inicio y piezas comunes.** Una superficie nueva que solo compone datos que ya existen, y un fichero de piezas (`ui.tsx`) con el que se montan todas.
- **C. Panel configurable por espacio.** Más de lo que pide un piloto (principio 5).

## Decisión

**B.**

- **Inicio** es la pantalla de entrada: caja de pregunta, estado del proceso, la siguiente decisión, procesos habilitados y última actividad. Preguntar desde Inicio lleva a Preguntar, donde está la evidencia.
- **Lo «vivo» es dato, no adorno.** Las cifras salen del motor y de la cola (`lib/home.ts`), cambian al decidir y el punto que late solo acompaña a algo recién calculado. En un espacio que guarda, de un proceso sin abrir no se enseñan cifras (principio 4).
- **Piezas comunes:** cabecera de pantalla, panel, selector, botones y caja de pregunta. Cada pantalla se titula como en el menú y explica en una frase para qué sirve.
- **Dictamen de regla en un bloque:** la regla en una frase y, plegada, la lógica que ejecuta el motor (`describeLogic`). Antes se enseñaba `expression`, un texto escrito a mano que en R-03 no coincide con la lógica evaluada.

## Consecuencias

- Una pantalla nueva se monta con las piezas y hereda formato. Los botones de dentro de los paneles aún no usan las constantes comunes.
- La barra móvil pasa de cinco a seis entradas; cabe a 375 px.
- El vídeo (`video/src/Cruza.tsx`) todavía rotula «Cómo lo evalúa el motor» y las capturas de la landing son del diseño anterior: hay que decidir si se rehacen.
- En Contrato se sigue viendo `expression`. Queda por decidir si las plantillas la regeneran desde la lógica.
- Sin medir: no hay tráfico. Sin probar con lector de pantalla.
