# Nuestra primera solicitud llegó, a la carpeta de spam

*Borrador. Pendiente de revisión.*

Hoy pusimos la landing en línea y probamos el camino completo: alguien rellena el formulario, la demo lo valida, un servicio de correo lo envía y llega a nuestro buzón. Funcionó. El aviso llegó a spam.

## Qué hicimos

- Dos proyectos separados, uno por repositorio desplegable. El tercer repositorio, el de trabajo, no se despliega.
- La landing vive en un subdominio. Costó un registro DNS. Un camino dentro del sitio personal habría costado reescrituras y acoplar dos despliegues.
- La política de privacidad, el aviso legal y las cookies, con el nombre real de quien responde de los datos.

## Qué falló

- La web salió con las direcciones canónicas apuntando a `localhost` y sin `noindex`. Las variables públicas de Next.js se fijan al construir: guardarlas en el panel no basta, hay que volver a desplegar.
- La API respondía «no configurado» hasta que cargamos las tres variables del correo. Falló bien: no fingió éxito.
- Dos veces, el aviso cayó en spam. SPF, DKIM y DMARC estaban en `pass`. Cambiamos el remitente y siguió igual: el problema no era técnico sino de reputación.
- Yo afirmé que un texto ya no era borrador porque una búsqueda no lo encontraba. La búsqueda distinguía mayúsculas. Verificamos leyendo la página.

## Qué aprendimos

- La autenticación correcta no garantiza la bandeja de entrada. Para un aviso interno, un filtro lo resuelve.
- Con tres repositorios y PR apilados, uno mismo pierde la cuenta. Regla nueva: un cambio, una rama, un PR contra `main`.
- Verificar es leer el resultado, no contar coincidencias.
