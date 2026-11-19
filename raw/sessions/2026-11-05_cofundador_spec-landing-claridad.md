# Sesión 2026-11-05 · cofundador · spec de claridad de la landing

## Tarea
Diego pasa una auditoría externa de la landing y un componente React para «Cómo funciona», y pide una spec.

## Qué se hizo
- Contraste de cada hallazgo con `landing` en `5e6257b`, `curl` a la portada, `product/lib/solaris-data.ts` y los ADR.
- `docs/spec-landing-claridad.md`: veredicto, requisitos, copy final y entregas. Sin cambios de código.

## Hallazgos que la auditoría no traía
- «Abrir en Revisar» del Hero es un `<span>` dentro de un bloque `aria-hidden`: parece un botón y no lo es.
- En táctil, la tarjeta de privacidad se queda en «nube»: el cambio solo ocurre con cursor o foco.
- `AV-9041` vence el 15/11/2026 y la landing dice «quedan menos de 30 días».
- «tu equipo» significa personas en `SolarisOnboarding.tsx:275`: la ambigüedad es real.

## Sin comprobar
- Las capturas `image_*`: no están en el repositorio, y el texto de la auditoría no se guarda aquí literalmente.
- Qué enseña el producto con `AV-9041` pasado el 15/11/2026.
- Las estimaciones de esfuerzo son suposiciones.

## Entrega 1
- Diego aprueba empezar con «en tu organización». Rama `copy/claridad-entrega-1` en la landing, sin commit.
- Corrección de la spec: mover la fecha de `AV-9041` a un futuro lejano habría hecho desaparecer el hueco, porque el producto evalúa con el reloj real.
- La tarjeta de privacidad se aparta de la spec: repetía «organización» en título y cuerpo.

## Fecha de muestra en el producto
- `SAMPLE_NOW` en Huecos, evaluación de preguntas predefinidas y `/api/ontology-query`. Rotulada en Huecos.
- Verificado con un espacio y un secreto de prueba generados para la sesión y eliminados después. No se tocó `.env.local`.
- Sin ejecutar con una fecha posterior al 15/11: la garantía es que esos puntos ya no leen el reloj.
- Corrección de la spec: `R-JUR-02` sí aparece en el texto del contrato de Jurídico, aunque no es una regla evaluable.
