# Despliegue de la demo (Nivel 1) y la landing

Estado: preparado, **sin desplegar**. Lo despliega Diego o se hace con su confirmación (CLAUDE.md). Decisiones del 02/11: Vercel para los dos, subdominio `vercel.app` con `noindex` hasta tener dominio, formulario a una ruta del producto con Resend y analítica con Umami Cloud.

## Bloqueos antes de activar el formulario
1. **Política de privacidad, aviso legal y cookies.** Los enlaces del pie y el de la casilla de privacidad apuntan a `#`. Con el envío real se recogen datos personales: hace falta el texto (responsable, finalidad, base legal, plazo, encargados **Vercel** y **Resend**, derechos). Sin él, se despliega con `NEXT_PUBLIC_SOLICITUD_URL` vacío y el formulario no envía (muestra el error y, si existe, el correo de contacto).
2. **Remitente en Resend.** Para `SOLICITUD_FROM` hace falta un dominio verificado. Hasta tener dominio propio, Resend solo permite enviar a la dirección de la cuenta con su remitente de pruebas: sirve para avisar a Illarium.

## 1. Producto (demo) → proyecto Vercel `solaris-demo`
- Repositorio `dasalazarr/illariumcore`, framework Next.js, rama `main`.
- Variables (Production):

| Variable | Valor | Cómo se obtiene |
|---|---|---|
| `SOLARIS_SESSION_SECRET` | ≥ 32 caracteres | `node scripts/nuevo-codigo.mjs --secreto` |
| `SOLARIS_SPACES` | JSON con hashes | `node scripts/nuevo-codigo.mjs --id demo-compras --packs compras --dias 60 --label "Demo compras"`. **Códigos nuevos**: los que estuvieron en el historial están quemados ([[R01]]) |
| `GEMINI_API_KEY` | opcional | Sin ella, la demo responde con la respuesta de muestra del pack. Con ella, las preguntas (sobre datos de muestra) van a Google |
| `LANDING_ORIGINS` | `https://<landing>.vercel.app` | URL de la landing, sin barra final |
| `RESEND_API_KEY`, `SOLICITUD_TO`, `SOLICITUD_FROM` | — | Cuenta de Resend. Sin las tres, `/api/solicitud` responde 503 |

- El producto ya lleva `noindex` en sus metadatos. El acceso es por código, no por `noindex`.

## 2. Landing → proyecto Vercel `solaris`
- Repositorio `dasalazarr/solaris_fronted`, framework Next.js (exportación estática a `out/`), gestor `pnpm`.
- Variables (Production):

| Variable | Valor |
|---|---|
| `NEXT_PUBLIC_SITE_URL` | `https://<landing>.vercel.app` |
| `NEXT_PUBLIC_NOINDEX` | `true` hasta tener dominio definitivo |
| `NEXT_PUBLIC_SOLICITUD_URL` | `https://<demo>.vercel.app/api/solicitud` (vacía mientras falte la política de privacidad) |
| `NEXT_PUBLIC_CONTACT_EMAIL` | buzón de Illarium para el plan B del formulario |
| `NEXT_PUBLIC_AGENDA_URL` | enlace de agenda (opcional; sin él no hay botón «Reservar llamada») |
| `NEXT_PUBLIC_UMAMI_WEBSITE_ID` | id del sitio en Umami Cloud (sin él no se carga ningún script) |

Las `NEXT_PUBLIC_*` se fijan en el build: si se cambian, hay que redesplegar.

## 3. Comprobaciones tras desplegar
- Landing: `view-source` muestra `<meta name="robots" content="noindex, nofollow">` y `robots.txt` no anuncia sitemap.
- Formulario: una solicitud de prueba con datos ficticios llega al buzón de `SOLICITUD_TO`; desde otro origen, `curl -X POST …/api/solicitud -H 'Origin: https://otro.example'` devuelve 403.
- Demo: un código inválido da la respuesta neutra; el 11.º intento en 15 min da 429; el espacio muestra «Nivel 1 · datos de muestra».
- Umami registra la visita y los eventos `cta_solicitar_demo`, `form_abierto` y `form_enviado`.
- Lighthouse móvil sobre la URL desplegada (PRD landing §8) → `raw/eval-runs/`.

## Riesgos conocidos
- El límite de intentos es por instancia de Vercel, no global ([[R02]], [[R04]]).
- `Origin` lo puede falsificar un cliente que no sea navegador: CORS no autentica. El freno al spam del formulario es el campo trampa más el límite por IP ([[R04]]).
