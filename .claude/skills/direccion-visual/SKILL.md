---
name: direccion-visual
description: Gusto, técnica y gramática de movimiento de Solaris para la landing (hero, capturas animadas) y los vídeos comerciales en Remotion. Úsalo antes de diseñar o animar cualquier pieza visual de Solaris, o cuando pidan «algo como el hero», «con la calidad del vídeo» o representar una función nueva con el mismo lenguaje.
---

# Dirección visual de Solaris

No es un catálogo para copiar planos. Es el lenguaje con el que Solaris se enseña: cada pieza nueva cuenta **otro contenido** con **la misma gramática**. Si una pieza nueva se parece al hero porque reutiliza sus frases y su pregunta, está mal; si se parece porque usa la misma luz, el mismo ritmo y la misma forma de probar, está bien.

Procedimiento de producción (brief, datos, gates, render): skill `video-funcional`. Tokens: `docs/marca.md`. Esta skill decide **cómo se ve y cómo se mueve**.

## La idea en una frase

**Luz solar sobre tinta, documento sobre hoja.** El fondo es noche (`ink`); el producto es papel (`sheet`) que flota en él; la luz dorada (`solar`) solo cae donde hay prueba. Todo lo demás se aparta.

## Gusto: qué nos gusta y qué no

| Sí | No |
|---|---|
| Interfaz real del producto, reconstruida con su menú y sus textos (`ventana.tsx`, `ProductWindow.tsx`) | Mockups genéricos, dashboards inventados, iconos de stock |
| Una idea por plano, una frase por leyenda | Dos ideas a la vez, leyendas de dos líneas en 16:9 |
| El dorado como foco y prueba: cita, regla, acción pendiente, cursor | Dorado decorativo, degradados de arcoíris, más de un acento |
| Movimiento con peso: entra rápido, se asienta lento | Rebotes, elásticos, giros gratuitos, transiciones de PowerPoint |
| Desenfoque como profundidad y como entrada (blur → nítido) | Sombras duras, bordes de neón, glassmorphism |
| Serif itálica dorada para la palabra que importa («*con contrato*») | Negritas, mayúsculas gritadas, emojis |
| Mono para lo técnico y verificable: `R-03`, `PROV-018`, «pág. 4» | Mono como adorno |
| Grano fino, viñeta suave, luz que respira | Fondos planos sin vida o partículas de ciencia ficción |
| Silencio y aire: el plano respira antes de cortar | Rellenar cada fotograma |
| Lo verificable se ve: entorno, «datos de muestra», cita exacta | Afirmar sin enseñar la fuente |

Registro: presentación de Apple con contenido de auditor. Sobrio, preciso, cálido. Nunca épico, nunca juguetón.

## Paleta en movimiento

- `ink #0d0f14` fondo; `ink-2` tarjetas oscuras; `sheet #fbfaf7` toda superficie de producto o documento.
- `solar #f2b544` es **la única** luz. Aparece en: halo del sol, barra de evidencia, haz cita→fuente, onda del clic, caret, chip activo, la acción primaria. Si algo dorado no señala una prueba o la acción, sobra.
- Contrapunto frío: un velo lavanda (`rgba(75,58,168,.16)`) arriba a la izquierda del fondo. Da profundidad sin competir.
- Estados semánticos solo dentro de la interfaz: `arcilla` incumple, `salvia` conforme, `niebla` informativo, `solar-soft` pendiente. Nunca como fondo de escena.
- Sobre oscuro, texto secundario en blanco al 60–76 %. Sobre `sheet`, `ink` al 62 % (`c.muted`).

## Tipografía en movimiento

- Titulares: Schibsted Grotesk 600, tracking −0,025 a −0,035 em, interlineado 1,02–1,08, `text-wrap: balance`.
- La palabra clave va entre asteriscos en `Titular` (`"tengan *contrato.*"`): pasa a Newsreader itálica 400 con degradado dorado (`solarHover → solar → #ffdf9e`) recortado al texto. Una por titular, como máximo.
- Eyebrow: JetBrains Mono, mayúsculas, tracking .14 em, en `solar`. Formato `01 · Cruza`.
- Citas y documentos: Newsreader. Identificadores y entorno: mono.
- Tamaños de vídeo (1920 × 1080 / 1080 × 1350): titular 104–136, leyenda 64–66, cierre secundario 50–52, eyebrow 26–36.

## La firma: siete movimientos

