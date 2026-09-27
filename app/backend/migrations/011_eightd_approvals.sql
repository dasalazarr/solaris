-- 011_eightd_approvals — Decisiones humanas (HITL) sobre el borrador 8D (M3-T4, F06). DATOS
-- SINTÉTICOS. La aplica `uv run python -m solaris.db.migrate` dentro de una transacción; no añadir
-- BEGIN/COMMIT aquí. Depende de 008 (esquema `eightd`, rol `eightd_app`).
--
-- Una fila por caso (PRIMARY KEY case_id): la primera decisión gana (INSERT ... ON CONFLICT DO
-- NOTHING); una segunda aprobación o una aprobación tras un rechazo → 409 en la API. El rol
-- `eightd_app` solo tiene SELECT e INSERT: **sin UPDATE ni DELETE**, así que el borrador aprobado
-- queda congelado también en la BD (los checkpoints sí admiten UPDATE: por eso la versión aprobada
-- se guarda aquí y la API y el grafo la comparan con el estado).
--
-- `version`          = sha256 de D1–D4 tal y como lo vio el aprobador (el que se le presentó).
-- `approved_version` = sha256 de D1–D4 tras sus ediciones (el que queda congelado).
-- `draft_original` / `draft_final` = los dos borradores (para "Ver cambios" y la métrica de H01).
-- `pct_edited`       = % de caracteres cambiados por el aprobador (métrica de H01, M5-T4).

CREATE TABLE eightd.approvals (
    case_id           uuid PRIMARY KEY REFERENCES eightd.cases (case_id),
    decision          text NOT NULL CHECK (decision IN ('approved', 'rejected')),
    decided_by        text NOT NULL CHECK (length(decided_by) BETWEEN 1 AND 200),
    decided_role      text NOT NULL CHECK (length(decided_role) BETWEEN 1 AND 64),
    decided_at        timestamptz NOT NULL DEFAULT now(),
    version           text NOT NULL CHECK (version ~ '^[0-9a-f]{64}$'),
    approved_version  text CHECK (approved_version IS NULL OR approved_version ~ '^[0-9a-f]{64}$'),
    pct_edited        numeric(5, 2) NOT NULL DEFAULT 0 CHECK (pct_edited BETWEEN 0 AND 100),
    edits             jsonb NOT NULL DEFAULT '[]',
    edited_paths      jsonb NOT NULL DEFAULT '[]',
    comment           text CHECK (comment IS NULL OR length(comment) <= 2000),
    reason            text CHECK (reason IS NULL OR length(reason) <= 2000),
    draft_original    jsonb NOT NULL,
    draft_final       jsonb,
    CHECK ((decision = 'approved' AND approved_version IS NOT NULL AND draft_final IS NOT NULL)
           OR (decision = 'rejected' AND reason IS NOT NULL))
);

REVOKE ALL ON eightd.approvals FROM PUBLIC, eightd_app;
GRANT SELECT, INSERT ON eightd.approvals TO eightd_app;
