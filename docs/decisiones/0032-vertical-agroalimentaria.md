---
id: ADR-0032
type: decision
title: "Vertical agroalimentaria en validación: proceso de muestra «Calidad y exportación» y venta dirigida a pymes navarras"
status: validating
owner_role: product
links: ["[[ADR-0030]]", "[[ADR-0026]]", "[[ADR-0024]]", "[[ADR-0018]]", "[[ADR-0015]]", "[[ADR-0010]]"]
evidence: ["product/lib/templates/agro.json", "product/lib/seeds/agro.ts", "product/tests/rules-engine.test.ts"]
updated: 2026-11-25
---

# ADR-0032 · Vertical agroalimentaria en validación

- Fecha: 2026-11-25
- Estado: propuesta. Diego pidió el 25/11 construir la vertical junto a la de despachos ([[ADR-0030]]); falta que acepte o corrija esta nota.

## Contexto

Un consultor de negocio depuró un listado de pymes agroalimentarias navarras (de 75 a 27, con 12 de prioridad alta: independientes o de grupo navarro, de 50 a 250 empleados) y dejó escrita una estrategia de contacto: llamada a gerencia, dolor como pregunta, demo solo si el dolor se confirma, secuencia de 14 días y un criterio para abandonar. La lista y los nombres viven en el repositorio privado de contenido, no aquí.

**Tesis (sin validar):** en esa pyme, la documentación de calidad y exportación depende de muy pocas personas: certificados por país, especificaciones de cada cadena, denominación de origen, producción ecológica y relevo generacional.

Hasta hoy, CLAUDE.md dejaba IFS Food y EUDR «sin funciones nuevas». Sus plantillas tienen una regla cada una y no cuentan esa tesis.

## Opciones

1. **No construir hasta tener llamadas.** Es lo que dice la propia estrategia. Pero la estrategia apunta a 4 demos en 4 semanas y no hay una demo que enseñe esta tesis.
2. **Ampliar IFS Food o EUDR.** Cambiaría lo que la landing ya enseña con ese nombre, y ninguna de las dos habla de especificaciones de cadena ni de dependencia de personas.
3. **Un proceso de muestra nuevo, `agro`, con los motores que ya existen.** Barato, no toca IFS ni EUDR, y la demo está lista para el día que un gerente confirme el dolor.

## Decisión

Opción 3.

- **Proceso «Calidad y exportación» (`agro`).** Una conservera ficticia con 4 certificados, 2 especificaciones de cadenas ficticias, 3 referencias y 3 expediciones. Cinco reglas: certificado a menos de 30 días (`days_until`), ficha técnica contra una versión vieja de la especificación (`compare_related`), expedición al anexo B sin certificado sanitario (`count_related`), etiqueta ecológica sin certificado (`count_related`) y **dossier sin suplente** (`==`), que es la regla que nombra el dolor de «depende de una persona». Sin cambios en el motor.
- **Todo inventado.** Empresa, cadenas, entidad certificadora, consejo regulador y personas. El alcance dice que las reglas son las del manual interno de la empresa, no una lectura oficial de ninguna norma ni de lo que exige ningún país.
- **La venta sigue la estrategia del consultor, no la adelanta.** Gerencia, dolor como pregunta, no se menciona la IA hasta que pregunten, la demo solo si se confirma el dolor. El guion y el embudo están en el repositorio privado.
- **«Asistente privado en los equipos de la empresa» es Nivel 2:** se dice en futuro, «en tu piloto» ([[ADR-0018]]).
- **IFS Food y EUDR siguen congelados.** Si `agro` valida, se decide aparte si sustituye a IFS en la landing.

## Puerta

La de la estrategia: tras unas 10 conversaciones, si nadie menciona por su cuenta la documentación o la dependencia de pocas personas, la hipótesis se descarta y `agro` queda como muestra, como Compliance ([[ADR-0020]]). Si un mismo dolor aparece en la mitad o más de los contactos, ese es el foco, y un piloto exige lo mismo que el de despachos: Fase 4, modelo local y veto de `security`.

## Consecuencias

- **Coste:** un día de dev (plantilla, datos, tests y regresión de oro). La regresión de los seis procesos anteriores no cambia. 381 tests, lint y build en verde; recorrido comprobado en el navegador en local, también a 375 px.
- **Desplaza:** nada del sprint CFO, que termina el 09/12. Compite con despachos por el tiempo de Diego, no por el de dev: el cuello de botella de las dos verticales son las llamadas.
- **Landing:** no cambia. No nombra `agro` mientras no pase la puerta.
- **Calidad y cumplimiento** deja de ser «solo caso de uso» en el contenido ([[ADR-0024]]): el tramo 3 puede usar este proceso.
- **Pendiente:** que alguien del sector revise las cinco reglas antes de enseñarlas como verosímiles.
