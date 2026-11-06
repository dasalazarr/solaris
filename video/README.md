# Vídeos funcionales de Solaris

Remotion 4. Tres funciones clave y una película que las une, en 16:9 y 4:5.

| Pieza | Función | Duración |
|---|---|---|
| `Cruza` | Preguntar: respuesta citada, párrafo exacto y «Sin fuente» | 30 s |
| `Detecta` | Huecos: cruce de reglas y objetos, tres huecos y un dato por validar | 28 s |
| `Firma` | Revisar: rol bloqueado, borrador editado, aprobación, registro y hueco cerrado | 31 s |
| `Pelicula` | Tesis, problema, las tres funciones y cierre | 92 s |

```bash
npm install
```

```bash
npm run dev
```

```bash
npm run render:all
```

Los MP4 salen en `out/` (no se versionan). Un solo vídeo: `node scripts/render-all.mjs Firma 4x5`. Hoja de contacto: `node scripts/stills.mjs "Firma-16x9:100,300" nombre`.

## Hacer una pieza nueva

1. Guarda el input tal cual en `raw/research/`.
2. Copia `briefs/_plantilla.md` y decide qué se aplica y qué no.
3. Copia `src/Plantilla.tsx`, lee los datos desde `src/datos.ts` y añade la pieza a `PIEZAS` en `src/Root.tsx`.
4. Revisa con `npm run contacto -- "Pieza-16x9:100,200" nombre` en ambos formatos, por separado.
5. Pasa `npm run gate` y renderiza. Una persona lo ve con sonido antes de publicar.

El ejemplo completo es `briefs/2026-11-06-compras.md`. El procedimiento y los errores ya cometidos están en la skill `video-funcional`.

## Estructura

| Ruta | Qué es |
|---|---|
| `src/tokens.ts`, `src/fonts.ts` | Marca, según `docs/marca.md` |
| `src/fx.tsx` | Efectos: cámara, titulares, destello, haz, cursor, evidencia, sol y sonido |
| `src/ventana.tsx` | Marco de producto |
| `src/datos.ts` | Puente con `product/lib` y comprobaciones del guion |
| `src/Cruza.tsx`, `Detecta.tsx`, `Firma.tsx`, `Titulos.tsx` | Escenas |
| `src/Plantilla.tsx` | Base para una función nueva |
| `briefs/` | Plantilla de brief y briefs de cada serie |
| `scripts/` | Sonido, render, hojas de contacto y vocabulario |

## Reglas

- **Los datos no se copian.** `src/datos.ts` importa el caso de muestra y el motor de `product/lib`. Si el producto cambia y el guion deja de ser cierto, el render falla.
- **Vocabulario de ADR-0010 y tuteo de ADR-0012.** Nada de «sello», «inmutable», «reglas vivas» ni «pack».
- **El entorno se ve siempre** (principio 4): la etiqueta «Demo en la nube · datos de muestra» está en todo plano de producto.
- **Sin nombres de proveedor**, solo `PROV-018` y `PROV-024`, hasta comprobarlos en el registro mercantil (H7 en `plan/STATUS.md`).
- **Sonido propio:** `scripts/sfx.mjs` lo sintetiza al instalar; no hay audio de terceros ni WAV versionados.

Licencia de Remotion: gratis para personas y empresas de hasta 3 empleados. A partir de 4 hace falta licencia de empresa (`node_modules/remotion/LICENSE.md`).
