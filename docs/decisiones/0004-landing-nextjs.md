# 0004 · La landing pasa de Vite a Next.js

- Fecha: 2026-10-31
- Estado: aceptada

## Contexto

El PRD de la landing (§8) pide Next.js con App Router y exportación estática. El prototipo estaba hecho en Vite, React Router y React 19. Migrar no cambia nada que vea el usuario y cuesta tiempo que no va al piloto.

## Opciones

1. Medir el presupuesto de rendimiento en Vite y decidir después.
2. Migrar ya.
3. Cambiar el PRD a Vite.

## Decisión

Migrar ya, a decisión de Diego: un solo stack para la landing y el producto.

## Consecuencias

- **Mismo stack** que el producto (Next 15), con metadatos por ruta, sitemap, robots y JSON-LD resueltos por el framework.
- **Salida estática** (`out/`): sirve en Vercel o en cualquier CDN, sin servidor.
- **Medido el día de la migración** (Lighthouse móvil, local):
  - Vite y Next.js dan lo mismo dentro del ruido: rendimiento 89–91, LCP ≈ 2,6 s, CLS 0,103, accesibilidad 96.
  - JS inicial de `/`: 124 KB, dentro del presupuesto de 150 KB.
  - El objetivo de 95 **no se cumple todavía**, pero no es por la migración. Hay dos causas:
    - la animación de la captura del hero mueve el layout;
    - hay textos pequeños con poca opacidad que no llegan a 4,5:1.
- **Tempo** (`tempo/`, `tempo-sdk`) deja de funcionar porque era un plugin de Vite. Se elimina del repositorio y queda en el historial.
- **TypeScript 5.9** en lugar de 7, porque Next 15 no admite el 7.
