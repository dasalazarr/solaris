-- 001_rag — Esquema RAG de Solaris (M2-T2). DATOS SINTÉTICOS (ADR-0004).
-- Sirve a: M2-T3 (ingesta F01), M2-T4 (AMFE F03), M2-T5 (recuperación híbrida con ACL), M2-T6 (citas F02).
-- La aplica `uv run python -m solaris.db.migrate` (desde app/backend) dentro de una transacción; no
-- añadir BEGIN/COMMIT aquí.
--
-- Decisiones:
--  * embedding vector(1024): dimensión nativa de BGE-M3 y de multilingual-e5-large, los dos
--    candidatos multilingües (ES/EN) de F01. Cabe en HNSW (límite de pgvector: 2000 dims para `vector`).
--    Cambiar de modelo a otra dimensión exige una migración nueva y re-ingesta (no se mezclan espacios).
--  * tsv con configuración 'simple': el corpus mezcla ES y EN en el mismo documento. 'spanish'
--    estemiza mal el inglés y elimina stopwords ES que en EN son tokens válidos; además la rama léxica
--    de la búsqueda híbrida existe sobre todo para códigos exactos (AR-1004, 8D-2025-014, cotas),
--    que 'simple' conserva intactos. La morfología (plurales, conjugaciones) la cubre la rama
--    semántica con embeddings multilingües.
--  * ACL: deny-by-default. Un chunk solo es visible si existe una fila (folder, role) en folder_acl.
--    Carpeta sin fila => invisible para todos (incluido admin). El filtro se aplica en SQL mediante
--    rag.visible_chunks(role) ANTES de cualquier ORDER BY de ranking.

CREATE EXTENSION IF NOT EXISTS vector;
CREATE SCHEMA IF NOT EXISTS rag;

-- Permisos por carpeta (derivados de app/data/synthetic/acl.json → solaris.rag.acl.sync_folder_acl).
CREATE TABLE rag.folder_acl (
    folder  text NOT NULL CHECK (folder ~ '^[a-z0-9_-]+(/[a-z0-9_-]+)*$'),
    role    text NOT NULL CHECK (role ~ '^[a-z_]+$'),
    PRIMARY KEY (folder, role)
);
CREATE INDEX folder_acl_role_idx ON rag.folder_acl (role, folder);

-- Un documento por (doc_id, version). Una versión nueva es una fila nueva (citas {doc_id, version, page}).
CREATE TABLE rag.documents (
    doc_id       text NOT NULL,
    version      text NOT NULL,
    title        text NOT NULL,
    path         text NOT NULL,                   -- relativo a la raíz del corpus
    folder       text NOT NULL,                   -- p. ej. 'calidad/8d'; gobierna la ACL
    doc_type     text NOT NULL,                   -- '8d', 'amfe', 'plan_control', 'it', ...
    language     text NOT NULL CHECK (language IN ('es', 'en', 'mixed')),
    part_refs    text[] NOT NULL DEFAULT '{}',    -- AR-xxxx citadas por el documento
    pages        int CHECK (pages IS NULL OR pages > 0),
    sha256       text NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$'),  -- idempotencia de la ingesta
    ingested_at  timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (doc_id, version),
    -- Destino de la FK compuesta de chunks/fmea_rows: garantiza que el folder desnormalizado
    -- coincide siempre con el del documento (y se propaga en un re-sync con ON UPDATE CASCADE).
    UNIQUE (doc_id, version, folder)
);
CREATE INDEX documents_folder_idx ON rag.documents (folder);
CREATE INDEX documents_part_refs_idx ON rag.documents USING gin (part_refs);

