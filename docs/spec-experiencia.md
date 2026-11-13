# Spec de experiencia del producto

Criterios de la Fase 1 ([`plan-evolutivo.md`](plan-evolutivo.md), [[ADR-0015]]). La referencia es `video/`: `src/Cruza.tsx`, `src/Detecta.tsx`, `src/Firma.tsx` y el [brief](../video/briefs/2026-11-06-compras.md). Referencia, no límite: si una pantalla funciona mejor de otra forma, se dice y se cambia.

## Principio

**Una idea por pantalla, con la fuente a un gesto.** Se toman del vídeo la jerarquía, el lenguaje y las secuencias.

**No se copia:** fondo oscuro con grano, desenfoques, cámara, cursor animado ni el número gigante. La app sigue clara y la entrada oscura ([`marca.md`](marca.md)).

## Estructura

| Elemento | Escritorio | Móvil |
|---|---|---|
| Navegación | Menú lateral con contadores | Barra inferior |
| Orden | Preguntar, Explorar, Huecos, Revisar; «Contrato» y «Registro» aparte | Igual, con «Más» para los dos últimos |
| Proceso activo | En el menú, con nombre legible | En la cabecera |
| Entorno | Siempre visible y completo | Siempre visible: sin perder «nube» ni «muestra» |
| Evidencia | Zona lateral de la superficie | Panel inferior que se abre desde la cita |

Esto cierra un pendiente abierto desde el 01/11: la landing y el vídeo muestran menú lateral y el producto, pestañas. Manda el menú lateral.

## Recorrido inicial

Sustituye al onboarding de 5 pasos. Desde [[ADR-0021]] se deriva de los datos de cada proceso.

- Una bienvenida de una pantalla: el párrafo citado, el nombre del proceso, la etiqueta del entorno y lo que hay dentro.
- Tres actos sobre el producto real: **Cruza → Detecta → Firma**, con las leyendas del vídeo. Se superan haciendo la acción (pulsar una cita, abrir la regla, aprobar con el rol que exige), no con «Siguiente».
- Al decidir, un puente a probar con una regla propia.
- Se puede saltar, se recuerda y se puede volver a abrir.
- No pide datos que el producto no use.
- «Reiniciar demo» vuelve al estado inicial y lo avisa antes.

## Superficies

| Superficie | Debe poder verse y hacerse | Referencia |
|---|---|---|
| **Preguntar** | Dos zonas: respuesta y evidencia. Dictamen primero, acción propuesta después. Pulsar una cita abre el párrafo exacto con página y sección. «Cómo lo evalúa el motor» visible en el dictamen. «Sin fuente» inequívoco, también en la pregunta libre | `Cruza.tsx` |
| **Huecos** | Matriz de reglas × objetos arriba, con «No evaluada» distinta de «Conforme». Una celda abre su detalle con regla, fuente y acción. Fecha de evaluación visible. «Datos por validar» aparte, con barra de confianza y mínimo de 0,80 | `Detecta.tsx` |
| **Revisar** | Por qué → borrador → decisión, con la decisión siempre visible en escritorio; en móvil sigue al borrador, para no tapar la cola. El bloqueo por rol aparece junto al botón. Al aprobar se ve el hueco cerrado y el contador baja, con enlace al registro | `Firma.tsx` |
| **Registro** | Quién, decisión, versión y evidencia. Códigos e identificadores en detalles técnicos. Exportación que respeta el filtro | `Firma.tsx` |
| **Explorar** | Documentos y objetos, con el contador sin ambigüedad. Cada dato con su fuente y el «sin fuente» tachado que el motor no usa | Guion, plano 2 |
| **Contrato** | Alcance, responsable, umbrales y KPI, que salen de Preguntar. Editable desde la Fase 3 | Nueva |

## Lenguaje

- De tú, sin «pack» ([[ADR-0012]]) ni términos vetados ([[ADR-0010]]).
- Las leyendas del vídeo son la primera opción para títulos y ayudas.
- Sin códigos en primer plano: `Timestamp`, `INGESTA_CANDIDATO` o `args_hash` van a detalles técnicos.
- Mismos nombres de proveedor en producto, landing y vídeo, una vez resuelta H7.

## Veracidad

Arreglos vistos en producción el 07/11:

- La pestaña dice «IA privada» en una demo en la nube.
- La entrada anuncia «Equipo propio del cliente», que no existe.
- Una respuesta fallida muestra «Respuesta en ES · citas en ES» y cajas vacías de objetos y reglas.
- El entorno móvil se abrevia a «Demo · muestra».
- Una pregunta libre no puede acabar en un mensaje de error de forma habitual.

## Criterios de aceptación

1. Cada plano de producto del vídeo tiene una pantalla real equivalente.
2. A 375 px no hay scroll horizontal y lo primero de Preguntar es la pregunta.
3. WCAG 2.2 AA: contraste, foco visible, nombres accesibles y matriz manejable con teclado y lector de pantalla.
4. La regla de Compras y sus huecos no cambian: `npm run gate` en `video/` y los tests pasan.
5. El recorrido completo se hace en menos de 90 segundos con el guion de [`guion-demo-90s.md`](guion-demo-90s.md), actualizado.
6. Alguien que no es Diego hace la demo sin ayuda.
