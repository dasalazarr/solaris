# Sinergia landing ↔ producto · auditoría del 2026-11-02

> Fuente: código de `landing/` (main, desplegado en `solaris.dasalazarr.com`) y `product/` (main, `illariumcore.vercel.app`), contrastado con `prd-producto.md` y `prd-landing.md`. Comprobado leyendo el código y con `curl` a la landing publicada. **Supuesto, no comprobado:** si `GEMINI_API_KEY` está configurada en el despliegue del producto.

## Conclusión

La landing y el producto cuentan la misma historia (cita, reglas, persona que aprueba, dos niveles) y comparten marca y caso. Pero hay **tres afirmaciones publicadas sin respaldo** y **dos promesas centrales que el producto todavía no cumple**: el motor de reglas determinista y la instalación local (Nivel 2). Las primeras se arreglan en una hora; las segundas son el trabajo real antes de cobrar el piloto.

## 1. Copy: lo que se afirma en público

| # | Afirmación en la landing | Dónde | Respaldo | Veredicto |
|---|---|---|---|---|
| C1 | Calidad IFS Food: «Piloto en curso» | `landing/src/data/content.ts` (`PACKS`) | Ninguno. No hay piloto IFS en `wiki/`, `plan/` ni `raw/`. El PRD dice «se mantiene, sin funciones nuevas». | **Falso. Corregir ya.** Propuesta: «Demo disponible bajo petición». |
| C2 | Diario: «El primer piloto en calidad alimentaria», «Un error que no volveremos a cometer», «Por qué cada respuesta lleva su párrafo» (24/10, 10/10, 27/09) | `content.ts` (`DIARY`) | Entradas inventadas como relleno. Las reales son las de `docs/diario/` (31/10 y 02/11). El PRD pide leer el RSS al compilar. | **Falso. Corregir ya.** Sustituir por las entradas reales que Diego publique, o retirar la sección hasta que haya tres. |
| C3 | «Una base, muchas vistas: los mismos documentos sirven a compras, calidad y dirección» | `Bento.tsx` | El producto aísla cada pack. Cruzar procesos es la «Federación entre procesos» de la Visión v2. | **Promete v2.** Reescribir: «Un motor, muchos procesos: cada proceso con su contrato, sus reglas y su vista.» |
| C4 | «0 documentos salen de su equipo» / «Se instala en su equipo» / FAQ «modelo de pesos abiertos en su equipo» | `Figure.tsx`, `Bento.tsx`, FAQ | El Nivel 2 no existe en el producto: solo un modal con un `docker-compose` cuyas imágenes `illarium/solaris-*` no están publicadas. La consulta usa Gemini en la nube. | **Promesa de oferta, no de producto.** Aceptable si el piloto se entrega instalado; es el mayor riesgo comercial (ver F2). No ampliar este mensaje hasta que exista. |
| C5 | «Sus reglas, escritas una vez y evaluadas siempre» / «Cruza sus reglas con cada expediente» | `Bento.tsx` | El estado de cada regla está escrito a mano en `solaris-data.ts`; el campo `expression` se muestra pero no se evalúa. | **Cierto en la demo, no en el motor.** Ver F1. |
| C6 | «Si no puede citarlo, no lo afirma» / «Cada respuesta cita documento, página y párrafo» | Bento, FAQ | Respuestas predefinidas: sí. Pregunta libre: las citas que devuelve el LLM no se validan; sin clave o con error, el servidor devuelve una respuesta fija con una cita que no responde a la pregunta. | **Parcial.** Ver F3. |
| C7 | «IA privada para sus procesos» (eyebrow y título SEO) | `Hero.tsx`, `site.ts` | Verdad en Nivel 2; la demo es nube, y la landing lo dice en la cifra. | Coherente mientras C4 se cumpla. |
| C8 | Pestañas de la maqueta: Preguntar · Huecos · Revisar · **Documentos** | `ProductWindow.tsx` | El producto tiene Preguntar · **Explorar** · Huecos · Revisar. | Ya en STATUS. Propuesta: manda el producto («Explorar»), porque es donde viven Objeto, Relación y Evidencia. |
| C9 | Títulos: «Solaris · IA privada para sus procesos» vs «Solaris — IA privada para procesos con contrato \| Illarium» | `site.ts`, `product/app/layout.tsx` | — | Menor. Unificar en «Solaris · IA privada para procesos con contrato». |

## 2. Funcionalidad: misma promesa, distinto grado de realidad

| Capacidad (PRD) | Landing (demo estática) | Producto | Hueco |
|---|---|---|---|
| Preguntar con cita literal | 3 preguntas con cita y resaltado | Preguntas predefinidas + pregunta libre con Gemini | Citas libres sin validar (F3) |
| «Sin fuente» visible | No se enseña | Sí (`hasNoSourceClaim`, `unverifiedWarning`) | **Oportunidad O3** |
| Explorar: objetos, atributos, evidencia | No aparece | Sí | La landing no enseña la ontología |
| Candidatos < 0,80 a validación humana | No aparece | Sí, simulado (formulario precargado, rotulado «Docling + Surya OCR») | Rótulo afirma un OCR que no corre (principio 4) |
| Huecos por reglas deterministas | Sí (4 huecos) | Sí, pero precalculados | Sin motor (F1) |
| Revisar con borrador, `step_id` + `args_hash` | Aprobar / rechazar → línea en registro | Sí, en estado del cliente; exportación CSV/PDF | Sin persistencia: el piloto la necesita |
| Contrato del proceso y KPIs | Una celda pequeña | Panel completo (responsable, alcance, umbrales, `policy_hash`, KPIs) | **Oportunidad O2** |
| Dos niveles, entorno siempre visible | Sí («Demostración · datos de muestra») | Sí (cabecera, entrada y recorrido) | Coherente |
| Packs | 4 con estados | 4 con datos de muestra | C1; Jurídico infravendido (O1) |