CREATE TABLE rag.chunks (
    id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    doc_id     text NOT NULL,
    version    text NOT NULL,
    chunk_no   int  NOT NULL CHECK (chunk_no >= 0),   -- orden dentro del documento
    page       int  CHECK (page IS NULL OR page > 0), -- NULL solo si el formato no pagina (xlsx)
    section    text,                                  -- ruta de encabezados, p. ej. 'D4 > Causa raíz'
    content    text NOT NULL CHECK (length(content) > 0),
    tsv        tsvector GENERATED ALWAYS AS (to_tsvector('simple'::regconfig, content)) STORED,
    embedding  vector(1024),                          -- NULL hasta calcularlo; la rama semántica lo excluye
    folder     text NOT NULL,                         -- desnormalizado para filtrar sin JOIN a documents
    UNIQUE (doc_id, version, chunk_no),
    FOREIGN KEY (doc_id, version, folder)
        REFERENCES rag.documents (doc_id, version, folder)
        ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE INDEX chunks_embedding_hnsw_idx ON rag.chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX chunks_tsv_gin_idx ON rag.chunks USING gin (tsv);
CREATE INDEX chunks_folder_idx ON rag.chunks (folder);
CREATE INDEX chunks_doc_idx ON rag.chunks (doc_id, version);

-- F03: filas de AMFE estructuradas. Los campos tipados admiten NULL (AMFE "sucio"); la fila
-- original, tal cual se leyó, queda en raw para trazabilidad y para medir exactitud por campo.
CREATE TABLE rag.fmea_rows (
    doc_id              text NOT NULL,
    version             text NOT NULL,
    row_no              int  NOT NULL CHECK (row_no > 0),  -- fila de la hoja (cita navegable)
    process_step        text,
    function            text,
    failure_mode        text,
    effect              text,
    severity            smallint CHECK (severity BETWEEN 1 AND 10),
    cause               text,
    occurrence          smallint CHECK (occurrence BETWEEN 1 AND 10),
    prevention_control  text,
    detection_control   text,
    detection           smallint CHECK (detection BETWEEN 1 AND 10),
    rpn                 int CHECK (rpn BETWEEN 1 AND 1000), -- tal como figura en la hoja (puede no cuadrar con S*O*D)
    actions             text,
    raw                 jsonb NOT NULL,
    folder              text NOT NULL,                      -- misma ACL que el documento origen
    PRIMARY KEY (doc_id, version, row_no),
    FOREIGN KEY (doc_id, version, folder)
        REFERENCES rag.documents (doc_id, version, folder)
        ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE INDEX fmea_rows_folder_idx ON rag.fmea_rows (folder);
CREATE INDEX fmea_rows_doc_idx ON rag.fmea_rows (doc_id, version);

-- Recuperación con ACL en SQL. Funciones LANGUAGE sql STABLE, sin SECURITY DEFINER ni SET: el
-- planificador las "inlinea" y el EXISTS se combina con el ORDER BY/LIMIT del llamador, así el
-- filtro de rol ocurre antes del ranking. Rol NULL o desconocido => 0 filas.
-- Patrón para M2-T5 (el rol lo resuelve el backend desde el usuario autenticado, nunca el LLM):
--   SET LOCAL hnsw.iterative_scan = strict_order;   -- evita devolver < k tras filtrar
--   SELECT id, doc_id, version, page, content
--     FROM rag.visible_chunks(%(role)s)
--    WHERE embedding IS NOT NULL
--    ORDER BY embedding <=> %(qvec)s::vector LIMIT %(k)s;
--   SELECT ... FROM rag.visible_chunks(%(role)s)
--    WHERE tsv @@ websearch_to_tsquery('simple', %(q)s)
--    ORDER BY ts_rank_cd(tsv, websearch_to_tsquery('simple', %(q)s)) DESC LIMIT %(k)s;
CREATE FUNCTION rag.visible_chunks(p_role text)
RETURNS SETOF rag.chunks
LANGUAGE sql STABLE
AS $$
    SELECT c.*
      FROM rag.chunks c
     WHERE EXISTS (SELECT 1 FROM rag.folder_acl a
                    WHERE a.folder = c.folder AND a.role = p_role)
$$;

CREATE FUNCTION rag.visible_fmea_rows(p_role text)
RETURNS SETOF rag.fmea_rows
LANGUAGE sql STABLE
AS $$
    SELECT f.*
      FROM rag.fmea_rows f
     WHERE EXISTS (SELECT 1 FROM rag.folder_acl a
                    WHERE a.folder = f.folder AND a.role = p_role)
$$;

COMMENT ON FUNCTION rag.visible_chunks(text) IS
    'Chunks visibles para un rol (deny-by-default). Único punto de entrada de la recuperación (M2-T5).';
COMMENT ON FUNCTION rag.visible_fmea_rows(text) IS
    'Filas AMFE visibles para un rol (deny-by-default).';
