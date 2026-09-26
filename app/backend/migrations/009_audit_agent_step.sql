-- 009_audit_agent_step — Tipo de evento `agent_step` en el audit log (M3-T3, F04/F08). DATOS
-- SINTÉTICOS. La aplica `uv run python -m solaris.db.migrate` dentro de una transacción; no añadir
-- BEGIN/COMMIT aquí. El nombre contiene `_audit` para que solaris.audit.testdb la aplique también a
-- la BD de tests `solaris_test`. Mismo patrón que 004 (aceptado por security en M2-T8).
--
-- El grafo 8D registra un evento por nodo (intake, D1…D4, await_approval) con el principal real,
-- el case_id, el resultado, la duración y SOLO metadatos (ids de documentos citados, herramientas
-- MCP llamadas, recuentos y avisos). Nunca el texto del borrador ni de la reclamación. Las llamadas
-- LLM, las recuperaciones y las herramientas MCP siguen con sus tipos propios (llm_call,
-- retrieval, tool_call); `agent_step` es la línea de tiempo del caso que M5-T3/L07 muestra.
-- Cambiar el CHECK no toca filas: ALTER TABLE no dispara el trigger de inmutabilidad ni la cadena.

ALTER TABLE audit.events DROP CONSTRAINT events_event_type_check;
ALTER TABLE audit.events ADD CONSTRAINT events_event_type_check CHECK (event_type IN (
    'llm_call', 'retrieval', 'tool_call', 'tool_denied', 'write_attempt',
    'approval', 'export', 'auth', 'ingest', 'agent_step'));
