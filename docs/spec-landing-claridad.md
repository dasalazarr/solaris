# Spec: claridad de la landing

Estado: borrador para decisión de Diego · Fecha: 2026-11-05 · Área: `landing/` ([[F06]]) · Base: `main` de `solaris_fronted` en `5e6257b`

Parte de una auditoría externa de seis ejes (propuesta de valor, casos de uso, recorrido, información, arquitectura y visual) y de un componente React para «Cómo funciona».

**Qué se ha comprobado:** el código en `5e6257b`, la portada publicada con `curl`, los datos de `product/lib/solaris-data.ts` y los ADR. **Qué no:** las capturas `image_*` no están en este repositorio, así que cada hallazgo se contrastó con el código, no con la imagen. Las estimaciones de esfuerzo son suposiciones.

## 1. Problema

Quien responde de un proceso, y sobre todo quien lo implanta ([[ADR-0011]]), tiene que entender en 30 segundos qué hace Solaris y por qué fiarse (PRD landing §1). Hoy tropieza con cuatro cosas: «Cómo funciona» son 6 columnas estrechas con códigos internos, el Hero y la demo abren en la misma pantalla, el cierre explica dos veces cómo empezar y «tu equipo» es ambiguo.

No resolverlo cuesta atención justo cuando Diego empieza a enseñar la página a consultoras. No bloquea el piloto: lo que lo bloquea es la persistencia de Revisar y la instalación de Nivel 2 (`fundacional.md` §6).

## 2. Veredicto sobre la auditoría

Su diagnóstico es bueno. **Su solución choca con los principios del producto en varios puntos**, sobre todo en el componente propuesto.

### Se acepta

| Propuesta | Comprobación |
|---|---|
| Dar ritmo a las tarjetas de El problema | `THESIS_CARDS`: repiten el título en el cuerpo |
| Describir la transformación en las tarjetas de proceso | `PACKS[].line`: enumeraciones sin verbo |
| Unificar los estados de proceso | Hay tres etiquetas para dos situaciones |
| Fusionar «Dos formas» y «Cuatro pasos» | `TwoWays` repite lo que `HowWeWork` detalla, y siguen seguidas |
| Pasar «Cómo funciona» de 6 a 3 tarjetas, y quitar `PROC-*` y `REV-*` | `Loop.tsx`, `ONTOLOGY_PACKS` |
| Que la demo no abra igual que el Hero | `useState<Tab>('Preguntar')` en `Demo.tsx:439` |
| Integrar las pestañas en la ventana de la demo | `tablist` fuera de `ProductWindow` |

### Se acepta con cambios

| Propuesta | Problema | Qué se hace |
|---|---|---|
| Subtítulo: «…detecta lo que falta y deja lista la decisión para que tú la apruebes» | Pierde «incumple». «Tú» es falso si lee quien no firma: aprueba el rol que exige la regla (principio 3). «De principio a fin» no añade nada | Copy en §7.1 |
| «Vive en tu infraestructura» o «En tu propio entorno» | «Equipo» es ambiguo de verdad: `SolarisOnboarding.tsx:275` lo usa como «personas». Pero «infraestructura» y «entorno» sugieren nube propia, y VPC no se promete ([[ADR-0010]]). Dónde corre sigue abierto (`nivel2-preguntas-y-contrato.md`, H1) | **«En tu organización»**, que ya es la cifra de la página. «Equipo» solo cuando se hable de hardware |
| Replantear Hoy · Siguiente · Visión | Tiene razón en que «se conserva entre sesiones» cuenta una carencia. Pero «En desarrollo» es falso: la Visión son hipótesis que no se construyen sin ADR. «Multi-usuario» no está comprometido (`fundacional.md` §6). «Despliegue privado» roza la palabra vetada. «Automáticamente» promete una federación inexistente | Copy en §7.4. El estado real se sigue diciendo aquí, una vez y bien dicho |
| Pill «nube» huérfana | El diagnóstico se queda corto: el cambio a «tu equipo» solo ocurre con cursor o foco, así que **en móvil se queda en «nube»**, justo lo contrario del título (`Bento.tsx:176-182`) | Estado final visible sin interacción. Sin emojis: icono de `lucide-react`, como el resto |
| Encender los pasos apagados | No es un fallo: el hilo está ligado al scroll y la captura salió a mitad de recorrido. Sí es cierto que termina tarde (`Loop.tsx`: la parte inferior debe llegar al 40 % de la pantalla) | El hilo termina cuando la última tarjeta entra entera (R3) |
| Hilo que avanza con hover | Dos fuentes de estado para un mismo hilo, y en móvil o con teclado no existe | El hilo sigue al scroll; hover y foco solo iluminan el borde de la tarjeta |
| Clic en «Abrir en Revisar» del Hero | Hoy es un `<span>` decorativo dentro de un bloque `role="img"` con `aria-hidden` (`HeroCapture.tsx:123`): parece un botón y no lo es. No basta con poner `onClick` | Control real fuera de ese bloque (R5) |
| Scroll suave | El PRD §6 lo prohíbe | Se permite solo como respuesta a un clic y nunca con movimiento reducido. Se cambia §6 |
| Estados «Probar demo» y «Solicitar con datos de muestra» | Mezclan estado y acción, y la tarjeta ya tiene un enlace | Pastilla con el estado y enlace con la acción (R4) |

