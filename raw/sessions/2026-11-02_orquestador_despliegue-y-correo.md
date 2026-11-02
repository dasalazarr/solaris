# Sesión 2026-11-02 · orquestador + dev + security · despliegue de la landing y del correo

## Tarea
Poner en línea la landing y el formulario (ROADMAP P0.3) y cerrar lo legal que lo bloqueaba. Decisiones de Diego: dos proyectos de Vercel, uno por repositorio desplegable; landing en subdominio; responsable del tratamiento como autónomo con nombre comercial Illarium; Resend para el aviso; Umami Cloud.

## Qué se hizo
- Landing publicada en `solaris.dasalazarr.com` (proyecto `solaris-fronted`); producto en `illariumcore.vercel.app`. Dominio en [[ADR-0008]].
- Política de privacidad (RGPD/LOPDGDD) escrita y aprobada por Diego; páginas Aviso legal y Cookies (solaris_fronted#4) con layout legal compartido. Cada página tiene su variable de «revisado».
- Correo: Resend con `dasalazarr.com` verificado, remitente `Solaris web <avisos@dasalazarr.com>`, destino `solaris@dasalazarr.com` (Cloudflare Email Routing → buzón central).
- Umami activo; `noindex` mantenido.
- Contactos de la landing: se quitó `hola@illarium.com` escrito a mano; se usa `CONTACT_EMAIL` (por defecto `solaris@dasalazarr.com`).

## Qué falló o se descubrió
- La landing publicada salió con `canonical` y sitemap apuntando a `localhost` y sin `noindex`: faltaban `NEXT_PUBLIC_SITE_URL` y `NEXT_PUBLIC_NOINDEX` en Vercel (las `NEXT_PUBLIC_*` se aplican al construir).
- La API devolvía 403 `origen` hasta cargar `LANDING_ORIGINS` y 503 `no_configurado` hasta tener las tres variables de Resend; `SOLICITUD_FROM` no existía.
- Dos avisos de prueba cayeron en spam de Gmail con SPF, DKIM y DMARC en `pass`. No era autenticación ni remitente igual al destinatario; se resuelve con «No es spam» y un filtro. Mi hipótesis inicial (reenvío de Cloudflare o remitente repetido) no se confirmó.
- Yo afirmé que la política ya no era borrador por una búsqueda que distinguía mayúsculas; era falso. Se corrigió al leer la página. Verificar leyendo el texto, no contando coincidencias.
- La política describía analítica que no estaba activa (faltaba `NEXT_PUBLIC_UMAMI_WEBSITE_ID`).
- Hay tres repositorios y PR apilados: confunde. Regla nueva en `wiki/patterns/PAT-005`.

## Evidencia
- curl: origen ajeno → 403; origen de la landing → 204 con CORS; `{}` → 400; solicitud válida → `{"ok":true}`.
- Cabeceras del correo recibido: `spf=pass`, `dkim=pass` (`dasalazarr.com` s=resend y amazonses), `dmarc=pass`, remitente `Solaris web <avisos@dasalazarr.com>`, `Reply-To` del solicitante.
- Prueba final con correo real de Diego: el aviso llegó (confirmado por Diego).
- `/aviso-legal` y `/cookies` 200, sin borrador tras `NEXT_PUBLIC_LEGAL_PAGES_REVIEWED=true`; `/privacidad` sin borrador tras `NEXT_PUBLIC_PRIVACY_REVIEWED=true`.
- Landing: lint + build pasan; páginas legales vistas a 375 px sin desbordamiento. Sin probar: Lighthouse sobre la URL publicada; Umami en tiempo real (lo mira Diego).
