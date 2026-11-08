# Solaris — Log de evolución

> Log cronológico, **solo se anexa** (equivale a `logs.md` en WikiSkill). Una entrada por sesión, con la más reciente al final.
> Formato: `## YYYY-MM-DD · <rol> · <tarea>`, con lo hecho, lo aprendido, el gate y la traza en `raw/sessions/`.

## 2026-11-01 · orquestador · workspace + pendientes técnicos + WikiSkill
- **Hecho:** workspace traído de la nube a `~/Projects/Solaris` (producto + landing como submódulos); 8D archivado; límite de intentos por IP, indicador de entorno en el onboarding, lockfile, contraste AA y CLS 0; PR a `main` en producto y landing; `main` creado en la raíz; WikiSkill adoptada en todo el workspace.
- **Aprendido:** [[PAT-001]] (un repo por proyecto, fetch al arrancar), [[PAT-002]], [[PAT-003]], [[PAT-004]].
- **Decisiones:** [[ADR-0005]] (WikiSkill), [[ADR-0006]] (8D aparcado).
- **Gate:** producto 22 tests + lint + build; landing lint + build; Lighthouse móvil 95 / 100; `wiki_lint.py` OK.
- **Traza:** `raw/sessions/2026-11-01_orquestador_workspace-y-pendientes.md`.

## 2026-11-02 · orquestador · equipo de agentes como Proceso (fase 0)
- **Hecho:** crítica dialéctica de la propuesta de agentes sobre OpenBot; síntesis en [[ADR-0007]]. Dos administradores (`landing-steward`, `product-steward`), contratos por rol en `plan/contratos/`, reglas deterministas REG-* en `wiki_lint.py`. Aparcados [[O03]] (comunicación), [[O04]] (runtime dedicado); idea [[O05]].
- **Aprendido:** la tesis de Solaris se aplica al propio equipo: los roles son Procesos con contrato y las reglas que frenan la sobreingeniería (A/B sin tráfico, insight sin cita) se escriben como código.
- **Gate:** `test_wiki_lint.py` 9 OK; `wiki_lint.py` OK.
- **Traza:** `raw/sessions/2026-11-02_orquestador_equipo-de-agentes.md`.

## 2026-11-02 · dev + security · preparar el despliegue de la demo
- **Hecho:** formulario de la landing conectado a `/api/solicitud` del producto (Resend), Umami opcional, modo `noindex`, FAQ sin respuestas pendientes; guía `docs/despliegue.md`; riesgo [[R04]].
- **Aprendido:** el formulario simulaba el éxito; un prototipo así no puede llegar a un despliegue. Política de privacidad pendiente bloquea activar el envío.
- **Gate:** producto lint + 31 tests + build; landing lint + build; `wiki_lint.py` OK. Sin probar: envío real por Resend y Lighthouse en el despliegue.
- **Traza:** `raw/sessions/2026-11-02_dev_preparar-despliegue.md`.

## 2026-11-02 · orquestador + dev + security · despliegue de la landing y del correo
- **Hecho:** landing en `solaris.dasalazarr.com` y producto en `illariumcore.vercel.app`; formulario → Resend → `solaris@dasalazarr.com` verificado de extremo a extremo; política de privacidad, Aviso legal y Cookies publicados (`noindex` sigue activo); Umami activo. Decisión de dominio en [[ADR-0008]]; regla de ramas en [[PAT-005]]; [[R04]] hecho y verificado.
- **Aprendido:** las `NEXT_PUBLIC_*` se aplican al construir; Gmail manda a spam un aviso con autenticación perfecta, así que la causa es la reputación; y no se verifica un texto contando coincidencias.
- **Gate:** landing lint + build; producto 31 tests (sin cambios); `wiki_lint.py` OK. Sin probar: Lighthouse en la URL publicada.
- **Traza:** `raw/sessions/2026-11-02_orquestador_despliegue-y-correo.md`.

## 2026-11-02 · orquestador · sinergia landing ↔ producto y documento fundacional
- **Hecho:** `docs/sinergia-landing-producto.md` (9 afirmaciones de copy, matriz de funciones, 3 fallos del producto, 9 oportunidades) y `docs/fundacional.md` (tesis, 5 promesas de valor falsables y su estado).
- **Aprendido:** la landing publicada afirma un piloto IFS y tres entradas de diario que no existen; el motor de reglas y el Nivel 2 son promesas sin código; PC-0412 tiene datos distintos en cada repo.
- **Gate:** `wiki_lint.py` OK. Sin cambios de código: ni tests ni build.
- **Traza:** `raw/sessions/2026-11-02_orquestador_sinergia-y-fundacional.md`.

