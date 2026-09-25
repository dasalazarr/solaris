-- 006_rag_app_role — Rol de BD del backend en runtime `solaris_app` (M4-T1, F09, PAT-005). DATOS SINTÉTICOS.
-- La aplica `uv run python -m solaris.db.migrate` (desde app/backend) dentro de una transacción; no
-- añadir BEGIN/COMMIT aquí. El nombre contiene `_rag` para que solaris.audit.testdb la aplique
-- también a la BD de tests `solaris_test`. Idempotente respecto a roles (son de clúster).
--
-- Separación de roles de BD:
--   * `solaris` (superusuario del contenedor, POSTGRES_PASSWORD/DATABASE_URL): SOLO administración:
--     migraciones, ingesta (solaris.rag.ingest), sync de ACL (solaris.rag.acl) y BD de tests.
--   * `solaris_app` (SOLARIS_APP_PASSWORD): la API en runtime. Sin SELECT sobre ninguna tabla de
--     `rag`; solo EXECUTE sobre rag.visible_chunks/visible_fmea_rows/visible_documents. Sin acceso
--     a `erp` (eso es del MCP con erp_reader) ni a `audit` (el backend escribe con audit_writer y lee
--     con audit_reader, ya separados en 003).
--   * `rag_definer` (NOLOGIN): propietario de las funciones visible_*, SECURITY DEFINER. Único con
--     SELECT sobre rag.chunks/fmea_rows/documents/folder_acl. Nadie inicia sesión con él.
--
-- Contrapartida conocida: una función SECURITY DEFINER (o con SET) no se "inlinea". El filtro de ACL
-- sigue ocurriendo antes del ranking (la función solo devuelve filas visibles), pero el ORDER BY
-- vectorial ya no usa el índice HNSW: es un kNN exacto sobre lo visible. Con el corpus del demo
-- (~340 chunks) cuesta milisegundos. Antes de un corpus grande (>~50k chunks): mover el ranking a
-- funciones definer parametrizadas (p. ej. rag.search_vector(role, qvec, k)) para recuperar el índice.
--
-- El rol de negocio sigue siendo un parámetro: la BD garantiza que nadie se salta la ACL por carpeta
-- de ALGÚN rol; que el rol sea el del usuario autenticado lo garantiza el backend (resolve_role desde
-- acl.json con el `sub` de un JWT verificado; nunca desde la petición ni desde el LLM).

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'solaris_app') THEN
        CREATE ROLE solaris_app LOGIN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'rag_definer') THEN
        CREATE ROLE rag_definer NOLOGIN;
    END IF;
END
$$;

ALTER ROLE solaris_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS
    NOINHERIT CONNECTION LIMIT 20;
-- Defensa en profundidad: la API solo lee. Una futura tabla escribible (p. ej. borradores 8D, F06)
-- exige una migración con su GRANT y abrir esa transacción READ WRITE de forma explícita.
ALTER ROLE solaris_app SET default_transaction_read_only = on;
ALTER ROLE solaris_app SET statement_timeout = '15s';
ALTER ROLE solaris_app SET idle_in_transaction_session_timeout = '30s';
ALTER ROLE rag_definer NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS
    NOINHERIT;

-- --- rag: nada directo para solaris_app; lectura solo para el propietario de las funciones ---------
REVOKE ALL ON ALL TABLES IN SCHEMA rag FROM PUBLIC, solaris_app, rag_definer;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA rag FROM PUBLIC, solaris_app, rag_definer;
REVOKE ALL ON SCHEMA rag FROM PUBLIC;
GRANT USAGE ON SCHEMA rag TO solaris_app, rag_definer;
GRANT SELECT ON rag.chunks, rag.fmea_rows, rag.documents, rag.folder_acl TO rag_definer;

