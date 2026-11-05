# Solaris: PRD de la landing

Autor: Diego Andrés Salazar · Fecha: 31 oct 2026 · Producto: Solaris, de Illarium

> **Cambios sobre el texto original**
> - 2026-10-31 · §4: la firma pasa de «por Illarium» a «un producto de Illarium», para que coincida con el producto. Ver `decisiones/0002-identidad-visual-unica.md`.
> - 2026-11-04 · §5 (filas 6 y 7) y §9: cifra «de su organización», demo con Explorar y rol, y formulario con contexto. Ver `decisiones/0010-vocabulario-de-interfaz.md`.
> - 2026-11-03 · §1 y §3: la landing deja de tener un único objetivo; sirve a clientes, aliados e inversores con un solo relato y tres salidas. Se añade el inversor a las audiencias. Ver `decisiones/0009-landing-tres-audiencias.md`.

## 1. Propósito

La landing cuenta un solo relato: qué es Solaris (procesos con contrato sobre una ontología de siete primitivas), cómo funciona (la demo) y qué existe hoy frente a lo que viene después. Ese relato sirve a tres audiencias y termina en tres salidas. La prioridad sigue siendo que un responsable de proceso entienda en 30 segundos qué hace Solaris y por qué puede confiar en él, y que solicite una demostración.

- **Acción principal:** solicitar una demostración, con formulario y reserva de llamada.
- **Acción secundaria:** ver cómo funciona, en una demo interactiva del proceso de compra dentro de la propia página.
- **Salidas por audiencia:** clientes → «Solicitar demostración»; aliados → «Cómo trabajamos»; inversores → «Material para inversores», solo bajo petición. El formulario recoge el perfil (cliente, aliado o inversor).
- **Regla de copy:** lo que está en presente existe en el producto v1; lo demás va en futuro y etiquetado («Siguiente» o «Visión · hipótesis»). Nada de cifras, clientes, pilotos, valoración ni precios no publicados, tampoco para inversores.
- **Pieza central:** la demo (sección 7). Las secciones anteriores preparan al lector para usarla y las posteriores resuelven las dudas que deja.

## 2. Marco

| Parámetro | Decisión |
|---|---|
| Idioma | Español; inglés en una segunda fase |
| Alojamiento | Vercel, con dominio propio (por confirmar tras la búsqueda de marca) |
| Enlaces cruzados | dasalazarr.com enlaza a la landing; la landing enlaza al diario |
| Referencia | OpenBot, solo por ritmo de secciones y nivel de acabado |
| Fuente de verdad | El PRD de producto v1: la landing no promete nada que no esté en v1 |

## 3. Audiencias y mensajes

La página habla a quien responde de un proceso, no al equipo técnico.

- **Mensaje central:** «Las empresas no necesitan más chatbots. Necesitan que sus procesos tengan contrato.»
- **Promesa:** lee sus documentos, responde citando la fuente exacta, detecta lo que incumple sus reglas y no ejecuta nada sin aprobación humana.

| Audiencia | Objeción | Respuesta | Dónde |
|---|---|---|---|
| Dirección financiera u operaciones de una pyme | «La IA se inventa cosas» | Cada respuesta cita documento, página y párrafo | Hero, Qué hace, Demo |
| Socio de un despacho profesional | «No puedo subir expedientes a la nube» | Con documentos reales, se instala en su equipo | Cifra, Dos formas, FAQ |
| Responsable de calidad o cumplimiento | «Mis reglas están en PDFs que nadie cruza» | Las reglas se evalúan solas y señalan lo que falta | El bucle, Demo |
| Consultora o socio de canal | «¿Qué gano yo?» | Packs por sector que pueden implantar con Illarium | Cómo trabajamos |
| Inversor | «¿Es una consultora o un producto que escala?» | Un motor y siete primitivas; cada sector es un pack. Hoy, siguiente y visión separados y etiquetados | La ontología de procesos, Hoy · Siguiente · Visión, salida «Material para inversores» |
| Comunidad técnica y lectores del diario | «¿Es real o humo?» | Se construye en público, con errores visibles | Construcción en público |

**Tono:** directo, concreto, sin superlativos, con cifras y ejemplos en lugar de adjetivos. Se trata al lector de tú; las páginas legales siguen de usted hasta validarlas ([[ADR-0012]]). Al lector se le habla de procesos; «pack» queda como término interno.

## 4. Identidad

