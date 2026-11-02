# Sesión 2026-11-02 · dev + security · preparar el despliegue de la demo

## Tarea
ROADMAP P0.3: dejar listos la demo y la landing para Vercel. Decisiones de Diego: Vercel para los dos, `vercel.app` con `noindex`, formulario a una ruta del producto con Resend, Umami Cloud.

## Qué se hizo
- Producto (`illariumcore`, rama `feat/solicitud-demo`, `9a90349`): `lib/solicitud.ts` y `app/api/solicitud/route.ts`, 9 tests nuevos (31 en total).
- Landing (`solaris_fronted`, rama `feat/formulario-real-y-umami`, `43137e6`): envío real, plan B por correo, agenda opcional, Umami opcional, `NEXT_PUBLIC_NOINDEX`, FAQ filtrada.
- Guía en `docs/despliegue.md`. Riesgo nuevo [[R04]].

## Qué falló o se descubrió
- El formulario de la landing simulaba el envío con un `setTimeout` y mostraba «Recibido»: desplegarlo así habría perdido solicitudes y mentido al visitante.
- La FAQ publicaba «[Respuesta pendiente de revisión jurídica.]».
- Política de privacidad, aviso legal y cookies enlazan a `#`. Es un bloqueo para activar el formulario.
- `{'' && <script/>}` dentro de `<head>` deja un nodo de texto y rompe la hidratación; se movió Umami a `next/script` en el `body`. El aviso de hidratación que queda en `next dev` viene de la fuente del overlay de Next, no de la landing (el HTML del servidor es igual con y sin el cambio).

## Evidencia
- curl: origen ajeno → 403; preflight → 204 con `Access-Control-Allow-Origin`; campos vacíos → 400 con la lista; campo trampa → `{"ok":true}`; sin Resend → 503.
- Navegador (landing 3001 → producto 3000): OPTIONS 204, POST 503 y mensaje «No hemos podido enviar su solicitud».
- Build con `NEXT_PUBLIC_NOINDEX=true`: `<meta name="robots" content="noindex, nofollow">` y `robots.txt` sin sitemap. Con id de Umami, el script aparece; sin id, 0 referencias.
- No probado: el envío real por Resend (no hay clave) ni Lighthouse sobre el despliegue.
