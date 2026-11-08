---
fecha: 2026-11-08
rol: cofundador
tema: crear un proceso como línea base
---

# Proceso nuevo y línea base

## Tarea
Diego pidió crear un proceso como línea base y eligió construirlo desde la app.

## Qué se hizo
- `lib/process-cases.ts`, tablas `processes` y `process_cases`, `app/api/process/new`, y casos de prueba en el editor.
- illariumcore#22 (Fase 3) abierto tras fusionar #21.

## Qué falló
- Tras crear, el editor no se abría: se consumía antes de cargar el proceso. Corregido.
- Dos eventos del registro con el mismo id al guardar casos y contrato a la vez. Corregido; el almacén de prueba conservaba el duplicado.
- Faltaba añadir tipos de objeto en el editor.
- Security: NO APTO en la primera versión. Cambiar los datos de un caso no invalidaba lo aprobado sobre él, y guardar casos se saltaba el tope diario. En el repaso, el arreglo abrió dos fallos más: no se podía reaprobar y volver a los datos anteriores revivía la aprobación. Todo corregido con tests; APTO en 757261e.

## Evidencia
- 253 tests, lint, build y gate de `video/`.
- Navegador local con códigos desechables, ya borrados: modo guardado (Comercial crea y define; Riesgos decide), demostración (copia de Compras con 4 casos) y 375 px sin scroll horizontal.

## Sin comprobar
- H03 con una persona. Pregunta libre con casos de prueba y el modelo real. Imagen Docker.