### No se acepta

| Propuesta | Por qué | Cómo comprobarlo |
|---|---|---|
| «Registro inmutable», «sello», «sellada», «Propone y sella» | Vetadas: el registro es estado de React y los hashes son de muestra ([[ADR-0010]], principio 4). El propio CSV dice «sin valor probatorio» | `product/lib/audit-export.ts:4` |
| «La IA lee y cita tus documentos» | Se corrigió ayer: la ingesta es simulada | `landing` commit `2c5195c` |
| Ejemplos de Jurídico y Calidad del componente (`CM-2026-14`, Anexo III, `L-8841`, humedad, `R-IFS-01` sobre alérgenos, Molinos del Sur) | No existen en el producto, y `content.ts` obliga a copiar los datos de allí. La landing enseñaría casos que la demo no puede abrir | `grep -n "L-8841\|CM-2026" product/lib/solaris-data.ts` no da resultados |
| «Verificación exacta sobre metadatos y firmas» | El motor compara atributos; no verifica firmas | `product/lib/rules-engine.ts` |
| «Exportable en 1 clic para auditoría IFS», «listo para enseñar al auditor externo» | Es una exportación de demostración sin valor probatorio | `audit-export.ts:4` |
| Copiar el componente tal cual | Ver §8 | §8 |
| Cita de la tabla: «supere los 15.000,00 €» | No es literal; el documento dice «los quince mil euros (15.000,00 €)». El código del componente sí la copia bien (principio 1) | `DEMO_QA[0]` |

### Ya resuelto

- **5 docs o 4 docs:** `ProductWindow`, `HeroCapture` y la portada publicada dicen 5, y el producto tiene 5 documentos en Compras. Queda como criterio de aceptación, sin trabajo.

## 3. Objetivos

1. Un dueño de consultora explica el ciclo en sus palabras tras 30 segundos en «Cómo funciona».
2. Quien baja del Hero ve algo nuevo en la demo y llega a Revisar sin buscarlo.
3. El lector distingue lo que existe hoy de lo que llega con el piloto, y no lo lee como un prototipo.
4. Ninguna frase nueva contradice el producto ni [[ADR-0010]].
5. Sin regresión de rendimiento ni accesibilidad.

## 4. Fuera de alcance

- **Persistencia, firma real o «inmutable» en el producto:** es trabajo de piloto. Si llega, cambia la tabla de [[ADR-0010]] y entonces el copy.
- **Datos de muestra nuevos:** la landing no enseña más de lo que tiene el producto.
- **Sección nueva o proceso comercial cercano al CRM:** sigue pendiente de Diego ([[ADR-0011]]).
- **Tests A/B:** sin tráfico medido no hay experimentos ([[ADR-0007]]).
- **Producción sin `noindex`:** esta spec no lo cambia.

## 5. Historias de usuario

