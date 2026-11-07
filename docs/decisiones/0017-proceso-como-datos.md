---
id: ADR-0017
type: decision
title: "El proceso es una definición versionada, con operadores fijos"
status: accepted
owner_role: dev
links: ["[[ADR-0015]]", "[[ADR-0016]]", "[[F07]]", "[[H03]]"]
evidence: ["raw/sessions/2026-11-07_cofundador_fase-3-parametrizacion.md"]
updated: 2026-11-07
---

# ADR-0017 · Proceso como datos

- Estado: aceptada por el cofundador (2026-11-07). La separación de funciones al final queda abierta para Diego.
- Contexto: cada proceso era código, así que cada alta exigía desarrollo y el setup no se podía vender como parametrización ([[F07]]).

## Opciones de reglas

1. **Expresiones libres.** Máxima flexibilidad, pero es un lenguaje que asegurar y explicar, y rompe el principio 2 en cuanto alguien escribe algo mal.
2. **Operadores fijos elegidos en formularios.** Menos expresivo y más seguro.
3. **Reglas redactadas por el modelo.** Descartada por el principio 2.

## Decisión

Opción 2. Además:

- **JSON validado.** `lib/templates/*.json` y `validateDefinition`. Lo desconocido se descarta, para que no entre en el hash.
- **`policy_hash` real.** SHA-256 del JSON canónico, con implementación síncrona propia porque el navegador lo calcula al escribir.
- **Una decisión vale mientras no cambie lo que se aprobó** (lógica, quién decide, acción, fuente o enlace) en ninguna versión posterior. Volver a publicar la versión antigua no la revive. Cambiar textos no reabre nada.
- **El registro lo redacta el servidor.** La nota de quien publica se conserva, rotulada como suya.
- **El responsable lo fija la versión vigente.** Nadie se nombra a sí mismo en lo que publica.

## Abierto para Diego: separación de funciones

Hoy el responsable del contrato puede cambiar una regla y aprobar después esa misma revisión. No se impide: queda marcado como «Autoaprobación» en el registro. En la plantilla jurídica, responsable y aprobador ya son el mismo rol, así que exigir cuatro ojos cambiaría cómo trabaja un despacho pequeño. Se decide con el primer piloto.

## Consecuencias

- Crear un proceso desde cero aún no existe: `SolarisPackId` sigue cerrado y un proceso sin objetos no tiene qué evaluar. Va en la siguiente entrega, ligado a la Fase 4. [[H03]] sigue sin medir hasta entonces.
- Las respuestas de muestra están redactadas con la plantilla: si cambia el contrato, la interfaz lo avisa.
- Validar datos no depende de ninguna regla; su rol no se edita todavía.
- Decisiones guardadas antes de esta versión no se migran: no existe ningún almacén, porque la Fase 2 no está fusionada ni hay carpeta de datos en el despliegue.
- Si se retira a la última persona con un rol, el proceso se para hasta darle ese rol a alguien en `SOLARIS_SPACES`. Va al manual del piloto.
- Publicar exige que alguien tenga cada rol de cada regla: en un espacio con pocas personas, obliga a asignar roles o a concentrarlos, y eso queda en el registro.
