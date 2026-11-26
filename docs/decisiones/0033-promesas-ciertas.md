---
id: ADR-0033
type: decision
title: "Cada promesa comercial se construye antes de decirse: importe expuesto, retenido hasta la firma, duplicados y cronómetro de revisión"
status: proposed
owner_role: product
links: ["[[ADR-0010]]", "[[ADR-0026]]", "[[ADR-0029]]", "[[ADR-0030]]"]
evidence: ["raw/research/2026-11-25_auditoria-venta-por-resultado.md"]
updated: 2026-11-25
---

# ADR-0033 · Promesas ciertas

- Fecha: 2026-11-25
- Estado: propuesta. Diego eligió el bloque 1 el 25/11.

## Contexto

La auditoría del 25/11 comparó lo que piden la venta por resultado y una segunda propuesta externa («capital interceptado», «bloquea pagos», «detecta duplicados», «ahorra horas») con lo que hace el producto. Ninguna de las cuatro era cierta. Diego prefiere construirlas antes que recortar el mensaje.

## Opciones

1. Recortar el mensaje a lo que hay.
2. Decirlo ya y construirlo después. Rompe el principio 4 y la coherencia entre landing y producto.
3. **Construir la versión cierta de cada promesa y solo después decirla.**

## Decisión

Opción 3. Bloque 1, sin cambiar el motor de sitio ni las siete primitivas:

- **Importe expuesto.** Vista derivada, como el brief de [[ADR-0029]]. Suma el importe de los objetos con un hueco que el motor decide (incumplida o requiere aprobación) y que nadie ha aprobado. Cada importe lleva su cita. Lo que no tiene importe con evidencia validada se cuenta aparte y no se suma. El contrato declara qué dato es el importe de cada tipo y en qué moneda va el proceso.
- **Retenido hasta la firma.** Etiqueta derivada de un hueco abierto y de su regla: nada sale de Solaris sin la firma del rol que exige. No bloquea nada fuera de Solaris; la interfaz no dice «bloqueado en el banco».
- **Duplicados.** Operador fijo `unique`: un objeto incumple si existe otro anterior del mismo tipo con los mismos valores en las claves indicadas y con la fecha a como mucho N días. Determinista; los dos objetos citan su evidencia.
- **Cronómetro.** Cada decisión guarda los milisegundos que la revisión estuvo abierta en pantalla antes de decidir (reloj monótono del navegador, con tope). Es «tiempo con la revisión abierta», no «horas ahorradas», y se nombra así.

## Consecuencias

- Finanzas pasa de 5 a 6 reglas (R-DUP-06) y gana un pago duplicado a Proveedor Ficticio Manglar en octubre.
- La landing no cambia hasta que esto esté fusionado. Después puede decir: «importe expuesto, con su cita», «retenido hasta la firma» y «detecta pagos duplicados» (en la demo, con datos de muestra).
- No se construye: bloqueo en banca, «capital salvado», calculadora de ROI.
- Desplaza los pendientes de dev de la auditoría del 14/11.
