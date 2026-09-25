# Solaris — Log de evolución

> Log cronológico, **solo se anexa** (equivale a `logs.md` en WikiSkill). Una entrada por sesión o iteración, con la más reciente al final.
> Formato: `## YYYY-MM-DD · <rol> · <hito>/<tarea>`, seguido de lo hecho, lo aprendido (patrones creados o editados), el resultado del gate y la traza en `raw/sessions/`.

## 2026-09-24 · product · M0/brainstorm + scaffolding
- **Hecho:** brainstorm de problemas, features y oportunidades sobre `raw/research/IllariumOS.md`. Se adopta WikiSkill (ADR-0001) y se siembran 7 P, 12 F, 8 L, 5 O, 6 H, 6 R, 5 ADR y 2 PAT. Se crean las skills, los agentes y `plan/`.
- **Decisiones:**
  - Cuña del demo: 8D en automoción.
  - Stack objetivo reducido (ADR-0002).
  - OpenRouter con evaluación de calidad-precio y preferencia por DeepSeek (ADR-0003), con la tensión de soberanía explícita en R01.
  - Datos sintéticos (ADR-0004).
- **Aprendido:** PAT-001 (un demo, una cuña), PAT-002 (tensiones explícitas en ADR).
- **Calendario crítico:** la ayuda foral cierra el 06/11/2026 (O04), así que el demo debe estar listo a mediados de octubre.
- **Gate:** `wiki_lint.py` OK.
- **Traza:** `raw/sessions/2026-09-24_product_brainstorm.md`.

