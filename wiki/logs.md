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

## 2026-11-03 · product-steward + dev + security · citas, entorno, motor de reglas y perfil
- **Hecho:** illariumcore #5 (citas verificadas, sin respuesta fija), #6 (`perfil` en `/api/solicitud`), #7 (Nivel 2 «previsto», ingesta «simulada») y #8 (motor de reglas mínimo; criterios en PRD §8.1). Borrador `docs/nivel2-preguntas-y-contrato.md`.
- **Aprendido:** la interfaz tenía dos afirmaciones falsas más (tiempo de evaluación aleatorio y la acción propuesta junto a respuestas libres). El motor encontró un hueco real que los datos escritos a mano ocultaban (R-02 en PC-0419).
- **Gate:** lint, tests y build en las cuatro ramas; navegador sin clave. Sin probar: clave real de Gemini y Resend con `perfil`.
- **Traza:** `raw/sessions/2026-11-03_product-steward_citas-entorno-motor.md`.
