# Solaris — PRD v1

*Síntesis v1 · se completa por iteraciones con Diego. Las secciones 1–5 son el texto de Diego; 6–8 se han añadido a partir de sus respuestas.*

## 1. Tesis y marca

- Illarium es la empresa y consultora; Solaris es el producto.
- **Tesis pública:** «Las empresas no necesitan más chatbots; necesitan que sus procesos tengan contrato.»
- **Qué hace:** convierte procesos críticos (compras, revisión de contratos, calidad IFS, aduanas EUDR) en objetos gobernados por un contrato explícito (alcance, responsable, reglas, umbrales y KPIs). Lee los documentos del proceso, detecta qué falta o incumple, propone la acción y espera la aprobación de la persona responsable.

## 2. Cinco principios innegociables

1. **Toda afirmación lleva cita:** documento, página y fragmento literal en papel serif; sin evidencia, se marca como «sin fuente».
2. **Las reglas son código, no memoria del LLM:** los incumplimientos los calcula un motor determinista reproducible sobre la ontología; el modelo solo redacta y explica.
3. **Una persona en el bucle (anti-atrofia):** ninguna acción externa se ejecuta sin decisión humana explícita, borrador editable e idempotencia (`step_id` + `args_hash`).
4. **El entorno dice la verdad:** la interfaz declara siempre si corre en la Nube de demostración (Nivel 1, datos de muestra) o en una Instancia local en el equipo del cliente (Nivel 2, documentos reales, sin salida a internet).
5. **Pulido sin sobreingeniería:** un único motor con interfaces abstractas (`LLMProvider`, `Store`, `Ingestor`); herramientas de venta (Sala Viva) y funciones experimentales quedan fuera del producto cliente.

## 3. Modelo de dominio: 7 primitivas

Una primitiva superior (**Proceso**, con `policy_hash` versionado en Pydantic v2) gobierna las 6 primitivas operativas:

- **Objeto** (entidad tipada) · **Relación** (vínculo) · **Evidencia** (fichero, página, párrafo, hash) · **Regla** (condición determinista) · **Acción** (borrador editable e idempotente) · **Revisión** (decisión humana trazada con `run_id` y `thread_id`).
- *Nota 2026-11-04:* el producto actual es TypeScript; el contrato no se valida con Pydantic y la interfaz ya no lo menciona ([[ADR-0010]]).
- **Reglas de rigor:** ningún atributo sin Evidencia evalúa reglas; toda extracción con confianza < 0,80 queda retenida como candidata hasta validación humana.

## 4. Superficies y packs de la v1

- **Entrada oscura + App clara:** acceso por código de espacio aleatorio de al menos 128 bits (≥ 128 bits) validado en servidor (cookie HttpOnly, sin listado público de espacios) y onboarding de 5 pasos con vía rápida y consentimiento desmarcado por defecto.
- **Cuatro superficies de trabajo:**
  1. **Preguntar** (3 columnas: Contrato y KPIs a la izquierda · Respuesta citada en el centro · Documento original en papel serif con fragmento resaltado en Ámbar Solar a la derecha).
  2. **Explorar** (grafo de objetos, atributos con su evidencia e ingesta OCR con cola de candidatos < 0,80).
  3. **Huecos** (incumplimientos detectados por reglas deterministas).
  4. **Revisar** (cola unificada de Aprobaciones, Bloqueos y Validaciones con borrador editable y registro de auditoría exportable en CSV/PDF).
- **Cuatro packs sobre el mismo motor:** Proceso de compra (P0, demo de landing), Jurídico y mercantil (P0, primer piloto de pago en despacho), IFS Food (P1) y EUDR (P1).
- *Cambio 2026-11-07 ([[ADR-0015]]):* los packs pasan a ser plantillas de una definición de proceso en datos; se añade la superficie **Contrato** para editarla; la navegación y las superficies siguen [`spec-experiencia.md`](spec-experiencia.md), y un recorrido de 3 pasos sustituye al onboarding de 5 con su consentimiento, que no se usaba.

## 5. Criterio de éxito de la v1

1 piloto real de Nivel 2 instalado en el equipo del despacho y convertido a contrato de pago, con ≥ 95 % de respuestas con cita verificada por el cliente y 0 afirmaciones sin fuente presentadas como hecho.

*Abierto desde 2026-11-07 ([[ADR-0015]]):* quién es el primer piloto (despacho o industria) se decide en la puerta tras la Fase 3 de [`plan-evolutivo.md`](plan-evolutivo.md). El listón de citas no cambia. Criterio intermedio: los cuatro modos de «listo» de ese plan.

## 6. Riesgos

Cada riesgo entra con su mitigación y su estado. Se añade un riesgo nuevo solo si Diego lo confirma.

