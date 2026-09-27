# Solaris · frontend (M5-T2)

Next.js 16 (App Router, TypeScript estricto), UI en castellano, datos 100 % sintéticos (ADR-0004).

## Arranque

```bash
# backend (1 worker: las sesiones viven en memoria). En este equipo el :8000 está ocupado → :8011
cd app/backend && uv run uvicorn solaris.api:app --workers 1 --host 127.0.0.1 --port 8011
# frontend (desarrollo)
cd app/frontend && pnpm install && SOLARIS_BACKEND_URL=http://127.0.0.1:8011 pnpm dev
# gate
cd app/frontend && pnpm lint && pnpm typecheck && pnpm test && pnpm build
```

`.claude/launch.json` tiene las configuraciones `backend` y `frontend` con esos puertos.

Variables (solo servidor, nunca `NEXT_PUBLIC_`):

| Variable | Por defecto | Uso |
|---|---|---|
| `SOLARIS_BACKEND_URL` | `http://127.0.0.1:8000` | URL del backend FastAPI |
| `SOLARIS_COOKIE_SECURE` | `true` en producción | `false` solo si se sirve por http fuera de localhost |

**Dos sesiones a la vez (guion, paso 9):** las cookies son por host, así que `inaki.calidad` en
`http://localhost:3000` y `jon.it` en `http://127.0.0.1:3000` (o una ventana privada).

## Arquitectura

```
navegador ──(cookie httpOnly, SameSite=Strict)──▶ Next (Route Handlers = BFF) ──(Bearer)──▶ FastAPI
```

- `src/app/api/session/route.ts`: login (`POST`), usuario actual (`GET`) y logout (`DELETE`).
  El JWT del backend se guarda en una cookie httpOnly; nunca llega al JavaScript del navegador.
- `src/app/api/backend/[...path]/route.ts`: proxy hacia el backend con allowlist de rutas
  (`8d`, `approvals`, `audit`, `ask`, `complaints`), solo cabeceras de contenido y
  comprobación same-origin + CSRF (`lib/bff.ts`).
- `src/proxy.ts`: CSP con nonce por petición y redirección al login sin cookie (solo UX).
- `src/app/(app)/layout.tsx`: cabecera con usuario y rol (de `GET /auth/me`), navegación por rol,
  aviso de IA (art. 50) y banda de datos sintéticos. `IdleGuard` cierra la sesión por inactividad.
- `src/lib/roles.ts`: qué pantallas ve cada rol. Solo UX; lo autoritativo es el backend y
  `tests/roles.test.ts` comprueba que coincide con `test_access_matrix.py::MATRIX`.
- `src/lib/api-client.ts`: cliente tipado con manejo de 401 (login), 403, 409 y errores genéricos.

Pantallas: `/inbox` (L01), `/casos` (L02), `/aprobaciones` (L03), `/auditoria` (L07); se
completan en M5-T3…T5.