- Como **dueño de una consultora**, quiero ver el mismo ciclo en varios procesos para comprobar que puedo implantar el motor en más de un sector.
- Como **responsable de un proceso**, quiero entender qué dice el documento, qué regla se incumple y quién aprueba para saber si esto resuelve mi problema.
- Como **visitante que baja desde el Hero**, quiero que la demo me enseñe algo nuevo para tener motivo para tocarla.
- Como **quien quiere probar**, quiero saber qué proceso puedo tocar ya y cuál debo pedir para no pulsar en falso.
- Como **socio de un despacho**, quiero saber dónde están mis documentos sin interpretar la palabra «equipo».
- Como **persona con teclado, móvil o movimiento reducido**, quiero el mismo contenido y las mismas acciones.
- Como **auditor o comprador escéptico**, quiero que lo que dice la página coincida con lo que veo en la demo.

## 6. Requisitos

### P0: entra sí o sí

**R1. Copy y vocabulario.** Aplicar §7 en `Hero`, `content.ts`, `Bento` y `TwoWays`.
- [ ] `grep -rn "tu equipo\|tu propio equipo" landing/src` solo devuelve frases sobre hardware.
- [ ] Ninguna palabra vetada por [[ADR-0010]] en presente; «pack» no aparece al lector ([[ADR-0012]]).
- [ ] Tarjeta de privacidad: sin cursor se ve el estado final, también en táctil. Título y pastilla no se contradicen.

**R2. «Cómo funciona» en 3 tarjetas.** Mismas seis ideas, agrupadas: pregunta y cita, regla y hueco, aprobación y registro.
- [ ] Selector Compras, Jurídico y Calidad IFS. Cambia el ejemplo y la estructura se mantiene.
- [ ] Cada dato, cita y regla está en `product/lib/solaris-data.ts`. La cita es literal.
- [ ] Sin `PROC-*`, `REV-*` ni etiquetas repetidas. Sí `R-03` y `PC-0412` ([[ADR-0010]]).
- [ ] Se mantiene el patrón WAI-ARIA de pestañas y el evento `ontologia_pack` de `Loop.tsx`.
- [ ] Las siete primitivas siguen visibles entre las tres tarjetas.

**R3. El hilo.**
- [ ] Sigue al scroll y los tres nodos están encendidos cuando la última tarjeta ha entrado entera en pantalla.
- [ ] Con movimiento reducido, todo encendido y sin animación.
- [ ] Hover y `focus-within` solo cambian el borde. En móvil, línea vertical.

**R4. Estados de proceso.** Dos estados y una acción por tarjeta (§7.3).
- [ ] Compras lleva a `#demo`. Los otros tres abren el formulario con el proceso marcado, como hoy.
- [ ] No queda «Disponible bajo petición» ni «Demo disponible bajo petición».

**R5. Del Hero a la demo.**
- [ ] La demo de la portada abre en **Huecos**. `/demo` sigue abriendo en Preguntar, porque allí no hay Hero antes (`standalone`).
- [ ] «Abrir en Revisar» del Hero es un control real, fuera del bloque `role="img"`, alcanzable con teclado y visible en todo el bucle, también con movimiento reducido.
- [ ] Al usarlo, la página llega a la demo con Revisar activa y el foco en la pestaña o el panel. Scroll suave solo sin movimiento reducido.
- [ ] Evento nuevo de analítica para ese clic. Sin dependencias nuevas.

**R6. Cierre fusionado.** `TwoWays` y `HowWeWork` pasan a una sección: Paso 1 Demostración, Paso 2 Piloto en tu organización y, debajo, la línea 01–04 como detalle del Paso 2.
- [ ] Siguen funcionando `#empezar` y `#como-trabajamos`.
- [ ] Se mantiene la salida de aliados «Implantar Solaris con Illarium» (PRD §1, [[ADR-0009]]).
- [ ] Se conservan los `origin` de analítica para poder comparar.

### P1: mejora notable, puede ir después

**R7. Pestañas dentro de la ventana de la demo.** Sin emojis ni animación permanente. Se mantiene `role="tablist"`, sin scroll horizontal de la página a 375 px y una sola navegación visible.

