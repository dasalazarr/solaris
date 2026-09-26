"""Agente 8D D1–D4 (M3-T3, F04): grafo LangGraph con checkpoints en Postgres.

- `graph.build_graph` / `graph.run_case` / `graph.view`: motor de estado (LangGraph).
- `nodes`: nodos (E/S con MCP, RAG y LLM); `domain`: reglas de dominio en Python puro;
  `envelope`: sobre de datos y validación de la salida del modelo; `store`: casos y checkpointer.
- `api`: `POST /8d`, `GET /8d/{case_id}` y `GET /8d/{case_id}/events` (SSE).
"""
