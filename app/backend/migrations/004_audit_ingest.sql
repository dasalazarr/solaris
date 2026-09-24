-- 004_audit_ingest — Tipo de evento `ingest` en el audit log (M2-T3, F01/F08). DATOS SINTÉTICOS.
-- La aplica `uv run python -m solaris.db.migrate` (desde app/backend) dentro de una transacción; no
-- añadir BEGIN/COMMIT aquí. El nombre contiene `_audit` para que solaris.audit.testdb la aplique
-- también a la BD de tests `solaris_test`.
--
-- La ingesta (solaris.rag.ingest) registra un evento por documento con SOLO metadatos (doc_id,
-- versión, sha256, carpeta, acción y recuentos), nunca contenido. Cambiar el CHECK no toca filas:
-- ALTER TABLE no dispara el trigger de inmutabilidad (UPDATE/DELETE/TRUNCATE) ni altera la cadena.

ALTER TABLE audit.events DROP CONSTRAINT events_event_type_check;
ALTER TABLE audit.events ADD CONSTRAINT events_event_type_check CHECK (event_type IN (
    'llm_call', 'retrieval', 'tool_call', 'tool_denied', 'write_attempt',
    'approval', 'export', 'auth', 'ingest'));