**R8. Fecha del caso de Jurídico.** `AV-9041` vence el 15/11/2026, y la landing decía «quedan menos de 30 días». En la landing se resuelve con una fecha fija: «A fecha de la muestra (03/11/2026) quedan 12 días». El producto evalúa ahora con `SAMPLE_NOW` (`lib/solaris-data.ts`) y rotula «a fecha de la muestra: 03/11/2026» en Huecos, en la rama `fix/fecha-de-muestra` de `illariumcore`.

### P2: tener presente, no se construye

- **Caso comercial cercano al CRM:** el selector debe admitir un cuarto caso sin rediseño ([[ADR-0011]]).
- **Generar el contenido de los casos desde el producto:** hoy se copian a mano; con un cuarto caso podría compensar.

## 7. Copy final

Segunda persona de tú. La palabra resaltada sigue el patrón actual.

### 7.1 Hero

> Solaris cruza tus documentos con tus reglas: responde con la cita exacta, señala lo que incumple o falta y deja lista la acción para que la apruebe quien responde de ella.

### 7.2 El problema

| Título | Cuerpo |
|---|---|
| IA usada a escondidas | Contratos y pedidos subidos a herramientas públicas, sin control de la empresa. |
| Respuestas a ciegas | Textos convincentes, sin enlace al documento ni a la página. |
| Normas muertas en PDFs | Políticas escritas que nadie alcanza a cruzar a mano con cada expediente. |

### 7.3 Por proceso

Las frases de la auditoría se han ajustado a las reglas que existen en el producto.

| Proceso | Línea | Estado | Acción |
|---|---|---|---|
| Compras | Cruza ofertas, certificados de proveedor y umbrales de firma antes de emitir el pedido. | Demo en esta página | Probar la demo |
| Jurídico y mercantil | Detecta vencimientos, anexos sin firmar y cláusulas de cambio de control en cada expediente. | Bajo petición · datos de muestra | Solicitar demostración |
| Calidad IFS Food | Cruza registros de proceso y certificados de envase de cada lote antes de liberarlo. | Bajo petición · datos de muestra | Solicitar demostración |
| Diligencia EUDR | Comprueba la geolocalización de cada parcela antes de emitir la declaración de diligencia. | Bajo petición · datos de muestra | Solicitar demostración |

### 7.4 Hoy · En tu piloto · Visión

| Columna | Nota | Elementos |
|---|---|---|
| **Hoy** | Pruébalo en la demostración, con datos de muestra | Citas con documento, página y fragmento literal · Reglas que evalúa el código, siempre igual · Huecos: lo que incumple, lo que falta y el dato sin evidencia · Aprobación por el rol que exige la regla, con registro exportable |
| **En tu piloto** | Lo preparamos contigo para el primer piloto | Instalación en tu organización, sin salida a internet, con tus documentos reales · El contrato del proceso, adaptado a tus normas · Registro permanente de aprobaciones |
| **Visión · hipótesis** | Por validar; no forman parte de la oferta | Modelos por proceso · Federación entre procesos: Compras consulta a Calidad por el certificado de un proveedor sin mezclar sus contratos |

### 7.5 Privacidad y cierre

- **Tarjeta:** «En tu organización» · «Con tus documentos reales, Solaris se instala dentro y sin salida a internet.» · pastilla «tu organización».
- **Título del cierre:** «De la demostración a tu *instalación*.»
- **Paso 1:** Demostración · 30 minutos, datos de muestra.
- **Paso 2:** Piloto en tu organización · Tus documentos reales.
- **Paso 03 de la línea:** «En tu organización, sin que los documentos salgan de ella.»
- **FAQ:** sustituir «tu equipo» por «tu organización» en «¿Dónde están mis datos?» y en la pendiente de RGPD. En «¿Qué modelo usa?» y «¿Necesito comprar hardware?» se habla de máquinas: usar «un equipo» de forma explícita.

### 7.6 Cómo funciona

- **Cabecera:** igual que hoy, con el final «…El motor es el mismo en cada sector; cada contrato define sus reglas.» Se mantiene «La IA redacta y explica».
- **Insignias:** `01 · Responde y cita`, `02 · Evalúa y detecta`, `03 · Propone y registra`.
- **Títulos:** Pregunta y evidencia, Regla y hueco, Aprobación y registro.

