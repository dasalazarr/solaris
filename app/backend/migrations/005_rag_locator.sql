-- 005_rag_locator — Unidad de cita generalizada (M2-T3, F01/F02). DATOS SINTÉTICOS.
-- La aplica `uv run python -m solaris.db.migrate` (desde app/backend) dentro de una transacción; no
-- añadir BEGIN/COMMIT aquí.
--
-- El corpus tiene tres unidades de cita (M1-T2): los PDF citan página, los DOCX citan sección
-- (D1–D8 en los 8D, apartado en IT/TPL/EVAL) y los XLSX citan hoja + rango de filas. La cita pasa
-- de {doc_id, version, page} a {doc_id, version, locator}.
--  * rag.chunks.locator jsonb: {"page": 3} | {"section": "D4", "heading": "..."} |
--    {"sheet": "AMFE", "rows": [11, 20]}; opcionalmente "part" (sección partida por longitud) y
--    "ocr": true (texto obtenido por OCR). Las columnas `page` y `section` se siguen rellenando
--    (redundantes) para filtrar y ordenar sin tocar el JSON.
--  * rag.fmea_rows.sheet: hoja de origen de la fila (la cita de una fila AMFE es hoja + fila).
-- rag.visible_chunks() devuelve SETOF rag.chunks con `c.*`: incluye la columna nueva sin redefinirla.

ALTER TABLE rag.chunks
    ADD COLUMN locator jsonb NOT NULL DEFAULT '{}'::jsonb
        CHECK (jsonb_typeof(locator) = 'object' AND octet_length(locator::text) <= 1024);

ALTER TABLE rag.fmea_rows ADD COLUMN sheet text;
