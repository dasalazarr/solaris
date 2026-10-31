# Estado del proyecto · 2026-10-31

Punto de partida para la próxima sesión. Todo está en la rama `claude/lucid-johnson-jz3tdk` de los tres repositorios; nada en `main` y nada desplegado.

## Retomar

```bash
git clone --recurse-submodules -b claude/lucid-johnson-jz3tdk https://github.com/dasalazarr/solaris.git
cd solaris && git submodule foreach git checkout claude/lucid-johnson-jz3tdk
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

## Acciones de Diego

1. **Configurar la demo antes de desplegarla.** Sin esto, todos los códigos se rechazan.
   - `SOLARIS_SESSION_SECRET`: `cd product && node scripts/nuevo-codigo.mjs --secreto`
   - `SOLARIS_SPACES`: una entrada por espacio con `node scripts/nuevo-codigo.mjs --id … --packs … --dias …`
2. **Evaluar el piloto con el despacho** siguiendo el playbook, y traer las conclusiones anonimizadas para el PRD §8.
3. **Revisión jurídica de la FAQ.** Una respuesta lleva «[Respuesta pendiente de revisión jurídica.]», y ese texto ahora también aparece en el JSON-LD.
4. **Dominio y logotipo definitivo**, tras la búsqueda de marca. Después, configurar `NEXT_PUBLIC_SITE_URL` en Vercel.
5. **Revisar y publicar** los borradores de `docs/diario/`.

## Pendiente técnico (por prioridad)

1. **Rendimiento y contraste de la landing.** Lighthouse móvil da rendimiento 89–91 y accesibilidad 96; el objetivo es ≥ 95.
   - CLS 0,10 (el objetivo es menos de 0,05), causado por la animación de la captura del hero.
   - Textos pequeños con `white/40` e `ink/50` por debajo de 4,5:1.
   - Son unas pocas horas.
2. **Coherencia entre landing y producto.** La maqueta de la landing muestra un menú lateral con «Documentos»; el producto tiene pestañas con «Explorar». Hay que alinearlo cuando haya capturas reales (PRD landing §10).
3. **Lockfile del producto.** No hay `package-lock.json`, así que `npm ci` falla y las instalaciones no son reproducibles.
4. **Límite de intentos por IP** en `/api/space`. Es el riesgo residual del PRD §6.
5. **Limpieza:**
   - en el producto, `metadata.json` (describe el antiguo «Illarium Core») y el `.eslintrc.json` duplicado;
   - en la landing, `public/icons.svg` (resto de la plantilla).
6. **Completar el PRD §8** con lo que salga del playbook: interfaces `LLMProvider`/`Store`/`Ingestor` y requisitos de la instalación de Nivel 2.
