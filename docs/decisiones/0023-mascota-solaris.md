---
id: ADR-0023
type: decision
title: "Solaris, la mascota dorada: presencia sutil en landing y producto"
status: validating
owner_role: product
links: ["[[ADR-0014]]", "[[ADR-0022]]", "[[F06]]"]
evidence: ["raw/sessions/2026-11-14_cofundador_mascota.md"]
updated: 2026-11-14
---

# ADR-0023 · La mascota Solaris

- Estado: propuesta. Diego decidió el 14/11 el uso y las tres opciones de abajo; falta ver el resultado en local y fusionar.
- Contexto: Diego encargó un kit de mascota (`mascota/solaris/`, v1.0): Solaris, una esfera dorada con ojos oscuros y un aura que la rodea, con siete estados, versión micro, versión para fondo claro y favicons. El kit trae un segundo personaje negro, sin nombre, que no se usa. Pide usar a Solaris de forma animada, con sensación de 3D y sutil, en la web y en el producto.

## Opciones decididas

| Pregunta | Elegido | Descartado |
|---|---|---|
| Logo y favicon | El favicon pasa a la mascota; el logo de cabecera sigue siendo el sol plano | Mascota también en la cabecera; mascota solo como ilustración |
| Color y tipografía | El oro del kit (`#F8C94F`) y sus colores viven solo en la mascota; la interfaz sigue con `solar` y Schibsted Grotesk | Migrar la interfaz a los tokens y fuentes del kit |
| Técnica del 3D | SVG en línea con la geometría del kit: el aura pasa por detrás y por delante del cuerpo, más parallax mínimo con el puntero | WebGL con three.js (+150 KB, modelado desde cero, peor en móvil) |

## Decisión

Un componente, `SolarisMascota`, con la misma copia en `product/components/` y `landing/src/components/`. Tres apariciones, una por pantalla como mucho:

1. **Caja de pregunta del producto** (Inicio y Preguntar), a 30 px en versión micro. Sustituye a la bola dorada que ya había. Pasa a «pensando» (el aura se inclina y oscila, los ojos miran arriba) **solo mientras hay una consulta en curso** (principio 4).
2. **Bienvenida del producto**, a 44 px junto al saludo, con flotación lenta.
3. **Hero de la landing**, a 72 px donde nace el haz de luz, con entrada por desenfoque, flotación, parpadeo y ojos y aura que siguen al puntero unos píxeles. Sin seguimiento en pantallas táctiles.

Con `prefers-reduced-motion` todo queda quieto. Es decorativa (`aria-hidden`): el texto de al lado ya dice lo que hay.

## Consecuencias

- El dorado deja de ser solo prueba o acción (skill `direccion-visual`). La excepción es la mascota y se limita a una aparición por pantalla.
- Estados del kit sin usar todavía: escuchando, hablando, logrado, error y pausa. «Logrado» al aprobar en Revisar sería el siguiente candidato, si se ve que suma.
- El favicon del producto incluye `icon.svg`. Los PNG del kit son RGB sobre fondo `#17110A`, no transparentes.
- Vídeos, capturas de la landing y `video/` no llevan la mascota. Si se quiere en ellos, va en una pieza aparte.
- El personaje negro y las primeras pruebas (`mascota/favicon/`, `mascota/Isotipo principal-html/`) no se versionan.
