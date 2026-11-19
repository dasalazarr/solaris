# Sesión 2026-11-05 · cofundador · tuteo y «proceso»

## Tarea
Diego pregunta si el «vídeo» de la demo sigue igual, y pide pasar «Sus» a «Tus» y buscar alternativas a «Pack».

## Qué se hizo
- No hay vídeo: es una animación en código (`HeroCapture.tsx`). Cambió en 401bcdd, pero los primeros 6 s son iguales.
- Comprobadas en producción las fusiones de illariumcore#13 y solaris_fronted#13.
- Tuteo en landing y producto. El «su» de tercera persona se mantiene. Legales sin tocar.
- «Pack» pasa a «proceso» de cara al lector. En el producto salen también «(P0)» y «Pregunta estrella».
- [[ADR-0012]], PRD, fundacional, guion y punteros de submódulos a `main`.

## Evidencia
Producto: 109 tests, lint y build. Landing: lint con los 3 avisos previos y build. `out/index.html` sin «pack», «usted» ni «Sus». Navegador local: sin desbordamiento a 375 px y sin errores de consola.

## Sin probar
Producto en navegador. Formulario de la landing con sus errores en pantalla. Revisión de security.
