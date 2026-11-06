---
name: video-funcional
description: Crea o actualiza vídeos funcionales de Solaris en Remotion (video/). Guarda el input, escribe el brief, reutiliza efectos y datos del producto, y pasa los gates. Úsalo cuando pidan vídeos, clips o animaciones de una función, o adaptar un post o un guion a vídeo.
---

# Vídeo funcional

Lee `video/README.md`. El ejemplo completo es `video/briefs/2026-11-06-compras.md`.

## Procedimiento

1. **Guarda el input** tal cual en `raw/research/AAAA-MM-DD_*.md`. Es evidencia, no copy aprobado.
2. **Contrasta antes de escribir** con `docs/decisiones/0010-*`, `0012-*`, `docs/guion-demo-90s.md` y `product/lib`. Un post o un brief puede pedir lo que el producto no hace.
3. **Escribe el brief** desde `video/briefs/_plantilla.md`, con la tabla de qué se aplica y qué no. Di a Diego lo que no se aplica y por qué.
4. **Construye sobre lo que hay:** `src/Plantilla.tsx`, `fx.tsx`, `ventana.tsx`. Otro proceso lee sus datos de `product/lib` igual que `datos.ts`, con una comprobación que haga fallar el render si el guion deja de ser cierto.
5. **Una idea por plano.** Leyenda corta, de tú, con la cámara en lo que dice. Efecto al servicio de la función, no de adorno.
6. **Revisa fotogramas** con `npm run contacto` antes de renderizar todo, y en los dos formatos.
7. **Pasa el gate y renderiza:** `npm run gate`, luego `npm run render:all` en segundo plano.

## Innegociables

- Etiqueta `<Entorno />` en todo plano de producto (principio 4).
- Ningún dato escrito a mano si existe en `product/lib`.
- Sin nombres reales combinados con datos inventados. Mientras siga abierta H7, proveedores solo por identificador.
- Colores y tipografías de `src/tokens.ts`. Si cambia `docs/marca.md`, cambia aquí.
- La publicación la confirma Diego. Di siempre qué no has visto ni oído: un agente no valida el sonido ni el ritmo en tiempo real.

## Errores ya cometidos

- **Hook después de un `return`:** la pantalla rompe solo cuando cambia de rama, y unas hojas de contacto que muestrean después no lo ven. Los hooks van antes de cualquier `return`.
- **Hojas de contacto con tamaños mezclados:** ffmpeg reinicia el mosaico. Una hoja por formato.
- **Zoom igual en 16:9 y 4:5:** recorta lo ancho. Usa `zv` en las claves de cámara y centra en `x: 798`.
- **Texto sobre el sol o leyendas de dos líneas en 16:9:** tapan el foco. Separa el sol y acorta la frase.
- **Sonoridad:** el render bruto sale en −23 LUFS. `render-all.mjs` lo normaliza; no publiques un MP4 sacado de otro comando sin hacerlo.
