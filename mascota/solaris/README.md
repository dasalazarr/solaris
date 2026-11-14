# Mascotas Solaris · v1.0

Recursos para web de los dos personajes:

- **Solaris**: cuerpo dorado, ojos oscuros (`solaris/`)
- **Personaje negro**: cuerpo negro, ojos de luz (`negro/`). El nombre está pendiente: cuando se decida, renombra la carpeta y los archivos `negro-*`.

Abre `vista-previa.html` en el navegador para ver todos los archivos en uso.

## Estructura

```
mascotas-solaris-v1.0/
├── README.md
├── vista-previa.html          página de prueba con todos los recursos
├── tokens/
│   ├── colores.css            variables CSS + animación de parpadeo y flotación
│   └── tokens.json            los mismos valores, para JS o herramientas de diseño
├── solaris/
│   ├── svg/
│   │   ├── solaris.svg              versión principal (≥ 64 px)
│   │   ├── solaris-animado.svg      parpadea y flota; funciona dentro de <img>
│   │   ├── solaris-micro.svg        para ≤ 32 px: sin brillos, anillo y ojos más gruesos
│   │   ├── solaris-fondo-claro.svg  anillo más oscuro y sombra, para fondos crema o blancos
│   │   └── estados/                 reposo, escuchando, pensando, hablando, logrado, error, pausa
│   ├── png/                   1024, 512, 256, 128 (principal) · 64, 32 (micro), fondo transparente
│   └── favicon/               favicon.ico (16/32/48), favicon.svg, apple-touch-icon, icon-192/512, site.webmanifest
└── negro/                     la misma estructura
```

## Qué archivo usar

| Uso | Archivo |
|---|---|
| Hero, landing, ilustración | `svg/<personaje>.svg` o `-animado.svg` |
| Avatar de agente en chat (≥ 40 px) | `svg/<personaje>.svg` |
| Avatar pequeño, iconos de lista (≤ 32 px) | `svg/<personaje>-micro.svg` |
| Fondo claro | `svg/<personaje>-fondo-claro.svg` |
| Estado del agente en la interfaz | `svg/estados/<personaje>-<estado>.svg` |
| Redes, correos, sitios que no aceptan SVG | `png/` |
| Pestaña del navegador y móvil | `favicon/` |

Usa siempre el SVG en la web; el PNG solo donde no se acepte SVG.

## Favicon

Copia el contenido de `favicon/` a la raíz del sitio y añade en el `<head>`:

```html
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
```

## Estados del agente

| Archivo | Cuándo |
|---|---|
| `reposo` | sin actividad |
| `escuchando` | el usuario escribe o habla |
| `pensando` | esperando la respuesta del modelo |
| `hablando` | la respuesta se está mostrando |
| `logrado` | tarea completada |
| `error` | fallo o sin conexión |
| `pausa` | sesión inactiva |

Para cambiar de estado, cambia el `src` de la imagen. Si se quieren transiciones suaves entre estados (el anillo girando de una posición a otra), hay que incrustar el SVG en línea y animar sus atributos; los archivos comparten la misma geometría para que eso sea posible.

## Reglas

- Tamaño mínimo: 16 px con la versión micro; la versión principal, desde 64 px.
- Zona de respeto: un cuarto del ancho del cuerpo alrededor del anillo.
- No deformar, no rotar el personaje entero, no añadir boca ni extremidades.
- No poner el anillo por encima de la cabeza: dejaría de leerse como aura y pasaría a ser una aureola.
- Sobre el dorado, el texto va en `#1A1206`, nunca en blanco.
- Respeta `prefers-reduced-motion`: los SVG animados y `colores.css` ya lo hacen.

## Colores y tipografía

En `tokens/colores.css` (variables `--solaris-*` y `--negro-*`) y `tokens/tokens.json`.
Tipografía: Space Grotesk para titulares e Inter para texto, ambas en Google Fonts.
