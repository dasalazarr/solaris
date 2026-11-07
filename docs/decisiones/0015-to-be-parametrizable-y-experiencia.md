---
id: ADR-0015
type: decision
title: "Construimos un To Be parametrizable, con la experiencia del vídeo como referencia"
status: accepted
owner_role: product
links: ["[[ADR-0003]]", "[[ADR-0010]]", "[[ADR-0011]]", "[[ADR-0014]]", "[[F07]]", "[[H03]]", "[[O01]]", "[[O06]]"]
evidence: ["raw/research/2026-11-07_estudio-mercado-sintesis.md", "raw/sessions/2026-11-07_cofundador_fase-0-plan-evolutivo.md"]
updated: 2026-11-07
---

# ADR-0015 · To Be parametrizable y experiencia según el vídeo

- Estado: aceptada (2026-11-07, Diego aprobó el plan e inició la Fase 0). Las decisiones de la lista final siguen abiertas.
- Contexto: el producto demuestra el comportamiento con datos escritos a mano. No lee documentos reales, no conserva nada al recargar y cada proceso nuevo exige programar. El vídeo enseña además una experiencia más clara que la del producto. Un estudio de mercado propone entrar por un sector regulado a través de una consultora ([síntesis](../../raw/research/2026-11-07_estudio-mercado-sintesis.md)).

## Opciones

1. **Pulir solo la demo.** Barato, pero nadie podría probarla con sus documentos ni crear un proceso.
2. **Profundizar en verticales.** Sigue la recomendación del estudio, pero apuesta por un sector antes de validarlo y repite trabajo por sector.
3. **Un recorrido real y parametrizable, para cualquier proceso.** Más caro, pero sirve para cualquier sector y hace posible vender el trabajo de configuración.

## Decisión

Opción 3, en las fases de [`plan-evolutivo.md`](../plan-evolutivo.md), con estas reglas:

- **Parametrizar antes que verticalizar.** Un proceso es una definición en datos. Compras, Jurídico, IFS y EUDR pasan a ser plantillas.
- **La experiencia sigue [`spec-experiencia.md`](../spec-experiencia.md).** El vídeo es referencia de jerarquía, lenguaje y secuencias, no excluyente.
- **Se adelanta `Store` e `Ingestor`** respecto a lo previsto en `nivel2-preguntas-y-contrato.md`. El modelo local y el instalador siguen esperando respuestas de un cliente.
- **El canal no cambia aún.** La consultora está sin confirmar y el primer piloto se decide en la puerta tras la Fase 3.
- **El motor sigue siendo puro.** Se amplía con operadores fijos, sin expresiones libres ni LLM ([principio 2](../prd-producto.md)).
- **El vídeo no se publica como enseñanza del producto** hasta que este tenga la matriz, la barra de confianza y el cierre visible.

## Consecuencias

- Cambia el alcance congelado de `plan/ROADMAP.md` y del PRD §4 y §8.1: entran el editor de reglas y las relaciones en las condiciones.
- Se desplazan el pack `equipo` ([[O05]]), el LCP y los avisos de la landing, la publicación de los vídeos ya renderizados y la Entrega 2 de la spec de claridad.
- Son unas 8–9 semanas de foco (estimación), sin un cliente validado. Diego decide seguir construyendo: las entrevistas van en paralelo y corrigen el rumbo, pero no bloquean ninguna fase.
- Ningún documento real entra hasta pasar la revisión de `security` y tener acuerdo de confidencialidad y encargo de tratamiento revisados.
- **`solaris` es un repositorio público.** El estudio original, el nombre del posible socio y los precios no publicados no se versionan.

## Abierto para Diego

1. Pregunta libre en la demo: clave con tope de gasto (recomendado) o quitar el campo.
2. Proveedor de contenedor en Europa y dominio del producto.
3. Modelo para documentos de prueba y su tratamiento de datos.
4. Primer piloto: despacho o industria, tras la Fase 3 ([[ADR-0011]]).
5. Nombres de proveedor de muestra (H7 en `plan/STATUS.md`).
