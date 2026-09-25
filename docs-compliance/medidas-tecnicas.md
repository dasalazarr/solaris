# Medidas técnicas y organizativas — Solaris (Illarium Industrial OS)

> **BORRADOR — requiere revisión legal.** Pack de cumplimiento M4-T5. Versión del repo: rama `master`, 2026-09-25.
> Alcance: **demo con datos 100 % sintéticos** (planta ficticia "Componentes Arga S.L.", OEM ficticio "OEM Norte"; ADR-0004).
> Este documento separa lo **implementado hoy** (sección A, con evidencia verificable en el repo) de lo que **falta antes
> de un piloto con datos reales** (sección B). Nada de la sección B debe presentarse como existente.

**Cómo leer la evidencia.** Cada medida de la sección A cita ficheros, migraciones y tests del repo. La ruta
`fichero.py::test_x` indica un test concreto. La autocomprobación `python3 docs-compliance/check_evidencias.py`
verifica que cada ruta existe y que cada test nombrado está definido en su fichero. Estado de los tests en la
última ejecución registrada (traza de M4-T1, 2026-09-25): backend 161 passed, MCP 35 passed, ruff limpio.

---

## A. Medidas implementadas (con evidencia)

<!-- check_evidencias: inicio -->

### A1. Control de acceso a documentos en SQL (ACL antes de recuperar) y rol `solaris_app`
- **Qué:** la ACL por carpeta es *deny-by-default* y se aplica **dentro de la base de datos, antes del ranking**:
  un fragmento solo existe para la consulta si su carpeta tiene fila `(folder, role)` en `rag.folder_acl`.
  El runtime se conecta como `solaris_app`, que **no tiene SELECT sobre ninguna tabla de `rag`**: solo puede
  ejecutar las funciones `rag.visible_chunks`, `rag.visible_fmea_rows` y `rag.visible_documents`
  (SECURITY DEFINER, `search_path` fijo, EXECUTE revocado a PUBLIC). La ACL deriva de `acl.json` (sintético).
- **Evidencia:**
  - Migraciones: `app/backend/migrations/001_rag.sql`, `app/backend/migrations/006_rag_app_role.sql`
  - Código: `app/backend/solaris/rag/acl.py`, `app/backend/solaris/rag/retrieve.py`, `app/data/synthetic/acl.json`
  - Tests: `app/backend/tests/test_rag_schema.py::test_planta_sees_no_8d_chunks`,
    `app/backend/tests/test_rag_schema.py::test_folder_without_acl_is_invisible_even_for_admin`,
    `app/backend/tests/test_rag_schema.py::test_vector_ranking_after_acl_filter`,
    `app/backend/tests/test_app_role.py::test_cannot_select_rag_tables_directly`,
    `app/backend/tests/test_app_role.py::test_can_use_visible_functions`,
    `app/backend/tests/test_app_role.py::test_public_has_no_temp_or_connect`,
    `app/backend/tests/test_rag_retrieve.py::test_sql_only_uses_visible_functions`
- **Límite conocido (R07 n.º 3):** el rol de negocio es un parámetro de `rag.visible_*`; la garantía depende de
  que solo el backend lo llame con el rol resuelto del usuario autenticado.

### A2. ERP de solo lectura con roles de base de datos
- **Qué:** el servidor MCP del ERP (mock) conecta como `erp_reader` (`default_transaction_read_only=on`, sin
  privilegios propios). En cada transacción hace `SET LOCAL ROLE erp_<rol>` con el rol validado del usuario;
  los roles `erp_calidad`, `erp_planta`, `erp_auditor` y `erp_admin` reflejan `acl.json → erp_tables`. No
  existe ninguna herramienta de escritura; un intento de escritura se rechaza **y** se registra en el audit.
- **Evidencia:**
  - Migraciones: `app/backend/migrations/002_erp_reader.sql`, `app/backend/migrations/007_erp_business_roles.sql`
  - Código: `app/mcp/erp_mock/solaris_erp_mock/db.py`, `app/mcp/erp_mock/solaris_erp_mock/acl.py`,
    `app/mcp/erp_mock/solaris_erp_mock/server.py`
  - Tests: `app/mcp/erp_mock/tests/test_tools_db.py::test_write_through_reader_rejected_and_logged`,
    `app/mcp/erp_mock/tests/test_tools_db.py::test_reader_role_attributes`,
    `app/mcp/erp_mock/tests/test_tools_db.py::test_reader_without_business_role_reads_nothing`,
    `app/mcp/erp_mock/tests/test_tools_db.py::test_db_grants_match_acl_json`,
    `app/mcp/erp_mock/tests/test_tools_db.py::test_db_blocks_table_even_if_python_acl_is_bypassed`,
    `app/mcp/erp_mock/tests/test_tools_db.py::test_reader_cannot_escalate_to_privileged_roles`,
    `app/mcp/erp_mock/tests/test_mcp_protocol.py::test_write_tool_does_not_exist_and_is_logged`
