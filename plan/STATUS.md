# Solaris — Tablero vivo

Léelo al empezar y actualízalo al cerrar. Última actualización: 2026-11-04 (solo #9 llegó a main; PR únicos abiertos; audiencia de consultoras e implantadores).

## Estado
- **04/11:** publicadas solaris_fronted#6 y #7 (visión, audiencias y demo con los datos del producto). La landing estuvo **sin `noindex`** como mucho entre el 02/11 y el 04/11 (`NEXT_PUBLIC_NOINDEX` no valía exactamente `true` en Vercel); Diego lo corrigió y se verificó en portada, Aviso legal, Privacidad y Cookies. Guarda en el build: solaris_fronted#8.
- En línea con `noindex`: landing en `solaris.dasalazarr.com` (proyecto `solaris-fronted`) y producto en `illariumcore.vercel.app`. El formulario envía de extremo a extremo: Resend (`avisos@dasalazarr.com`) → `solaris@dasalazarr.com`. Privacidad, Aviso legal y Cookies publicados; Umami activo.
- `main` de los tres repositorios incluye todo, salvo un cambio menor del producto (`.env.example`) y los commits de esta sesión de cierre.
- WikiSkill ([[ADR-0005]]). 8D aparcado ([[ADR-0006]]). Equipo como Proceso ([[ADR-0007]]). Dominio ([[ADR-0008]]). Flujo de ramas: [[PAT-005]].

## Siguiente tarea por rol
| Rol | Tarea | Enlaza |
|---|---|---|
| Diego | **Fusionar los dos PR `fix/publicar-alineamiento` a la vez** (illariumcore y solaris_fronted, sin apilar): los #10-#12 de cada repo cayeron en sus ramas base y en producción solo está el #9. `curl` a `noindex` después | [[F03]], [[F06]], [[ADR-0010]] |
| Diego | Decidir: pack comercial cercano al CRM y si Jurídico sigue siendo el primer piloto | [[ADR-0011]], [[O01]] |
| Diego | Crear el enlace de agenda y poner `NEXT_PUBLIC_AGENDA_URL` en Vercel; confirmar que la micro-agenda del formulario refleja la llamada | [[F06]] |
| Diego | Antes de poner `NEXT_PUBLIC_AGENDA_URL`: añadir el proveedor de agenda a Privacidad, avisar de que se abre un servicio externo y no precargar datos en la URL (H4 de security) | [[F06]] |
| Diego | Comprobar en el Registro Mercantil o BORME «Suministros Industriales del Norte S.L.» y «Logística y Embalajes Delta S.A.», o cambiarlos por nombres claramente ficticios: a la segunda se le atribuye un certificado caducado (H7) | [[R01]] |
| dev | Hallazgos de security sin corregir: H6 (saltos de línea y `reply_to` en `/api/solicitud`) y la relación de EXP-M219, que apunta a `M-219`. H1, H2, H3 y H5 corregidos en los PR | [[R01]], [[F06]] |
| dev | Mover los punteros de `landing` y `product` en la raíz tras fusionar. El de `landing` aún no incluye solaris_fronted#8 | [[PAT-005]] |
| landing-steward | Envío real con `perfil` y fricciones a `/api/solicitud`: en esta sesión se interceptó la petición | [[F06]] |
| landing-steward | Publicados #6 y #7 (04/11): Lighthouse móvil en la URL publicada (en local no hay regresión: 79 → 79, LCP igual) y envío real con `perfil` a `/api/solicitud` | [[F06]] |
| landing-steward | Copy que ya es cierto: «Si no puede citarlo, no lo afirma» también en la pregunta libre (#5); «Sus reglas, escritas una vez y evaluadas siempre» (#8). No usar Docling/Surya ni «instalador» como algo que ya existe (#7) | [[F06]] |
| security | Antes de configurar `GEMINI_API_KEY` en el despliegue: tope de gasto en la clave (condición del APTO de #5) | [[R02]] |
| product-steward | Llevar al despacho el bloque 4 de `docs/nivel2-preguntas-y-contrato.md` junto con el playbook | [[O01]] |
| product-steward | Ejecutar el playbook con el despacho y traer conclusiones anonimizadas al PRD §8 | [[O01]], [[H01]] |
| landing-steward | Con Umami activo, fijar la línea base de visitas y solicitudes durante 2 semanas antes de proponer cualquier experimento | [[F06]], [[ADR-0007]] |
| dev | Bajar el LCP de la landing (2,9 s móvil simulado) revisando la animación de palabras del titular | [[F06]] |
| dev | Resolver los 3 avisos de oxlint (`Footer.tsx`, `Closing.tsx`, `lib/hooks.ts`) | [[L02]] |
| security | Revisar antes de abrir al público: Deployment Protection en Preview, códigos de espacio nuevos y caducidad, `p=none` de DMARC (añadir `rua=`) y Gmail personal como buzón de datos de prospectos | [[R01]], [[R02]], [[R04]] |
| dev | Limpiar ramas fusionadas, activar el borrado automático en los tres repos y subir el cambio de `.env.example` del producto ([[PAT-005]]) | [[PAT-005]] |
| product-steward | Decidir cuándo indexar: además de quitar `NEXT_PUBLIC_NOINDEX`, poner `SOLARIS_PERMITIR_INDEXAR=true` en producción (con la guarda de #8, si no, el build falla). Ahí aparecen nombre y domicilio en buscadores | [[F06]] |
| dev | Fase 1 de [[ADR-0007]]: pack `equipo` en el producto. **Desplazado** por el motor de reglas mínimo (F03, illariumcore#8): va después de fusionar #8 | [[O05]] |

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
