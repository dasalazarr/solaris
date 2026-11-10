---
fecha: 2026-11-10
rol: cofundador
tema: vertical Compliance
---

# Vertical Compliance: investigación y caso de estudio

## Tarea
Diego pidió investigar y estructurar la vertical Compliance con su caso de estudio. Eligió: comparar ámbitos y recomendar, caso de muestra ficticio, y plantilla en el producto.

## Qué se hizo
- `raw/research/2026-11-10_compliance-vertical.md`: cinco ámbitos, seis criterios, fuentes con nivel de comprobación.
- `docs/caso-de-estudio-compliance.md`: asesoría ficticia, 2 tipos de objeto, 5 documentos, 5 reglas con los operadores actuales, 6 clientes con resultado esperado.
- ADR-0020 (propuesta), O07 y H04.

## Qué falló
- EUR-Lex no devolvió el Reglamento (UE) 2024/1624.
- El BOE cargó, pero parte de los artículos llegó resumida por el modelo y no literal.
- La hipótesis previa daba opciones al compliance penal: no tiene fecha que obligue y es terreno de las suites GRC.

## Evidencia
- `python3 scripts/wiki_lint.py`.

## Sin comprobar
- Lista en el informe, apartado «Sin comprobar». Ninguna regla la ha revisado alguien cualificado.
- La plantilla del producto no se ha empezado: espera la aceptación de ADR-0020.
