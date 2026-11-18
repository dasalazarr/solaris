---
id: ADR-0027
type: decision
title: "Consultas guiadas deterministas sobre una base ficticia de seis meses"
status: proposed
owner_role: product
links: ["[[ADR-0026]]", "[[ADR-0017]]", "[[ADR-0019]]"]
evidence: []
updated: 2026-11-18
---

# ADR-0027 · Consultas guiadas y base ficticia

- Estado: propuesta. Diego pidió avanzar el 18/11; la acepta o la corrige al revisar el PR.
- Contexto: en la demo de Finanzas casi toda pregunta libre acaba en «no consta». El modelo solo ve un mes y 14 fragmentos. Además, la pregunta libre depende de Gemini, que no existe en local ni existirá en el Nivel 2 sin red.

## Opciones

1. **Solo pregunta libre.** No cuesta nada, pero sigue dependiendo del modelo y de la red.
2. **Base ficticia más rica.** La misma empresa con seis meses de datos. Sin un límite, todas las evidencias van al prompt y el coste por pregunta crece.
3. **Base ficticia y consultas guiadas.** Chips que componen una consulta (qué × cuándo × filtro). La responde el código sobre los objetos, con una cita por fila. La pregunta libre se queda para lo que no cabe en una consulta.

## Decisión

Opción 3, en dos entregas:

1. **Base ficticia.**
   - Empresa: Comercial Ficticia Guayacán S.A.
   - Periodo: mayo a octubre de 2026.
   - Movimientos, comprobantes del SRI y cartera por cliente y proveedor.
   - Se genera con una función determinista, sin aleatoriedad en ejecución, para que la regresión de oro no cambie entre ejecuciones.
   - Octubre conserva los importes del caso actual.
2. **Consultas guiadas.**
   - Un catálogo fijo de consultas por tipo de objeto: suma, recuento y lista, con filtros por mes, tipo y relación.
   - Cada fila del resultado cita su evidencia.
   - Sin modelo ni red: la misma función pura que el motor de reglas.
   - Al modelo solo le llegan las evidencias de los objetos consultados.

## Por qué

- Es el principio 2 llevado al chat: los números los calcula el código y el modelo solo redacta.
- Funciona en local y en el Nivel 2 sin red.
- Sin datos de varios meses, las consultas guiadas tendrían poco que consultar.

## Consecuencias

- **Coste:** unos 4 días. Desplaza la prueba del lector de XML del SRI (P2 de [[ADR-0026]]) y retrasa algo más la Fase 4.
- **Datos:** la base es ficticia y lleva «(muestra)», como el resto.
- **Landing:** no se menciona mientras la puerta del 09/12 no se decida.
- **Fuera:** consultas libres en SQL o en lenguaje natural traducido a consulta. El catálogo es cerrado, como los operadores del motor ([[ADR-0017]]).