- **Concepto:** luz sobre los documentos, que hace verificable lo ya escrito. Continúa el rediseño de la app para que landing y producto se lean como una sola cosa.
- **Firma visual:** un barrido de resaltado ámbar sobre las palabras clave de cada titular, como una cita en un documento. Se usa solo en titulares de sección, nunca en el cuerpo.
- **Motivo de fondo:** un haz solar cálido que baja desde arriba, en el hero y en el cierre.
- **Paleta:**
  - ink `#0D0F14` e ink-2 `#151821` para las zonas oscuras.
  - paper `#F4F5F7` y sheet `#FBFAF7` para las zonas claras.
  - Un único acento, solar `#F2B544`. Se usa solo como fondo de botón y nunca como texto sobre claro; para enlaces sobre claro, solar-ink `#8A5A00`.
  - Cuatro pares semánticos: lavanda (ontología), salvia (cumplido), niebla (packs) y arcilla (bloqueo).
- **Tipografía:**
  - Schibsted Grotesk 500/600 para titulares e interfaz. Titulares de 56 a 88 px con tracking −2,5 %.
  - Newsreader para las citas y para una palabra en cursiva por titular.
  - JetBrains Mono para referencias, códigos y etiquetas.
- **Logotipo provisional:** disco solar con un anillo fino. «un producto de Illarium» va en el pie y en la navegación móvil. El definitivo depende de la búsqueda de marca.
- **De OpenBot:**
  - Se toma el ritmo de secciones, el acabado y el mosaico final como gesto de cierre.
  - No se toman su marca, su paleta, sus textos, su composición, sus tarjetas de descarga («Solaris no se descarga, se implanta») ni sus hexágonos. En su lugar, un campo de documentos que se iluminan.

## 5. Estructura: 13 secciones que alternan fondo oscuro y claro

| # | Sección | Qué cumple | Pieza clave |
|---|---|---|---|
| 1 | Navegación | Botón principal siempre visible | Barra fija de 64 px que se difumina al hacer scroll; en móvil, menú a pantalla completa |
| 2 | Hero | Tesis y prueba en el primer pantallazo | «Tus procesos, con contrato.» y captura de Preguntar en bucle de 9 s |
| 3 | Tesis | Nombrar el problema | «Las empresas no necesitan más chatbots.» con 3 tarjetas |
| 4 | El bucle | Explicar el funcionamiento | Pregunta → Cita → Regla → Hueco → Aprobación → Registro, con el caso PC-0412 y animación ligada al scroll |
| 5 | Qué hace Solaris | Capacidades | Cuadrícula de 12 columnas: 2 celdas grandes con capturas reales, 4 pequeñas y microgestos al pasar el cursor |
| 6 | La cifra | Privacidad | «0 documentos salen de su organización», siempre con la nota de que la demo usa la nube |
| 7 | Demo | Prueba central | Pestañas Preguntar, Explorar, Huecos y Revisar; sin backend y funcional sin red; borrador editable y rol simulado; aprobar añade una línea al registro |
| 8 | Packs | Producto por proceso | Compras, Jurídico, Calidad IFS y EUDR, con estados honestos |
| 9 | Dos formas de empezar | Sustituye a las descargas | Demostración en la nube frente a instalación en su equipo |
| 10 | Cómo trabajamos | Canal y consultoría | Diagnóstico → Piloto → Instalación → Acompañamiento |
| 11 | Construcción en público | Credibilidad | Las 3 últimas entradas del RSS del diario, leídas al compilar |
| 12 | Preguntas | Resolver objeciones | 7 preguntas en `<details>` accesible e indexable, una abierta a la vez |
| 13 | Cierre y pie | Última llamada a la acción | «Pon tus procesos bajo contrato.» sobre el campo de documentos, y pie con 4 columnas |

## 6. Movimiento

**Principio:** el movimiento explica, no decora. Hay tres momentos orquestados (hero, bucle y cierre); el resto son entradas discretas.

| Elemento | Duración | Curva | Cuándo se dispara |
|---|---|---|---|
| Entrada de bloque | 500 ms | cubic-bezier(.2,.7,.2,1) | Con el 20 % visible, una sola vez |
| Resaltado de titular | 700 ms | Misma curva | 200 ms después de la entrada |
| Captura del hero | Bucle de 9 s | Lineal por fases | Solo con el hero visible |
| El bucle | Ligado al scroll | Sin curva | Mientras la sección cruza la pantalla |
| Microgestos | 180 ms | ease-out | Al pasar el cursor o con el foco |
| Campo de documentos | Onda de 2,4 s | ease-in-out | Al entrar y luego cada 8 s |
| Haz solar | Deriva de 20 s | Sinusoidal | Continua, a 30 fps como máximo |

**Reglas:**

- Todo el contenido es legible aunque la animación no se ejecute.
- Con movimiento reducido no hay bucles, scroll ligado ni deriva, y los resaltados aparecen ya aplicados.
- Las animaciones se pausan fuera de pantalla y con la pestaña oculta.
- No hay parallax ni scroll suavizado.

## 7. Responsive y accesibilidad