- **Límite:** es un ERP **simulado** (Postgres). Un ERP real (SAP B1, Odoo…) exigirá su propio usuario técnico de
  solo lectura y la misma prueba de rechazo.

### A3. Registro de auditoría de solo anexar, con cadena de hash y fail-closed
- **Qué:** tabla `audit.events` con eventos `llm_call`, `retrieval`, `tool_call`, `tool_denied`, `write_attempt`,
  `approval`, `export`, `auth` e `ingest`. El escritor (`audit_writer`) solo tiene INSERT; el lector
  (`audit_reader`) solo SELECT. Un trigger bloquea UPDATE, DELETE y TRUNCATE **incluso al propietario y al
  superusuario**; otro encadena cada fila con `sha256(prev_hash || canónico)`. `verify_chain()` recalcula la
  cadena en Python. El servidor MCP es **fail-closed**: si el audit no escribe, la herramienta no devuelve datos.
  `GET /audit` y el export CSV exigen rol `admin` o `auditor`; el CSV neutraliza fórmulas.
- **Evidencia:**
  - Migraciones: `app/backend/migrations/003_audit.sql`, `app/backend/migrations/004_audit_ingest.sql`
  - Código: `app/backend/solaris/audit/store.py`, `app/backend/solaris/audit/api.py`,
    `app/mcp/erp_mock/solaris_erp_mock/audit.py`
  - Tests: `app/backend/tests/test_audit.py::test_trigger_blocks_owner_and_superuser`,
    `app/backend/tests/test_audit.py::test_writer_has_insert_only`,
    `app/backend/tests/test_audit.py::test_verify_chain_detects_tampering`,
    `app/backend/tests/test_audit.py::test_concurrent_inserts_keep_chain`,
    `app/backend/tests/test_audit_api.py::test_audit_requires_admin_or_auditor`,
    `app/backend/tests/test_audit_api.py::test_export_csv_escapes_formulas_and_is_audited`,
    `app/mcp/erp_mock/tests/test_audit_sink.py::test_mcp_fails_closed_if_audit_unavailable`,
    `app/mcp/erp_mock/tests/test_audit_sink.py::test_sink_fails_closed_without_password`
- **Límites:** (1) en el **backend** el modo por defecto del demo es `AUDIT_REQUIRED=false` (fail-open si falta
  el escritor); el MCP ya es fail-closed. (2) Un superusuario de la BD puede reescribir la cadena entera o
  truncar la cola sin que `verify_chain` lo detecte si no hay **ancla externa** (ver B2). (3) No hay purga por
  retención implementada (ver B6).

### A4. Redacción de secretos y minimización en el audit
- **Qué:** antes de escribir en el audit se sustituyen por `[REDACTED]` las claves de secreto y los valores con
  forma de secreto (`sk-…`, `Bearer …`, credenciales en URL, JWT, SCRAM, claves AWS, PEM) y **todos** los campos
  `SecretStr` de la configuración. Prompts y respuestas se guardan como `{sha256, chars}` más un extracto de
  400 caracteres (`AUDIT_PROMPT_MODE=truncate`) o solo el hash (`hash`). La ingesta registra solo metadatos,
  nunca contenido. Los secretos viven en `.env`, excluido de git; `.env.example` lleva las claves vacías.
- **Evidencia:**
  - Código: `app/backend/solaris/audit/redact.py`, `app/backend/solaris/settings.py`, `.gitignore`, `.env.example`
  - Tests: `app/backend/tests/test_redact_secrets.py::test_every_secretstr_field_is_scrubbed`,
    `app/backend/tests/test_audit.py::test_redaction_rules_without_db`,
    `app/backend/tests/test_audit.py::test_api_key_never_stored`,
    `app/backend/tests/test_llm_route.py::test_key_and_content_never_logged`,
    `app/backend/tests/test_rag_ingest.py::test_ingest_events_are_audited_without_content`

