# Pedimos un diagnóstico de nuestro producto y lo peor no estaba en él

*Borrador. Pendiente de revisión.*

Nos llegó una revisión externa de la landing y la demo. Tenía razón en lo que se ve: enseñábamos códigos de nuestro backlog, hashes y etiquetas de prueba a quien responde de un proceso. Y nuestro hero terminaba en la cita, así que se leía como un chat con PDF.

Antes de aplicarla, la comparamos con el código.

## Qué encontramos

- Proponía un «Registro Inmutable» con «huella criptográfica». Nuestro registro vive en la memoria del navegador y se pierde al recargar.
- Elogiaba el selector de rol. No era un selector: era un campo de texto, y nadie lo comprobaba. Se podía escribir «Becario» y aprobar un pedido de 18.450 €.
- Confirmar un bloqueo marcaba el pedido como validado, con el certificado todavía caducado.

Lo primero es un error de la revisión. Los otros dos eran nuestros, y llevaban ahí desde el principio.

## Qué decidimos

Quitamos la jerga, pero no la sustituimos por sellos. Lo técnico va a un desplegable, rotulado como de muestra. Y escribimos una lista de palabras que no usamos hasta que sean ciertas: inmutable, criptográfica, en segundo plano.

Vendemos confianza verificable. Un sello que se desmonta al pulsarlo es peor que un hash feo.

## Qué falló

Publicamos un commit con un test en rojo, porque encadenamos el test y el commit sin condición. El fallo estaba en el propio test, pero el mensaje ya decía que todo pasaba. Ahora el commit depende del resultado.

## Qué aprendimos

Una revisión externa ve lo que el usuario ve. No ve si es verdad. Hay que leerla con el código abierto.

Y el fallo más grave estaba justo en lo que parecía nuestro mejor acierto.
