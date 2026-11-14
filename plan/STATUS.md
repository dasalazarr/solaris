# Solaris — Tablero vivo

Léelo al empezar y actualízalo al cerrar. Última actualización: 2026-11-14 (Inicio vivo y piezas comunes en producción por illariumcore#30, ADR-0022 propuesta; primer uso y alta de espacios ya fusionados).

## Estado
- **04/11:** publicadas solaris_fronted#6 y #7 (visión, audiencias y demo con los datos del producto). La landing estuvo **sin `noindex`** como mucho entre el 02/11 y el 04/11 (`NEXT_PUBLIC_NOINDEX` no valía exactamente `true` en Vercel); Diego lo corrigió y se verificó en portada, Aviso legal, Privacidad y Cookies. Guarda en el build: solaris_fronted#8.
- En línea con `noindex`: landing en `solaris.dasalazarr.com` (proyecto `solaris-fronted`) y producto en `illariumcore.vercel.app`. El formulario envía de extremo a extremo: Resend (`avisos@dasalazarr.com`) → `solaris@dasalazarr.com`. Privacidad, Aviso legal y Cookies publicados; Umami activo.
- `main` de los tres repositorios incluye todo, salvo un cambio menor del producto (`.env.example`) y los commits de esta sesión de cierre.
- WikiSkill ([[ADR-0005]]). 8D aparcado ([[ADR-0006]]). Equipo como Proceso ([[ADR-0007]]). Dominio ([[ADR-0008]]). Flujo de ramas: [[PAT-005]].

## Siguiente tarea por rol
| Rol | Tarea | Enlaza |
|---|---|---|
| Diego | Hacer un envío real del formulario desde `www.illarium.com/solaris` y confirmar que llega al buzón. El 13/11 se añadieron los orígenes de illarium.com a `LANDING_ORIGINS` y se redesplegó el producto: el preflight ya responde 204 | [[F06]] |
| Diego | Aceptar o corregir [[ADR-0021]] y [[ADR-0022]] (ya en producción: illariumcore#26 y #30). Decidir si se rehacen las capturas de la landing y el rótulo «Cómo lo evalúa el motor» del vídeo, que son del diseño anterior | [[ADR-0021]], [[ADR-0022]], [[F06]] |
| dev | Auditoría del 14/11 sin corregir: `expression` de R-03 no coincide con su lógica y Contrato aún la muestra; «Compras» en el selector frente a «Proceso de compra» en la cabecera; `NEXT_PUBLIC_LANDING_URL` cae por defecto en `illarium.com` (sin comprobar qué vale en Vercel); botones de dentro de los paneles sin las constantes comunes | [[ADR-0022]] |
| dev | Inicio y piezas comunes: Jurídico y Compliance en navegador, espacio con persona identificada y lector de pantalla | [[ADR-0022]] |
| dev | Primer uso: los tres actos en móvil, modo con persona identificada y teclado sobre los bloques apartados | [[ADR-0021]] |
| Diego | Decidir quién revisa las reglas de la plantilla Compliance (fusionada en illariumcore#25) antes de enseñarlas a un despacho. [[ADR-0020]] aceptada el 10/11 | [[ADR-0020]], [[O07]] |
| dev | En móvil, con cinco reglas el texto de las celdas de la matriz se aprieta y «Incumplida» se corta | [[F03]] |
| landing-steward | Proponer cómo nombra la landing el proceso Compliance (la plantilla ya está fusionada) | [[F06]], [[ADR-0020]] |
| product-steward | Añadir a las entrevistas las tres preguntas de [[H04]] | [[H04]], [[O07]] |
| Diego | **Veto de security, para dar códigos a prospectos:** tope de gasto en la clave de Gemini puesto (Diego, 10/11; alerta sin confirmar); que alguien cualificado valide Privacidad; un código nuevo por prospecto, a ≤ 30 días, sin códigos antiguos activos | [[R01]], [[R02]], [[F01]] |
| Diego | Antes de activar Umami en el producto: nombrarlo en Privacidad, con CSP y `Referrer-Policy` ya puestas | [[F06]], [[R02]] |
| Diego | Ver los 8 MP4 de `video/out/` con sonido antes de publicarlos | [[ADR-0015]], [[ADR-0014]] |
| Diego | Decidir si la landing sigue titulando «IA privada para procesos con contrato» mientras el Nivel 2 no exista | [[ADR-0015]], [[F06]] |
| Diego | Elegir proveedor de contenedor en Europa, con disco y TLS, y dominio del producto | [[ADR-0016]] |
| security | **Veto a desplegar el contenedor:** construir la imagen y repasar los arreglos de illariumcore#21 | [[ADR-0016]], [[R01]] |
| Diego | Decidir si se exige separación de funciones: hoy solo se marca como «Autoaprobación». Fases 2 y 3 ya fusionadas (#21, #23). No poner `SOLARIS_DATA_DIR` en Vercel | [[ADR-0017]], [[F07]] |
| Diego | Aceptar o corregir [[ADR-0018]] (demo y MVP, mismo producto) y [[ADR-0019]] (sin lienzo de nodos ni LangChain por ahora) | [[ADR-0018]], [[ADR-0019]] |
| Diego | Medir [[H03]] con una persona sin programar: un proceso suyo, cronometrado y sin ayuda. Decide si después va el mapa de solo lectura ([[ADR-0019]]) | [[H03]] |
| dev | **Siguiente:** Fase 4, documentos reales: ingesta en pasos tipados y recuperación por el grafo ([[ADR-0019]]). Antes, idealmente, dos entrevistas | [[ADR-0015]] |
| Diego | Probar con un lector de pantalla real (VoiceOver), o decidir que espere: no se ha hecho y WCAG 2.2 AA no queda demostrado | [[ADR-0015]] |
| dev | Pendiente de security, antes de la Fase 2: contador de consultas compartido, dictamen del motor encima del texto del modelo, cabeceras de seguridad, `no-store` en `/api/space` y etiquetas de entorno que lean `environmentLevel` y `dataNature` | [[R01]], [[R02]] |
| product-steward | Preparar las 5–10 entrevistas para el final de la Fase 1, con el playbook y la síntesis del estudio | [[O06]], [[O01]] |
| Diego | Confirmar «proceso» como sustituto de «pack» y «En tu piloto» | [[ADR-0012]], [[ADR-0013]] |
| Diego | Decidir: pack comercial cercano al CRM y si Jurídico sigue siendo el primer piloto | [[ADR-0011]], [[O01]] |
| Diego | Crear el enlace de agenda y poner `NEXT_PUBLIC_AGENDA_URL` en Vercel; confirmar que la micro-agenda del formulario refleja la llamada | [[F06]] |
| Diego | Antes de poner `NEXT_PUBLIC_AGENDA_URL`: añadir el proveedor de agenda a Privacidad, avisar de que se abre un servicio externo y no precargar datos en la URL (H4 de security) | [[F06]] |
| dev | Hallazgos de security sin corregir: H6 (saltos de línea y `reply_to` en `/api/solicitud`) y la relación de EXP-M219, que apunta a `M-219`. H1, H2, H3 y H5 corregidos en los PR | [[R01]], [[F06]] |
| landing-steward | Envío real con `perfil` y fricciones a `/api/solicitud`: en esta sesión se interceptó la petición | [[F06]] |
| landing-steward | Publicados #6 y #7 (04/11): Lighthouse móvil en la URL publicada (en local no hay regresión: 79 → 79, LCP igual) y envío real con `perfil` a `/api/solicitud` | [[F06]] |
| landing-steward | Copy que ya es cierto: «Si no puede citarlo, no lo afirma» también en la pregunta libre (#5); «Sus reglas, escritas una vez y evaluadas siempre» (#8). No usar Docling/Surya ni «instalador» como algo que ya existe (#7) | [[F06]] |
| product-steward | Llevar al despacho el bloque 4 de `docs/nivel2-preguntas-y-contrato.md` junto con el playbook | [[O01]] |
| product-steward | Ejecutar el playbook con el despacho y traer conclusiones anonimizadas al PRD §8 | [[O01]], [[H01]] |
| landing-steward | Con Umami activo, fijar la línea base de visitas y solicitudes durante 2 semanas antes de proponer cualquier experimento | [[F06]], [[ADR-0007]] |
| dev | [desplazado] Bajar el LCP de la landing (2,9 s móvil simulado) revisando la animación de palabras del titular | [[F06]] |
| dev | [desplazado] Resolver los 3 avisos de oxlint (`Footer.tsx`, `Closing.tsx`, `lib/hooks.ts`) | [[L02]] |
| security | Revisar antes de abrir al público: Deployment Protection en Preview, códigos de espacio nuevos y caducidad, `p=none` de DMARC (añadir `rua=`) y Gmail personal como buzón de datos de prospectos | [[R01]], [[R02]], [[R04]] |
| dev | Limpiar ramas fusionadas, activar el borrado automático en los tres repos y subir el cambio de `.env.example` del producto ([[PAT-005]]) | [[PAT-005]] |
| product-steward | Decidir cuándo indexar: además de quitar `NEXT_PUBLIC_NOINDEX`, poner `SOLARIS_PERMITIR_INDEXAR=true` en producción (con la guarda de #8, si no, el build falla). Ahí aparecen nombre y domicilio en buscadores | [[F06]] |
| dev | [desplazado] Fase 1 de [[ADR-0007]]: pack `equipo` en el producto. **Desplazado** por el motor de reglas mínimo (F03, illariumcore#8): va después de fusionar #8 | [[O05]] |

## 2026-11-03 · landing-steward · visión y audiencias
- **Hecho:** [[ADR-0009]]; PRD landing §1 y §3; solaris_fronted#5 abierto (O1: IFS, diario, Bento, título). Propuesta del PR 2 presentada.
- **Gate:** landing lint + build; `out/` a 375 px sin scroll horizontal. Sin probar: Lighthouse.
- **Traza:** `raw/sessions/2026-11-03_landing-steward_vision-y-audiencias.md`.

## 2026-11-03 · landing-steward · PR 2 y PR 3 (visión, audiencias y demo)
- **Hecho:** solaris#10 (fundacional §6); solaris_fronted#6 (Cómo funciona con ontología y selector Compras/Jurídico, Hoy · Siguiente · Visión, botón de aliados, Perfil) y #7 (demo con PC-0412/PC-0419/PROV-024 del producto y pregunta «no consta»). Sin fusionar.
- **Gate:** lint + build; teclado, sin red y 375 px en local; Lighthouse móvil local sin regresión frente a `main`. Sin probar: Lighthouse en la preview (protegida) y envío real con perfil.
- **Traza:** `raw/sessions/2026-11-03_landing-steward_vision-pr2-pr3.md`.

## 2026-11-04 · cofundador · alineamiento a partir de un diagnóstico externo
- **Hecho (PR abiertos, sin fusionar):** illariumcore #9 a #12; solaris_fronted #9 a #12; [[ADR-0010]], `docs/guion-demo-90s.md`, PRD y `fundacional.md` §6. Decisiones de Diego: VPC no se promete, agenda con enlace, alcance completo.
- **Cambio visible:** Compras pasa a 5 documentos; cualquiera ya no puede aprobar; aprobar cierra el hueco.
- **Security:** no veta. #9 y solaris_fronted#12 APTOS con condiciones, los otros seis APTOS. H1 (un rol sin firma revertía una aprobación), H2 (CSV), H3 (Nivel 2 en presente) y H5 (recorte del comentario) corregidos y propagados por ambas pilas. La revisión de security es anterior a estos arreglos. La condición de rol en servidor sigue en pie para el piloto: sin ella no hay Nivel 2.
- **Gate:** producto con 109 tests, lint y build; landing con lint y build; navegador local. Sin probar: envío real, preview conjunta y Lighthouse publicado.
- **Traza:** `raw/sessions/2026-11-04_cofundador_alineamiento-diagnostico.md`.

## 2026-11-04 · cofundador · lo fusionado no llegó a producción, correcciones y audiencia
- **Hecho:** Diego fusionó los 8 PR apilados, pero solo los #9 llegaron a `main`. PR únicos `fix/publicar-alineamiento` abiertos, con OCR fuera de los datos, «La IA redacta y explica» y el aviso del piloto reducido a Siguiente y una FAQ. [[ADR-0011]].
- **Gate:** producto 109 tests, lint y build; landing lint y build. Producción con `noindex` en las 4 páginas. El último commit de textos no se ha visto en navegador ni lo ha revisado security.
- **Traza:** `raw/sessions/2026-11-04_cofundador_main-y-audiencia.md`.

## 2026-11-05 · cofundador · tuteo y «proceso»
- **Hecho:** alineamiento comprobado en producción (landing con `curl`; producto solo por fuera). PR de tuteo en landing y producto; [[ADR-0012]]; punteros a `main`.
- **Gate:** producto 109 tests, lint y build; landing lint y build; navegador local a 375 px y escritorio. Sin revisar por security; sin pasar por el producto en navegador.
- **Traza:** `raw/sessions/2026-11-05_cofundador_tuteo-y-proceso.md`.

## 2026-11-05 · cofundador · spec de claridad de la landing
- **Hecho:** `docs/spec-landing-claridad.md`; Entrega 1 fusionada en solaris_fronted#15, con [[ADR-0013]]; fecha de muestra fusionada en illariumcore#15. La Entrega 2 se revisa tras la Fase 1 del plan evolutivo.
- **Gate:** `wiki_lint.py`; producto 110 tests, lint y build; landing lint y build; navegador local.
- **Traza:** `raw/sessions/2026-11-05_cofundador_spec-landing-claridad.md`.

## 2026-11-07 · cofundador · Fase 0 del plan evolutivo
- **Hecho:** [[ADR-0015]], `docs/plan-evolutivo.md`, `docs/spec-experiencia.md`, síntesis anónima del estudio, ROADMAP y PRD. Trabajo pendiente del 05/11 commiteado y punteros a `main`.
- **Aprendido:** `solaris` es público: el estudio original no entra. La ayuda regional de 2026 cerró el 06/11 y no cubre licencias recurrentes.
- **Gate:** `wiki_lint.py` y `npm run gate` en `video/`. Sin cambios de código en el producto ni en la landing. Bases del BON leídas en la web, sin abrir el PDF.
- **Traza:** `raw/sessions/2026-11-07_cofundador_fase-0-plan-evolutivo.md`.

## 2026-11-07 · cofundador · Fase 1 de experiencia
- **Hecho:** illariumcore#17 (modelo de Gemini configurable) y #18 (experiencia según el vídeo). Diego decide que las entrevistas no bloquean la construcción.
- **Gate:** 118 tests, lint, build y gate de `video/`; navegador local a 1440 y 375 px. Sin probar: Gemini con clave, PDF impreso y lector de pantalla. Sin revisión de security.
- **Traza:** `raw/sessions/2026-11-07_cofundador_fase-1-experiencia.md`.

## 2026-11-07 · cofundador · Fase 1 en producción
- **Hecho:** illariumcore#17, #18 y solaris#17 fusionados por Diego. La pregunta libre responde en producción con cita literal y dice «no consta» cuando no hay fuente. Abierto illariumcore#19.
- **Aprendido:** una respuesta sin cita enseñaba un dictamen ajeno porque el modelo declara objetos consultados; solo se vio al probar con el modelo real.
- **Gate:** 118 tests, lint y build en #19; dos preguntas reales en producción; navegador local con respuesta simulada. Sin probar: PDF impreso y lector de pantalla. Sin revisión de security.
- **Traza:** `raw/sessions/2026-11-07_cofundador_fase-1-en-produccion.md`.

## 2026-11-07 · cofundador · menú real en landing y vídeo
- **Hecho:** solaris_fronted#17 y `video/src/ventana.tsx` muestran Contrato y Registro, con los iconos de la app. 8 MP4 vueltos a renderizar.
- **Gate:** `pnpm lint`, `pnpm build`, `npm run gate`, hojas de contacto y sonoridad (−16,2 a −16,7 LUFS). Sin ver a tiempo real ni oír.
- **Traza:** `raw/sessions/2026-11-07_cofundador_menu-real.md`.

## 2026-11-07 · security · revisión de la Fase 1
- **Dictamen:** APTO con condiciones. Se mantiene el veto a dar códigos hasta cumplirlas. Sin fallos de acceso ni de autenticación.
- **Hecho:** illariumcore#20 (sustituye a #19) y solaris_fronted#17 recogen lo corregible en código, la accesibilidad y el PDF.
- **Gate:** 120 tests, lint, build y navegador local con respuestas simuladas. Sin lector de pantalla ni axe.
- **Traza:** `raw/sessions/2026-11-07_security_revision-fase-1.md`.

## 2026-11-07 · cofundador · correcciones en producción
- **Hecho:** illariumcore#20, solaris_fronted#17 y solaris#18 fusionados. Pregunta sin fuente: «No consta», sin dictamen y con el panel que lo dice. Pregunta larga: tres citas literales, sin truncarse con el tope de 4.000 tokens. Privacidad nombra la API de Gemini y la landing sigue con `noindex`.
- **Gate:** dos preguntas reales con la sesión de Diego, sin errores en los logs de Vercel de esos 20 minutos.
- **Traza:** `raw/sessions/2026-11-07_cofundador_correcciones-en-produccion.md`.

## 2026-11-07 · cofundador · Fase 2 en PR
- **Hecho:** illariumcore#21: SQLite por espacio, decisiones en servidor y código por persona. En Vercel no cambia lo que se ve. [[ADR-0016]].
- **Aprendido:** security encontró que quien no firma podía sustituir el texto que aprobaba otro; corregido antes de abrir el PR.
- **Gate:** 166 tests, lint, build, gate de `video/` y versión de producción en local. Imagen Docker sin construir.
- **Traza:** `raw/sessions/2026-11-07_cofundador_fase-2-nucleo.md`.

## 2026-11-07 · cofundador · Fase 3 en rama
- **Hecho:** `feat/parametrizacion`: definición de proceso en JSON, motor con dos operadores nuevos, editor con vista previa y versiones con hash real. Sin PR hasta fusionar illariumcore#21, para no apilar. [[ADR-0017]].
- **Aprendido:** una aprobación debe ligarse a lo que se aprobó, no solo a la lógica; y la nota de quien publica no sirve de rastro.
- **Gate:** 234 tests, regresión de oro de los cuatro procesos, lint, build y hoja de contacto del vídeo.
- **Traza:** `raw/sessions/2026-11-07_cofundador_fase-3-parametrizacion.md`.

## 2026-11-08 · cofundador · proceso nuevo y línea base de H03
- **Hecho:** `feat/proceso-nuevo`: crear procesos en blanco o como copia, con casos de prueba escritos a mano. «Alta de cliente» creado de principio a fin desde la app.
- **Aprendido:** el editor no permitía añadir tipos de objeto; sin eso, un proceso en blanco no es definible.
- **Gate:** 253 tests, lint, build, gate de `video/` y navegador local en modo guardado, demostración y 375 px.
- **Traza:** `raw/sessions/2026-11-08_cofundador_proceso-nuevo.md`, `raw/eval-runs/2026-11-08_h03-linea-base.md`.

## 2026-11-10 · cofundador · vertical Compliance
- **Hecho:** comparación de cinco ámbitos con fuentes, caso de estudio ficticio (`docs/caso-de-estudio-compliance.md`), [[ADR-0020]] propuesto, [[O07]] y [[H04]]. Sin código.
- **Aprendido:** la reforma europea de 2026 deja la diligencia de terceros para grupos muy grandes; el ámbito con fecha cercana es el blanqueo.
- **Gate:** `wiki_lint.py`. Varias normas solo en resumen o por fuente secundaria: lista en el informe.
- **Traza:** `raw/sessions/2026-11-10_cofundador_vertical-compliance.md`.

## 2026-11-10 · cofundador · plantilla Compliance
- **Hecho:** [[ADR-0020]] aceptada por Diego. Plantilla `pbc` en la rama `feat/plantilla-compliance` de illariumcore: seis clientes ficticios, cinco reglas, sin tocar el motor. ROADMAP y PRD §4 al día. El puntero del submódulo no se mueve hasta fusionar.
- **Aprendido:** había dos listas cerradas de procesos fuera de los tipos: el script de códigos y un test que contaba cuatro.
- **Gate:** 266 tests, regresión de oro de los cuatro procesos, lint, build y navegador local a escritorio y 375 px. Sin lector de pantalla ni pregunta libre con el modelo real.
- **Security:** APTO con condiciones. Sin hallazgos de acceso, secretos ni datos reales. Tres retoques de texto y un test de acceso, aplicados en la rama.
- **Traza:** `raw/sessions/2026-11-10_cofundador_plantilla-compliance.md`.

## 2026-11-10 · cofundador · evolución de la experiencia, recorrido y R-01
- **Hecho:** documento «Solaris · Evolución de la experiencia» (Claude Docs). illariumcore#24 fusionado y en producción: el recorrido se pliega en una píldora fuera de su pantalla y R-01 de compras dice solo lo que comprueba (certificado AEAT). [[ADR-0018]] y [[ADR-0019]] propuestos.
- **Aprendido:** un lienzo de nodos o LangGraph no encajan hoy: las reglas no forman un flujo y la revisión ya guarda el estado.
- **Gate:** tests, lint y build del producto en #24; navegador local en escritorio y 375 px; `wiki_lint` OK.

## Bloqueos
- Para quitar `noindex`: confirmar que Aviso legal y Cookies los validó alguien cualificado (jurisdicción, `solaris-utm`, «Umami sin cookies» sin verificar en su documentación) y decidir la fecha.
- Dominio definitivo de marca y logotipo (tras la búsqueda de marca).
- Revisión jurídica de la FAQ («[Respuesta pendiente de revisión jurídica.]», oculta en la web).
- Plan de Vercel: Hobby es no comercial según mi conocimiento; comprobar antes de cobrar el piloto.

## Sin commit / local
- `~/Projects/Solaris-8D-archivo`: `marketing/accounts.*` y `.env` solo existen allí.
- `product/.env.local` (ignorado) con el espacio de demo local.

## 2026-11-02 · orquestador + dev + security · despliegue de la landing y del correo
- **Hecho:** landing y producto en línea con `noindex`; formulario → Resend → buzón verificado; política, Aviso legal y Cookies publicados; Umami activo. [[ADR-0008]], [[PAT-005]], [[R04]] hecho y verificado.
- **Aprendido:** las `NEXT_PUBLIC_*` solo surten efecto al reconstruir; Gmail manda a spam un aviso con SPF, DKIM y DMARC en `pass`.
- **Gate:** landing lint + build; `wiki_lint.py` OK. Sin probar: Lighthouse en la URL publicada.
- **Traza:** `raw/sessions/2026-11-02_orquestador_despliegue-y-correo.md`.

## 2026-11-03 · product-steward + dev + security · citas, entorno, motor y perfil
- **Hecho (PR abiertos en illariumcore, sin fusionar):** #5 citas verificadas, sin respuesta fija ni recurso a Compras, con límite de consultas; #6 `perfil` en `/api/solicitud`; #7 «Arquitectura prevista del Nivel 2» e ingesta «simulada»; #8 motor de reglas mínimo (criterios en PRD §8.1). Borrador `docs/nivel2-preguntas-y-contrato.md`.
- **PC-0412 no cambia** (R-03 requiere aprobación, R-02 conforme). **Cambio visible en Compras:** el motor añade el hueco R-02 «falta evidencia» en PC-0419. EUDR gana el atributo `superficie_f03 = 7,4 ha` (literal en EV-EUDR-01).
- **Gate:** lint, tests (48/35/31/70) y build en cada rama; navegador sin clave y Huecos. Security: #5 APTO con condiciones (aplicadas, salvo el tope de gasto, que está fuera del código); #6 APTO. Sin probar: clave real de Gemini y Resend con `perfil`.
- **Traza:** `raw/sessions/2026-11-03_product-steward_citas-entorno-motor.md`.

## 2026-11-04 · orquestador · publicación de visión y audiencias, y noindex
- **Hecho:** #7 apilado sobre #6 (preview conjunta); Diego fusionó solaris_fronted #7 → #6 → main y solaris#10; puntero de `landing` en solaris#11. Detectado y corregido el incidente de `noindex`; guarda en solaris_fronted#8 (abierto).
- **Gate:** landing lint + build sobre la combinación #6+#7; guarda probada en 4 casos. `curl` a producción: contenido nuevo y `noindex` en las 4 páginas.
- **Traza:** `raw/sessions/2026-11-04_orquestador_publicacion-y-noindex.md`.

## 2026-11-06 · cofundador · vídeos funcionales en Remotion
- **Hecho:** `video/` con cuatro piezas en dos formatos; input, brief, plantilla y skill `video-funcional`; [[ADR-0014]]. Diego aprueba el resultado.
- **Gate:** `npm run gate`, hojas de contacto y sonoridad.
- **Traza:** `raw/sessions/2026-11-06_cofundador_videos-remotion.md`.