Son los gestos que hacen que algo «se vea Solaris». Están implementados; úsalos antes de inventar otro.

| Gesto | Qué significa | Vídeo (`video/src/fx.tsx`) | Web (`landing/src/app/globals.css`) |
|---|---|---|---|
| **Palabra a palabra con desenfoque** | La idea se enfoca | `Titular`: cada palabra sube 0,34 em, blur 14 → 0, escala .97 → 1, en 26 fotogramas, desfase 3 (leyendas 2) | `.word`: 0,25 em, 520 ms, desfase 40 ms |
| **Barra de evidencia** | Esto está probado | `Evidencia`: barra `solar` de 0,42 em al 88 %, barrida palabra a palabra | `.evidence.is-lit`, 700 ms con 200 ms de retraso |
| **Haz cita → fuente** | De dónde sale | `Haz`: curva cuadrática dorada con halo y punta luminosa | (no hay; en web el panel se abre y el fragmento se ilumina) |
| **El sol** | Marca y amanecer de la tesis | `SolGrande`: núcleo, anillo, halo, destello anamórfico, respiración ±1,2 % | `.sunbeam`: cono y elipse dorados con blur 8 px, deriva de 20 s |
| **Cámara sobre la ventana** | Te llevo a lo que importa | `Camara`: perspectiva 2600, claves `{f,x,y,z,zv,rx,ry}`, deriva ±0,4 % | Sin cámara: la ventana es fija y lo que cambia es el contenido |
| **Profundidad de campo** | Esto no importa ahora | `Foco d`: opacidad −62 %, blur 3,5 px, desaturación | `.blur-in` para entradas de sección |
| **Destello en el cristal** | Algo acaba de quedar listo | `Destello`: barrido diagonal 112° en `screen` | (no se usa en web) |

Complementos: `Cursor` con onda dorada al clic y pulsación de −16 %; `Aparece` para respuestas que se escriben; caret dorado parpadeando cada 8 fotogramas; `Fundido` entre escenas (blur 12 px + empuje de escala 2–3,5 %); `Grano` (5,5 % overlay, cambia cada 2 fotogramas) y `Vineta`.

## Ritmo y curvas

- **SALIDA** `bezier(.16, 1, .3, 1)`: entradas. Llega rápido y se posa.
- **SUAVE** `bezier(.65, 0, .35, 1)`: cámara, cursor, salidas, fundidos.
- Web: `--ease-solar: cubic-bezier(.2, .7, .2, 1)`; equivalente templado de SALIDA.
- Resortes solo para la marca del cierre (`useResorte`, damping 18–20). Nunca para interfaz.
- A 30 fps: entrada de bloque 12–26 f; salida de titular 14 f (sube 22 px y se desenfoca 16 px); una leyenda vive 60–75 f; un capítulo 74 f; apertura 220 f.
- Escalonar siempre: palabras 2–3 f, filas de lista 8 f, documentos 7 f. Nada aparece todo a la vez.
- La cámara se mueve entre ideas, no durante la lectura. Si hay texto entrando, la cámara está quieta o deriva.

## Composición

- Ventana de producto 1400 × 860 a escala: 74 % del ancho en 16:9, 94 % en 4:5; centrada en vertical al 62 % (61 % en 4:5). Sombra con halo dorado abajo (`0 60px 160px -40px rgba(242,181,68,.34)`).
- La leyenda vive arriba, sobre un velo de `ink` que cubre el 25 % superior. Así se lee sobre la ventana sin taparla.
- En 4:5 usa `zv` en las claves de cámara y centra en `x: 798`; lo ancho no cabe con el mismo zoom.
- El sol nunca detrás del texto: sol al 30 % de alto, titular al 50 %.
- `<Entorno />` abajo a la izquierda en todo plano de producto. Es contenido, no letra pequeña.

## Recetas (estructura, no texto)

### Apertura de tesis (el «hero» en vídeo, `Titulos.tsx · Apertura`)
1. Negro → el sol se enciende (f 4–70) y con él la luz del fondo. Golpe grave en f 2.
2. Primera frase: el problema, palabra a palabra (f 34). Sale con blur (f 112) mientras el sol sube y se atenúa. Soplo suave.
3. Segunda frase: la tesis, con la palabra clave en serif dorada (f 124). Se queda.
Para otra pieza: cambia el problema y la palabra clave; conserva luz → problema → tesis.

