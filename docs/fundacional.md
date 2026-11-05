# Solaris · documento fundacional

> Por qué existe Solaris, qué valor añade y qué no hará. Es la referencia para escribir copy, decidir alcance y responder a un prospecto. Se deriva de `prd-producto.md` y `prd-landing.md`; si chocan, mandan los PRD y este documento se corrige. Versión 1 · 2026-11-02.

## 1. Tesis

**Las empresas no necesitan más chatbots. Necesitan que sus procesos tengan contrato.**

Un proceso crítico (comprar, revisar un contrato, liberar un lote, declarar una importación) ya tiene reglas. Están escritas en políticas, manuales, normas y contratos. El problema no es que falten reglas; es que nadie las cruza con cada expediente, y cuando alguien pregunta «¿se puede aprobar esto?», la respuesta depende de la memoria de una persona o de un chatbot que no puede demostrar de dónde la saca.

Solaris convierte ese proceso en un objeto gobernado por un contrato explícito: alcance, responsable, reglas, umbrales y KPIs. Sobre ese contrato:

1. **Lee** los documentos del proceso.
2. **Responde** citando documento, página y fragmento literal.
3. **Detecta** con reglas deterministas lo que incumple o falta.
4. **Propone** la acción como un borrador editable.
5. **Espera** la aprobación registrada de la persona que exige la regla.

## 2. El problema, en palabras del cliente

| Quién | Qué vive hoy | Coste |
|---|---|---|
| Dirección financiera u operaciones de una pyme | Pedidos que superan umbrales sin las ofertas o la firma exigidas; facturas sin pedido | Se descubre en auditoría, tarde |
| Socio de un despacho | Vencimientos, anexos sin firmar y cláusulas de cambio de control repartidos en expedientes | Riesgo profesional; no puede subir expedientes a la nube |
| Responsable de calidad o cumplimiento | Reglas en PDFs (IFS, EUDR) que nadie cruza con los registros | Un hueco que nadie vio hasta la no conformidad |
| Todos | Empleados que usan IA a escondidas con documentos confidenciales | Fuga de datos y respuestas sin fuente |

Problemas registrados: [[P01]] (procesos sin contrato) y [[P02]] (respuestas sin cita no auditables). Ambos en validación con el despacho.

## 3. Qué es y qué no es

| Solaris es | Solaris no es |
|---|---|
| Un motor de procesos con contrato que usa un LLM para leer y redactar | Un chatbot sobre sus documentos |
| Un sistema que dice «no consta» cuando no hay fuente | Un sistema que siempre responde |
| Un propositor: prepara la acción y la deja lista para firmar | Un agente que envía, emite o firma por su cuenta |
| Una capa sobre el ERP y las carpetas que ya existen | Un sustituto del ERP ni un gestor documental |
| Instalado en el equipo del cliente cuando hay documentos reales | Un SaaS multicliente (el Nivel 3 está descartado por diseño) |

## 4. Cómo funciona: siete primitivas

Un **Proceso** (el contrato, con `policy_hash` versionado) gobierna seis primitivas: **Objeto**, **Relación**, **Evidencia**, **Regla**, **Acción** y **Revisión**. El motor no cambia entre sectores; cada pack define sus tipos.

Dos reglas de rigor sostienen todo lo demás:

- Un atributo sin Evidencia no evalúa ninguna regla.
- Una extracción con confianza < 0,80 queda como candidata hasta que una persona la valide.

## 5. El valor añadido de Solaris

El valor no es «IA». Es **confianza verificable** en un proceso que ya existe. Se descompone en cinco promesas; cada una es falsable y tiene su prueba.

| Promesa | Qué gana el cliente | Por qué un chatbot no lo da | Cómo se prueba |
|---|---|---|---|
| **1. Cada afirmación se puede comprobar en un clic** | Deja de discutir si la respuesta es cierta: abre el fragmento | El chatbot parafrasea y no distingue lo que leyó de lo que supuso | ≥ 95 % de respuestas con cita verificada por el cliente; 0 afirmaciones sin fuente presentadas como hecho ([[H02]]) |
| **2. Las reglas deciden; el modelo explica** | El mismo expediente da el mismo resultado hoy y dentro de un año; se puede auditar por qué | La decisión del modelo cambia con el prompt, la versión o la temperatura | Una regla se evalúa por código, con tests, sobre atributos con Evidencia |
| **3. El hueco aparece antes de la auditoría** | Pasa de descubrir incumplimientos a prevenirlos | Un chatbot solo responde a lo que se le pregunta | Huecos confirmados por el responsable del proceso durante el piloto |
| **4. Ninguna acción sin una persona** | Acelera sin ceder el control ni la responsabilidad; registro exportable para el auditor | El agente autónomo ejecuta, y el error se descubre después | Cada acción tiene Revisión con rol, `step_id` + `args_hash` y entrada en el registro |
| **5. Los documentos no salen de su organización** | Puede usar IA con expedientes bajo secreto profesional o datos personales | El chatbot en la nube cede los datos a un tercero | Instalación de Nivel 2 sin salida a internet, verificable por el cliente |

