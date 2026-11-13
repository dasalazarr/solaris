---
fecha: 2026-11-13
rol: cofundador
tema: primer uso del producto (bienvenida, actos y cierre)
---

# Primer uso del producto

## Tarea
Diego comparó el onboarding de ElevenLabs con el de Solaris, aprobó una maqueta del primer minuto y pidió implementarla para los casos de uso prioritarios, con poco código y pensando en varios entornos.

## Qué se hizo
- Comprobado que la captura interactiva del hero (solaris_fronted#19) está en producción y funciona. No diferencia: la página en reposo es idéntica.
- Auditado el primer minuto del producto en local: sin bienvenida, recorrido que se lee, sin puente tras aprobar.
- Maqueta en `docs/maquetas/primer-minuto-producto.html`.
- Rama `feat/primer-minuto` de illariumcore: `lib/first-run.ts`, `components/workspace/FirstRun.tsx` (sustituye a `GuidedTour.tsx`), marcas `data-part` en Preguntar y Revisar, y apertura del formulario de proceso nuevo desde el cierre.
- ADR-0021 propuesta y `docs/spec-experiencia.md` actualizada.
- Conexión con la landing: la puerta del producto manda a `illarium.com/solaris/solicitar` a quien no tiene código, y el pie de la landing enlaza «Entrar con tu código» al producto.
- PR: dasalazarr/illariumcore#26 y dasalazarr/solaris_fronted#20.

## Verificación
- 276 tests, lint y build del producto.
- En navegador, en local, con un código desechable: Compras de punta a punta (bienvenida, tres actos, cierre y puente) y Jurídico hasta el acto de firma. Bienvenida en móvil a 375 px.
- Compliance, IFS y EUDR: solo por test, no en navegador.

## Qué falló y qué se aprendió
- La barra de evidencia sobre un párrafo de cuatro líneas parecía un tachado: se bajó a subrayado fino.
- Con la tarjeta de pregunta apartada arriba, lo que había que hacer quedaba bajo el pliegue: cada indicación se lleva ahora a la vista al empezar su acto.
- El panel del navegador integrado no avanza las animaciones cuando está oculto: los estados se comprobaron por el DOM y no solo por captura.

## Pendiente
- Diego: revisar y fusionar illariumcore#26 y solaris_fronted#20.
- **Formulario roto desde illarium.com:** el preflight CORS de `/api/solicitud` responde 403 desde `https://www.illarium.com` y `https://illarium.com` (204 solo desde `solaris.dasalazarr.com`). Falta añadirlos a `LANDING_ORIGINS` en Vercel. Probablemente desde el 12/11, cuando la landing pasó a illarium.com; sin comprobar si se perdió alguna solicitud (la landing ofrece el correo al fallar).
- Lector de pantalla real y navegación con teclado sobre los bloques apartados.
- Los tres actos en móvil.