### Captura en bucle (el hero de la landing, `HeroCapture.tsx`)
Bucle de 9 s sobre la pantalla real: la pregunta se teclea (0,3–1,9 s) → «Buscando en N documentos…» (2,1–2,8 s) → respuesta con chips de cita (2,8–4,1 s) → se abre el panel de evidencia (4,9 s) → se ilumina el fragmento (5,5 s) → aparece la regla y la acción que pide aprobación (6,3 s) → pausa de lectura hasta 9 s.
Para otra función: misma curva **pregunta → búsqueda → respuesta → prueba → acción pendiente de una persona**. Cambia la pantalla (Huecos, Revisar), no la curva.

### Plano de función (vídeos `Cruza`, `Detecta`, `Firma`)
Leyenda que dice la idea → cursor o tecleo que la provoca → la interfaz responde → cámara al detalle → gesto de firma (barra, haz, destello) → `Foco` aparta lo demás → siguiente idea.

### Problema (`Titulos.tsx · Problema`)
Hojas `sheet` flotando en 3D con profundidad y deriva; una se adelanta, se endereza y se marca en `arcilla`. El resto se desenfoca. Enseña el hueco sin decir «riesgo».

### Cierre
Tesis corta en titular grande, subtítulo en blanco al 76 % peso 400, logo con resorte, «un producto de Illarium» en mono al 60 %, y «Caso ficticio con datos de muestra» abajo.

## Web frente a vídeo

| | Landing | Vídeo |
|---|---|---|
| Motor | CSS (transiciones, keyframes) y un temporizador por estado | Todo derivado de `useCurrentFrame()`; nada de transiciones CSS |
| Movimiento reducido | Obligatorio: `prefers-reduced-motion` muestra el estado final; botón de pausa; se para fuera de pantalla o con la pestaña oculta | No aplica, pero hay versión 4:5 y sonido opcional |
| Accesibilidad | `role="img"` con `aria-label` que narra el bucle entero; contraste AA | Leyendas legibles sin sonido |
| Estabilidad | Reserva el tamaño final (texto invisible) para CLS 0 | Reserva el tamaño para que la cámara no salte |
| Escala | Textos 10,5–15 px dentro de la ventana; ventana 14 px de radio | Los mismos elementos a ×1,6 aprox.; radio 22 px |

## Lecciones aprendidas

- **La calidad sale de la interfaz verdadera**, no de los efectos. Los planos que funcionan son los que reproducen el menú y los textos reales del producto con sus datos (`datos.ts` desde `product/lib`).
- **El dorado se gasta.** Cuando todo brilla, la cita deja de destacar. Un brillo por plano.
- **Desenfoque mejor que fundido a negro.** Entrar y salir con blur da continuidad; el corte seco o el negro rompen el tono.
- **Texto y cámara no se mueven a la vez.** O se lee o se viaja.
- **Las leyendas largas se comen el foco.** En 16:9 una línea; si no cabe, la frase es demasiado larga, no la letra demasiado grande.
- **El sol estorba si toca texto.** Sepáralos o atenúa el sol cuando entra la frase.
- **El mismo zoom no sirve en 16:9 y 4:5.** Claves `zv` y centro propio.
- **Revisa fotogramas, no la idea.** Hojas de contacto por formato antes de renderizar; detectan lo que el gate de tipos no ve.
- **En web, el CLS se cuida desde el diseño:** todo lo que aparece ocupa su sitio desde el principio (opacidad, no montaje).
- **El sonido acompaña el gesto:** golpe grave en la luz, soplo en la transición, tic en el tecleo, campana en la aprobación. Sintetizado propio, normalizado; un agente no valida cómo suena.

## Antes de entregar una pieza

- [ ] ¿Se entiende sin sonido y sin leer la letra pequeña?
- [ ] ¿Cada plano tiene una sola idea y un solo brillo dorado?
- [ ] ¿La interfaz es la del producto (menú, textos, datos), no una invención?
- [ ] ¿Se ve el entorno y que los datos son de muestra?
- [ ] ¿Las curvas son SALIDA/SUAVE (o `--ease-solar`) y nada rebota?
- [ ] ¿Revisado en 16:9 y 4:5 (vídeo) o en 375 px y escritorio con movimiento reducido (web)?
- [ ] ¿La palabra en serif dorada es la que de verdad importa?
- [ ] ¿Lo que se enseña lo hace hoy el producto v1? Si no, no entra.