## 2026-11-03 · landing-steward · visión y audiencias
- **Hecho:** [[ADR-0009]] (un relato, tres salidas: clientes, aliados, inversores); PRD landing §1 y §3; PR solaris_fronted#5 quita «Piloto en curso» (IFS), el diario inventado, «Una base, muchas vistas» y unifica el título.
- **Aprendido:** `dasalazarr.com/diario` y `/ensayos` dan 404; el pie enlazaba a páginas inexistentes. Alinear PC-0412 con el producto cambia el hueco de la demo (firma de DF, no la tercera oferta).
- **Gate:** landing lint + build; navegador a 375 px. Sin probar: Lighthouse.
- **Traza:** `raw/sessions/2026-11-03_landing-steward_vision-y-audiencias.md`.

## 2026-11-03 · product-steward + dev + security · citas, entorno, motor de reglas y perfil
- **Hecho:** illariumcore #5 (citas verificadas, sin respuesta fija), #6 (`perfil` en `/api/solicitud`), #7 (Nivel 2 «previsto», ingesta «simulada») y #8 (motor de reglas mínimo; criterios en PRD §8.1). Borrador `docs/nivel2-preguntas-y-contrato.md`.
- **Aprendido:** la interfaz tenía dos afirmaciones falsas más (tiempo de evaluación aleatorio y la acción propuesta junto a respuestas libres). El motor encontró un hueco real que los datos escritos a mano ocultaban (R-02 en PC-0419).
- **Gate:** lint, tests y build en las cuatro ramas; navegador sin clave. Sin probar: clave real de Gemini y Resend con `perfil`.
- **Traza:** `raw/sessions/2026-11-03_product-steward_citas-entorno-motor.md`.

