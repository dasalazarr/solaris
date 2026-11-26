# 2026-11-25 · cofundador · PMM-OS y venta dirigida

- **Entrada:** Diego trae el PRD de PMM-OS (orquestador de marketing multiagente) para uso interno. Al ver la evaluación, propone pivotar a venta dirigida (ABM de 15–20 cuentas), vender el resultado y abrir con una oferta cuña de 21 días.
- **Evaluación:** PMM-OS duplica el ~70 % de ADR-0024, supone un equipo que no hay, choca con ADR-0019 (LangGraph) y con «sin publicación automática». El cuello de botella son las conversaciones (0 entrevistas, lista de cuentas vacía). Del giro: «60 % menos de tiempo» no tiene evidencia (se mide en la cuña); EUDR/IFS están congelados; extraer facturas es commodity; la cuña con documentos reales choca con la falta de Fase 4 y de modelo local.
- **Decisión de Diego:** uso interno; nicho despachos.
- **Hecho:** ADR-0030 (propuesta). En el repo privado de contenido (sin commit, regla mensual): oferta «Primer contrato · despachos» e investigación de 16 despachos a nivel de despacho. STATUS con dos filas.
- **Hallazgo lateral retirado:** creí que el aval de la demo Jurídico (15/11/2026) estaba vencido. No lo está: la demo evalúa con `SAMPLE_NOW` (03/11/2026, `product/lib/solaris-data.ts:234`) y lo rotula en Inicio y Huecos. Error mío por suponer que el motor usaba el reloj.
- **Gate:** `python3 scripts/wiki_lint.py`.

## Segunda parte · vertical agroalimentaria

- **Entrada:** Diego trae la estrategia de un consultor de negocio para pymes agroalimentarias navarras (27 empresas, 12 de nivel A, llamada a gerencia, demo solo con dolor confirmado, criterio de abandono tras ~10 conversaciones) y pide construir la vertical como MVP técnico y de marketing, junto a despachos.
- **Decisión:** proceso de muestra nuevo `agro` en vez de ampliar IFS o EUDR (congelados y con nombre ya visible en la landing). ADR-0032 (propuesta).
- **Hecho:** illariumcore `feat/plantilla-agro` (plantilla, datos ficticios, temas de Inicio, 11 tests nuevos, regresión de oro ampliada sin tocar los seis procesos anteriores). Repo privado: guion de llamada, demo de 15 min y embudo. Sin nombres de empresas ni personas en la raíz.
- **Gate:** 381 tests, lint y build; navegador local con un espacio desechable (Inicio, cita, Huecos, Revisar con rol, 375 px, consola sin errores). Configuración y ficheros temporales borrados.
- **Riesgos anotados:** correo en frío (LSSI art. 21); «asistente privado en sus equipos» es Nivel 2 y va en futuro.
