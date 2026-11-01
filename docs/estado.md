# Estado del proyecto · 2026-11-01

Punto de partida para la próxima sesión. La base está en `claude/lucid-johnson-jz3tdk` y los pendientes técnicos cerrados el 01/11 en `claude/pendientes-estado`, en los tres repositorios. Nada en `main`, nada desplegado y `claude/pendientes-estado` sin push.

## Retomar

```bash
git clone --recurse-submodules -b claude/pendientes-estado https://github.com/dasalazarr/solaris.git
cd solaris && git submodule foreach git checkout claude/pendientes-estado
```

## Hecho

| Qué | Dónde | Cómo se verificó |
|---|---|---|
| Espacio de trabajo: repo raíz con `product/` y `landing/` como submódulos | `README.md`, ADR 0001 | Clonado y push en los tres repos |
| Una sola marca: sol de Solaris, «un producto de Illarium», tokens comunes, favicon | `docs/marca.md`, ADR 0002 | Capturas a 1440/1100/390 px, contraste AA de todos los pares de tokens |
| Cabecera del producto responsive; indicador de entorno siempre visible | `product/components/SolarisWorkspace.tsx` | Capturas, sin scroll horizontal |
| PRD de landing y síntesis del PRD de producto | `docs/prd-landing.md`, `docs/prd-producto.md` | Releídos contra el texto de Diego |
| Seguridad de la demo: códigos fuera del repo (hash en entorno), sesión firmada, sin atajo Alt+D ni `PUT`, API con sesión obligatoria | `product/lib/space-auth.ts`, ADR 0003 | 16 tests (vitest), lint, build, pruebas en navegador y `curl` |
| Landing migrada a Next.js con exportación estática, 404, sitemap, robots, JSON-LD | `landing/src/app/`, ADR 0004 | Capturas idénticas píxel a píxel a Vite; teclado y sin red; Lighthouse igual que antes |
| Playbook para evaluar el piloto | `docs/playbook-evaluacion-piloto.md` | — |
| Límite de 10 intentos de entrada por IP cada 15 min en `/api/space` (429 + `Retry-After`) | `product/lib/rate-limit.ts` | 22 tests; `curl`: el intento 11 da 429 |
| Indicador de entorno y firma de Illarium también en el recorrido inicial | `product/components/SolarisOnboarding.tsx` | Navegador a 375 y 1280 px, sin scroll horizontal |
| Lockfile del producto; fuera 5 dependencias sin uso (1115 → 573 paquetes), `.eslintrc.json` duplicado y `metadata.json` antiguo | `product/package-lock.json` | `npm ci`, lint, tests, build |
| Landing: contraste AA en todos los textos, fuentes con `next/font` y captura del hero sin saltos; fuera `icons.svg` | `landing/src/app/fonts.ts` | Lighthouse móvil con `serve`: rendimiento 91 → 95, accesibilidad 96 → 100, CLS 0,089 → 0 |

## Acciones de Diego

1. **Configurar la demo antes de desplegarla.** Sin esto, todos los códigos se rechazan.
   - `SOLARIS_SESSION_SECRET`: `cd product && node scripts/nuevo-codigo.mjs --secreto`
   - `SOLARIS_SPACES`: una entrada por espacio con `node scripts/nuevo-codigo.mjs --id … --packs … --dias …`
2. **Evaluar el piloto con el despacho** siguiendo el playbook, y traer las conclusiones anonimizadas para el PRD §8.
3. **Revisión jurídica de la FAQ.** Una respuesta lleva «[Respuesta pendiente de revisión jurídica.]», y ese texto ahora también aparece en el JSON-LD.
4. **Dominio y logotipo definitivo**, tras la búsqueda de marca. Después, configurar `NEXT_PUBLIC_SITE_URL` en Vercel.
5. **Revisar y publicar** los borradores de `docs/diario/`.

## Pendiente técnico (por prioridad)

1. **Coherencia entre landing y producto.** La maqueta de la landing muestra un menú lateral con «Documentos»; el producto tiene pestañas con «Explorar». Hay que decidir cuál manda y alinearlo cuando haya capturas reales (PRD landing §10).
2. **Límite de intentos global.** El contador vive en memoria de cada instancia; en serverless cada instancia cuenta por separado. Basta para la demo; si se ve abuso, se cambia el almacén (p. ej. Vercel KV) tras la misma interfaz.
3. **LCP de la landing (2,9 s en móvil simulado).** El rendimiento ya llega a 95; bajar el LCP pasa por revisar la animación de palabras del titular.
4. **Avisos de oxlint en la landing** (`Footer.tsx`, `Closing.tsx`, `lib/hooks.ts`): no bloquean.
5. **Completar el PRD §8** con lo que salga del playbook: interfaces `LLMProvider`/`Store`/`Ingestor` y requisitos de la instalación de Nivel 2.
