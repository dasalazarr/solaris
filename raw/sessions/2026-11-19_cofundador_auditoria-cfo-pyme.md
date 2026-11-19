---
fecha: 2026-11-19
rol: cofundador
tema: Auditoría del proceso y del vertical CFO PYME (Ecuador)
---

# Auditoría CFO PYME

## Tarea
Diego: auditar el proceso y el vertical CFO, e investigar y estructurar los procesos y procedimientos que necesita una PYME. Llegó de nuevo la propuesta de canal (expediente mensual, cuatro reglas, firma del especialista).

## Hecho
- Búsqueda web sobre el SRI (104, 103, ATS, noveno dígito, RIMPE), la bancarización de más de 500 $ (Ley de Eficiencia Económica, 2023), el IESS y la Supercias.
- Lectura de `cfo.json`, `seeds/cfo.ts` y `rules-engine.ts` en `feat/motor-linear-cfo`.
- `raw/research/2026-11-19_cfo-pyme-procesos-ecuador.md`: mapa de procesos, clasificación por operador, 11 hallazgos, propuesta priorizada y preguntas para el contador.
- O08 pasa a `validating`. ADR-0026 recibe el punto abierto 3.

## Aprendido
- La regla con más valor económico (bancarización de más de 500 $) no se ve en el extracto: un pago en efectivo no deja movimiento. Hay que mirar el comprobante recibido.
- Usar el total de créditos bancarios como «ingresos» da falsos conformes: un préstamo hace cumplir R-MAR-03.

## Sin comprobar
- Ninguna fuente oficial leída a mano; los datos de prensa se contradicen en el día no hábil y en las fechas de RIMPE.
- No se tocó código; las propuestas no se probaron en el motor.
