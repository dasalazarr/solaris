# Lighthouse móvil de la landing · 2026-11-01

Lighthouse 12.6.1, `--form-factor=mobile`, Chrome headless, `serve@14` sobre `out/` (2 pasadas por rama, mismo servidor y misma máquina).

| Métrica | Base (`claude/lucid-johnson-jz3tdk`) | Después (`claude/pendientes-estado`) |
|---|---|---|
| Rendimiento | 91–92 | 95 |
| Accesibilidad | 96 | 100 |
| CLS | 0,089 | 0 |
| FCP | 2,0 s | 0,9 s |
| LCP | 2,8–2,9 s | 2,9 s |

Con `python -m http.server` (sin compresión) el rendimiento da 75 y 80, y el LCP 5,3 s: no usar ese servidor para medir.
Origen del CLS: cambio de fuente (el párrafo del hero pasaba de 3 a 4 líneas), no la animación del hero.
Contraste: 42 clases de texto subidas a `ink/60` y `white/50` (ver commit `1caa43f` de `solaris_fronted`).