| | Compras · `PC-0412` | Jurídico · `AV-9041` | Calidad IFS · `L-2610-C` |
|---|---|---|---|
| **01 Pregunta** | ¿Por qué está retenido el pedido PC-0412 y qué exige el contrato para emitirlo? | ¿Qué contratos tienen garantías próximas a vencer y qué falta en el expediente? | ¿El lote L-2610-C cumple los parámetros térmicos PCC-2 y qué falta para liberarlo a Francia? |
| **01 Cita** | Política Corporativa de Compras y Gasto v3.2 · pág. 4 · § 2.1: «Todo pedido de compra cuyo importe neto supere los quince mil euros (15.000,00 €) requerirá la firma de aprobación expresa de la Dirección Financiera…» | Póliza M-219 · pág. 6 · Estipulación Novena: «El aval bancario solidario n.º AV-9041 por importe de 85.000,00 € vencerá improrrogablemente el día 15 de noviembre de 2026…» | Registro de autoclave · pág. 3: «Lote L-2610-C esterilizado en autoclave n.º 3 a 121,4 °C durante 28 minutos (Valor F0 acumulado: 8,4 min; límite crítico IFS >= 6,0 min).» |
| **02 Regla** | R-03: importe neto > 15.000 € ⇒ firma de Dirección financiera antes de emitir | R-JUR-03: aval a menos de 30 días de vencer ⇒ renovación aprobada por el socio | R-IFS-02: sin ensayo de migración vigente del envase, el lote no se libera |
| **02 Hueco** | Tiene sus 3 ofertas, pero supera 15.000 € y falta la firma | A fecha de la muestra (03/11/2026) quedan 12 días y no consta la renovación | F0 conforme, pero falta el certificado de migración de la tapa TO-63 |
| **03 Acción** | Borrador: emitir la orden de compra PC-0412. No se envía sola | Borrador: instrucción de renovación del aval. No se envía sola | Borrador: solicitud del certificado de migración. No se envía sola |
| **03 Registro** | Aprueba Dirección financiera; queda registrado con la versión del contrato y la evidencia enlazada. Repetir el paso no duplica la acción | Igual, con el Socio director | Igual, con Dirección de Calidad y Seguridad Alimentaria |

Pie de primitivas: Proceso, Objeto y Relación, Evidencia en la 01; Regla y estado en la 02; Acción y Revisión en la 03. Valores de los ya presentes en `ONTOLOGY_PACKS` y, para Calidad, de `contract` y `objects` del producto.

## 8. Qué se aprovecha del componente propuesto

**Se aprovecha:** la estructura de 3 tarjetas, el bloque doble y el pie de primitivas. Y buena parte del texto de Compras.

**No se aprovecha:** lo demás. `Loop.tsx` ya resuelve casi todo lo que aquí falla.

| Problema | Regla que incumple | Se resuelve con |
|---|---|---|
| Colores `#EBB343`, `#0C0D0E` y `zinc-*` | `marca.md`: solar es `#F2B544`, ink es `#0D0F14` | Tokens |
| Selector sin `role="tab"`, sin flechas y sin analítica | WCAG, PRD §7 y §9 | El de `Loop.tsx` |
| Iluminación solo con `onMouseEnter` | Teclado y táctil no existen | `:hover` y `:focus-within` |
| Nodos `hidden md:grid` | PRD §7: en móvil, vertical | La línea actual |
| `activeCard = 2` al cargar: todo encendido | El hilo deja de explicar nada; PRD §6 lo liga al scroll | La lógica actual con `n = 3` |
| Sin movimiento reducido | PRD §6 | `usePrefersReducedMotion` |
| `zinc-500` a 10 px sobre el fondo: 3,84:1 | AA pide 4,5:1 | Opacidades ya comprobadas |
| Hueco y registro en serif cursiva | Newsreader se reserva a citas: parecerían citas sin serlo (principio 1) | Serif solo en el bloque de cita |
| Tres columnas desde `md` (768 px) | Texto muy estrecho | `lg`, como hoy |
| Resaltado propio; datos dentro del componente; `export default` con tilde en el nombre | Convenciones del repositorio | `Evidence`, `content.ts` y exportación con nombre |
| Errata «ASESORÍA JURÍDica» y `REV-*` en las etiquetas | Contradice su propio diagnóstico | Se retira |

