---
fecha: 2026-11-07
rol: cofundador
tema: comprobar la Fase 1 y la pregunta libre en producción
---

# Fase 1 en producción

## Tarea
Comprobar en producción la pregunta libre tras fusionar illariumcore#17 y #18.

## Qué se hizo
- `main` del producto en 886c2bd, desplegado. Título nuevo y menú lateral a la vista.
- Pregunta con fuente: «¿Quién debe firmar un pedido de más de 15.000 euros?». HTTP 200, responde Dirección Financiera y cita la Política de Compras v3.2, pág. 4.
- Pregunta sin fuente: «¿Cuál es el salario de la directora financiera?». Responde «No consta» con el bloque «Sin fuente».
- illariumcore#19: sin cita no se muestra dictamen y el panel de evidencia lo dice.

## Qué falló
- La respuesta sin fuente enseñaba el dictamen R-03 de PC-0412 y un párrafo resaltado sin relación. Parecía respaldar la respuesta.
- La prueba local no se vio antes porque, sin clave, solo se llega a «No puedo responder ahora».
- Un código de prueba con mayúsculas no entra: `normalizeCode` pasa a minúsculas antes de calcular el hash. Los códigos de `nuevo-codigo.mjs` son hexadecimales y no se ven afectados.

## Decisiones
- El arreglo va en el componente y deja de lado `verifyAnswer`, porque cubre también las preguntas predefinidas.

## Evidencia
- Dos consultas reales a Gemini con datos de muestra. Sin errores de `ontology-query` en los logs de Vercel de esos 10 minutos.
- #19: 118 tests, lint y build. Navegador local con la respuesta del modelo simulada. Código de prueba desechable, ya borrado.

## Sin comprobar
- Qué causaba el rechazo anterior de Google: cambiar a `gemini-3.5-flash-lite` lo resolvió, pero el código de error nunca quedó registrado.
- Tope de gasto de la clave, imprimir a PDF, lector de pantalla y revisión de security.