Y uno transversal: **el entorno dice la verdad**. La interfaz siempre muestra si son datos de muestra en la nube o documentos reales en local. Un producto que vende confianza no puede exagerar ni en su propia cabecera.

### En una frase, por audiencia

- **Dirección financiera:** «Sabrás qué pedido incumple tu política antes de firmarlo, con el párrafo que lo dice.»
- **Socio de despacho:** «IA sobre tus expedientes, en tu equipo, que cita cada cláusula y no firma nada por ti.»
- **Calidad y cumplimiento:** «Tus normas cruzadas con cada lote, con el hueco señalado antes de la auditoría.»
- **Consultora o canal:** «Un motor, un contrato por proceso: tú aportas el proceso, Illarium aporta el contrato.»

## 6. Dónde estamos frente a esa promesa (2026-11-04)

Ser honestos con el estado es parte del valor. Detalle en [`sinergia-landing-producto.md`](sinergia-landing-producto.md).

| Promesa | Estado |
|---|---|
| 1. Cita en un clic | Hecho en respuestas predefinidas. Pregunta libre: el servidor descarta toda cita que no sea del pack o no sea literal, y sin modelo responde «No puedo responder ahora» (illariumcore#5, fusionado el 03/11). El texto del párrafo lo redacta el modelo y se rotula así. |
| 2. Reglas deciden | Motor mínimo `evaluate(regla, objetos)` con tests por pack: el estado de cada regla y `evaluatedRuleCodes` salen del código (illariumcore#8, fusionado el 03/11). Sin Relaciones entre objetos todavía. |
| 3. Hueco antes de la auditoría | Hecho: Huecos lo calcula el motor (#8); ya detecta lo que falta (R-02 en PC-0419) y no da por conforme un dato sin evidencia o < 0,80. |
| 4. Persona en el bucle | Hecho como interfaz: borrador, exportación CSV/PDF y, desde illariumcore#9 (sin fusionar), el rol exigido se comprueba en el cliente. Falta persistencia y comprobación en servidor. Los `args_hash` son de muestra. |
| 5. Nada sale de su organización | Diseñado, no construido. La demo ya no ofrece un instalador que no existe (illariumcore#7, fusionado el 03/11). Preguntas para el despacho y contrato de interfaces en `nivel2-preguntas-y-contrato.md`. |

**Consecuencia:** el piloto de pago ([[H01]]) depende de cerrar 4 (persistencia de Revisar) y 5 (instalación local de Nivel 2). La demo pública ya demuestra 1, 2 (motor mínimo), 3 y 4 con datos de muestra.

**Lectura para la landing** ([[ADR-0009]], sección «Hoy · Siguiente · Visión»): *Hoy* = filas 1–4 tal como están; *Siguiente* = solo lo comprometido para el piloto (persistencia de Revisar e instalación local), sin fechas; *Visión* = hipótesis de la Visión v2 del PRD, siempre rotuladas como tales.

## 7. Lo que no haremos (y por qué es parte del valor)

- **No ejecutar acciones externas sin Revisión aprobada.** Ni aunque el cliente lo pida para «ganar tiempo».
- **No presentar una respuesta sin fuente como hecho.** Mejor «no consta» que una buena frase.
- **No mezclar clientes en una base compartida.** Nivel 3 descartado.
- **No construir la Visión v2** (modelos por proceso, federación entre procesos, portal de proveedores) sin un ADR de Diego.
- **No publicar cifras, clientes ni pilotos que no existan.** Ni en la landing ni en el diario.

## 8. Cómo usar este documento

- **Copy:** toda frase de la landing debe poder señalar una fila de §5 y un estado de §6 que la respalde. Si el estado es «no construido», la frase describe la oferta («se instala»), nunca un resultado («nuestros clientes ahorran»).
- **Alcance:** una tarea que no mueve ninguna de las cinco promesas hacia «hecho» pasa detrás de las que sí.
- **Ventas:** las frases de §5 son el guion de los primeros dos minutos de la demostración.
- **Mantenimiento:** se actualiza §6 al cerrar cada hito, junto con `plan/STATUS.md`.
