---
id: ADR-0021
type: decision
title: "El primer uso se deriva de los datos del proceso, no se escribe por plantilla"
status: validating
owner_role: product
links: ["[[ADR-0015]]", "[[ADR-0017]]", "[[ADR-0020]]", "[[F06]]"]
evidence: ["raw/sessions/2026-11-13_cofundador_primer-uso.md", "docs/maquetas/primer-minuto-producto.html"]
updated: 2026-11-13
---

# ADR-0021 · Primer uso derivado del proceso

- Estado: propuesta. Construida en la rama `feat/primer-minuto` de illariumcore, sin fusionar.
- Contexto: el recorrido de tres tarjetas ([[ADR-0015]]) se leía en vez de hacerse y no había bienvenida. Diego pide una primera experiencia de primer nivel para los casos de uso prioritarios, con el menor código posible y sobre una base que sirva para más procesos y entornos.

## Opciones

- **A. Guion por plantilla.** Cada proceso declara su bienvenida y sus pasos. Control fino, pero cada proceso nuevo trae código o contenido de recorrido que mantener.
- **B. Derivado de los datos.** Una función lee lo que el proceso ya tiene (pregunta destacada, cita visible, revisión pendiente, rol exigido) y de ahí salen la bienvenida y los tres actos.
- **C. Capa genérica de recorridos.** Motor de pasos configurable para cualquier pantalla. Más de lo que pide un piloto (principio 5).

## Decisión

**B.** `lib/first-run.ts` deriva el camino; ninguna plantilla lo declara.

- **Bienvenida:** una pantalla con el párrafo citado, el nombre del proceso, la etiqueta real del entorno y un inventario dicho como resultado.
- **Tres actos que se superan haciendo:** pulsar una cita, abrir la regla en Revisar y aprobar con el rol que exige la regla. No hay «Siguiente».
- **El rol empieza sin permiso de firma** en la demostración, para vivir el principio 3. Con persona identificada el rol lo impone la sesión y no se toca.
- **Cierre:** tras decidir, un puente a crear un proceso propio en Contrato.
- **Las pantallas no tienen lógica de recorrido:** cada bloque declara a qué acto pertenece (`data-part`) y el estilo aparta lo demás.

## Consecuencias

- Un proceso nuevo tiene primer uso sin escribir nada: un test recorre todas las plantillas y falla si alguna no ofrece el camino.
- Si un proceso no tiene pregunta con cita y revisión pendiente, la bienvenida se queda en el inventario. Es el caso de los procesos creados en la zona de pruebas.
- El texto de los actos es el mismo para todos los procesos. Si un sector necesita otro tono, habrá que abrir la opción A para ese texto, no antes.
- Un entorno sigue siendo una entrada de `SOLARIS_SPACES` con sus procesos; esta decisión no cambia cómo se despliega.
- Sin medir: no hay tráfico. Los eventos `recorrido_paso`, `recorrido_completado` y `puente_regla_propia` quedan puestos para cuando Umami esté activo en el producto.
- Pendiente: lector de pantalla real, y que los bloques apartados siguen siendo alcanzables con el teclado.
