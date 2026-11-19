---
id: ADR-0025
type: decision
title: "La demo pública guía el primer minuto y cierra con un formulario corto"
status: validating
owner_role: landing-steward
links: ["[[ADR-0024]]", "[[ADR-0010]]"]
evidence: []
updated: 2026-11-18
---

# ADR-0025 · Demo guiada y formulario corto

- Estado: propuesta. Construido en la rama `feat/demo-bienvenida` de la landing (solaris_fronted#25), sin desplegar ni medir.
- Contexto: las publicaciones de LinkedIn ([[ADR-0024]]) enlazan a `/solaris/demo`. Esa página enseñaba la demo sin bienvenida, sin cabecera y sin ninguna salida: quien llegaba desde un post no podía pedir una demostración. El formulario de la landing pide perfil, nombre, empresa, correo, proceso y comentario, y se abre en un panel aparte.

## Opciones

| Pregunta | Elegido | Descartado |
|---|---|---|
| Cómo se recibe | Ventana modal al llegar, con el problema del post y dos salidas («Empezar» o «Explorar por mi cuenta»). Una vez por sesión | Todo en la página a la vez (primera versión, descartada por Diego el 18/11); vídeo |
| Cómo se avanza | Por eventos: un globo anclado junto a lo que hay que hacer (hoja inferior en móvil), que cambia al abrir la regla, al cambiar de rol y al aprobar | Tarjetas con «Siguiente»; riel fijo con todas las instrucciones |
| Dónde se pide el contacto | En una ventana modal tras aprobar, con «Hecho» arriba; y un botón flotante «Pedir demostración» en cuanto no hay recorrido en marcha | Formulario fijo al pie de la página; antes de la demo |
| Qué se pide | Nombre, empresa, correo de empresa y privacidad. Proceso (Compras) y perfil (cliente) los pone la demo | Los seis campos del formulario largo; solo correo |

## Decisión

Solo la página propia de la demo guía. La sección de demo dentro de la landing no cambia. El formulario corto usa la misma API (`/api/solicitud`) y las mismas reglas que el largo: correo de empresa, casilla de privacidad y campo trampa. No se toca el producto.

## Consecuencias

- Se aparta del PRD de la landing (§9, campos del formulario) solo en esta página. Hay que reflejarlo en el PRD si se mantiene.
- Eventos nuevos: `demo_guia` (paso), `demo_guia_saltada`, `cta_solicitar_demo` con `section` `demo-pildora`, y `form_enviado` con `section` `demo-corto` o `demo-corto-guiado`, y `form_error`.
- Sin tráfico medido no se puede decir que convierta más. Se mide desde el primer post: solicitudes con `origen` de la demo frente a las del formulario largo.
- No se ha probado el envío real del correo: en local la API valida el formulario y responde «no configurado» por falta de clave.
