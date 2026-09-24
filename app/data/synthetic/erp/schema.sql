-- ERP mock de Componentes Arga S.L. — DATOS SINTÉTICOS (ADR-0004). Fuente de verdad: app/data/synthetic/PLANT.md
-- Solo el esquema `erp` (M1-T3). Las tablas RAG (documents, chunks, acl) llegan en M2-T2.
-- Acceso desde el producto: solo lectura vía MCP (F05). El rol de BD de solo lectura se crea en M3-T1.

CREATE EXTENSION IF NOT EXISTS vector;
CREATE SCHEMA IF NOT EXISTS erp;

CREATE TABLE erp.customers (
    code           text PRIMARY KEY,              -- C-OEMN, C-RIBE, C-LEIZ
    name           text NOT NULL,
    customer_type  text NOT NULL CHECK (customer_type IN ('OEM', 'Tier1')),
    report_template text NOT NULL,                -- plantilla 8D exigida
    report_language text NOT NULL,
    containment_hours int NOT NULL,               -- plazo de contención
    report_days    int NOT NULL                   -- plazo 8D (días laborables)
);

CREATE TABLE erp.suppliers (
    code      text PRIMARY KEY,                   -- S-ULTZ, S-BIDA, ...
    name      text NOT NULL,
    supplies  text NOT NULL
);

CREATE TABLE erp.parts (
    ref            text PRIMARY KEY,              -- AR-1001..AR-1012
    description    text NOT NULL,
    customer_code  text NOT NULL REFERENCES erp.customers(code),
    routing        text NOT NULL,                 -- 'L1>L3' | 'L1>L2>L3'
    material       text NOT NULL,                 -- DC04, HSLA 420, ...
    thickness_mm   numeric(3,1) NOT NULL,
    special_char   text NOT NULL,
    char_class     text NOT NULL CHECK (char_class IN ('CC', 'SC')),
    press          text NOT NULL,                 -- PR-400 | PR-250
    die            text NOT NULL,                 -- MT-xx
    weld_cell      text,                          -- CR-01 | CR-02 | SP-01 | NULL
    uses_weld_nut  boolean NOT NULL DEFAULT false
);

CREATE TABLE erp.material_lots (
    lot_code       text PRIMARY KEY,              -- <proveedor>-<AA><nnnn>
    supplier_code  text NOT NULL REFERENCES erp.suppliers(code),
    material       text NOT NULL,
    received_date  date NOT NULL,
    qty            numeric NOT NULL,
    unit           text NOT NULL,
    certificate_ok boolean NOT NULL DEFAULT true,
    notes          text
);

CREATE TABLE erp.production_orders (
    order_id       text PRIMARY KEY,              -- OF-<AA>-<nnnnn>
    part_ref       text NOT NULL REFERENCES erp.parts(ref),
    planned_qty    int NOT NULL,
    start_date     date NOT NULL,
    status         text NOT NULL CHECK (status IN ('open', 'closed'))
);

CREATE TABLE erp.lots (
    lot_code       text PRIMARY KEY,              -- L<AA><DDD>-<ref sin guion>-<nn>
    part_ref       text NOT NULL REFERENCES erp.parts(ref),
    order_id       text NOT NULL REFERENCES erp.production_orders(order_id),
    production_date date NOT NULL,
    shift          text NOT NULL CHECK (shift IN ('mañana', 'tarde', 'noche')),
    press          text NOT NULL,
    weld_cell      text,
    qty_produced   int NOT NULL,
    qty_scrap      int NOT NULL,
    steel_lot_code text NOT NULL REFERENCES erp.material_lots(lot_code),
    wire_lot_code  text REFERENCES erp.material_lots(lot_code),
    nut_lot_code   text REFERENCES erp.material_lots(lot_code),
    ecoat_lot_code text NOT NULL REFERENCES erp.material_lots(lot_code),
    status         text NOT NULL CHECK (status IN ('released', 'in_stock', 'blocked'))
);

CREATE TABLE erp.shipments (
    shipment_id    text PRIMARY KEY,              -- AL-<AA>-<nnnnn> (albarán)
    lot_code       text NOT NULL REFERENCES erp.lots(lot_code),
    customer_code  text NOT NULL REFERENCES erp.customers(code),
    ship_date      date NOT NULL,
    qty            int NOT NULL
);

CREATE TABLE erp.complaints (
    complaint_id   text PRIMARY KEY,              -- <cliente>-<AAAA>-<nnnn>
    customer_code  text NOT NULL REFERENCES erp.customers(code),
    part_ref       text NOT NULL REFERENCES erp.parts(ref),
    lot_code       text REFERENCES erp.lots(lot_code),
    received_date  date NOT NULL,
    defect         text NOT NULL,
    qty_affected   int NOT NULL,
    status         text NOT NULL CHECK (status IN ('open', 'closed')),
    report_8d_id   text                           -- 8D-ARGA-<AAAA>-<nnn> (documento en calidad/8d)
    -- La familia de recurrencia NO se guarda aquí: es la verdad del escenario (PLANT.md §5 / golden set)
    -- y el agente la debe descubrir, no leerla del ERP (PAT-004).
);

CREATE INDEX ON erp.lots (part_ref, production_date);
CREATE INDEX ON erp.lots (wire_lot_code);
CREATE INDEX ON erp.shipments (lot_code);
CREATE INDEX ON erp.complaints (part_ref);