-- Documentos visibles para un rol (metadatos: título, tipo, part_refs). Sustituye al JOIN directo a
-- rag.documents del retrieve (M2-T5, punto 2): los títulos de carpetas ocultas tampoco se ven.
CREATE FUNCTION rag.visible_documents(p_role text)
RETURNS SETOF rag.documents
LANGUAGE sql STABLE
AS $$
    SELECT d.*
      FROM rag.documents d
     WHERE EXISTS (SELECT 1 FROM rag.folder_acl a
                    WHERE a.folder = d.folder AND a.role = p_role)
$$;
COMMENT ON FUNCTION rag.visible_documents(text) IS
    'Documentos visibles para un rol (deny-by-default). SECURITY DEFINER (rag_definer), M4-T1.';

-- Las tres funciones: SECURITY DEFINER como rag_definer (no como superusuario) y search_path fijo
-- con pg_temp al final (sin él, un objeto temporal podría suplantar a uno del catálogo).
ALTER FUNCTION rag.visible_chunks(text) SECURITY DEFINER;
ALTER FUNCTION rag.visible_chunks(text) SET search_path = pg_catalog, pg_temp;
ALTER FUNCTION rag.visible_chunks(text) OWNER TO rag_definer;
ALTER FUNCTION rag.visible_fmea_rows(text) SECURITY DEFINER;
ALTER FUNCTION rag.visible_fmea_rows(text) SET search_path = pg_catalog, pg_temp;
ALTER FUNCTION rag.visible_fmea_rows(text) OWNER TO rag_definer;
ALTER FUNCTION rag.visible_documents(text) SECURITY DEFINER;
ALTER FUNCTION rag.visible_documents(text) SET search_path = pg_catalog, pg_temp;
ALTER FUNCTION rag.visible_documents(text) OWNER TO rag_definer;

-- Por defecto PUBLIC tiene EXECUTE en toda función nueva: con SECURITY DEFINER eso sería abrir el
-- corpus a cualquier rol. Solo solaris_app.
REVOKE ALL ON FUNCTION rag.visible_chunks(text) FROM PUBLIC;
REVOKE ALL ON FUNCTION rag.visible_fmea_rows(text) FROM PUBLIC;
REVOKE ALL ON FUNCTION rag.visible_documents(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION rag.visible_chunks(text) TO solaris_app;
GRANT EXECUTE ON FUNCTION rag.visible_fmea_rows(text) TO solaris_app;
GRANT EXECUTE ON FUNCTION rag.visible_documents(text) TO solaris_app;

-- --- aislamiento de solaris_app respecto a erp y audit (si existen en esta BD) ----------------------
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'erp') THEN
        REVOKE ALL ON SCHEMA erp FROM solaris_app, rag_definer;
        REVOKE ALL ON ALL TABLES IN SCHEMA erp FROM solaris_app, rag_definer;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'audit') THEN
        REVOKE ALL ON SCHEMA audit FROM solaris_app, rag_definer;
        REVOKE ALL ON ALL TABLES IN SCHEMA audit FROM solaris_app, rag_definer;
    END IF;
END
$$;

-- --- privilegios por defecto de PUBLIC (punto 6 de M3-T1) ------------------------------------------
-- TEMP y CONNECT dejan de ser de PUBLIC en esta BD; CONNECT se concede solo a los roles de servicio.
-- Un rol de servicio nuevo necesita su GRANT CONNECT en su migración. USAGE sobre `public` se
-- mantiene (tipo y operadores de la extensión vector); CREATE en `public` ya no es de PUBLIC en PG15+,
-- se revoca igualmente por si la BD viene de una versión anterior.
DO $$
DECLARE
    db text := current_database();
    r  text;
BEGIN
    EXECUTE format('REVOKE TEMPORARY, CONNECT ON DATABASE %I FROM PUBLIC', db);
    FOREACH r IN ARRAY ARRAY['solaris_app', 'erp_reader', 'audit_writer', 'audit_reader'] LOOP
        IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = r) THEN
            EXECUTE format('GRANT CONNECT ON DATABASE %I TO %I', db, r);
        END IF;
    END LOOP;
END
$$;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
