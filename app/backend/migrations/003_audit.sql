-- 003_audit — Audit log de solo anexar con cadena de hash (M4-T2, F08). DATOS SINTÉTICOS.
-- La aplica `uv run python -m solaris.db.migrate` (desde app/backend) dentro de una transacción; no
-- añadir BEGIN/COMMIT aquí. Es idempotente respecto a roles (cluster) para poder aplicarse también a
-- la BD de tests `solaris_test` (solaris.audit.testdb).
--
-- Diseño (ver raw/sessions/2026-09-25_security_M4-T2.md):
--  * Roles:
--      audit_owner  NOLOGIN. Propietario de esquema, tabla, secuencia y funciones. Único con
--                   UPDATE/DELETE/TRUNCATE (implícitos por ser propietario), bloqueados por trigger.
--      audit_writer LOGIN. Solo USAGE del esquema + INSERT en audit.events. Sin SELECT (ni RETURNING)
--                   ni permiso sobre la secuencia: id, ts y hashes los fija el trigger.
--      audit_reader LOGIN. Solo USAGE + SELECT. Transacciones read-only por defecto.
--    Las contraseñas NO están aquí: el runner las fija desde AUDIT_WRITER_PASSWORD y
--    AUDIT_READER_PASSWORD (.env) con verificador SCRAM (solaris.db.roles). Sin ellas no hay login.
--  * Cadena de hash: BEFORE INSERT (SECURITY DEFINER como audit_owner, search_path fijo):
--      1. pg_advisory_xact_lock(AUDIT_LOCK) -> serializa a todos los escritores hasta el COMMIT.
--      2. lee el hash de la última fila confirmada (READ COMMITTED: snapshot nuevo tras el lock;
--         se RECHAZA insertar en REPEATABLE READ/SERIALIZABLE, que bifurcarían la cadena).
--      3. asigna id = nextval() DESPUÉS del lock (orden de id = orden de la cadena), ts =
--         clock_timestamp() (el escritor no puede fecharlo) y prev_hash.
--      4. hash = sha256(prev_hash || canónico) en hex. Génesis: prev_hash = 64 ceros.
--    Canónico v1 = 'solaris-audit-v1|' || netstring(id, ts_epoch_us, actor_user, actor_role,
--    event_type, case_id, source, model, provider, payload::text), netstring(x) = '<bytes>:<x>' o
--    '~' si NULL. Lo recalcula en Python, de forma independiente, solaris.audit.verify_chain().
--  * Inmutabilidad: trigger de sentencia BEFORE UPDATE OR DELETE OR TRUNCATE que lanza error a
--    TODOS (propietario y superusuario incluidos). Solo se salta desactivándolo explícitamente:
--      ALTER TABLE audit.events DISABLE TRIGGER audit_events_immutable;   -- propietario/superusuario
--    o con session_replication_role = replica (superusuario; esto desactiva también el trigger de
--    cadena, así que un INSERT falla por hash NOT NULL). Ambas son acciones deliberadas y la
--    manipulación resultante la detecta verify_chain() (salvo reescritura completa de la cadena o
--    truncado de la cola por un superusuario: para eso hay que anclar la cabeza fuera de la BD).

DO $$
BEGIN
    IF current_setting('server_encoding') <> 'UTF8' THEN
        RAISE EXCEPTION 'audit: el canónico asume server_encoding UTF8 (es %)',
            current_setting('server_encoding');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'audit_owner') THEN
        CREATE ROLE audit_owner NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'audit_writer') THEN
        CREATE ROLE audit_writer LOGIN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'audit_reader') THEN
        CREATE ROLE audit_reader LOGIN;
    END IF;
END
$$;

ALTER ROLE audit_owner NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS
    NOINHERIT;
ALTER ROLE audit_writer LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS
    NOINHERIT CONNECTION LIMIT 20;
ALTER ROLE audit_writer SET statement_timeout = '5s';
ALTER ROLE audit_writer SET idle_in_transaction_session_timeout = '30s';
ALTER ROLE audit_reader LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS
    NOINHERIT CONNECTION LIMIT 10;
