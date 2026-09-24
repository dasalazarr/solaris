-- Consultas de humo del ERP mock (gate de M1-T3). Cada consulta imprime ok = true si el escenario es coherente.
\echo '1. Recuentos básicos'
SELECT (SELECT count(*) FROM erp.parts) = 12 AND (SELECT count(*) FROM erp.suppliers) = 6
   AND (SELECT count(*) FROM erp.customers) = 3 AS ok;

\echo '2. 15 reclamaciones cerradas con 8D y 5 abiertas sin 8D'
SELECT count(*) FILTER (WHERE status = 'closed' AND report_8d_id IS NOT NULL) = 15
   AND count(*) FILTER (WHERE status = 'open' AND report_8d_id IS NULL) = 5 AS ok
FROM erp.complaints;

\echo '3. Familia A: el lote reclamado de AR-1003 lleva el hilo nuevo S-GOIE-260117, soldado en CR-01, turno de noche'
SELECT wire_lot_code = 'S-GOIE-260117' AND weld_cell = 'CR-01' AND shift = 'noche' AS ok
FROM erp.lots WHERE lot_code = 'L26241-AR1003-02';

\echo '4. Alcance de la contención (familia A): lotes de AR-1003/AR-1004 con el hilo S-GOIE-260117 y sus envíos a OEM Norte'
SELECT l.part_ref, count(DISTINCT l.lot_code) AS lotes, count(s.shipment_id) AS envios, coalesce(sum(s.qty), 0) AS piezas_enviadas,
       count(DISTINCT l.lot_code) FILTER (WHERE l.status = 'in_stock') AS lotes_en_stock
FROM erp.lots l LEFT JOIN erp.shipments s ON s.lot_code = l.lot_code
WHERE l.wire_lot_code = 'S-GOIE-260117' AND l.part_ref IN ('AR-1003', 'AR-1004')
GROUP BY l.part_ref ORDER BY l.part_ref;

\echo '5. Familia A histórica: 3 reclamaciones de AR-1003 en turno de noche'
SELECT count(*) = 3 AS ok FROM erp.complaints c JOIN erp.lots l USING (lot_code)
WHERE c.part_ref = 'AR-1003' AND c.status = 'closed' AND l.shift = 'noche';

\echo '6. Familia B: 2 históricas + 1 abierta de AR-1007 (prensa PR-250, matriz MT-07)'
SELECT count(*) = 3 AS ok FROM erp.complaints c JOIN erp.parts p ON p.ref = c.part_ref
WHERE c.part_ref = 'AR-1007' AND p.die = 'MT-07';

\echo '7. Integridad: todo envío va al cliente de la pieza'
SELECT count(*) = 0 AS ok FROM erp.shipments s JOIN erp.lots l USING (lot_code) JOIN erp.parts p ON p.ref = l.part_ref
WHERE s.customer_code <> p.customer_code;
