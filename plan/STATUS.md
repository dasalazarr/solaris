# Solaris — Tablero vivo

Léelo al empezar y actualízalo al cerrar. Última actualización: 2026-11-03 (citas verificadas, entorno honesto, motor de reglas y perfil en solicitud: PR abiertos).

## Estado
- En línea con `noindex`: landing en `solaris.dasalazarr.com` (proyecto `solaris-fronted`) y producto en `illariumcore.vercel.app`. El formulario envía de extremo a extremo: Resend (`avisos@dasalazarr.com`) → `solaris@dasalazarr.com`. Privacidad, Aviso legal y Cookies publicados; Umami activo.
- `main` de los tres repositorios incluye todo, salvo un cambio menor del producto (`.env.example`) y los commits de esta sesión de cierre.
- WikiSkill ([[ADR-0005]]). 8D aparcado ([[ADR-0006]]). Equipo como Proceso ([[ADR-0007]]). Dominio ([[ADR-0008]]). Flujo de ramas: [[PAT-005]].

## Siguiente tarea por rol
| Rol | Tarea | Enlaza |
|---|---|---|
| Diego | Revisar y fusionar en `illariumcore`, en este orden: #6 (`perfil`), #7 (entorno), #5 (citas) y #8 (motor, apilado sobre #5). Después, actualizar el puntero `product` en la raíz | [[F01]], [[F03]] |
| landing-steward | **Listo para la landing:** `/api/solicitud` acepta `perfil` opcional (`cliente` \| `aliado` \| `inversor`; sin distinguir mayúsculas; otro valor → 400 con `campos: ['perfil']`). En producción solo cuando se fusione y despliegue illariumcore#6. Si la política de privacidad enumera los campos, añadir el perfil | [[F06]] |
| landing-steward | Copy que pasa a ser cierto al fusionar: «Si no puede citarlo, no lo afirma» también en la pregunta libre (#5); «Sus reglas, escritas una vez y evaluadas siempre» (#8). No usar Docling/Surya ni «instalador» como algo que ya existe (#7) | [[F06]] |
| security | Antes de configurar `GEMINI_API_KEY` en el despliegue: tope de gasto en la clave (condición del APTO de #5) | [[R02]] |
| product-steward | Llevar al despacho el bloque 4 de `docs/nivel2-preguntas-y-contrato.md` junto con el playbook | [[O01]] |
| landing-steward | **Urgente:** quitar de la landing publicada «Piloto en curso» (IFS), las 3 entradas de diario inventadas y «Una base, muchas vistas» (promete v2) — O1 de `docs/sinergia-landing-producto.md` | [[F06]] |
| dev | Un mismo caso PC-0412 en landing y producto; el producto es la fuente (O3) | [[F06]] |
| landing-steward | Decidir cuál manda en la maqueta (propuesta: «Explorar» del producto): menú lateral «Documentos» de la landing o pestañas «Explorar» del producto; alinear. | [[F06]], [[P04]] |
| product-steward | Ejecutar el playbook con el despacho y traer conclusiones anonimizadas al PRD §8 | [[O01]], [[H01]] |
| landing-steward | Con Umami activo, fijar la línea base de visitas y solicitudes durante 2 semanas antes de proponer cualquier experimento | [[F06]], [[ADR-0007]] |
| dev | Bajar el LCP de la landing (2,9 s móvil simulado) revisando la animación de palabras del titular | [[F06]] |
| dev | Resolver los 3 avisos de oxlint (`Footer.tsx`, `Closing.tsx`, `lib/hooks.ts`) | [[L02]] |
| security | Revisar antes de abrir al público: Deployment Protection en Preview, códigos de espacio nuevos y caducidad, `p=none` de DMARC (añadir `rua=`) y Gmail personal como buzón de datos de prospectos | [[R01]], [[R02]], [[R04]] |
| dev | Limpiar ramas fusionadas, activar el borrado automático en los tres repos y subir el cambio de `.env.example` del producto ([[PAT-005]]) | [[PAT-005]] |
| product-steward | Decidir cuándo quitar `noindex` (`NEXT_PUBLIC_NOINDEX=false`): ahí aparecen nombre y domicilio en buscadores | [[F06]] |
| dev | Fase 1 de [[ADR-0007]]: pack `equipo` en el producto. **Desplazado** por el motor de reglas mínimo (F03, illariumcore#8): va después de fusionar #8 | [[O05]] |

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
