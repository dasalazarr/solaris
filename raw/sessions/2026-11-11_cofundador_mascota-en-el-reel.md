# 2026-11-11 · cofundador · la mascota en el reel 9:16

**Pedido:** introducir a Solaris (mascota) como logo y compañero en el vídeo comercial 9:16, con los archivos de `mascota/Isotipo principal-html`.

**Hecho:** `video/src/mascota.tsx` replica la geometría del isotipo, con dos paletas. `Companero` la anima sobre todo el reel y el cierre la usa como logo. Corregido de paso un solape en la escena de la regla (la etiqueta de entorno pisaba la lógica del motor).

**Decisiones:**
- El fichero dibuja una esfera negra y la imagen pegada es dorada: se renderizan las dos y elige Diego.
- La mascota no ejecuta acciones en pantalla (principio 3).
- Se gira en la esquina para mirar a la interfaz; como logo conserva la vista del isotipo.

**Gate:** `npm run gate`, hoja de contacto de 16 fotogramas, dos renders 9:16 a −16 LUFS. Sin ver el movimiento ni oír el audio.

**Pendiente:** elegir variante; llevar la mascota a `docs/marca.md`, landing y producto es una decisión de marca aparte.
