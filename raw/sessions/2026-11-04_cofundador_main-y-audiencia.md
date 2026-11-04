# Sesión 2026-11-04 · cofundador · lo fusionado no llegó a main, correcciones y audiencia

## Tarea
Diego fusionó los PR, pidió las correcciones leves (repetición del aviso del piloto incluida) y fijó audiencia y tono: dueños de consultoras e implantadores de CRM, procesos generales, sin vender de más ni subestimarse.

## Qué se descubrió
- GitHub marca los 8 PR como MERGED, pero #10, #11 y #12 de cada repositorio se fusionaron en su rama base. `main` solo tiene el #9. Producción: «4 docs», sin barra en el hero. Lo detectó comprobar producción, no el estado de los PR.
- Causa: yo apilé los PR y dejé a Diego el paso manual de cambiar la base. Es una trampa de diseño mía, no un error suyo.

## Qué se hizo
- PR únicos `fix/publicar-alineamiento` en ambos repos, desde la punta completa, con las correcciones.
- [[ADR-0011]]; ADR-0010 con «lee» y «OCR» y el tono; diario sin la afirmación «desde el principio», que no se había comprobado en git.

## Evidencia
`curl`: `noindex` en portada, Aviso legal, Privacidad y Cookies. Producto 109 tests, lint y build. Landing lint y build; textos en `out/index.html`.

## Sin probar
El commit de textos en navegador; revisión de security de ese commit; envío real del formulario.