### A5. Autenticación con JWT (nivel demo)
- **Qué:** login con usuario y contraseña de demo (desde `.env`, ≥16 caracteres, comparación en tiempo
  constante). JWT HS256 con algoritmo fijado y `iss`, `aud`, `sub`, `sid`, `iat`, `nbf`, `exp` obligatorios;
  sin `AUTH_JWT_SECRET` no hay login (falla cerrado). **El rol no viaja en el token.** Sesión con vida máxima
  de 30 min y cierre por inactividad a los 15 min; logout revoca; bloqueo tras 5 fallos.
- **Evidencia:**
  - Código: `app/backend/solaris/auth/core.py`, `app/backend/solaris/auth/deps.py`, `app/backend/solaris/auth/api.py`
  - Tests: `app/backend/tests/test_auth.py::test_forged_tokens_rejected`,
    `app/backend/tests/test_auth.py::test_no_secret_fails_closed`,
    `app/backend/tests/test_auth.py::test_idle_timeout_closes_session`,
    `app/backend/tests/test_auth.py::test_logout_revokes_token`,
    `app/backend/tests/test_auth.py::test_lockout_after_repeated_failures`
- **Límite (R07):** no es SSO ni un IdP; sesiones en memoria, sin TLS, `/docs` público. Solo apto para el demo.

### A6. Identidad *on-behalf-of* (el agente actúa con la identidad del usuario)
- **Qué:** el rol se resuelve **en cada petición** desde `acl.json` a partir del usuario autenticado; ninguna ruta
  acepta `user`, `role` ni `actor` del cliente (guarda estructural sobre el OpenAPI). La recuperación exige un
  `Principal` (`retrieve_as`), el LLM registra al usuario real y la identidad hacia el MCP se construye solo en
  `mcp_obo.py` desde la sesión, rechazando argumentos de identidad que proponga el modelo.
- **Evidencia:**
  - Código: `app/backend/solaris/mcp_obo.py`, `app/backend/solaris/auth/deps.py`, `app/backend/solaris/rag/retrieve.py`
  - Tests: `app/backend/tests/test_access_matrix.py::test_access_matrix`,
    `app/backend/tests/test_access_matrix.py::test_no_route_takes_identity_params`,
    `app/backend/tests/test_auth.py::test_role_change_in_acl_applies_immediately`,
    `app/backend/tests/test_auth.py::test_llm_route_audits_the_authenticated_actor`,
    `app/backend/tests/test_rag_retrieve.py::test_retrieve_as_requires_principal_and_uses_its_identity`,
    `app/backend/tests/test_mcp_obo.py::test_identity_in_llm_arguments_is_rejected`,
    `app/backend/tests/test_mcp_obo.py::test_meta_comes_from_the_authenticated_principal`
- **Límite:** el transporte MCP es solo `stdio` (mismo proceso de confianza); la identidad en `_meta` no va
  firmada. Un transporte de red exigiría firmarla.

### A7. Allowlist de ingesta
- **Qué:** solo se ingieren las rutas declaradas en `manifest.json`, con extensiones permitidas (`.docx`, `.pdf`,
  `.xlsx`); se excluyen expresamente `acl.json`, `PLANT.md`, el propio manifest y código o SQL. Los ficheros en
  disco fuera del manifest se ignoran. Cada documento ingerido se registra en el audit (solo metadatos).
- **Evidencia:**
  - Código: `app/backend/solaris/rag/manifest.py`, `app/backend/solaris/rag/ingest.py`,
    `app/data/synthetic/docs/manifest.json`
  - Tests: `app/backend/tests/test_rag_ingest.py::test_allowlist_ignores_files_outside_manifest`,
    `app/backend/tests/test_rag_ingest.py::test_reingest_is_idempotent`
- **Límite (R07 n.º 7):** no hay límites de tamaño, celdas ni tiempo por documento (un xlsx malicioso puede
  bloquear la ingesta). El contenido oculto (hojas/columnas ocultas, texto invisible) aún no se marca (M4-T4).

### A8. Solo datos sintéticos en el demo
- **Qué:** planta, OEM, personas, lotes y documentos son ficticios (ADR-0004). El corpus se genera por script y
  un check automático valida su coherencia y la ausencia de marcas reales; security revisó el dataset (M1-T6,
  APPROVE: sin marcas reales ni datos personales reales).
- **Evidencia:**
  - Código: `app/data/synthetic/docs/build_corpus.py`, `app/data/synthetic/docs/check_corpus.py`,
    `app/data/synthetic/PLANT.md`
  - Traza: `raw/sessions/2026-09-25_security_M1-T6.md`
