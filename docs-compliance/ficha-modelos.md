<!-- GENERADO por docs-compliance/gen_ficha_modelos.py a partir de models.yaml, settings.py y uv.lock. NO EDITAR A MANO: edita la fuente y regenera. -->

# Ficha de modelos — Solaris (Illarium Industrial OS)

> **BORRADOR — requiere revisión legal.** Documento del pack de cumplimiento (M4-T5).
> Estado: demo con **datos 100 % sintéticos** (ADR-0004). No apto como ficha de un piloto con datos
> reales hasta que exista la ruta solo UE (R01) y M3-T5 fije los modelos definitivos.

## 1. Modelos de lenguaje (LLM) por tarea

Todas las llamadas pasan por `solaris.llm.route()` → OpenRouter (ADR-0003, F10). El modelo y el proveedor
no se pueden cambiar por llamada; cambiar de modelo = editar `app/backend/config/models.yaml`.
Una ficha con `data_collection` distinto de `deny` no carga (`app/backend/solaris/llm/config.py`).

| Tarea | Modelo primario | Procedencia | Fallback | Procedencia fallback | max_tokens / temp. | eval_score |
|---|---|---|---|---|---|---|
| `rag_answer` | `deepseek/deepseek-chat` | DeepSeek (CN) | `mistralai/mistral-medium-3` | Mistral AI (FR) | 1500 / 0.1 | pendiente M3-T5 |
| `complaint_parse` | `deepseek/deepseek-chat` | DeepSeek (CN) | `mistralai/mistral-medium-3` | Mistral AI (FR) | 1200 / 0.0 | pendiente M3-T5 |
| `8d_draft` | `deepseek/deepseek-chat` | DeepSeek (CN) | `mistralai/mistral-medium-3` | Mistral AI (FR) | 4000 / 0.2 | pendiente M3-T5 |
| `translate` | `deepseek/deepseek-chat` | DeepSeek (CN) | `mistralai/mistral-medium-3` | Mistral AI (FR) | 2000 / 0.0 | pendiente M3-T5 |

### Política de proveedor (objeto `provider` de OpenRouter) y nota de región

- **Tareas:** `rag_answer`, `complaint_parse`, `8d_draft`, `translate`
  - **Política:** `data_collection: deny` · `allow_fallbacks: true` · `zdr`: sin activar · `only`: sin restringir
  - **Nota de región (literal de models.yaml):** Modelo de pesos abiertos de origen CN servido por proveedores de OpenRouter (mayoría EE. UU.); no hay garantía de región UE. Aceptable solo con datos sintéticos. Fallback de origen UE (Mistral, FR). Tensión con soberanía: R01.

### Lectura de security (no generada: criterio fijo)

- La **procedencia** es la organización que publica el modelo, **no** el lugar donde se ejecuta. Con
  OpenRouter, la región real de inferencia depende del proveedor que elija el enrutado; hoy no hay
  restricción `only` a proveedores UE, así que **no hay garantía de región UE** para ninguna tarea.
- La misma política se aplica al primario y al fallback (R07 n.º 6 / M2-T8 S5). La ruta solo UE necesita
  política por modelo, `zdr: true` y `only` con proveedores UE antes de un piloto.
- `eval_score` vacío = los modelos aún no se han medido contra el golden set (M3-T5).

## 2. Modelos locales (se ejecutan en el equipo; no envían datos a terceros)

Se descargan una vez (revisión fijada) y corren con ONNX Runtime 1.30.0 en local. ADR-0003 no aplica: no son llamadas LLM.

| Uso | Modelo | Artefacto / revisión | Procedencia | Licencia | Estado |
|---|---|---|---|---|---|
| Embeddings (F01/F02) | `intfloat/multilingual-e5-large` | `qdrant/multilingual-e5-large-onnx` @ `ac6781cd1cf8` | Microsoft (intfloat) (US) | MIT | Por defecto |
| Rerank (F02) | `BAAI/bge-reranker-base` | `BAAI/bge-reranker-base` @ `2cfc18c9415c` | BAAI (Beijing Academy of AI) (CN) | MIT | Por defecto |
| Rerank alternativo | `jinaai/jina-reranker-v2-base-multilingual` | configurable con `RERANK_MODEL` | Jina AI (DE) | **CC-BY-NC-4.0 (NO comercial)** | **No usar en entornos comerciales.** Sin guarda en código todavía (M2-T8 L1, R07 n.º 8) |
| OCR de PDF escaneados (F01) | `rapidocr-onnxruntime` 1.4.4 | paquete pip (uv.lock) | RapidAI (modelos de PaddleOCR, Baidu) (CN) | Apache-2.0 (modelos PP-OCRv4, Apache-2.0) | Por defecto |

## 3. Qué falta para que esta ficha sea válida en un piloto

1. M3-T5: modelos ganadores por tarea, `eval_score`, coste por 8D y latencia p95.
2. Verificar qué proveedores de inferencia usa OpenRouter para cada modelo y su región, y si `zdr: true`
   es viable (si no, documentarlo aquí).
3. Ruta solo UE conmutable por config y probada, con política por modelo (R01, R07 n.º 6).
4. Guarda contra el reranker CC-BY-NC (R07 n.º 8).
5. Añadir versión exacta del modelo servido y proveedor efectivo por llamada (ya queda en el audit
   `llm_call`: `model_used`, `provider`, `fallback_used`).
