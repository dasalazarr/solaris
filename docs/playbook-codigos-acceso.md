# Playbook: códigos de acceso a la demo (Nivel 1)

Un código por prospecto, un espacio por código. Aplica a `illariumcore.vercel.app`.
Fuente: `product/scripts/espacio.ts` (`npm run espacio`) y [despliegue.md](despliegue.md).

## Reglas
1. Un código por prospecto. Solo se comparte uno en una demo en directo, con caducidad corta (días).
2. El código tiene 128 bits, se muestra **una vez** y no se puede recuperar. Vercel guarda solo el hash SHA-256.
3. Nunca en el repositorio, en `docs/` ni en el cliente. El código en claro vive en tu gestor de contraseñas hasta que se lo envías al prospecto.
4. Sin datos del prospecto en `SOLARIS_SPACES`: ni nombre de empresa ni de persona en `id` o `label`. Es una variable de entorno.
5. `noindex` no es control de acceso. El control es el código.
6. Un código que haya estado en el historial del repositorio está quemado ([[R01]]). No se reutiliza.

## Convención de nombres
- `id`: `prospecto-AAAA-MM-x` (x = a, b, c… dentro del mes). Ejemplo: `prospecto-2026-11-a`.
- `label`: genérico, p. ej. `Espacio de demostración`. Es lo que ve el prospecto.
- `--procesos`: solo los que necesita. `compras` para consultoras y procesos de compra; `juridico` para despachos. `pbc` para compliance; `ifs` y `eudr` solo si el prospecto los pide.
- `--dias`: 14 para una prueba corta, 30 por defecto, 60 como máximo (el comando no acepta más). Se renueva con `renueva`, que da otro código; no se alarga el anterior.

## Crear un código
1. Crea el espacio. Necesitas la CLI de Vercel con sesión iniciada:
   ```bash
   cd product && npm run espacio -- alta --procesos compras --dias 30
   ```
   El comando lee `SOLARIS_SPACES` de producción, añade la entrada con id `prospecto-AAAA-MM-x` y la valida con el mismo criterio que el servidor: si algo cerraría espacios, no guarda nada. Después pregunta si redespliega y comprueba en producción que el código entra.
2. Copia el código en claro a tu gestor de contraseñas. Solo se muestra esta vez.
3. Prueba tú el código en una ventana privada antes de enviarlo: entra, ve solo el proceso asignado y aparece el aviso de datos de muestra.
4. Envía el mensaje que imprime el comando por un canal privado, **separado de la URL** si el canal es dudoso (URL por un lado, código por otro).
5. Anótalo en tu registro privado (ver abajo).

Códigos por persona, para que el servidor imponga el rol: `npm run espacio -- persona <id> --nombre "…" --roles "…"`. Si no pones `--roles`, te lista los que admite el espacio.

Para ver qué hay: `npm run espacio -- lista` (estado y caducidad, sin hashes). Con `--archivo ruta.json` trabaja sobre un fichero local en vez de Vercel: para pruebas y para instancias de Nivel 2.

## Registro privado (fuera del repositorio)
Una nota o hoja tuya con: `id`, destinatario, fecha de envío, caducidad, pack, estado (activo / caducado / revocado) y si entró. **No** se versiona.

## Revocar
- `npm run espacio -- revoca <id>` (o `--persona <id-persona>` para un solo código) y acepta el redespliegue: sin él, la revocación no está en vigor.
- Cuándo: se filtra, el prospecto lo pide, termina la prueba antes de caducar o lo envías a la dirección equivocada.
- Comprueba tras redesplegar que el código ya no entra.

## Renovar
`npm run espacio -- renueva <id> [--dias 30]`: revoca el código y da otro con los mismos procesos, en una sola escritura. Los códigos de persona no se copian; dales uno nuevo con `persona`.

## Mantenimiento
- Cada mes, revisa `npm run espacio -- lista` y quita a mano en Vercel las entradas caducadas o revocadas.
- Si los espacios activos pasan de unos diez a la vez, valora automatizar la gestión (ADR). Hoy sería sobreingeniería.
- Si sospechas que se filtró algo, rota también `SOLARIS_SESSION_SECRET` (`npm run espacio -- secreto`): invalida todas las sesiones abiertas.

## Checklist antes de enviar
- [ ] Código probado en ventana privada
- [ ] Solo el pack necesario
- [ ] Caducidad puesta y anotada
- [ ] Sin datos del prospecto en `id`/`label`
- [ ] Código guardado en el gestor, no en `docs/`
- [ ] Enviado por canal privado
