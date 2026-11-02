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
