---
name: dev-agent
description: Procedimientos del rol dev en Solaris. Convenciones de product/ (Next 15, npm) y landing/ (Next 15 estático, pnpm), tests, gates y definición de hecho. Úsalo en tareas de rol dev.
---

# Rol dev

- **Producto** (`product/`): `npm ci`; `npm run lint`, `npm test` (vitest), `npm run build`. Lógica pura sin Next en `lib/` para poder probarla. Todo endpoint nuevo exige sesión (`requireSpace`).
- **Landing** (`landing/`): `pnpm install --frozen-lockfile`; `pnpm lint`, `pnpm build` (genera `out/`). Medir Lighthouse sobre `out/` con `serve` (no con `http.server`).
- **Definición de hecho:** cumple el PRD, lint/tests/build pasan, WCAG 2.2 AA y móvil, sin secretos ni datos reales.
- **Secretos:** solo en `product/.env.local` (ignorado por git). Códigos nuevos con `node scripts/nuevo-codigo.mjs`.
- Una rama por tarea; commits que digan qué y por qué. Primero el submódulo, luego el puntero en la raíz.
- Si toca acceso, sesión, prompts o datos, pide revisión del rol security antes de marcar Accepted.
