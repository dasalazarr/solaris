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
- Favicon (desde 2026-11-14, [[ADR-0023]]): la mascota Solaris en versión micro, del kit `mascota/solaris/solaris/favicon/` (`landing/public/solaris/`; copia en `product/app/`: `favicon.ico`, `icon.svg`, `icon.png`, `apple-icon.png`). Es distinto del logo de interfaz, que sigue plano y definido arriba. Si se cambia, cámbialo en los dos repositorios.
- `theme-color`: `#0d0f14`.

## Mascota

Solaris, la esfera dorada con aura ([[ADR-0023]]). Kit completo y reglas de uso en `mascota/solaris/README.md`.

- Componente `SolarisMascota` (`product/components/`, copia en `landing/src/components/`), con sus estilos `.sol-*` en `globals.css` de cada repositorio.
- Sus colores (`#F8C94F` cuerpo, `#FFE08A` aura, `#1A1206` ojos) solo viven en la mascota. No son tokens de interfaz.
- Una aparición por pantalla como mucho: caja de pregunta y bienvenida del producto, hero de la landing.
- Estados honestos: «pensando» solo mientras hay una consulta en curso.
- Movimiento: parpadeo cada 5,5 s, flotación de 6 s y parallax de pocos píxeles. Todo se para con `prefers-reduced-motion`. Nada de rebotes.
- No se deforma, no se rota entera, no lleva boca ni extremidades y el aura no se pone sobre la cabeza.

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