## 9. Métricas

La página sigue con `noindex` y sin línea base: **hoy no hay un número con el que comparar**, así que no pongo objetivos de conversión inventados.

**Antes de publicar (se decide con esto):**

| Prueba | Umbral |
|---|---|
| 5 personas del perfil consultora o implantador, 30 s en «Cómo funciona»: «explícamelo» | Al menos 4 nombran cita, regla y aprobación |
| Las mismas: «¿qué existe hoy y qué llega con el piloto?» | Al menos 4 lo separan bien |
| Las mismas: «¿dónde están tus documentos?» | Al menos 4 responden sin ayuda |
| Lighthouse móvil | Sin regresión frente a `main`. El objetivo del PRD sigue siendo ≥ 95 (última medida local: 79) |

**Tras publicar, con Umami y línea base de 2 semanas** (ya pendiente en `plan/STATUS.md`):

- **Adelantados:** porcentaje de sesiones con `demo_pestana`, `demo_aprobacion`, `ontologia_pack` y el nuevo clic del Hero.
- **Retrasados:** solicitudes por perfil, sobre todo «aliado», y demostraciones que acaban en diagnóstico.

Revisión a las 4 semanas de quitar `noindex`. Los objetivos numéricos se fijan con la línea base delante.

## 10. Preguntas abiertas

| # | Pregunta | Quién | ¿Bloquea? | Propuesta |
|---|---|---|---|---|
| Q1 | ¿«En tu organización» en lugar de «en tu equipo»? | Diego | Resuelta (05/11) | Sí, [[ADR-0013]] |
| Q2 | ¿Cómo mantenemos cierto el caso `AV-9041` tras el 15/11/2026? | Diego y dev | Falta publicar antes del 15/11 | Resuelta: fecha de muestra fija y rotulada en producto y landing. Mover el vencimiento habría hecho desaparecer el hueco, porque con el reloj real deja de cumplir `< 30 días` |
| Q3 | ¿Renombrar «Siguiente» a «En tu piloto»? Cambia la regla de copy del PRD §1 | Diego | No | Aplicado en la Entrega 1, pendiente de su visto bueno ([[ADR-0013]]) |
| Q4 | ¿Son ficticios «Suministros Industriales del Norte», «Logística y Embalajes Delta» y «Envases Ibéricos»? | Diego | Antes de indexar | Ya abierto como H7. El tríptico da más visibilidad al primero; el tercero se añade a la comprobación |
| Q5 | ¿Jurídico sigue siendo el primer piloto? Afecta al orden del selector, no a su contenido | Diego | No | Mantener Compras, Jurídico, Calidad IFS ([[ADR-0011]]) |

## 11. Entrega

**Coste y qué desplaza:** en torno a 2,5 días de dev (suposición). Retrasa H6, y sobre todo el trabajo de piloto. **Mi recomendación:** hacer ya la Entrega 1, porque es barata y Diego ya enseña la página; la 2 a continuación; y la 3 solo si la prueba con personas la pide.

| Entrega | Contenido | Esfuerzo |
|---|---|---|
| 1 | R1, R4 y R8 | Medio día |
| 2 | R2 y R3 | 1 día |
| 3 | R5, R6 y R7 | 1 día |

Un PR a `main` por entrega, sin apilar. Cada uno se crea cuando el anterior está en `main` y comprobado en producción, incluido `noindex`.

**Gate de cada entrega:** lint y build de `landing`; teclado, sin red y 375 px en local; movimiento reducido; preview en navegador. `security` solo si cambia el formulario o la analítica envía datos nuevos.

**Documentación al aprobar:**

- Hecho con la Entrega 1: [[ADR-0013]], `docs/prd-landing.md` (§1, §3 y §5, filas 8 y 9) y `docs/fundacional.md` (§3 y §6).
- Con la Entrega 2: PRD §5 fila 4 y `wiki/features/F06-landing-comercial.md`.
- Con la Entrega 3: PRD §5 filas 9 y 10 (pasan a 12 secciones) y §6 (scroll con clic).
- La frase de `SolarisOnboarding.tsx:275` no cambia: ahí «tu equipo» son personas.