| Riesgo | Por qué importa | Mitigación | Estado |
|---|---|---|---|
| **Seguridad de la demo (Nivel 1)** | Los códigos de espacio estaban escritos en el código fuente (y siguen en el historial de git), existía un acceso sin código (atajo Alt+D / `PUT /api/space`) y las rutas de consulta no comprobaban la sesión. Incumple el §4. | Espacios en variables de entorno con el código guardado como hash; sesión firmada (HMAC) sin el código; eliminación del acceso sin código; todas las rutas de API exigen sesión; códigos nuevos generados con script. Ver `decisiones/0003-acceso-espacios.md`. | Resuelto en código (pendiente: configurar variables en el despliegue) |
| ↳ Residual: fuerza bruta sobre el código | Con 128 bits no es práctica, pero no hay límite de intentos. | Límite por IP cuando haya despliegue público estable. | Abierto |

## 7. Visión v2 (hipótesis, no se construyen sin ADR)

Nada de esta sección se implementa sin una decisión de Diego registrada en `docs/decisiones/`. Se pueden proponer experimentos pequeños para validarlas.

- **Modelos por proceso:** cada pack o proceso usa el modelo que mejor rinde para su tipo de documentos y preguntas, detrás de `LLMProvider`.
- **Federación entre procesos:** un proceso consulta objetos o resultados de otro (p. ej., Compras pregunta a Calidad por el certificado de un proveedor) sin mezclar sus contratos.

## 8. Abierto (a completar con Diego)

Los tres primeros puntos se obtienen con el despacho siguiendo [`playbook-evaluacion-piloto.md`](playbook-evaluacion-piloto.md).

- Criterios de aceptación por superficie (Preguntar, Explorar, Huecos, Revisar). → Playbook, bloque 1.
- Métricas del piloto, además del ≥ 95 % de citas verificadas (tiempo de respuesta, huecos detectados confirmados, horas ahorradas…). → Playbook, bloque 2.
- Qué queda explícitamente fuera de v1. → Playbook, bloque 3.
- Contrato de las interfaces `LLMProvider`, `Store` e `Ingestor`, y qué implementaciones lleva el Nivel 2. → Borrador en [`nivel2-preguntas-y-contrato.md`](nivel2-preguntas-y-contrato.md).
- Requisitos de la instalación de Nivel 2 en el despacho (hardware, red, actualización, copia de seguridad). → Preguntas del bloque 4 en el mismo documento.

### 8.1 Criterios de aceptación · motor de reglas mínimo (F1/O4)

Propuestos el 2026-11-03 a partir de la auditoría de sinergia (F1). Los cierra Diego al revisar el PR.

1. **Función pura.** `evaluate(regla, objetos, { ahora }) → { estado, evidencias, objetos }`. Mismo contrato, mismos objetos y misma fecha ⇒ mismo resultado. Sin LLM, sin red, sin reloj implícito.
2. **Estados.** `conforme`, `incumplida`, `requiere_aprobacion`, `candidato` (algún atributo necesario con confianza < 0,80 o sin validar) y `sin_evidencia` (el atributo necesario no existe o no tiene `evidenceId`). Un objeto fuera del ámbito de la regla es `no_aplica`.
3. **Rigor del §3.** Solo se usan atributos con `evidenceId`, `validated` y confianza ≥ 0,80. Un atributo que no cumple las tres cosas no decide nada: deja la regla como `candidato` o `sin_evidencia`, nunca como `conforme`.
4. **Evidencias.** El resultado lista los `evidenceId` de los atributos que decidieron el estado, para enlazar cada hueco con su fragmento.
5. **Regla declarativa.** Cada regla del pack declara su lógica como datos (ámbito por tipo de objeto, condiciones `when` y obligaciones `require` con operadores fijos). `expression` queda como texto legible; no se interpreta.
6. **Huecos sale del motor.** El estado de cada regla y los objetos afectados se calculan con `evaluate`; los datos de muestra no llevan `status` ni `affectedObjectIds`. El tiempo de evaluación que se enseña es el medido, no uno inventado.
7. **`evaluatedRuleCodes` lo calcula el motor** a partir de los objetos consultados (pregunta libre y predefinidas). El LLM ya no lo declara.
8. **Tests por pack** con al menos un caso `conforme`, uno `incumplida` y uno `requiere_aprobacion` sobre los datos de muestra o variaciones mínimas, además de `candidato` y `sin_evidencia`.
9. **El caso PC-0412 no cambia:** R-03 `requiere_aprobacion` y R-02 `conforme`.

Fuera de alcance de este primer motor: Relaciones entre objetos en las condiciones (p. ej., Pedido → Proveedor), persistencia de resultados y editor de reglas. *Las tres entran en el plan desde 2026-11-07: Fases 2 y 3 ([[ADR-0015]], [[F07]]).*
