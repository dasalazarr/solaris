-- 007_erp_business_roles — ACL del ERP por rol de negocio en la BD (M4-T1, F05/F09, PAT-005).
-- DATOS SINTÉTICOS. La aplica `uv run python -m solaris.db.migrate` dentro de una transacción; no
-- añadir BEGIN/COMMIT aquí. Solo para la BD del demo (el esquema erp no existe en solaris_test).
--
-- Antes (M3-T1): erp_reader tenía SELECT sobre todo erp.* y la matriz `erp_tables` de acl.json solo
-- se aplicaba en Python (ErpAcl.check). Ahora:
--   * Un rol NOLOGIN por rol de negocio (erp_calidad, erp_planta, erp_auditor, erp_admin) con SELECT
--     solo sobre las tablas que acl.json le permite.
--   * erp_reader deja de tener SELECT propio: es miembro de esos roles con INHERIT FALSE y SET TRUE,
--     así que no hereda nada y solo puede leer tras `SET LOCAL ROLE erp_<rol>` dentro de la
--     transacción. El MCP lo hace con el rol que ya validó ErpAcl.resolve() desde `_meta`.
--   * La ACL en Python sigue siendo la primera capa (mensaje claro + evento tool_denied); la BD es
--     la segunda: aunque un bug de la app se saltara ErpAcl.check, la BD rechaza la tabla.
-- La matriz está duplicada respecto a acl.json (fuente de verdad): el test
-- app/mcp/erp_mock/tests/test_tools_db.py::test_db_grants_match_acl_json detecta la deriva.
-- Una tabla nueva en erp exige una migración que la conceda a los roles que correspondan.

DO $$
DECLARE
    r text;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'erp') THEN
        RAISE EXCEPTION '007: el esquema erp no existe (se crea con el ERP mock, M1-T3)';
    END IF;
    FOREACH r IN ARRAY ARRAY['erp_calidad', 'erp_planta', 'erp_auditor', 'erp_admin'] LOOP
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = r) THEN
            EXECUTE format('CREATE ROLE %I NOLOGIN', r);
        END IF;
        EXECUTE format('ALTER ROLE %I NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION '
                       'NOBYPASSRLS NOINHERIT', r);
        EXECUTE format('REVOKE ALL ON ALL TABLES IN SCHEMA erp FROM %I', r);
        EXECUTE format('GRANT USAGE ON SCHEMA erp TO %I', r);
        EXECUTE format('GRANT %I TO erp_reader WITH INHERIT FALSE, SET TRUE', r);
    END LOOP;
END
$$;

-- acl.json → erp_tables: calidad "*", admin "*", planta [lots, production_orders], auditor [complaints]
GRANT SELECT ON ALL TABLES IN SCHEMA erp TO erp_calidad, erp_admin;
GRANT SELECT ON erp.lots, erp.production_orders TO erp_planta;
GRANT SELECT ON erp.complaints TO erp_auditor;

-- erp_reader: solo conexión + USAGE del esquema; sin SELECT propio.
REVOKE ALL ON ALL TABLES IN SCHEMA erp FROM erp_reader;
