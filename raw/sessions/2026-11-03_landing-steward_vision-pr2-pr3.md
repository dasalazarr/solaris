---
type: session
rol: landing-steward
fecha: 2026-11-03
tarea: "PR 2 visión y audiencias, PR 3 demo con datos del producto y fundacional §6, tras el visto bueno de Diego"
---

# 2026-11-03 · landing-steward · PR 2 y PR 3

## Tarea
Visto bueno de Diego (03/11) con cambios:
- Fusionar bucle y ontología, con selector Compras/Jurídico.
- Sin botón para inversores; aliados con botón propio.
- Perfil obligatorio.
- «Hoy · Siguiente · Visión» a partir de fundacional §6 actualizado.
- PR 3: demo con los datos del producto.
- No fusionar: `main` de la landing se despliega solo.

## Qué se hizo
- dasalazarr/solaris#10: fundacional §6 con #5, #7 y #8 fusionados, más cómo se lee la tabla en la landing.
- dasalazarr/solaris_fronted#6 (`feat/vision-y-audiencias`, `11fe64f`):
  - «Cómo funciona · La ontología de procesos»: primitiva bajo cada paso y selector Compras/Jurídico con pestañas WAI-ARIA y `aria-live`.
  - Sección «Hoy · Siguiente · Visión».
  - Botón «Implantar Solaris con Illarium» (perfil = aliado).
  - Campo Perfil: aliado e inversor envían `proceso: Otro`. `perfil` en Umami y en la política de privacidad.
- dasalazarr/solaris_fronted#7 (`feat/demo-datos-producto`, `27d73af`):
  - Preguntar, Huecos, Revisar, hero y Bento con PC-0412 (R-03), PC-0419 (R-01 y R-02 sin evidencia) y PROV-024.
  - Pregunta «no consta» (O5).
  - Registro inicial tomado de la auditoría del producto.

## Evidencia
- `pnpm lint` sin errores (3 avisos previos) y `pnpm build` OK en ambas ramas. JS inicial de `/`: 124 → 127 kB.
- `out/` en local:
  - selector con flechas y anuncio;
  - formulario con perfil precargado, «Proceso» oculto y foco en el error;
  - demo completa sin red;
  - 375 px sin scroll horizontal.
- Capturas de escritorio con movimiento reducido.
- Lighthouse 11.7 móvil, 3 ejecuciones, `main` frente a `main` + #6 + #7: rendimiento 79/79, accesibilidad 100/100, SEO 92/92 (`noindex`), LCP mediana 5,52 s / 5,52 s, CLS 0 / 0. Sin regresión. Servidor local sin compresión ni CDN: valores absolutos no comparables con producción.
- #6 y #7 se fusionan sin conflictos entre sí (comprobado en una rama temporal local).

## Qué falló / aprendido
- Las previews de Vercel exigen inicio de sesión (Deployment Protection): no se puede pasar Lighthouse en la preview sin un bypass, que es decisión de Diego.
- PROV-018 declara «Homologación A» citando EV-COMP-02, que no habla de homologación. La pregunta de proveedor usa PROV-024, con evidencia literal.
- En el pack Jurídico, `relations: []`: la relación AV-9041 → contrato M-219 la respalda la cita EV-JUR-02, pero no está modelada.
