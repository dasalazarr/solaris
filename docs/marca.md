# Marca Solaris

Fuente de verdad de la identidad visual. La landing (`landing/src/index.css`, `landing/src/components/ui.tsx`) es la referencia de implementación; el producto (`product/app/globals.css`, `product/components/SolarisLogo.tsx`) copia los mismos valores. Si cambias un token, cámbialo en los dos repositorios y aquí, en el mismo par de commits.

## Jerarquía

- **Solaris** es la marca de producto. Tiene logo propio: el sol dorado.
- **Illarium** es la empresa. Aparece solo como firma de texto: «un producto de Illarium», en mono, al 50–60 % de opacidad. No usamos el hexágono de Illarium dentro del producto ni en la landing.

## Logo

Sol de dos círculos concéntricos sobre cuadro de 26 × 26:

```svg
<svg width="26" height="26" viewBox="0 0 26 26" aria-hidden="true">
  <circle cx="13" cy="13" r="12" fill="none" stroke="#F2B544" stroke-opacity=".55" stroke-width="1"/>
  <circle cx="13" cy="13" r="7.5" fill="#F2B544"/>
</svg>
```

- Palabra: «Solaris», Schibsted Grotesk 600, 19 px, tracking −0,02 em.
- `tone="light"` (texto blanco) sobre fondos `ink`; `tone="dark"` (texto `ink`) sobre fondos claros.
- Favicon (desde 2026-11-05): sol dorado con brillo, en PNG y `.ico` con fondo transparente (`landing/public/solaris/`; copia en `product/app/`: `favicon.ico`, `icon.png`, `apple-icon.png`). Sin SVG: el arte es un raster y un SVG con PNG incrustado pesaba 2,9 MB. Es distinto del logo de interfaz, que sigue plano y definido arriba. Si se cambia, cámbialo en los dos repositorios.
- `theme-color`: `#0d0f14`.

## Color

| Token          | Valor     | Uso                                                                 |
|----------------|-----------|---------------------------------------------------------------------|
| `ink`          | `#0d0f14` | Fondo oscuro (hero, entrada), texto principal sobre claro           |
| `ink-2`        | `#151821` | Tarjetas sobre oscuro, bloques oscuros en la app                     |
| `ink-3`        | `#1e2230` | Hover sobre oscuro                                                   |
| `paper`        | `#f4f5f7` | Fondo claro de secciones y de la app                                 |
| `sheet`        | `#fbfaf7` | Hoja de documento (visor de evidencia)                               |
| `solar`        | `#f2b544` | **Única** acción primaria, resaltado de evidencia, foco             |
| `solar-hover`  | `#f6c565` | Hover de la acción primaria                                          |
| `solar-ink`    | `#8a5a00` | Texto/icono ámbar sobre claro                                        |
| `solar-soft`   | `#fbecc9` | Fondo suave ámbar (aprobación pendiente, fragmento citado)          |
| `lavanda` / `lavanda-ink` | `#eee9ff` / `#4b3aa8` | Ontología: primitivas, objetos, esquema, pack     |
| `salvia` / `salvia-ink`   | `#e3eedf` / `#1e6b3a` | Conforme, validado                                |
| `arcilla` / `arcilla-ink` | `#f6e1d8` / `#8c2a1f` | Bloqueo, incumplimiento de regla                  |
| `niebla` / `niebla-ink`   | `#dfe8f3` / `#23476e` | Información neutra                                |

Neutros: grises por opacidad de `ink` (landing) o escala `stone` de Tailwind (producto). No llevan marca.

### Contraste comprobado (WCAG 2.2 AA, texto normal ≥ 4,5:1)

| Par                          | Ratio  |
|------------------------------|--------|
| `ink` sobre `solar`          | 10,47  |
| `solar-ink` sobre blanco     | 5,93   |
| `solar-ink` sobre `solar-soft` | 5,06 |
| `lavanda-ink` sobre `lavanda`| 7,18   |
| `salvia-ink` sobre `salvia`  | 5,45   |
| `arcilla-ink` sobre `arcilla`| 6,76   |
| blanco sobre `lavanda-ink`   | 8,50   |

`solar` no se usa como color de texto sobre fondo claro (no pasa AA).

## Tipografía

| Rol        | Familia            | Uso                                                    |
|------------|--------------------|--------------------------------------------------------|
| Interfaz   | Schibsted Grotesk  | Todo el texto de interfaz y titulares                  |
| Documento  | Newsreader         | Citas y visor de evidencia; énfasis itálico en titulares de la landing («*con contrato*») |
| Técnico    | JetBrains Mono     | Identificadores, hashes, reglas (`R-03`), indicador de entorno, etiquetas |

- Landing: `@fontsource` autoalojado. Producto: `next/font/google`.
- Firma visual: el **resaltado de evidencia**, una barra `solar` de 0,42 em bajo el fragmento citado (`.evidence` en la landing).

## Forma

- Acciones primarias y píldoras: `rounded-full`.
- Tarjetas y ventanas: `rounded-lg` a `rounded-2xl`.
- Foco visible: contorno `solar` de 2 px con 2 px de separación.
- El indicador de entorno («Nivel 1 · Datos de muestra») se ve siempre, en todos los anchos (principio 4).
