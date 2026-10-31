# 0002 · Una sola identidad visual: el sol de Solaris

- Fecha: 2026-10-31
- Estado: aceptada

## Contexto

La landing usaba un sol dorado como logo de Solaris, una paleta propia (`ink`, `solar`, `lavanda`…) y tres familias tipográficas. El producto usaba como logo de Solaris el hexágono violeta de Illarium (un PNG de 1024 px), no tenía favicon y escribía los colores a mano: hex sueltos y la escala `amber`/`purple` de Tailwind. Quien pasaba de la landing a la demo veía dos marcas distintas.

## Opciones

1. El sol en todas partes. Illarium solo como firma de texto.
2. El sol como logo, con el hexágono de Illarium pequeño como sello.
3. El hexágono en todas partes, cambiando también la landing.

## Decisión

Opción 1. El sol dorado es Solaris en la landing y en el producto. Illarium aparece como «un producto de Illarium». Los tokens de la landing son la referencia y el producto los copia literalmente. El violeta pasa a ser `lavanda` y queda reservado para la ontología.

## Consecuencias

- Una sola marca de producto, con una única acción primaria (`solar`) en los dos sitios.
- `docs/marca.md` es la fuente de verdad. Cambiar un token supone cambiarlo en los dos repositorios.
- El hexágono de Illarium sale del producto. Si Illarium necesita su logo (web de la consultora, propuestas), se usa allí, no en Solaris.
- Los grises neutros del producto (`stone-*`) se mantienen: no llevan marca y cambiarlos sería ruido.
