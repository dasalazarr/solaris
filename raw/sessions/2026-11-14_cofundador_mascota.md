---
fecha: 2026-11-14
rol: cofundador
tema: Solaris, la mascota dorada, en landing y producto
---

# La mascota Solaris

## Tarea
Diego: la mascota y la marca están en `mascota/solaris`. Usar a Solaris (dorado) como mascota, animada y con sensación de 3D, de forma sutil en la web y en el producto.

## Decisiones de Diego (14/11)
- El favicon pasa a la mascota; el logo de cabecera se queda.
- El oro del kit solo en la mascota; la interfaz sigue con `solar` y Schibsted.
- SVG en línea con profundidad, no WebGL.

## Qué se hizo
- `SolarisMascota` en producto y landing (misma copia): geometría del kit, estados reposo y pensando, flotación, parpadeo y parallax con el puntero.
- Producto, rama `feat/mascota`: la caja de pregunta (Inicio y Preguntar) sustituye la bola dorada por la mascota micro, que piensa mientras hay consulta; bienvenida con la mascota junto al saludo; favicon, `icon.svg`, `icon.png` y `apple-icon.png` del kit.
- Landing, rama `feat/mascota`: mascota en el hero donde nace el haz, con entrada por desenfoque y seguimiento del puntero; favicons del kit en `public/solaris/`.
- ADR-0023, `docs/marca.md` y una excepción en la skill `direccion-visual`.

## Verificación
- Producto: 299 tests, lint y build. Landing: lint (oxlint y tsc) y build.
- Navegador en local. Landing: hero en escritorio, seguimiento del puntero, iconos con 200 y 375 px sin scroll horizontal (sin seguimiento en táctil). Producto, con un código desechable (borrado al terminar): bienvenida, caja de pregunta en reposo y en «pensando» durante una consulta con la respuesta retrasada a mano, y vuelta a reposo al terminar.
- Sin probar: lector de pantalla, movimiento reducido en navegador (solo por CSS), producción y la respuesta real de Gemini.

## Qué falló
- En el hero, `blur-in` depende de un observador; la mascota habría podido quedar invisible. Se usa una entrada propia por CSS.
- En modo desarrollo, el giro del aura empezó con cerca de un segundo de retraso; sin comprobar en build.
