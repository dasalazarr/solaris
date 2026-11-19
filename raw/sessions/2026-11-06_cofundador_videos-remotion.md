# 2026-11-06 · cofundador · vídeos funcionales en Remotion

**Pedido:** vídeos funcionales de Solaris en Remotion, estilo presentación de Apple, centrados en funciones clave, con la plantilla Cruza · Detecta · Firma del post de Compras.

**Hecho:** `video/` con Cruza, Detecta, Firma y Película en 16:9 y 4:5; ADR-0014. Datos importados de `product/lib`; el render falla si los huecos cambian.

**Decisiones:**
- Se conserva la estructura 01 · 02 · 03 del post, sin «pack», «sellado», «se ejecutan solas», «se auditan solos», «un clic» ni «cientos» (ADR-0010, ADR-0012).
- Proveedores solo por identificador (H7 sin resolver).
- Fondo de hoja con el token `sheet` de la marca, no el crema `#F8F6F0` del post.
- Sonido sintetizado propio.

**Gate:** `tsc --noEmit`; hojas de contacto de fotogramas en ambos formatos; sonoridad medida con ffmpeg. Sin escuchar el audio.

**Aprendido:** un `return` antes de un hook rompe el render solo en los fotogramas donde cambia de rama; las hojas de contacto no lo detectaron porque solo muestreaban después.

## Infraestructura para futuras piezas

Diego aprueba el resultado y pide guardar el input y la infraestructura como base. Se añaden: input en `raw/research/`, brief y plantilla en `video/briefs/`, `src/Plantilla.tsx`, comprobación de vocabulario, `npm run gate` y la skill `video-funcional`.
