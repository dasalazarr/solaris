---
fecha: 2026-11-07
rol: cofundador
tema: Fase 2, núcleo persistente
---

# Fase 2: núcleo persistente

## Tarea
Que lo decidido se conserve y que el servidor imponga el rol, sin cambiar lo que hace Vercel hoy.

## Qué se hizo
- illariumcore#21: `lib/store/`, `lib/review-service.ts`, `app/api/reviews`, `app/api/workspace`, `people` en `SOLARIS_SPACES`, `Dockerfile`.
- [[ADR-0016]] con las alternativas.

## Qué falló
La revisión de security de la primera versión dio NO APTO para el contenedor:
- Quien no firmaba podía sustituir con «pedir cambios» el texto que aprobaba otro. Comprobado contra el servidor. Corregido.
- Cuerpos sin límite, crecimiento de disco y `x-forwarded-for` falsificable. Corregidos.
- Nombres en filas que no se reescriben. Ahora se guarda el id.
- Textos que afirmaban de más: el diálogo de entorno y «no se pueden borrar». Corregidos.
- Ids o códigos duplicados que saltaban revocaciones. Ahora no se abre ningún espacio.
- Un código de prueba en mayúsculas no entraba: los códigos se normalizan a minúsculas antes del hash.

## Evidencia
- 166 tests, lint, build y `npm run gate`.
- Versión de producción con `node server.js` en local, con códigos desechables ya borrados: rol equivocado 403, aprobación que sobrevive al reinicio, sustitución sin efecto, 200 MB cortados (memoria de 83 a 147 MB, frente a 762 MB antes) y 429 aunque rote `x-forwarded-for`.

## Sin comprobar
- Imagen Docker: el servicio de Docker no estaba en marcha.
- Repaso de security de los arreglos, lector de pantalla y móvil en modo guardado.
- Varias instancias sobre un fichero: el diseño asume una por espacio.
