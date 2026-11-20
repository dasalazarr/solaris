---
id: ADR-0030
type: decision
title: "La muestra de un proceso puede cambiar los textos del recorrido, no sus pasos"
status: proposed
owner_role: product
links: ["[[ADR-0021]]", "[[ADR-0026]]", "[[ADR-0028]]"]
evidence: ["product/lib/first-run.ts", "product/lib/seeds/cfo.ts", "product/tests/first-run.test.ts"]
updated: 2026-11-20
---

# ADR-0030 · Textos del recorrido por muestra

- Estado: propuesta. Diego la acepta o la corrige al revisar el PR del producto.
- Contexto: el diseño de onboarding de la demo de Finanzas (laboratorio de onboarding, 19/11) pide textos que hablen el idioma del contador: «Esta cuenta no la hace la IA: faltan 1.222,00 $ para el margen del 15 %». [[ADR-0021]] dice que ninguna plantilla declara su recorrido. La bienvenida de Finanzas ya la sustituye el brief del cierre (rama `feat/brief-cfo`), así que aquí solo entran los pasos 2 a 5.

## Opciones

1. **Dejar los textos genéricos.** No cuesta nada. «Pulsa una cita» no le dice a un contador por qué le importa.
2. **Textos en la plantilla (`lib/templates/*.json`).** La plantilla también la usa un piloto con datos reales, y los textos citan cifras de la muestra: un piloto vería 8.420,00 $ que no son suyos. Rompe los principios 1 y 4.
3. **Textos en la muestra (`lib/seeds/*.ts`), opcionales.** Cambian lo que se dice en cada paso; los pasos, la pregunta, la cita y la decisión siguen saliendo de los datos.

## Decisión

Opción 3. `PackSeed.firstRun` (tipo `FirstRunCopy`) trae título y cuerpo para `cita`, `regla`, `firma` y `cierre`. Sin él, el recorrido usa los textos genéricos.

- La firma con persona identificada usa siempre el texto genérico: el rol lo fija la sesión.
- El cierre pone el recuento real de incumplimientos abiertos (`{abiertos}`) y tiene un título para cuando no queda ninguno.
- El cierre de Finanzas no abre la zona de pruebas: lleva a pedir un diagnóstico con un mes real en la landing (concierge de [[ADR-0026]]). No se sube nada al producto.
- Un test comprueba que el texto nombra la regla, el rol y la cita a los que lleva el recorrido, y que «faltan 1.222,00 $» es lo que calcula R-LIQ-01 sobre la muestra.

## Consecuencias

- **Se gana:** cada muestra puede hablar el idioma de su comprador sin tocar el motor ni el recorrido.
- **Cuesta:** los textos se pueden desalinear de la muestra; por eso el test. Si alguien edita R-LIQ-01 en la zona de pruebas, el texto del paso 3 sigue diciendo 1.222,00 $ (sin corregir: el recorrido ocurre antes de editar nada).
- **Matiza [[ADR-0021]]:** la plantilla sigue sin declarar el recorrido; la muestra solo pone palabras.
