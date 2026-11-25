# 2026-11-25 · cofundador · PMM-OS y venta dirigida

- **Entrada:** Diego trae el PRD de PMM-OS (orquestador de marketing multiagente) para uso interno. Al ver la evaluación, propone pivotar a venta dirigida (ABM de 15–20 cuentas), vender el resultado y abrir con una oferta cuña de 21 días.
- **Evaluación:** PMM-OS duplica el ~70 % de ADR-0024, supone un equipo que no hay, choca con ADR-0019 (LangGraph) y con «sin publicación automática». El cuello de botella son las conversaciones (0 entrevistas, lista de cuentas vacía). Del giro: «60 % menos de tiempo» no tiene evidencia (se mide en la cuña); EUDR/IFS están congelados; extraer facturas es commodity; la cuña con documentos reales choca con la falta de Fase 4 y de modelo local.
- **Decisión de Diego:** uso interno; nicho despachos.
- **Hecho:** ADR-0030 (propuesta). En el repo privado de contenido (sin commit, regla mensual): oferta «Primer contrato · despachos» e investigación de 16 despachos a nivel de despacho. STATUS con dos filas.
- **Hallazgo lateral:** el aval de la demo Jurídico vence el 15/11/2026, ya pasado.
- **Gate:** `python3 scripts/wiki_lint.py`.