ALTER ROLE audit_reader SET default_transaction_read_only = on;
ALTER ROLE audit_reader SET statement_timeout = '15s';
ALTER ROLE audit_reader SET idle_in_transaction_session_timeout = '30s';

CREATE SCHEMA audit AUTHORIZATION audit_owner;
REVOKE ALL ON SCHEMA audit FROM PUBLIC;

CREATE SEQUENCE audit.events_id_seq AS bigint;

-- id: equivale a bigserial, pero sin DEFAULT: lo asigna el trigger tras tomar el lock, de modo que
-- el orden por id coincide con el orden de la cadena aunque haya escritores concurrentes.
CREATE TABLE audit.events (
    id          bigint PRIMARY KEY,
    ts          timestamptz NOT NULL DEFAULT now(),
    actor_user  text,
    actor_role  text,
    event_type  text NOT NULL CHECK (event_type IN (
                    'llm_call', 'retrieval', 'tool_call', 'tool_denied', 'write_attempt',
                    'approval', 'export', 'auth')),
    case_id     text,
    source      text NOT NULL DEFAULT 'backend' CHECK (source ~ '^[a-z][a-z0-9_-]{0,31}$'),
    model       text,
    provider    text,
    payload     jsonb NOT NULL DEFAULT '{}'::jsonb
                CHECK (jsonb_typeof(payload) = 'object' AND octet_length(payload::text) <= 65536),
    prev_hash   text NOT NULL CHECK (prev_hash ~ '^[0-9a-f]{64}$'),
    hash        text NOT NULL UNIQUE CHECK (hash ~ '^[0-9a-f]{64}$')
);
ALTER SEQUENCE audit.events_id_seq OWNED BY audit.events.id;

CREATE INDEX events_ts_idx ON audit.events (ts);
CREATE INDEX events_type_ts_idx ON audit.events (event_type, ts);
CREATE INDEX events_actor_ts_idx ON audit.events (actor_user, ts);
CREATE INDEX events_case_idx ON audit.events (case_id) WHERE case_id IS NOT NULL;

COMMENT ON TABLE audit.events IS
    'Audit log de solo anexar (F08). Cadena sha256 por fila; UPDATE/DELETE/TRUNCATE bloqueados por '
    'trigger. Verificar con solaris.audit.verify_chain().';

-- Netstring de un campo: longitud en bytes UTF-8 + ':' + valor, o '~' si es NULL.
CREATE FUNCTION audit.ns(v text) RETURNS text
    LANGUAGE sql IMMUTABLE PARALLEL SAFE
    SET search_path = pg_catalog
    RETURN CASE WHEN v IS NULL THEN '~' ELSE octet_length(v)::text || ':' || v END;

CREATE FUNCTION audit.event_hash(
    prev_hash text, id bigint, ts timestamptz, actor_user text, actor_role text,
    event_type text, case_id text, source text, model text, provider text, payload jsonb
) RETURNS text
    LANGUAGE sql IMMUTABLE PARALLEL SAFE
    SET search_path = pg_catalog
    RETURN encode(sha256(convert_to(
        prev_hash || 'solaris-audit-v1|'
        || audit.ns(id::text)
        || audit.ns(((extract(epoch FROM ts) * 1000000)::bigint)::text)
        || audit.ns(actor_user) || audit.ns(actor_role) || audit.ns(event_type)
        || audit.ns(case_id) || audit.ns(source) || audit.ns(model) || audit.ns(provider)
        || audit.ns(payload::text),
        'UTF8')), 'hex');

CREATE FUNCTION audit.events_chain() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
    last_hash text;
