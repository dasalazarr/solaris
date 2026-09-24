---
name: dev-agent
description: Procedimientos del rol desarrollo en Solaris. Convenciones de código, arquitectura del demo (FastAPI + LangGraph + pgvector + MCP + Next.js), tests, evals y definición de hecho. Úsalo en tareas de hitos con rol dev.
---

# Rol desarrollo

## Arquitectura del demo ([[ADR-0002]])
```
app/
  backend/      FastAPI; solaris/{llm,rag,agents,audit,auth}/; tests/
  mcp/          erp_mock/ (solo lectura sobre Postgres o SQLite), docs/
  frontend/     Next.js (App Router), UI en español
  data/synthetic/  corpus documental + seed del ERP (lo genera product en M1)
  evals/        golden/*.jsonl, runner.py, redteam/
docker-compose.yml   postgres+pgvector, backend, mcp, frontend
.env.example         OPENROUTER_API_KEY=, DATABASE_URL=, ...
```

## Convenciones
- Python 3.12, `uv` para dependencias, `ruff` + `pytest`. TypeScript estricto en el frontend.
- **Lógica de dominio en Python puro**. LangGraph solo como motor de estado, checkpoints e interrupts.
- **LLM:** siempre `solaris.llm.route(task: str, messages, **opts)`. Resuelve el modelo desde `app/backend/config/models.yaml`, que es la ficha por tarea: modelo, proveedor, procedencia, coste y score. Usa OpenRouter con política ZDR cuando exista ([[ADR-0003]]).
- **RAG:** filtrado ACL **antes** de recuperar (en el SQL), nunca después de generar. Citas `{doc_id, version, page}` obligatorias. Sin evidencia se responde "no encontrado".
- **MCP:** herramientas declaradas con esquema, solo lectura y allowlist por rol. Cada llamada se registra en el audit con la consulta ejecutada.
- **HITL:** interrupt de LangGraph antes de D5 y antes de exportar. Una aprobación = usuario + versión + timestamp en el audit.
- El contenido de la reclamación se pasa al LLM **delimitado como datos** y nunca se concatena a las instrucciones del sistema.

## Definición de hecho (por defecto)
- Tests unitarios del cambio en verde (`pytest -q`) y lint limpio.
- Si toca RAG o agentes: ejecuta `python app/evals/runner.py --suite <suite>` y guarda el JSON en `raw/eval-runs/`.
- Si toca MCP, auth, prompts o audit: pide la revisión del rol security antes de marcar Accepted.
- Documenta los comandos nuevos en `CLAUDE.md`.

## Comparativa de modelos (F10/H04)
Mismo golden set y mismo prompt, al menos 3 modelos (DeepSeek y alternativas de calidad-precio). Registra la calidad (precisión de citas, % de hipótesis correctas), la latencia p95 y el coste por 8D. El resultado va en `raw/eval-runs/` y el resumen, en la página H04.
