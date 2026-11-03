# Sesión 2026-11-03 · product-steward + dev + security · citas verificadas, entorno honesto, motor de reglas, perfil y Nivel 2

## Tarea
Encargo de la sesión «Análisis de sinergia Solaris»: corregir F3, F1 y el principio 4 del producto, añadir `perfil` a `/api/solicitud` para la landing y preparar las preguntas del Nivel 2 (F2) sin código.

## Qué se hizo
| Tarea | Rama / PR (dasalazarr/illariumcore) | Estado |
|---|---|---|
| 1 · Citas verificadas (F3/O2) | `fix/citas-verificadas` · #5 | Abierto; security APTO con condiciones, aplicadas |
| 4 · `perfil` en `/api/solicitud` | `feat/solicitud-perfil` · #6 | Abierto; security APTO |
| 2 · El entorno dice la verdad | `fix/entorno-dice-la-verdad` · #7 | Abierto |
| 3 · Motor de reglas mínimo (F1/O4) | `feat/motor-reglas-minimo` · #8 (apilado sobre #5) | Abierto; criterios en PRD §8.1 |
| 5 · Preguntas del Nivel 2 y contrato de interfaces | `docs/nivel2-preguntas-y-contrato.md` | Borrador |

- **Tarea 1:** lógica pura en `lib/ontology-query.ts`. Se descarta toda cita cuyo `evidenceId` no esté en el pack del espacio o cuyo `quote` no aparezca literalmente en la Evidencia. Sin clave o con error: 503 «No puedo responder ahora», sin cita. Condiciones de security: límite de 20 por espacio e IP cada 15 min, tiempo máximo de 20 s, 413 por encima de 16 KB, registro sin la pregunta, fragmento verificado en la interfaz y texto rotulado «redactado por el modelo».
- **Tarea 2:** modal → «Arquitectura prevista del Nivel 2», sin `docker-compose`; ingesta → «simulada (datos de muestra)», sin Docling/Surya.
- **Tarea 3:** `lib/rules-engine.ts`, `evaluate(regla, objetos, { now })`. Las reglas declaran `logic`; los datos pierden `status`, `affectedObjectIds` y los `evaluatedRuleCodes` de las preguntas. Huecos, el contador y «Re-evaluar» (antes ms aleatorios) salen del motor.
- **Tarea 4:** `perfil` opcional `cliente | aliado | inversor`, validado, en el cuerpo y el asunto del aviso.

## Qué falló o se descubrió
- La «Acción propuesta» de la pregunta predefinida se veía junto a una respuesta libre. Corregido en #5.
- «Re-evaluar contrato» enseñaba un tiempo aleatorio (11–18 ms): otra afirmación falsa de la interfaz. Corregido en #8.
- El motor encuentra un hueco que los datos escritos a mano no tenían: **R-02 en PC-0419** (9.200 € ≥ 6.000 € sin evidencia de ofertas). PC-0412 no cambia.
- Sin Relaciones en las condiciones, R-01 aplica solo a los pedidos que traen el certificado del proveedor. Limitación documentada en el PRD §8.1.
- Un `cat >` sin heredoc colgó un comando 2 minutos. Lección: no redirigir a un fichero sin entrada.

## Decisiones
- #8 apilado sobre #5 porque ambos tocan `app/api/ontology-query/route.ts`.
- Estados del motor: `sin_evidencia` y `candidato` nunca se presentan como `conforme` (PRD §3).
- Puntero del submódulo `product` en la raíz sin cambios: los PR no están fusionados.

## Sin verificar
- Pregunta libre con una clave real de Gemini: no hay clave local. Sí probado: sin clave → «No puedo responder ahora», sin cita.
- `/api/solicitud` con `perfil` de extremo a extremo con Resend.
- Tope de gasto en la clave de Gemini (fuera del código; condición de security para desplegar).

## Evidencia
- #5: `npm test` → 48 passed; lint y build OK. #6: 35 passed. #7: 31 passed. #8: 70 passed (21 del motor); lint y build OK en todas.
- Navegador (`next dev` local con un espacio de prueba temporal no versionado): pregunta libre sin clave; Huecos de Jurídico (R-JUR-01 incumplida, R-JUR-03 requiere aprobación) y Compras (R-03, R-01 y R-02 «FALTA EVIDENCIA» en PC-0419); «Re-evaluar» → «Evaluado en < 1 ms en este navegador».
