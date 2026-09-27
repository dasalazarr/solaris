-- 010_audit_hitl — Tipos de evento `approval_denied` e `instruction_ignored` en el audit log (M3-T4,
-- F06/F08). DATOS SINTÉTICOS. La aplica `uv run python -m solaris.db.migrate` dentro de una
-- transacción; no añadir BEGIN/COMMIT aquí. El nombre contiene `_audit` para que
-- solaris.audit.testdb la aplique también a la BD de tests `solaris_test`. Mismo patrón que 004 y 009.
--
-- * `approval` (ya existía, 003): una decisión humana sobre el borrador 8D (aprobar o rechazar),
--   con usuario, versión (hash de D1–D4), % editado y comentario.
-- * `approval_denied`: un intento de aprobar, rechazar, reanudar o exportar sin permiso o sin una
--   aprobación válida (rol no aprobador, versión antigua, caso ya decidido, export sin aprobar,
--   el nodo `hitl_gate` del grafo sin registro válido).
-- * `instruction_ignored`: una instrucción embebida en contenido externo (reclamación) detectada y
--   neutralizada. Sustituye al `llm_call` con `outcome: not_called` del parser (punto S-T2-1 de
--   raw/sessions/2026-09-26_dev_M3-T2.md). Solo metadatos (canal, ubicación, regla), nunca el texto.
-- Cambiar el CHECK no toca filas: ALTER TABLE no dispara el trigger de inmutabilidad ni la cadena.

ALTER TABLE audit.events DROP CONSTRAINT events_event_type_check;
ALTER TABLE audit.events ADD CONSTRAINT events_event_type_check CHECK (event_type IN (
    'llm_call', 'retrieval', 'tool_call', 'tool_denied', 'write_attempt',
    'approval', 'export', 'auth', 'ingest', 'agent_step',
    'approval_denied', 'instruction_ignored'));