## 2026-09-24 · product · M1-T1
- **Hecho:** ficha de la planta ficticia (`app/data/synthetic/PLANT.md`) + `acl.json`. Es la fuente de verdad para el corpus, el ERP, las reclamaciones y el golden set. Dos familias de recurrencia con causa raíz fijada (A: soldadura AR-1003; B: rebaba AR-1007).
- **Aprendido:** PAT-003 (nombres ficticios vs marcas reales). Se renombra "Ebro" → "Ribera".
- **Gate:** consistencia 9/9 carpetas; personas cubiertas → Accepted (skill-impact #1).
- **Traza:** `raw/sessions/2026-09-24_product_M1-T1.md`.

## 2026-09-24 · dev · M1-T3
- **Hecho:** ERP mock (`erp` schema + seed determinista), docker-compose con pgvector, `.env.example` y smoke tests. PLANT.md §11 fija el registro de 8D y reclamaciones abiertas.
- **Aprendido:** PAT-004 (la verdad de evaluación fuera del alcance del agente). Corrección del grado del acero en PLANT.md.
- **Gate:** smoke 7/7, seed idempotente → Accepted (skill-impact #2).
- **Traza:** `raw/sessions/2026-09-24_dev_M1-T3.md`.

## 2026-09-25 · dev · M2-T1
- **Hecho:** esqueleto del backend (FastAPI, uv, ruff, pytest) y `solaris.llm.route()` sobre OpenRouter con ficha de modelo por tarea (F10 → building). Primario DeepSeek, fallback Mistral (UE).
- **Aprendido:** la política de privacidad del proveedor se impone en código, no por convención (fichas sin `deny` no cargan). Se anota en F10 y R01.
- **Gate:** 13 tests + ruff OK → Accepted (skill-impact #3). Revisión de security en M2-T8 con 6 puntos anotados en la traza.
- **Traza:** `raw/sessions/2026-09-25_dev_M2-T1.md`.

## 2026-09-25 · dev · M2-T2
- **Hecho:** esquema `rag` (documents, chunks vector(1024) + tsvector `simple`, folder_acl, fmea_rows) con HNSW y GIN, funciones `visible_*` con ACL antes del ranking, runner de migraciones y carga de ACL. F01/F02 → building.
- **Aprendido:** PAT-005. El filtro en SQL funciona, pero el backend como superusuario puede saltárselo; queda como DoD de M4-T1 (rol `solaris_app`). Las migraciones van por runner y no por el init de compose (desviación justificada).
- **Gate:** 26 tests (BD reales) + ruff → Accepted (skill-impact #4).
- **Traza:** `raw/sessions/2026-09-25_dev_M2-T2.md`.

## 2026-09-25 · dev · M3-T1
- **Hecho:** servidor MCP erp-mock con 7 herramientas de solo lectura y consultas trazadas, identidad on-behalf-of vía `_meta` y rol de BD `erp_reader`. F05 → building. Se adelanta de M3 porque M2-T3 espera al corpus.
- **Aprendido:** la solo lectura queda garantizada por la BD, pero la ACL por tabla vive en Python (se amplía PAT-005). Los 6 puntos de seguridad se añaden al DoD de M3-T6.
- **Gate:** 23 + 29 tests con BD real + ruff → Accepted (skill-impact #5).
- **Traza:** `raw/sessions/2026-09-25_dev_M3-T1.md`.

## 2026-09-25 · product · M1-T2
- **Hecho:** corpus sintético de 41 documentos + manifest (15 8D coherentes con el ERP, AMFE sucio, IT escaneada, pistas de las familias A/B sin etiquetarlas).
- **Aprendido:**
  - PAT-006: congelar los generadores cuando otro artefacto cita sus IDs; los irrealismos del seed se corrigen solo por post-proceso.
  - Unidades de cita (page/section/sheet), anotadas en F02 y en el DoD de M1-T5.
  - Exclusiones de la ingesta añadidas al DoD de M2-T3.
  - PLANT.md: tipo `REG` y la estación de tuercas de CR-02.
- **Gate:** `check_corpus.py` OK → Accepted (skill-impact #6).
- **Traza:** `raw/sessions/2026-09-25_product_M1-T2.md`.

## 2026-09-25 · security · M4-T2
- **Hecho:** audit log de solo anexar con garantías en BD: trigger + roles + cadena de hash. Integrado en `llm.route()` (con `fallback_used`) y en el MCP (fail-closed, rechazos de esquema). Endpoints de consulta y export. F08 → building. Tests aislados en `solaris_test`.
- **Aprendido:** fail-closed como patrón para el audit. Riesgo residual (sin ancla externa de la cadena), añadido a M6-T3. Los puntos de seguridad heredados se cierran sobre todo en M4-T1 (auth, `solaris_app`, `_meta`, PUBLIC).
- **Gate:** 52 + 1 xfail / 27 tests + ruff; APPROVE → Accepted (skill-impact #7).
- **Traza:** `raw/sessions/2026-09-25_security_M4-T2.md`.

## 2026-09-25 · product · M1-T4
- **Hecho:** 5 reclamaciones abiertas (4 PDF + 1 EML) coherentes con el ERP.
  - #1 caso estrella (familia A), #2 familia B, #3 **distractor**, #4 con una causa distinta al 8D previo con el mismo síntoma, #5 con 3 variantes de inyección y códigos testigo.
  - La verdad del escenario vive en `app/evals/scenario_truth.json`, fuera del corpus (PAT-004).
- **Aprendido:** hueco en la contención: piezas no expedidas de lotes `released` (anotado en F05 → M3). Lista de irrealismos del seed aceptados, añadida a PAT-006.
- **Gate:** `check_complaints.py` + `check_corpus.py` OK → Accepted (skill-impact #8).
- **Traza:** `raw/sessions/2026-09-25_product_M1-T4.md`.

## 2026-09-25 · dev · M2-T3
- **Hecho:** ingesta del corpus con allowlist por manifest, chunking por locator, OCR y embeddings locales 1024-d. Primer paso de F03 (36 filas de AMFE, 7 del AMFE sucio). F03 → building.
- **Aprendido:** desviación de ADR-0002 (sin Docling), registrada en el ADR. Un documento con muchos chunks (REG de boquillas, 94) domina el ranking; anotado en el DoD de M2-T5. 7 puntos de security al DoD de M2-T8.
- **Gate:** 74 + 1 xfail / 27 tests, ruff, ingesta real OK → Accepted (skill-impact #9).
- **Traza:** `raw/sessions/2026-09-25_dev_M2-T3.md`.

## 2026-09-25 · product · M1-T5
- **Hecho:** golden set de 50 Q&A y 5 casos 8D, con validador robusto (detecta mutaciones de página, versión, sección, hoja, filas, ACL, etiquetas y contención).
- **Aprendido:** dos criterios de F04/M3 eran imposibles con el escenario; se ajustan (skill-impact #11). Una pieza sin AMFE es un hallazgo de valor, no un fallo del agente. 3 errores en la verdad del escenario → nueva tarea M1-T7.
- **Gate:** `validate_golden.py` OK → Accepted (skill-impact #10).
- **Traza:** `raw/sessions/2026-09-25_product_M1-T5.md`.