- **Escritorio primero:** 1200 px y 12 columnas a partir de 1280 px.
- **Tableta (768–1279 px):** 8 columnas; la cuadrícula de capacidades pasa a 2 columnas y los packs a 2 × 2.
- **Móvil (< 768 px):** 4 columnas y márgenes de 20 px. El hero baja a 44 px; el bucle y los pasos pasan a vertical.
- **WCAG 2.2 AA:**
  - Contraste de al menos 4,5:1.
  - Foco visible con un anillo solar de 2 px y enlace «Saltar al contenido».
  - Texto alternativo en las capturas y control de pausa en los vídeos.
  - Demo usable solo con teclado y cambios anunciados con `aria-live`.

## 8. Stack y rendimiento

**Stack:** Next.js (App Router) con exportación estática, Tailwind con los tokens como variables CSS y Motion para la animación. El scroll usa animaciones CSS ligadas al scroll. El haz y el campo usan Canvas 2D o OGL con carga diferida. Fuentes autoalojadas y repositorio propio.

**Islas interactivas:** solo se hidratan el hero, el bucle, la demo y el formulario.

**Presupuesto en móvil de gama media con 4G:**

| Métrica | Objetivo |
|---|---|
| LCP | < 2,0 s, y el titular es siempre el elemento LCP |
| CLS | < 0,05 |
| INP | < 200 ms |
| JS inicial | < 150 KB comprimido |
| Primera vista | < 600 KB |
| Lighthouse (rendimiento, accesibilidad y SEO) | ≥ 95 |

## 9. Formulario, analítica y SEO

**Formulario:**

- Campos: nombre, empresa, correo profesional, proceso (Compras, Jurídico, Calidad, EUDR u Otro), fricciones opcionales por proceso y comentario opcional. El proceso llega marcado si se abre desde un pack o la demo.
- Micro-agenda de la llamada de 30 minutos sobre el botón de envío. La agenda no se embebe: el enlace aparece tras enviar.
- Casilla de privacidad sin marcar.
- Antispam sin CAPTCHA: campo trampa y límite por IP.
- Errores junto al campo, explicando qué falta y cómo corregirlo.
- Al enviar: confirmación en el panel, enlace de agenda y aviso por correo a Illarium, más un CRM (por decidir).

**Analítica sin cookies** (Plausible o Umami), para no necesitar banner. Eventos:

- Clic en la llamada a la acción, con la sección de origen.
- Formulario abierto, enviado y con error.
- Pestaña de la demo usada y aprobación en la demo.
- Pregunta frecuente abierta.
- Profundidad de scroll al 25, 50, 75 y 100 %.
- Los parámetros UTM se conservan hasta el envío.

**SEO:**

- Título «Solaris · IA privada para sus procesos» y descripción de 150 caracteres.
- Imagen Open Graph de 1200 × 630.
- Datos estructurados Organization, SoftwareApplication y FAQPage.
- `lang="es"`, sitemap y robots. La app sigue en noindex.

## 10. Dependencias de contenido

Todas se cierran tras la fase 1 del PRD de producto:

- Logotipo en SVG y favicon.
- Vídeo del hero (≤ 9 s, ≤ 1,5 MB, con póster).
- 4 recortes de captura para la sección de capacidades.
- Datos de muestra coherentes del pack Compras.
- 6 ejemplos del caso PC-0412, uno por nodo del bucle.
- Textos finales revisados contra el PRD de producto.
- Respuestas de la FAQ revisadas por un abogado (RGPD y secreto profesional).
- Un único juego de iconos.
- Imagen Open Graph.
- Textos legales: aviso legal, privacidad y cookies.
- RSS del diario.

## 11. Criterios de aceptación

La landing se publica cuando cumple todo esto:

- Las 13 secciones tienen textos finales y capturas reales.
- Cada afirmación está respaldada por el PRD v1 y nada promete funciones de la Visión v2.
- La demo funciona con teclado y sin red.
- Se cumple el presupuesto de rendimiento y Lighthouse da ≥ 95.
- Con movimiento reducido, la página se lee completa.
- El formulario llega a Illarium y los eventos aparecen en la analítica.
- Está probada en Safari, Chrome y Firefox de escritorio, y en Safari iOS y Chrome Android.

## 12. Pendiente de decidir

- Dominio y logotipo definitivo, que dependen de la búsqueda de marca.
- Herramienta de agenda y CRM.
- Mención a ayudas públicas, solo si se confirma la elegibilidad.
- Revisión jurídica de la FAQ.
- Textos finales: el copy actual es un borrador.

En el prototipo ya están las 13 secciones, la demo, el formulario y el sistema de movimiento. Del PRD faltan el stack Next.js, las capturas reales, el RSS en vivo, el backend del formulario y la analítica conectada.