BEGIN
    IF current_setting('transaction_isolation') <> 'read committed' THEN
        RAISE EXCEPTION 'audit.events solo admite INSERT en READ COMMITTED (es %)',
            current_setting('transaction_isolation')
            USING ERRCODE = 'feature_not_supported';
    END IF;
    PERFORM pg_advisory_xact_lock(84011502);  -- AUDIT_LOCK (distinto del del runner de migraciones)
    SELECT e.hash INTO last_hash FROM audit.events e ORDER BY e.id DESC LIMIT 1;
    NEW.id        := nextval('audit.events_id_seq');
    NEW.ts        := clock_timestamp();
    NEW.payload   := coalesce(NEW.payload, '{}'::jsonb);
    NEW.source    := coalesce(NEW.source, 'backend');
    NEW.prev_hash := coalesce(last_hash, repeat('0', 64));
    NEW.hash      := audit.event_hash(NEW.prev_hash, NEW.id, NEW.ts, NEW.actor_user,
                         NEW.actor_role, NEW.event_type, NEW.case_id, NEW.source, NEW.model,
                         NEW.provider, NEW.payload);
    RETURN NEW;
END
$$;

CREATE FUNCTION audit.events_immutable() RETURNS trigger
    LANGUAGE plpgsql
    SET search_path = pg_catalog
AS $$
BEGIN
    RAISE EXCEPTION 'audit.events es de solo anexar: % no permitido', TG_OP
        USING ERRCODE = 'insufficient_privilege',
              HINT = 'Solo se desactiva de forma explícita (ALTER TABLE ... DISABLE TRIGGER '
                     'audit_events_immutable) y queda detectado por verify_chain().';
END
$$;

CREATE TRIGGER audit_events_chain
    BEFORE INSERT ON audit.events
    FOR EACH ROW EXECUTE FUNCTION audit.events_chain();

CREATE TRIGGER audit_events_immutable
    BEFORE UPDATE OR DELETE OR TRUNCATE ON audit.events
    FOR EACH STATEMENT EXECUTE FUNCTION audit.events_immutable();

-- Propiedad: todo a audit_owner (NOLOGIN). El SECURITY DEFINER corre como audit_owner, no como
-- superusuario.
ALTER TABLE audit.events OWNER TO audit_owner;
ALTER SEQUENCE audit.events_id_seq OWNER TO audit_owner;
ALTER FUNCTION audit.ns(text) OWNER TO audit_owner;
ALTER FUNCTION audit.event_hash(text, bigint, timestamptz, text, text, text, text, text, text,
    text, jsonb) OWNER TO audit_owner;
ALTER FUNCTION audit.events_chain() OWNER TO audit_owner;
ALTER FUNCTION audit.events_immutable() OWNER TO audit_owner;

-- Privilegios: nada por defecto, y solo lo mínimo a cada rol de servicio.
REVOKE ALL ON audit.events FROM PUBLIC;
REVOKE ALL ON SEQUENCE audit.events_id_seq FROM PUBLIC;
REVOKE ALL ON FUNCTION audit.events_chain() FROM PUBLIC;
REVOKE ALL ON FUNCTION audit.events_immutable() FROM PUBLIC;

GRANT USAGE ON SCHEMA audit TO audit_writer, audit_reader;
GRANT INSERT ON audit.events TO audit_writer;
GRANT SELECT ON audit.events TO audit_reader;
-- audit_reader puede recalcular hashes en SQL si lo necesita (verify_chain lo hace en Python).
GRANT EXECUTE ON FUNCTION audit.ns(text) TO audit_reader;
GRANT EXECUTE ON FUNCTION audit.event_hash(text, bigint, timestamptz, text, text, text, text,
    text, text, text, jsonb) TO audit_reader;

-- Aislamiento: los roles de audit no ven el corpus ni el ERP (si existen en esta BD).
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'rag') THEN
        REVOKE ALL ON SCHEMA rag FROM audit_writer, audit_reader;
        REVOKE ALL ON ALL TABLES IN SCHEMA rag FROM audit_writer, audit_reader;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'erp') THEN
        REVOKE ALL ON SCHEMA erp FROM audit_writer, audit_reader;
        REVOKE ALL ON ALL TABLES IN SCHEMA erp FROM audit_writer, audit_reader;
    END IF;
END
$$;
