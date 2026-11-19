# 2026-11-13 · cofundador · alta de espacios en un comando

## Contexto
Diego quiere probar el producto y pide mejorar el flujo para generar códigos. El flujo tenía cinco pasos a mano: ejecutar el script, abrir `SOLARIS_SPACES` en Vercel, pegar JSON, redesplegar y enviar el código. Si había un error de formato o un id repetido, `loadSpaces` no abría ningún espacio, y nadie se enteraba.

## Hecho
- `npm run espacio -- alta|persona|renueva|revoca|lista|secreto` (illariumcore#27). Valida con el mismo `loadSpaces` que el servidor antes de guardar. Saca procesos y roles del producto. Pregunta antes de redesplegar y comprueba en producción que el código entra.
- `renueva` en lugar de prórroga: el playbook pide renovar con un código nuevo, no alargando el anterior. Id por defecto `prospecto-AAAA-MM-x`; caducidad de 60 días como máximo.
- Revisión de security sin veto. Un ajuste: el código solo se comprueba contra una URL https o local.
- Playbook de códigos, despliegue y estado actualizados.

## Qué falló
- `vercel env run -p … --scope … -e production -- node <fichero>` no ejecutó el comando: la CLI lo tomó como `vercel <ruta>`. Creó tres proyectos sueltos (`cuenta` con un script de una línea, `tmp` vacío, y `product` conectado al repo, que lanzó un build al hacer push). Se canceló el build (estaba detrás de SSO) y Diego aprobó borrar los tres. Borrados y comprobados con `vercel project ls`.
- El clasificador de permisos bloquea leer valores de producción con `env pull`. Es lo correcto: la primera ejecución real contra Vercel la hace Diego.

## Gate
290 tests, lint, tipos y build del producto. Órdenes y errores probados a mano con `--archivo`. Sin probar contra Vercel.
