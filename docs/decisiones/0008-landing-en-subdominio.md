# ADR-0008 · La landing vive en un subdominio

- Estado: aceptada (2026-11-02)
- Contexto: la landing se publica bajo el dominio personal `dasalazarr.com`, cuyo DNS está en Cloudflare y cuyo correo (MX, SPF, DMARC) no debe tocarse.

## Opciones

1. `solaris.dasalazarr.com` (subdominio).
2. `dasalazarr.com/solaris` (camino), con `basePath` en la landing y reescrituras en el sitio personal.

## Decisión

Subdominio. Un CNAME en Cloudflare (solo DNS, sin proxy) hacia Vercel; sin cambios de código en la landing; despliegues independientes del sitio personal; `noindex` y analítica separados.

## Consecuencias

- La ventaja de SEO del camino es teórica mientras no haya tráfico. Si más adelante interesa consolidar, se hace con una redirección 301.
- La demo (producto) va en un host distinto, para aislar la cookie de sesión.
- Variables que dependen del dominio: `NEXT_PUBLIC_SITE_URL` (landing, se aplica al construir) y `LANDING_ORIGINS` (producto). Sin la primera, el canonical y el sitemap apuntan a `localhost`.
- Mientras la política de privacidad no esté revisada, `NEXT_PUBLIC_NOINDEX=true`.
