# Nivel 2 · preguntas para el despacho y contrato de interfaces (borrador)

> Borrador del 2026-11-03 (product-steward). Cierra los dos últimos puntos del PRD §8: los requisitos de la instalación y el contrato `LLMProvider` / `Store` / `Ingestor`. **No se construye nada del Nivel 2 hasta tener las respuestas** (auditoría de sinergia, F2). Se usa como bloque 4 del [playbook](playbook-evaluacion-piloto.md), en la misma sesión o en una llamada técnica con quien lleve la informática del despacho. Las respuestas, anonimizadas, van al acta y de ahí al PRD §8.

## Por qué preguntamos esto antes de escribir código

La landing vende que los documentos no salen del despacho. Si el equipo, la red o la forma de actualizar no encajan, el piloto falla el primer día por algo que no es el producto. Cada pregunta decide una cosa concreta; si la respuesta no cambia nada, sobra.

## Bloque 4 · Instalación (preguntas)

### 4.1 Equipo (hardware)

| # | Pregunta | Qué decide |
|---|---|---|
| H1 | ¿Dónde correría Solaris: un servidor del despacho, un equipo dedicado nuevo o el portátil de una persona? | Si hay que proponer y presupuestar un equipo |
| H2 | ¿Qué sistema operativo usa ese equipo y quién tiene permisos de administrador? | Formato del paquete (contenedores o instalador nativo) |
| H3 | ¿Tiene tarjeta gráfica? ¿Cuál y con cuánta memoria? Si no la tiene, ¿aceptarían comprar o alquilar un equipo con una? | Tamaño del modelo local y tiempo de respuesta esperado |
| H4 | ¿Cuántos documentos y páginas tiene el lote del piloto, y cuántos se añaden al mes? | Disco, tiempo de ingesta y si hace falta OCR por lotes nocturno |
| H5 | ¿Cuántas personas lo usarían a la vez y desde dónde: el mismo equipo o otros puestos de la red interna? | Si basta un puesto o hace falta servir en la red local |
| H6 | ¿Qué tiempo de respuesta por pregunta les parece aceptable (5 s, 30 s, 2 min)? | Equilibrio entre tamaño del modelo y equipo |

### 4.2 Red

| # | Pregunta | Qué decide |
|---|---|---|
| R1 | ¿El equipo puede quedar sin salida a internet de forma permanente, o solo durante el uso? | Si el aislamiento se hace por red o por política |
| R2 | ¿Quién gestiona su red y el cortafuegos? ¿Pueden bloquear la salida de un equipo concreto y enseñarnos cómo verificarlo? | Cómo demuestra el cliente que «no sale nada» (promesa 5) |
| R3 | ¿Dónde están hoy los expedientes: carpeta de red, gestor documental o correo? ¿Solaris podría leerlos en solo lectura? | Diseño del `Ingestor` y permisos |
| R4 | ¿Hay algún requisito de su seguro, colegio profesional o cliente sobre dónde se tratan los datos? | Requisitos que no sabemos que existen |

### 4.3 Actualización

| # | Pregunta | Qué decide |
|---|---|---|
| A1 | Si el equipo no tiene internet, ¿cómo prefieren recibir las actualizaciones: soporte físico, una ventana de conexión programada o una visita? | Canal y frecuencia de actualización |
| A2 | ¿Quién aprueba instalar una versión nueva y con cuánto aviso? | Proceso de cambio y registro (`policy_hash` por versión) |
| A3 | ¿Aceptan que alguien de Illarium acceda en remoto para soporte? Si es así, ¿en qué condiciones? Si no, ¿quién del despacho haría de manos? | Modelo de soporte y coste del piloto |

### 4.4 Copias de seguridad y continuidad

| # | Pregunta | Qué decide |
|---|---|---|
| C1 | ¿Tienen ya una política de copias? ¿Solaris debe entrar en ella o necesita la suya? | Qué copia `Store` y adónde |
| C2 | ¿Cuánto trabajo pueden perder sin problema (un día, una hora) y cuánto tiempo pueden estar sin Solaris? | Frecuencia de copia y plan de recuperación |
| C3 | El registro de Revisiones y auditoría, ¿cuánto tiempo hay que conservarlo y quién puede borrarlo? | Retención y borrado (principio 3) |
| C4 | Al terminar el piloto, ¿qué esperan que pase con los datos: devolución, borrado certificado o continuidad? | Cláusula de salida del contrato del piloto |

## Contrato de interfaces (propuesta para discutir, no implementar)

Principio 5: un único motor con interfaces abstractas. El Nivel 1 ya tiene una implementación implícita de cada una (Gemini en la nube, datos en memoria del navegador, ingesta simulada); el Nivel 2 añade otra detrás del mismo contrato. Los nombres son de trabajo.

### `LLMProvider`: redacta y explica, nunca decide

```ts
interface LLMProvider {
  /** Identifica el modelo, para el registro y el entorno visible. */
  readonly id: string;          // p. ej. 'gemini-2.5-flash' o un modelo local
  readonly location: 'nube' | 'local';
  /** Devuelve JSON conforme a `schema`. Debe respetar `signal` (tiempo máximo). */
  generateJson(prompt: string, schema: JsonSchema, opts: { signal: AbortSignal }): Promise<string>;
}
```

- El servidor sigue verificando las citas (PR #5). El proveedor no cambia esa regla.
- `location` alimenta la cabecera del entorno: la interfaz no puede decir «local» si el proveedor es `nube` (principio 4).
- Ya existe un punto de inserción: `AnswerGenerator` en `product/lib/ontology-query.ts`.

### `Store`: objetos, evidencias, revisiones y registro

```ts
interface Store {
  loadPack(processId: string): Promise<SolarisPackData>;
  saveObject(obj: OntologyObject): Promise<void>;
  appendReview(review: HumanReviewItem): Promise<void>;     // idempotente por step_id + args_hash
  appendAudit(record: AuditRecord): Promise<void>;          // solo anexar
  exportAudit(processId: string, format: 'csv' | 'pdf'): Promise<Uint8Array>;
}
```

- Lo exige O8 (persistir Revisar y el registro). Sin `Store` no se demuestra el principio 3 en un piloto.
- El motor de reglas (PR #8) ya es puro: no necesita `Store`, solo recibe objetos.
- Abierto: dónde vive la verdad de una Revisión aprobada si hay varios puestos (H5).

### `Ingestor`: de fichero a Evidencia con hash

```ts
interface Ingestor {
  /** Lee un fichero en solo lectura y devuelve evidencias con hash y atributos candidatos. */
  ingest(file: { path: string; bytes: Uint8Array }): Promise<{
    evidences: EvidenceFragment[];          // fichero, página, párrafo, sha256
    candidates: ObjectAttribute[];          // confianza < 0,80 ⇒ validated: false
  }>;
}
```

- Hoy la ingesta es una simulación rotulada como tal (PR #7).
- Abierto: qué OCR y qué lector de documentos. No se elige hasta saber H2, H3 y H4.

## Qué haremos con las respuestas

1. Acta anonimizada en `raw/interviews/` y conclusiones en el PRD §8.
2. Una nota de decisión (ADR) con el equipo, el paquete y el canal de actualización. Diego la aprueba.
3. Solo entonces: tarea de dev para `LLMProvider` local, `Store` persistente e `Ingestor` real, en ese orden de riesgo.
