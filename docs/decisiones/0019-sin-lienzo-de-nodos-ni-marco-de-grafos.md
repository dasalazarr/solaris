---
id: ADR-0019
type: decision
title: "Ni lienzo de nodos ni LangChain o LangGraph por ahora; el grafo ya es la ontología"
status: parked
owner_role: dev
links: ["[[ADR-0015]]", "[[ADR-0017]]", "[[ADR-0018]]", "[[H03]]"]
evidence: ["product/lib/process-definition.ts", "product/app/api/ontology-query/route.ts", "product/lib/ontology-query.ts"]
updated: 2026-11-10
---

# ADR-0019 · Lienzo de nodos y marcos de grafos

- Estado: aparcada por el cofundador (2026-11-10), pendiente de que Diego la acepte. Se reabre con la evidencia que se cita abajo.
- Contexto: Diego planteó dos ideas. Una es parametrizar procesos con un editor visual de nodos, al estilo de n8n o ComfyUI. La otra es adoptar LangChain y una arquitectura de grafos como base.

## Qué hay hoy

- **Reglas.** Cada regla es una comprobación independiente: una lista de condiciones `when` y otra `require`, todas en conjunción, sobre objetos y relaciones, con operadores fijos ([[ADR-0017]]). No hay flujo entre reglas ni un orden de ejecución.
- **Modelo.** Se llama una sola vez por pregunta, con salida estructurada y cita obligatoria. El proveedor está detrás de la interfaz `AnswerGenerator`: una función que recibe `{ system, prompt }` y devuelve texto. Se manda el proceso entero y no hay recuperación.
- **Revisión y registro.** El servidor los guarda en SQLite por espacio, con `policy_hash` ([[ADR-0016]]).

## Opciones

1. **Lienzo de nodos editable.** Un lienzo con flechas sugiere un orden de ejecución que el motor no tiene, y eso choca con el principio 4. Conectar nodos libremente equivale a un lenguaje de expresiones, la opción que [[ADR-0017]] descartó. Además, arrastrar exige una alternativa accesible (criterio 2.5.7 de WCAG 2.2) y obliga a mantener dos editores. Coste estimado: de 2 a 3 semanas.
2. **Mapa del contrato de solo lectura.** Se genera a partir del JSON y muestra:
   - los objetos y sus relaciones;
   - cada regla colgada de lo que comprueba;
   - el rol que revisa y la acción que desbloquea.

   No cambia el modelo de datos. Coste estimado: de 2 a 3 días.
3. **LangChain o LangGraph.** LangGraph aporta estado, puntos de control e interrupciones para la intervención humana. En Solaris eso ya lo cubren la Revisión, el registro y `policy_hash`. Un segundo almacén de estado duplicaría el rastro de auditoría que hay que defender ante un cliente. LangChain añade abstracciones y dependencias que cambian a menudo para una sola llamada al modelo. En el Nivel 2, sin red, cada dependencia es superficie que auditar.
4. **Seguir con funciones tipadas y la interfaz `AnswerGenerator`.** Cambiar de proveedor o pasar a un modelo local en el Nivel 2 es un adaptador nuevo detrás de esa interfaz.

## Decisión

- **Opciones 4 y 2.** La opción 2 es un experimento que solo se construye si la medición de [[H03]] lo justifica.
- **El lienzo editable (opción 1) queda aparcado.** Se reabre si al menos dos personas de las sesiones de [[H03]] fallan por no tener una vista global del proceso o la piden.
- **LangChain y LangGraph (opción 3) quedan aparcados.** Se reabren con cualquiera de estas condiciones:
  - Aparece un flujo de varios pasos con bucles o reintentos que el código directo no expresa con claridad. Por ejemplo, un agente que propone acciones y consulta herramientas.
  - Hay que orquestar más de dos llamadas al modelo por petición.

## Sí sentamos ya, en la Fase 4

La parte útil de «arquitectura de grafos» no es un marco, sino tratar la ontología como el grafo que ya es:

- **Pasos explícitos.** La ingesta de documentos se escribe como pasos separados, tipados y probados uno a uno: cargar, partir por página, extraer atributos con cita, validar y evaluar con el motor. Cada paso puede convertirse en un nodo más adelante sin reescribirlo.
- **Recuperación por el grafo.** Se recupera recorriendo objetos y relaciones en SQLite, no mandando el proceso entero. Así baja el coste por consulta y cada cita apunta a la página.
- **Sin cambio de proveedor.** El proveedor y el modelo los decide Diego. Esta decisión no los cambia.

## Consecuencias

- La Fase 4 no se desplaza.
- Si se mide [[H03]] y el problema es rellenar reglas, se mejoran los formularios. Si el problema es entender la estructura, se construye el mapa.
- La landing no habla de editor visual ni de agentes.
