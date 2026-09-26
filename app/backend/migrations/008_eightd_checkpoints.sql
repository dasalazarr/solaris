-- 008_eightd_checkpoints — Casos 8D y checkpoints de LangGraph (M3-T3, F04/F06). DATOS SINTÉTICOS.
-- La aplica `uv run python -m solaris.db.migrate` (desde app/backend) dentro de una transacción; no
-- añadir BEGIN/COMMIT aquí. Solo para la BD del demo (los tests del grafo usan un checkpointer en
-- memoria; los de este esquema se saltan si la migración no está aplicada). Idempotente respecto a
-- roles (son de clúster).
--
-- Rol de BD `eightd_app` (y no `solaris_app` ni el superusuario):
--   * El checkpointer de LangGraph ESCRIBE (INSERT ... ON CONFLICT DO UPDATE) en cada paso del grafo.
--     `solaris_app` es de solo lectura por diseño (default_transaction_read_only, 006) y lee el corpus
--     vía rag.visible_*: darle escritura rompería esa garantía. El superusuario queda para
--     administración (PAT-005).
--   * `eightd_app` solo ve el esquema `eightd`: SELECT/INSERT/UPDATE en las tablas del checkpointer y
--     SELECT/INSERT en `cases`. Sin DELETE ni TRUNCATE (un caso no se borra desde la API; la
--     retención es tarea del piloto), sin CREATE (las tablas las crea esta migración, NO
--     `PostgresSaver.setup()`), sin acceso a rag, erp ni audit.
--   * search_path fijado en el rol: el SQL del checkpointer usa nombres sin esquema.
--
-- Las tablas del checkpointer replican `langgraph.checkpoint.postgres.base.MIGRATIONS` (v0–v9) de
-- langgraph-checkpoint-postgres 3.1.x, en el esquema `eightd` y con la versión registrada en
-- `checkpoint_migrations`, así `setup()` no hace falta. Un cambio de versión de la librería que
-- añada migraciones exige una migración nueva aquí (test_eightd_store la compara).
--
-- La contraseña NO está aquí: `solaris.db.migrate` la fija desde EIGHTD_APP_PASSWORD (.env) con un
-- verificador SCRAM (solaris.db.roles). Sin ella el rol no inicia sesión (falla cerrado).

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'eightd_app') THEN
        CREATE ROLE eightd_app LOGIN;
    END IF;
END
$$;

ALTER ROLE eightd_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS
    NOINHERIT CONNECTION LIMIT 20;
ALTER ROLE eightd_app SET search_path = eightd;
ALTER ROLE eightd_app SET statement_timeout = '15s';
ALTER ROLE eightd_app SET idle_in_transaction_session_timeout = '30s';

CREATE SCHEMA IF NOT EXISTS eightd;
REVOKE ALL ON SCHEMA eightd FROM PUBLIC;

-- Caso 8D: quién lo creó y el fichero de la reclamación (la UI de M5 lo muestra al hacer clic en
-- una cita). El borrador, el estado y el progreso viven en los checkpoints del hilo = case_id.
CREATE TABLE eightd.cases (
    case_id       uuid PRIMARY KEY,
    complaint_id  text CHECK (complaint_id IS NULL OR complaint_id ~ '^C-[A-Z]{4}-\d{4}-\d{4}$'),
    created_by    text NOT NULL,
    created_role  text NOT NULL,
    created_at    timestamptz NOT NULL DEFAULT now(),
    source        text NOT NULL CHECK (source IN ('upload', 'inbox')),
    filename      text NOT NULL CHECK (length(filename) BETWEEN 1 AND 200),
    sha256        text NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    size          int  NOT NULL CHECK (size > 0 AND size <= 10485760),
    file          bytea NOT NULL CHECK (octet_length(file) = size)
);
CREATE INDEX cases_complaint_idx ON eightd.cases (complaint_id);

CREATE TABLE eightd.checkpoint_migrations (
    v INTEGER PRIMARY KEY
);
CREATE TABLE eightd.checkpoints (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    checkpoint_id TEXT NOT NULL,
    parent_checkpoint_id TEXT,
    type TEXT,
    checkpoint JSONB NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
);
CREATE TABLE eightd.checkpoint_blobs (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    channel TEXT NOT NULL,
    version TEXT NOT NULL,
    type TEXT NOT NULL,
    blob BYTEA,
    PRIMARY KEY (thread_id, checkpoint_ns, channel, version)
);
CREATE TABLE eightd.checkpoint_writes (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    checkpoint_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    idx INTEGER NOT NULL,
    channel TEXT NOT NULL,
    type TEXT,
    blob BYTEA NOT NULL,
    task_path TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
);
CREATE INDEX checkpoints_thread_id_idx ON eightd.checkpoints (thread_id);
CREATE INDEX checkpoint_blobs_thread_id_idx ON eightd.checkpoint_blobs (thread_id);
CREATE INDEX checkpoint_writes_thread_id_idx ON eightd.checkpoint_writes (thread_id);
INSERT INTO eightd.checkpoint_migrations (v) SELECT generate_series(0, 9);

-- --- privilegios ----------------------------------------------------------------------------------
REVOKE ALL ON ALL TABLES IN SCHEMA eightd FROM PUBLIC, eightd_app;
GRANT USAGE ON SCHEMA eightd TO eightd_app;
GRANT SELECT, INSERT ON eightd.cases TO eightd_app;
GRANT SELECT, INSERT, UPDATE ON eightd.checkpoints, eightd.checkpoint_blobs,
    eightd.checkpoint_writes TO eightd_app;
GRANT SELECT ON eightd.checkpoint_migrations TO eightd_app;

-- Aislamiento: nada en rag, erp ni audit (por si una migración futura concediera a PUBLIC).
DO $$
DECLARE
    s text;
BEGIN
    FOREACH s IN ARRAY ARRAY['rag', 'erp', 'audit'] LOOP
        IF EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = s) THEN
            EXECUTE format('REVOKE ALL ON SCHEMA %I FROM eightd_app', s);
            EXECUTE format('REVOKE ALL ON ALL TABLES IN SCHEMA %I FROM eightd_app', s);
        END IF;
    END LOOP;
    EXECUTE format('GRANT CONNECT ON DATABASE %I TO eightd_app', current_database());
END
$$;
