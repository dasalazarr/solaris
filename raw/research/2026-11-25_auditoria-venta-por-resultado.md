# Auditoría: vender el resultado, no el stack (25/11/2026)

Entradas: `www.illarium.com/solaris` (leída el 25/11), dos posts de LinkedIn de Illarium (18.450 € y 9.200 €), captura de la demo Finanzas · Cierre mensual, [[ADR-0026]], [[ADR-0030]], `plan/STATUS.md`.

## 0. Conclusión

1. **La jerga es real, pero no es el cuello de botella.** Hay cero conversaciones con compradores, la landing sigue con `noindex`, sin imagen Open Graph y sin enlace de agenda. Reescribir el texto cuesta medio día y vale la pena. Rediseñar la parte visual hoy no mueve ninguna métrica: no hay tráfico con el que medirlo.
2. **Antes de reescribir hay que elegir comprador.** Hoy hay cuatro mensajes en cuatro sitios:
   - Landing: Compras en una empresa española (€, Dirección financiera).
   - LinkedIn: Compras y Finanzas en España (€, Agencia Tributaria, #Pamplona).
   - Demo Finanzas: PYME de Ecuador ($, SRI). Un director financiero español que llega del post de 9.200 € y abre esa demo ve dólares y un organismo que no conoce.
   - [[ADR-0030]] (de hoy): despachos de 2 a 19 personas en Pamplona y Logroño.
   El brief pide orientarlo todo al director financiero de una PYME. Eso contradice la ADR-0030 o la amplía. Lo decide Diego.
3. **Tres peticiones del brief no se pueden cumplir sin mentir.**
   - «Conciliación de facturas sin intervención manual»: Solaris no lee facturas reales (la Fase 4 no existe) y la [[ADR-0030]] descarta la extracción de facturas como oferta.
   - «Elevator pitch centrado en el ROI» con cifras: no hay nada medido. [[ADR-0010]] y [[ADR-0026]] lo prohíben hasta medirlo en la oferta cuña.
   - «Prueba en entorno aislado» con documentos del cliente: no hay Nivel 2. El entorno aislado que existe es la demo con datos de muestra.
4. **Una corrección urgente:** el post de 18.450 € dice en presente «Solaris se instala en tu organización. No salen de ella.». Hoy es falso (principio 4; es el mismo hallazgo H3 que security cerró en la landing el 04/11). Hay que editarlo: «La instalación dentro de tu organización es el siguiente paso del piloto».

## 1. Propuesta comercial: la oferta cuña

### Oferta (versión dirección financiera, misma forma que la ADR-0030)

**Revisión de 21 días: tu política de compras y pagos, contra tus expedientes.**

| Semana | Qué pasa | Qué te llevas |
|---|---|---|
| 1 | En una hora contigo, elegimos un circuito (pedidos o pagos a proveedor) y escribimos de 3 a 5 de tus normas como reglas comprobables: umbral de firma, certificados vigentes, factura que respalda el pago. | Tus normas escritas, cada una con la página de tu política que la exige. |
| 2 | Revisamos hasta 20 expedientes cerrados contra esas reglas, en tus oficinas o sobre copias anonimizadas. Cronometramos tu revisión actual y la nuestra. | Lista de excepciones, cada una con el documento y la página que la prueban. |
| 3 | Entregamos el dictamen y la medida de antes y después, y te enseñamos Solaris aplicando tus reglas a datos de muestra. | Una decisión: piloto con precio de fundador, o adiós sin coste. |

Condiciones que no se negocian: ningún documento tuyo entra en Solaris ni en un sistema nuestro durante la revisión. Ninguna cifra de ahorro se promete antes de la semana 3.

### Pitch de dos líneas

> Tu política dice quién firma, qué certificado debe estar vigente y qué pago necesita factura, pero hoy eso lo comprueba la memoria de alguien.
> En 21 días revisamos tus últimos expedientes contra esas normas y te enseñamos, con página y párrafo, lo que se escapó y cuánto tardaste en verlo; si no compensa, no sigues.

El ROI aparece como algo que se mide en la revisión, no como una cifra inventada.

### De característica a resultado

| Hoy decimos (característica) | Debería decir (resultado) | ¿Es cierto hoy? |
|---|---|---|
| Responde con cita: documento, página y párrafo | Cualquier auditor comprueba cada excepción en un clic | Sí, en la demo |
| Reglas que evalúa el código, no el modelo | El mismo expediente da el mismo resultado, lo revise quien lo revise | Sí |
| Revisión por el rol que exige la regla | Cada excepción queda firmada por quien la autorizó, con fecha | Sí, en la demo |
| Huecos: incumple, falta, dato sin evidencia | Te avisa también de lo que falta, no solo de lo que está mal | Sí |
| Registro exportable | El rastro para el auditor ya está hecho | Sí, en la demo |
| IA privada, instalación local | Tus documentos no salen de la empresa | **No.** Solo en futuro |
| (brief) Extracción automática con LLM local | (brief) Conciliación de facturas sin intervención manual | **No.** No se escribe |
| R-SRI-02, débito sin comprobante | Cada pago a proveedor sin factura que lo respalde aparece marcado | Sí, con datos de muestra |

## 2. Landing

### 2.1 Propuesta de valor (hero)

| Elemento | Hoy | Propuesta |
|---|---|---|
| Etiqueta | IA privada para procesos | Para Compras y Dirección financiera |
| H1 | Tus procesos, con contrato. | Lo que tu política exige, comprobado en cada pedido antes de que salga. |
| Subtítulo | Lo que vence, lo que falta y lo que incumple. Con la página exacta. | Firmas que faltan, certificados caducados, pagos sin factura. Cada uno con la página de tu política que lo exige. |
| CTA principal | Solicitar demostración | Ver un caso en 2 minutos (abre la demo en PC-0412) |
| CTA secundario | Probar la demo | Hablar de la revisión de 21 días |
| Sello | (ninguno) | Datos de muestra · nada se envía sin la firma de una persona |

«Procesos con contrato» es la tesis de la empresa, no el problema del comprador. Se queda como lema de marca en el pie y en los hashtags, no en el H1.

### 2.2 Casos de uso

| Hoy | Propuesta |
|---|---|
| Las empresas no necesitan más chatbots. | El fallo no está en el pedido. Está en el documento que nadie cruzó con él. |
| IA usada a escondidas | Un pedido de 18.450 € sale sin la firma que exige tu política. |
| Respuestas a ciegas | Un proveedor con el certificado de Hacienda caducado recibe un pedido de 9.200 €. |
| Normas muertas en PDFs | Un pago sale sin la factura que lo respalda y aparece en la auditoría, meses después. |
| Compras / Jurídico / IFS Food / EUDR al mismo nivel | Compras arriba. Jurídico como segundo caso. IFS y EUDR en una línea: «También en calidad alimentaria y diligencia EUDR, bajo petición». |

El encuadre de hoy compite con «la IA»; el director financiero no compra «no ser un chatbot», compra no tener la excepción.

### 2.3 Recorrido del comprador

Hoy: post → enlace en comentarios → landing genérica (cuatro sectores) → dos CTA con el mismo peso → formulario → respuesta a mano por correo → llamada.

Fricción, ordenada por impacto:
1. **No hay enlace de agenda** (`NEXT_PUBLIC_AGENDA_URL` sin poner). Cada solicitud espera a que Diego conteste. Es el mayor freno. Antes, Privacidad debe nombrar al proveedor de agenda (H4 de security).
2. **El post y la landing no hablan del mismo caso.** El post de 9.200 € lleva a un hero de 18.450 €. Debería llevar a la misma escena: `/solaris?caso=aeat#demo` con UTM ([[ADR-0031]]).
3. **Sin imagen Open Graph:** el enlace sale sin vista previa en LinkedIn.
4. **Dos CTA iguales** («Solicitar demostración» y «Probar la demo»): no se sabe cuál es el siguiente paso.
5. **Demo Finanzas en dólares y SRI** para un público de España.

Propuesta: post → landing en el mismo caso → demo de 2 minutos en ese caso (abrir cita, ver la excepción, firmar) → CTA en la demo «Quiero esta revisión con mis normas» → formulario de 3 campos con agenda en la misma pantalla → llamada de 30 minutos → propuesta de 21 días por escrito.

### 2.4 Orden de los bloques

| # | Hoy | Propuesta |
|---|---|---|
| 1 | Hero | Hero: resultado y un caso concreto |
| 2 | El problema (chatbots) | El problema: tres excepciones reales de Compras y pagos |
| 3 | Cómo funciona (ontología, 7 piezas) | Qué te llevas: lista de excepciones con cita, firmas registradas, rastro para auditoría |
| 4 | Lo que hace Solaris | Cómo funciona sin riesgo: 3 pasos (escribimos tus normas, Solaris las comprueba, una persona decide) |
| 5 | Demo interactiva | Demo interactiva con datos de muestra (el entorno aislado que sí existe) |
| 6 | Por proceso (4 sectores) | La revisión de 21 días (la oferta) |
| 7 | Hoy · En tu piloto · Visión | Tus datos: qué pasa hoy (nada entra en Solaris) y qué pasa en el piloto |
| 8 | Dos formas de empezar | FAQ |
| 9 | Cómo trabajamos (consultoras) | Cierre con agenda |
| — | FAQ, cierre | Fuera de la home: ontología (a una página «Cómo está hecho»), Visión e hipótesis, la sección para consultoras (página propia) |

### 2.5 Visual e interfaz

La paleta oscura con dorado ya transmite solidez; lo que suena a herramienta para desarrolladores es la tipografía monoespaciada y los identificadores.

- Fuera de la web y de los posts: `PROC-COMP-01`, `R-03`, `REV-COMP-01`, `R-LIQ-01`. Se sustituyen por la frase de la norma: «Firma de Dirección financiera por encima de 15.000 €».
- Monoespaciada solo para las citas (documento · página · párrafo), que es donde aporta: parece un expediente.
- Etiquetas en versalitas espaciadas («COMPRAS Y FINANZAS», «DESLIZA →»): pasarlas a minúsculas normales en la sans.
- Importes con cifras tabulares y siempre con su moneda; nunca mezclar € y $ ante el mismo público.
- Mascota con cara en el hero: para un director financiero suena a producto de consumo. Opinión sin medir; [[ADR-0023]] está propuesta. Recomiendo que viva en el contenido y el primer uso, no en el hero de la landing.
- Animación del hero: una secuencia de menos de 3 s (párrafo de la política que se resalta → «Falta la firma» → firma registrada), sin brillos ni partículas, con `prefers-reduced-motion`. Quitar la animación palabra a palabra del H1, que además pesa en el LCP (2,9 s en móvil simulado).
- Confianza: quién está detrás (Diego, con nombre y cara), razón social, el sello «datos de muestra» siempre visible. Ningún logo de cliente que no exista.
- En los posts, cambiar las etiquetas de la ontología (→ Relación, → Evidencia, → Regla, → Revisión) por verbos: «→ Sigue el pedido hasta el proveedor», «→ Te enseña la página que lo prueba», «→ Decide con una regla escrita», «→ Deja la firma a quien le toca».

## 3. Producto y demo

### Concierge más plantilla

Ya tenemos la plantilla ([[ADR-0018]]): espacios con datos ficticios precargados. Lo que falta es el concierge:

1. **Antes de la llamada:** el prospecto nos da 3 normas suyas por escrito (umbral, certificado, factura), **no documentos**. Diego ajusta los umbrales en una copia de la plantilla de Compras y crea 3 expedientes ficticios que las disparan. De 1 a 2 horas por prospecto.
2. **En la llamada (30 min):** 5 min de su proceso con sus palabras; 10 min en el espacio con **sus** normas: abre la excepción, la cita, firma; 10 min de qué pasaría en la revisión de 21 días; 5 min de siguiente paso con fecha.
3. **Momento «ajá»:** el prospecto ve una excepción que reconoce como suya, abre la cita y firma. Objetivo: menos de 2 minutos desde que entra. Es lo que hay que medir en cada demo.
4. **Qué demo para quién:** a un director financiero español, Compras (en €). Finanzas · Cierre mensual está en $ y con el SRI: solo para el canal de Ecuador ([[ADR-0026]]). Una versión española (AEAT, IVA, €) cuesta trabajo de dev; esperar a la puerta del 09/12.
5. **Bloqueo:** dar un espacio propio a cada prospecto sigue vetado por security (falta validar Privacidad y la política de códigos de ≤ 30 días). Hasta entonces la demo se hace en la llamada, con pantalla compartida.

### Métrica norte del piloto de 21 días

**Excepciones materiales confirmadas por el responsable que su revisión actual no había detectado, cada una con su cita**, por cada 20 expedientes.

- No «horas ahorradas»: en el concierge la revisión la hacemos a mano y el ahorro aún no es del producto. El director financiero firma por el riesgo que evita, no por el tiempo.
- Métricas de control: minutos por expediente antes y después (lo que sí se puede contar después) y excepciones rechazadas por el responsable (falsos positivos).
- Criterio de firma, hipótesis para que Diego lo fije: al menos 1 excepción material confirmada cuyo coste supere el precio del piloto, y menos de 1 de cada 4 excepciones rechazadas.

## 4. Qué haría y qué desplaza

| Orden | Tarea | Quién | Coste | Desplaza |
|---|---|---|---|---|
| 1 | Editar el post de 18.450 € (Nivel 2 en presente) | Diego | 5 min | Nada |
| 2 | Elegir comprador para la landing: despachos (ADR-0030) o dirección financiera de PYME en España | Diego | Una decisión | Nada |
| 3 | Enlace de agenda + Privacidad | Diego | 1 h | Nada |
| 4 | Reescribir hero, problema y «Cómo funciona»; sacar ontología, Visión y consultoras de la home; imagen OG | landing-steward | ½–1 día, un PR | Pulido de interfaz del producto |
| 5 | Guion de demo con el concierge (3 normas del prospecto) | product-steward | ½ día | Nada |
| — | Rediseño visual completo | — | No ahora | Sin tráfico no se puede medir |

## 5. Contraste con la segunda propuesta (pegada por Diego el 25/11)

Comprobado en `product/lib/templates/cfo.json`: 5 reglas (R-LIQ-01, R-SRI-02, R-MAR-03, R-CON-04, R-BAN-05). Ninguna detecta duplicados y ninguna bloquea pagos: marcan la excepción y dejan la firma a una persona.

### Se adopta

- Llamada de diagnóstico como CTA, no «comprar».
- Animación del hero con un documento tangible: entra una factura, pasa por la política y sale con la firma o con la excepción marcada. Coincide con 2.5.
- Interior claro: fondos blancos y grises cálidos como dentro del producto, y el verde para «cumple». Tiene sentido, pero es un rediseño: va después del texto y cuando haya tráfico.
- Una cifra en euros al cierre del piloto (ver la métrica corregida abajo).
- «Sin tocar tu ERP»: es cierto y ya está en la FAQ. Hay que subirlo.

### Se rechaza, porque hoy es falso o inventado

| Propuesta | Problema | Versión cierta |
|---|---|---|
| «Audita el 100 % de tus facturas» | No lee facturas reales: la Fase 4 no existe | «Comprueba cada expediente contra tus normas» (en la demo) |
| «Bloqueando pagos indebidos» | No bloquea nada ni está conectado a la banca | «Marca la excepción antes de que salga el pago y deja la firma a quien le toca» |
| «Detecta pagos duplicados» | No hay ninguna regla de duplicados | Fuera, hasta que exista una regla |
| «Cero alucinaciones, precisión absoluta» | La regla es determinista; la lectura del documento y la redacción no lo son. La demo enseña una lectura con confianza 0,74 que pide validación | «La decisión de si cumple la toma una regla que puedes leer, no la IA» |
| «Privacidad total: nunca abandonan tu infraestructura» | No hay Nivel 2. Es el mismo error del post de 18.450 € | «En el piloto, la instalación es dentro de tu organización» (futuro) |
| «Conciliación sin intervención manual» | Lo mismo; además, la ADR-0030 descarta la extracción de facturas como oferta | «Cada pago sin factura que lo respalde aparece marcado» |
| Diagnóstico con lote de documentos reales del cliente cargados en Solaris | Lo prohíben la Fase 5, la ADR-0026 y la ADR-0030 hasta tener modelo local, acuerdo de confidencialidad, encargo de tratamiento y el veto de security levantado | Concierge: revisión a mano en sus oficinas o sobre copias anonimizadas; en Solaris, solo datos de muestra |
| «Solaris extrajo el dato» en la demo | Los datos de muestra vienen estructurados. ADR-0029: la interfaz no dice que los haya procesado el modelo | «Con datos de muestra ya leídos» |
| Calculadora de ROI u horas ahorradas en la landing | Nada medido; lo prohíben ADR-0010 y ADR-0026 | Fuera hasta tener la medida de la semana 3 de un piloto |
| Social proof de «auditores aliados» | No existe ninguno. Inventarlo rompe la regla de datos y la confianza | Nada, o la persona que hay detrás con nombre y cara |
| «340 documentos, 12.450 $ interceptados, 38 horas» | Cifras inventadas, en dólares | Plantilla con huecos que se rellenan al medir |
| Casos SRI y $ en la landing | El público de los posts y de la landing está en España | SRI solo en el canal de Ecuador (ADR-0026); en España, AEAT y € |
| H1 «Cierra el mes sin sorpresas» | Promete un resultado contable completo que no depende solo de Solaris | H1 de 2.1 |
| «Eliminar el planeta amarillo» | Coincido en sacarlo del hero (2.5). La paleta oscura no es lo que suena a cripto; lo son los brillos y la tipografía mono | Ver 2.5 |
| «Sin migraciones ni integraciones» | El Nivel 2 exige instalar un equipo en el cliente | «No sustituye a tu ERP ni se conecta a tu banco» |

### Métrica norte, ajustada con la idea del capital

**Importe expuesto en excepciones confirmadas por el responsable** que su revisión actual no había detectado, cada una con su cita. Ejemplo: «pedido de 18.450 € sin la firma que exige la política, pág. 4». Es una cifra en euros y es cierta, porque la confirma el cliente. No es «capital salvado»: ese dinero no se ha perdido ni recuperado.

Plantilla del cierre: «En 21 días revisamos [N] expedientes. Tu equipo confirmó [M] excepciones que se habían escapado, por [X] €, cada una con su página. Tu revisión pasó de [a] a [b] minutos por expediente». Cada hueco se rellena con lo medido; ninguno se rellena antes.
