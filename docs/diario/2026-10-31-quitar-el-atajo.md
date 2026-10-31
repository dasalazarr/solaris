# Quitamos el atajo de entrada

*Borrador. Pendiente de revisión.*

Nuestro PRD dice que a un espacio de Solaris se entra con un código aleatorio de 128 bits, validado en el servidor. La demo cumplía eso en la pantalla y lo incumplía por detrás.

## Qué encontramos

- Los códigos estaban escritos en el código fuente.
- Un atajo de teclado, pensado para hacer pruebas, abría cualquier espacio sin código.
- La cookie de sesión guardaba el código tal cual.
- Las rutas que consultan los documentos no comprobaban la sesión.

Ninguna de estas cosas se ve desde fuera. Por eso son peligrosas.

## Qué hicimos

- Los códigos salen del repositorio. El servidor solo guarda su huella (hash), en una variable de entorno.
- La sesión va firmada y no lleva el código.
- El atajo desaparece. Si un espacio debe abrir varios procesos, se dice en su configuración, no con un truco de teclado.
- Toda ruta que toca datos exige una sesión válida.
- Hay pruebas automáticas para cada caso: código válido, inexistente, caducado, revocado y cookie manipulada.

## Qué aprendimos

- Un atajo «solo para mí» acaba siendo para cualquiera que pulse las teclas.
- Borramos dos rutas que nadie usaba. El código que no se usa no hay que protegerlo.
- Antes de migrar la landing a Next.js, hicimos capturas de la versión anterior. Al terminar, eran idénticas píxel a píxel. Esa es la prueba de que la migración no cambió nada que vea el usuario.
