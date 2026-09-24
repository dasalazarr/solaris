-- 002_erp_reader — Rol de BD de solo lectura para el servidor MCP erp-mock (M3-T1, F05). DATOS SINTÉTICOS.
-- La aplica `uv run python -m solaris.db.migrate` (desde app/backend) dentro de una transacción; no
-- añadir BEGIN/COMMIT aquí.
--
-- Decisiones:
--  * La contraseña NO está aquí (las migraciones se versionan). El runner la fija después desde
--    ERP_READER_PASSWORD (.env) con un verificador SCRAM calculado en el cliente
--    (solaris.db.roles). Sin esa variable el rol existe pero no puede iniciar sesión (pg_hba exige
--    scram-sha-256): falla cerrado.
--  * Defensa en profundidad para "solo lectura": (1) solo SELECT sobre erp.*; (2) transacciones
--    read-only por defecto a nivel de rol; (3) el servidor MCP abre además sus transacciones en
--    READ ONLY. Cualquiera de las tres basta para rechazar un INSERT/UPDATE.
--  * Sin acceso a `rag` (ni USAGE del esquema): el MCP del ERP no puede leer el corpus ni llamar a
--    rag.visible_chunks().
--  * GRANT explícito sobre las tablas actuales (no DEFAULT PRIVILEGES): una tabla nueva en erp exige
--    una migración nueva que la conceda de forma consciente.

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'erp_reader') THEN
        CREATE ROLE erp_reader LOGIN;
    END IF;
END
$$;

ALTER ROLE erp_reader LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS
    NOINHERIT CONNECTION LIMIT 10;
ALTER ROLE erp_reader SET default_transaction_read_only = on;
ALTER ROLE erp_reader SET statement_timeout = '5s';
ALTER ROLE erp_reader SET idle_in_transaction_session_timeout = '30s';

REVOKE ALL ON SCHEMA rag FROM erp_reader;
REVOKE ALL ON ALL TABLES IN SCHEMA rag FROM erp_reader;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA rag FROM erp_reader;

REVOKE ALL ON ALL TABLES IN SCHEMA erp FROM erp_reader;
GRANT USAGE ON SCHEMA erp TO erp_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA erp TO erp_reader;