- **Límite:** es una medida de **demo**. En un piloto, los datos serán reales y aplica todo el DPA.

### A9. Otras medidas implementadas de apoyo
- La base de datos del demo solo escucha en `127.0.0.1` (`docker-compose.yml`).
- Ruta única de LLM: `route()` fija modelo y proveedor por tarea; una ficha sin `data_collection: deny` no
  carga (`app/backend/solaris/llm/router.py`, `app/backend/solaris/llm/config.py`,
  `app/backend/tests/test_llm_route.py::test_per_call_opts_allowed_but_model_and_provider_locked`).
- Modelos locales con revisión fijada (embeddings, rerank, OCR): ver `docs-compliance/ficha-modelos.md`.

<!-- check_evidencias: fin -->

---

## B. Lo que falta antes de un piloto con datos reales

Ninguno de estos controles existe hoy. Fechas objetivo **[H] a confirmar por el fundador**; la condición dura es
"antes de cargar el primer dato real".

| # | Carencia | Riesgo / origen | Qué hace falta | Objetivo |
|---|---|---|---|---|
| B1 | Auth de demo (R07 n.º 1, 2, 5) | R07 | IdP (Keycloak o federación con Entra ID/AD del cliente, OIDC), MFA, sesiones persistentes, `/docs` protegido, límite de intentos por IP/global | Antes del piloto |
| B2 | Sin ancla externa de la cadena de audit | F08, M4-T2 | Publicar periódicamente el hash de cabeza fuera de la BD (almacenamiento WORM o firmado) y verificar contra el ancla | Antes del piloto (plan en M6-T3) |
| B3 | Sin ruta de modelos solo UE | R01, R07 n.º 6 | Ruta conmutable por config y probada: `only` con proveedores UE, `zdr: true`, política por modelo, o inferencia local (vLLM). Security la firma | Antes del piloto |
| B4 | Sin TLS | R07 n.º 1 | TLS 1.2+ (objetivo 1.3) en API y conexiones a BD fuera del host | Antes del piloto |
| B5 | Audit del backend fail-open y con extractos de prompt | M4-T2 riesgo 4 | `AUDIT_REQUIRED=true` y `AUDIT_PROMPT_MODE=hash` (minimización RGPD) | Antes del piloto |
| B6 | Retención del audit sin implementar | E3-US3, DPA | Retención configurable (1 año por defecto) **compatible** con el trigger de inmutabilidad (p. ej. particiones por periodo que se archivan y eliminan con procedimiento de doble control y ancla) | Antes del piloto |
| B7 | Cifrado en reposo no configurado | Research §2.3 | Volumen o BD cifrados (AES-256) con gestión de claves (KMS/Vault); copias cifradas | Antes del piloto |
| B8 | Sin copias de seguridad ni plan de continuidad | NIS2 | Backups probados, RPO/RTO definidos, restauración ensayada | Antes del piloto |
| B9 | HITL aún no implementado (F06, M3-T4) | ADR-0005 | Interrupción tras D4 y aprobación por API con test 403 | M3 (antes del demo) |
| B10 | Aviso de IA del art. 50 aún no implementado (F11, M4-T3/M5-T2) | AI Act | Flag `ai_generated` en la API y aviso visible en toda salida | M4/M5 (antes del demo) |
| B11 | Suite red-team incompleta (M4-T4) | R03 | 6/6 casos en verde, contenido oculto marcado | M4 (antes del demo) |
| B12 | Límites de parsing en la ingesta | R07 n.º 7 | Límites de tamaño, celdas, filas y tiempo por documento | Antes del piloto |
| B13 | Reranker CC-BY-NC activable | R07 n.º 8 | Lista de modelos permitidos en código | Antes del piloto |
| B14 | Escalado del índice vectorial | R07 n.º 4 | Revisar SECURITY DEFINER vs RLS con identidad propagada (`SET LOCAL` + RLS) | Antes de corpus > ~50k fragmentos |
| B15 | Aislamiento multiinquilino | Research §2.3 | Esquema o BD por cliente; el demo es monoinquilino | Antes del 2.º cliente |
| B16 | Medidas organizativas | NIS2, RGPD | Política de seguridad, registro de actividades, procedimiento de incidentes, gestión de vulnerabilidades (hoy: `pip-audit` manual en M2-T8), formación | Ver cuestionario NIS2 |
