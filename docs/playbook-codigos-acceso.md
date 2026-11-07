# Playbook: códigos de acceso a la demo (Nivel 1)

Un código por prospecto, un espacio por código. Aplica a `illariumcore.vercel.app`.
Fuente: `product/scripts/nuevo-codigo.mjs` y [despliegue.md](despliegue.md).

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
- `--packs`: solo los que necesita. `compras` para consultoras y procesos de compra; `juridico` para despachos. `ifs` y `eudr` solo si el prospecto los pide.
- `--dias`: 14 para una prueba corta, 30 por defecto, 60 como máximo. Se renueva generando otro código, no alargando el anterior.

## Crear un código
1. Genera el código:
   ```bash
   cd product && node scripts/nuevo-codigo.mjs --id prospecto-2026-11-a --packs compras --dias 30 --label "Espacio de demostración"
   ```
2. Copia el código en claro a tu gestor de contraseñas.
3. Añade la línea JSON al **array** de `SOLARIS_SPACES` en Vercel (proyecto `illariumcore` → Settings → Environment Variables → Production). Si ya hay entradas, se suma al array; no lo sustituyas.
4. Redespliega (las variables solo aplican a despliegues nuevos).
5. Prueba tú el código en una ventana privada antes de enviarlo: entra, ve solo el pack asignado y se ve el aviso de datos de muestra.
6. Envíalo por un canal privado, **separado de la URL** si el canal es dudoso (URL por un lado, código por otro).
7. Anótalo en tu registro privado (ver abajo).

## Registro privado (fuera del repositorio)
Una nota o hoja tuya con: `id`, destinatario, fecha de envío, caducidad, pack, estado (activo / caducado / revocado) y si entró. **No** se versiona.

## Revocar
- Pon `"revoked": true` en su entrada de `SOLARIS_SPACES` y redespliega, o elimina la entrada.
- Cuándo: se filtra, el prospecto lo pide, termina la prueba antes de caducar o lo envías a la dirección equivocada.
- Comprueba tras redesplegar que el código ya no entra.

## Renovar
Genera un código nuevo con `id` nuevo (`...-b`), revoca el anterior. No edites `expiresAt` a mano.

## Mantenimiento
- Cada mes, quita del array las entradas caducadas o revocadas.
- Si los espacios activos pasan de unos diez a la vez, valora automatizar la gestión (ADR). Hoy sería sobreingeniería.
- Si sospechas que se filtró algo, rota también `SOLARIS_SESSION_SECRET` (`node scripts/nuevo-codigo.mjs --secreto`): invalida todas las sesiones abiertas.

## Checklist antes de enviar
- [ ] Código probado en ventana privada
- [ ] Solo el pack necesario
- [ ] Caducidad puesta y anotada
- [ ] Sin datos del prospecto en `id`/`label`
- [ ] Código guardado en el gestor, no en `docs/`
- [ ] Enviado por canal privado