### El caso PC-0412 no es el mismo caso

Un prospecto que prueba la demo de la landing y luego entra en el producto ve dos PC-0412 distintos:

| | Landing | Producto |
|---|---|---|
| Importe | 18.400 € | 18.450,00 € |
| Proveedor | Metalúrgica Duero (envases metálicos) | Proveedor Ficticio Norte (válvulas INOX) |
| Regla | R-COMP-07: > 15.000 € ⇒ 3 ofertas + firma DF | R-03: > 15.000 € ⇒ firma DF; R-02: 3 ofertas entre 6.000 y 15.000 € |
| Documento | «Política de compras v3.2», pág. 4 §3.2 | «Política Corporativa de Compras y Gasto v3.2» |

PRD landing §10 pide «datos de muestra coherentes del pack Compras». Propuesta: el producto es la fuente; la landing copia sus importes, proveedor, códigos de regla y documento. Coste: una tarde en `content.ts`, sin tocar el diseño.

## 3. Fallos del producto que la landing deja al descubierto

**F1 · No hay motor de reglas.** El principio 2 («las reglas son código») es la diferencia con un chatbot, y hoy es un campo de texto. Además, `evaluatedRuleCodes` lo rellena el LLM: el modelo declara qué reglas se evaluaron, justo lo contrario del principio. Mínimo para el piloto: una función pura `evaluate(rule, objects) → {estado, evidencias}` sobre atributos con `evidenceId` y `validated`, con tests, que alimente Huecos y sustituya `evaluatedRuleCodes` del LLM.

**F2 · No hay Nivel 2.** Ni `LLMProvider`/`Store`/`Ingestor`, ni imágenes, ni instalador. La landing vende la privacidad como argumento principal para despachos. El modal «Instalador de Nivel 2» ofrece copiar un `docker-compose` que no arranca: debería rotularse «Arquitectura prevista» hasta que exista. PRD §8 ya lo deja abierto; el playbook del despacho debe cerrarlo antes de escribir código.

**F3 · Citas de pregunta libre sin verificar.** En `app/api/ontology-query/route.ts`:
- El `evidenceId` y la `confidence` que devuelve el modelo no se contrastan con el pack.
- Sin `GEMINI_API_KEY`, o ante cualquier error, se devuelve una respuesta fija («consta acreditado en el expediente…») con la primera evidencia, responda o no a la pregunta. En el `catch`, además, siempre del pack Compras, aunque el espacio sea Jurídico.
- Corrección pequeña: descartar o marcar «sin fuente» toda cita cuyo `evidenceId` no exista en el pack; comprobar que el fragmento citado aparece literalmente; y ante fallo, responder «No puedo responder ahora» sin cita. Esto además hace medible [[H02]].

## 4. Oportunidades (ordenadas por impacto en el piloto / coste)

| # | Oportunidad | Por qué | Coste | Desplaza |
|---|---|---|---|---|
| O1 | Corregir C1, C2, C3 y C9 en la landing | Afirmaciones falsas en una URL que ya reciben prospectos | 1 h | Nada |
| O2 | Validar citas y quitar la respuesta fija (F3) | Sin esto, la FAQ «compruébelo en un clic» puede fallar delante de un socio | ½ día | Nada |
| O3 | Un mismo PC-0412 en landing y producto | Continuidad landing → demo → producto; PRD landing §10 | ½ día | Nada |
| O4 | Motor de reglas mínimo (F1) | Es el diferencial; sin él, Huecos es una maqueta | 2–3 días | Pack `equipo` ([[ADR-0007]] fase 1) |
| O5 | Enseñar «sin fuente» en la demo de la landing: una cuarta pregunta cuya respuesta dice «no consta en los documentos» | Ningún competidor chatbot lo enseña; responde la objeción nº 1 («la IA se inventa cosas») mejor que un adjetivo | 2 h | Nada |
| O6 | Jurídico «Demo disponible» y una pestaña o página `/demo/juridico` con el aval AV-9041 y el anexo IV | El piloto de pago es un despacho y la landing solo enseña compras; los datos ya existen en el producto | 1 día | LCP del hero |
| O7 | Contrato del proceso visible en la landing: responsable, alcance, umbrales y un KPI | Es la tesis («procesos con contrato») y hoy es la celda más pequeña | ½ día | — |
| O8 | Persistir Revisar y el registro de auditoría | Un piloto sin registro persistente no demuestra el principio 3 | 1–2 días, depende de `Store` (F2) | — |
| O9 | El proceso elegido en el formulario y la UTM preseleccionan el pack del espacio de demo | Menos fricción entre solicitud y reunión | 2 h | — |

Propuesta de orden: **O1 → O2 → O3** esta semana (ninguna necesita decisión de Diego más allá de aprobar los PR). **O4** y el diseño de Nivel 2 (F2) son el bloque del piloto, después del playbook. O5–O7 cuando haya línea base de Umami.

## 5. Qué no se recomienda

- Añadir a la landing métricas de ahorro, clientes o «horas recuperadas»: no hay ni un piloto medido.
- Abrir más packs o idiomas en la landing: el producto ya tiene ES/FR/EN, pero el mercado P0 es España.
- Escribir el instalador de Nivel 2 antes de saber el hardware y la red del despacho (playbook, bloque 3).
