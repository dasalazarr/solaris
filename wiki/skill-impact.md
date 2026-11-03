# Solaris — Skill & feature impact tracker

> Registro de auditoría de **cada propuesta de cambio** atómica (a una skill, una feature o el código) y de su resultado en el gate. Equivale a `skill-impact.md` en WikiSkill.
> **Solo se anexa.** Las propuestas rechazadas también se registran: la wiki persiste y evita repetir errores.

| # | Fecha | Rol | Objetivo | Cambio | Gate | Resultado del gate | Decisión |
|---|---|---|---|---|---|---|---|
| 1 | 2026-11-01 | security | F05 / R02 límite de intentos | `product/lib/rate-limit.ts` + 429 en `/api/space` (commit `8ec2c36` de illariumcore) | vitest + `curl` | 22 tests; intento 11 → 429 con `Retry-After` | **Accepted** |
| 2 | 2026-11-01 | dev | P03 indicador de entorno en onboarding | `SolarisOnboarding.tsx` (commit `0a27591`) | Navegador 375 y 1280 px | Visible, sin scroll horizontal | **Accepted** |
| 3 | 2026-11-01 | dev | L01 lockfile y limpieza | `package-lock.json`, −5 dependencias, `.eslintrc.json`, `metadata.json` (commit `79cd6aa`) | `npm ci` + lint + tests + build | OK; 1115 → 573 paquetes | **Accepted** |
| 4 | 2026-11-01 | dev | F06 contraste AA | 42 clases subidas a `ink/60` y `white/50` (commit `1caa43f` de solaris_fronted) | Lighthouse accesibilidad | 96 → 100 | **Accepted** |
| 5 | 2026-11-01 | dev | F06 CLS | `next/font/local` + tamaño reservado en el hero (commit `e998464`) | Lighthouse con `serve` | CLS 0,089 → 0; rendimiento 91 → 95 | **Accepted** |
| 6 | 2026-11-01 | wiki | Repo (WikiSkill) | Capas raw/wiki/skills/plan, `wiki_lint.py`, ADR-0005 y 0006 | `wiki_lint.py` | OK | **Accepted** |
| 7 | 2026-11-02 | product | ADR-0007 equipo de agentes | `landing-steward` y `product-steward` (agentes y skills), `product` como alias, contratos en `plan/contratos/`, reglas REG-* en `wiki_lint.py`, paso nuevo en `session-protocol` | `test_wiki_lint.py` + `wiki_lint.py` | 9 tests OK; lint OK | **Accepted** |
| 8 | 2026-11-02 | dev | P0.3 despliegue · formulario | `/api/solicitud` con Resend en el producto (`9a90349`); envío real, Umami, `noindex` y FAQ filtrada en la landing (`43137e6`) | vitest + lint + build ×2 + curl + navegador | 31 tests; 403/204/400/503 esperados; error honesto en la UI | **Accepted** |
| 9 | 2026-11-02 | dev | P0.3 despliegue · legal y correo | Landing en subdominio (ADR-0008), Resend con `avisos@`, política + Aviso legal + Cookies (solaris_fronted#4), Umami | curl + cabeceras de correo + navegador a 375 px | SPF/DKIM/DMARC `pass`; envío real recibido por Diego; páginas sin borrador | **Accepted** |
| 10 | 2026-11-03 | landing-steward | F06 copy · ADR-0009 | ADR-0009 tres audiencias; PRD §1/§3; O1 en solaris_fronted#5 (`ae10ec4`) | lint + build + `out/` en navegador a 375 px + curl | 0 afirmaciones C1/C2/C3/C9 en la página; sin scroll horizontal | **Accepted** |
| 11 | 2026-11-03 | dev + security | F01/F03 producto · principios 1, 2 y 4 | Citas verificadas (illariumcore#5), perfil en solicitud (#6), entorno honesto (#7), motor de reglas (#8) | vitest + lint + build + navegador + revisión security | 48/35/31/70 tests; security #5 APTO con condiciones (aplicadas), #6 APTO | **Accepted** (fusionados el 03/11) |
