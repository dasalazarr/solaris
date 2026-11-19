# Sesión 2026-11-02 · orquestador · sinergia landing ↔ producto y documento fundacional

## Tarea
Diego: analizar producto y landing, validar la sinergia en copy y funciones, encontrar oportunidades y cerrar con el valor añadido de Solaris en documentación fundacional.

## Qué se hizo
- Lectura de `landing/src/data/content.ts`, componentes con copy, `product/lib/solaris-data.ts`, `components/SolarisWorkspace.tsx` y `app/api/ontology-query/route.ts`, contra ambos PRD.
- `curl` a `https://solaris.dasalazarr.com`: aparecen «Piloto en curso» y «primer piloto en calidad» en la página publicada.
- Escritos `docs/sinergia-landing-producto.md` y `docs/fundacional.md`; STATUS, `docs/README.md` y `wiki/logs.md` actualizados.

## Qué se descubrió
- Copy sin respaldo publicado: piloto IFS, diario inventado, «una base, muchas vistas» (federación v2).
- El estado de las reglas está escrito en los datos; `expression` no se evalúa; `evaluatedRuleCodes` lo devuelve el LLM.
- La pregunta libre no valida `evidenceId`; sin clave o con error devuelve una respuesta fija con cita, y el `catch` usa siempre el pack Compras.
- El modal de Nivel 2 ofrece un `docker-compose` con imágenes `illarium/solaris-*` inexistentes; el formulario de ingesta se rotula «Docling + Surya OCR» sin OCR real.
- PC-0412: 18.400 € / Metalúrgica Duero / R-COMP-07 en la landing; 18.450 € / Suministros Industriales del Norte / R-03 y R-02 en el producto.

## Sin verificar
- Si `GEMINI_API_KEY` está configurada en el despliegue del producto.

## Evidencia
- `curl -s https://solaris.dasalazarr.com | grep -oE "Piloto en curso|primer piloto en calidad"` → 2 y 3 coincidencias.