## 2026-11-03 · landing-steward · PR 2 y PR 3
- **Hecho:** «Cómo funciona» une bucle y ontología con selector Compras/Jurídico; «Hoy · Siguiente · Visión»; botón de aliados y Perfil; la demo pasa al caso de muestra del producto (solaris_fronted#6 y #7, sin fusionar). Fundacional §6 al día (solaris#10).
- **Aprendido:** las previews de Vercel están protegidas; Lighthouse se mide en local frente a `main`. Dos huecos en los datos del producto: la Relación jurídica no está modelada y la homologación de PROV-018 no tiene evidencia propia.
- **Gate:** lint + build; navegador local; Lighthouse local sin regresión.
- **Traza:** `raw/sessions/2026-11-03_landing-steward_vision-pr2-pr3.md`.

## 2026-11-04 · orquestador · publicación de visión y audiencias, y noindex
- **Hecho:** solaris_fronted #6 y #7 publicados juntos (#7 apilado sobre #6); solaris #10 y #11. Guarda de `noindex` en solaris_fronted#8, pendiente de fusión por Diego.
- **Aprendido:** fusionar en `main` de landing o producto es desplegar en producción; dos PR que se publican juntos se apilan para tener una sola preview; las previews exigen sesión de Vercel; una variable `NEXT_PUBLIC_*` con un valor distinto de `true` quitó el `noindex` sin que nada fallara.
- **Gate:** landing lint + build; guarda probada en 4 casos; `curl` a producción. Sin probar: Lighthouse en producción y envío real con `perfil`.
- **Traza:** `raw/sessions/2026-11-04_orquestador_publicacion-y-noindex.md`.

## 2026-11-04 · cofundador · alineamiento a partir de un diagnóstico externo
- **Hecho:** illariumcore #9 a #12 y solaris_fronted #9 a #12, abiertos; [[ADR-0010]]; guion de demo corregido.
- **Aprendido:** una revisión externa ve lo que ve el usuario, no si es cierto; el rol no se comprobaba y nadie lo había visto; un gate encadenado con `;` no es un gate.
- **Gate:** producto 109 tests, lint y build; landing lint y build; navegador local; security no veta (H1, H2, H3 y H5 corregidos). Sin probar: envío real y preview conjunta.
- **Traza:** `raw/sessions/2026-11-04_cofundador_alineamiento-diagnostico.md`.

## 2026-11-04 · cofundador · lo fusionado no llegó a main
- **Hecho:** PR únicos `fix/publicar-alineamiento`; correcciones de OCR, «lee» y aviso del piloto; [[ADR-0011]].
- **Aprendido:** MERGED no significa en `main`; con PR apilados, la base hay que cambiarla antes de fusionar. No se vuelve a apilar: un PR a `main` por entrega. Tras fusionar, comprobar producción.
- **Gate:** producto 109 tests, lint y build; landing lint y build; `curl` a `noindex`. Sin probar: textos en navegador y envío real.
- **Traza:** `raw/sessions/2026-11-04_cofundador_main-y-audiencia.md`.

## 2026-11-05 · cofundador · tuteo y «proceso»
- **Hecho:** tuteo en landing y producto; «pack» pasa a «proceso» de cara al lector; [[ADR-0012]].
- **Aprendido:** no todo «su» es el lector: las reglas de tercera persona se quedan, y por eso no vale reemplazar a ciegas.
- **Gate:** producto 109 tests, lint y build; landing lint y build; navegador local en la landing. Sin probar: producto en navegador.
- **Traza:** `raw/sessions/2026-11-05_cofundador_tuteo-y-proceso.md`.

## 2026-11-06 · cofundador · vídeos funcionales en Remotion
- **Hecho:** `video/` con cuatro piezas en dos formatos, leyendo `product/lib`; [[ADR-0014]]. Input, brief, plantilla y skill `video-funcional` para futuras piezas.
- **Gate:** `npm run gate`, hojas de contacto y sonoridad. Audio sin escuchar por el agente.
- **Traza:** `raw/sessions/2026-11-06_cofundador_videos-remotion.md`.

## 2026-11-07 · cofundador · Fase 0 del plan evolutivo
- **Hecho:** [[ADR-0015]]; plan, spec de experiencia y síntesis anónima del estudio; [[F07]], [[H03]] y [[O06]].
- **Aprendido:** el repositorio es público; la ayuda regional está cerrada y no cubre licencias recurrentes; la pregunta libre falla en producción.
- **Gate:** `wiki_lint.py` y `npm run gate` en `video/`.
- **Traza:** `raw/sessions/2026-11-07_cofundador_fase-0-plan-evolutivo.md`.

## 2026-11-07 · cofundador · Fase 1 de experiencia
- **Hecho:** illariumcore#17 y #18; matriz, recorrido, Revisar por pasos, Registro y Contrato.
- **Aprendido:** Google limita los modelos 2.5 a quien ya los usaba; un panel de decisión fijo no cabe en móvil.
- **Gate:** 118 tests, lint, build, gate de `video/` y navegador local.
- **Traza:** `raw/sessions/2026-11-07_cofundador_fase-1-experiencia.md`.

## 2026-11-07 · cofundador · Fase 1 en producción
- **Hecho:** pregunta libre comprobada en producción con la clave real; illariumcore#19 abierto.
- **Aprendido:** el modelo declara objetos consultados también cuando no cita nada; sin cita no debe aparecer ningún dictamen.
- **Gate:** 118 tests, lint, build, dos preguntas reales y navegador local.
- **Traza:** `raw/sessions/2026-11-07_cofundador_fase-1-en-produccion.md`.

## 2026-11-07 · cofundador · menú real en landing y vídeo
- **Hecho:** Contrato y Registro en la ventana de la landing y del vídeo; 8 MP4 renderizados.
- **Aprendido:** añadir los puntos debajo de Revisar no mueve lo que apuntan las cámaras.
- **Gate:** lint, build, gate de `video/`, hojas de contacto y sonoridad.
- **Traza:** `raw/sessions/2026-11-07_cofundador_menu-real.md`.

## 2026-11-07 · security · revisión de la Fase 1
- **Hecho:** APTO con condiciones y veto a dar códigos hasta cumplirlas. Corregido lo que depende de código en illariumcore#20 y solaris_fronted#17.
- **Aprendido:** un nombre de muestra sin comprobar coincidía con una sociedad registrada; los diálogos modales no retenían el foco aunque lo declaraban.
- **Gate:** 120 tests, lint, build, navegador local y PDF. Sin lector de pantalla.
- **Traza:** `raw/sessions/2026-11-07_security_revision-fase-1.md`.

## 2026-11-07 · cofundador · correcciones en producción
- **Hecho:** comprobadas en producción las correcciones de security; punteros de `product` y `landing` a `main`.
- **Aprendido:** una respuesta larga cabe en 4.000 tokens con el modelo por defecto.
- **Gate:** dos preguntas reales y logs de Vercel limpios.
- **Traza:** `raw/sessions/2026-11-07_cofundador_correcciones-en-produccion.md`.

## 2026-11-07 · cofundador · Fase 2 en PR
- **Hecho:** illariumcore#21 con `Store` en SQLite, decisiones en servidor y códigos por persona.
- **Aprendido:** abrir «pedir cambios» a cualquiera permitía cambiar lo que firma otro; lo pedido debe ir aparte de lo aprobado.
- **Gate:** 166 tests, lint, build y versión de producción en local.
- **Traza:** `raw/sessions/2026-11-07_cofundador_fase-2-nucleo.md`.

## 2026-11-07 · cofundador · Fase 3 en rama
- **Hecho:** `feat/parametrizacion`, con editor, versiones y motor ampliado.
- **Aprendido:** la hoja de contacto detectó que `video/` no resolvía el alias `@/`; el gate de tipos no lo vio.
- **Gate:** 234 tests y regresión de oro.
- **Traza:** `raw/sessions/2026-11-07_cofundador_fase-3-parametrizacion.md`.
