# 0003 · Acceso a espacios: hash en entorno y sesión firmada

- Fecha: 2026-10-31
- Estado: aceptada

## Contexto

El PRD de producto (§4) exige un código de espacio aleatorio de al menos 128 bits, validado en servidor, con cookie HttpOnly y sin listado público. La demo incumplía estos requisitos en varios puntos:
- los códigos estaban escritos en `lib/space-auth.ts` y en el historial de git;
- `PUT /api/space` (el atajo Alt+D) abría sesión sin código;
- la cookie guardaba el código en claro y sin firma;
- las rutas de consulta no comprobaban la sesión.

## Opciones

1. **Variable de entorno con hashes y una sesión firmada (HMAC).** Sin base de datos.
2. Base de datos de espacios con panel de administración.
3. Un proveedor de identidad externo.

## Decisión

Opción 1:
- `SOLARIS_SPACES` es un array JSON de `{id, codeHash, packIds, label, expiresAt, revoked}`.
- `SOLARIS_SESSION_SECRET` firma la cookie.
- `scripts/nuevo-codigo.mjs` genera los códigos.
- Un espacio puede abrir varios packs. Así Diego tiene un código para enseñar los cuatro sin depender de un atajo.

## Consecuencias

- **Lo que se gana:**
  - el repositorio ya no contiene códigos, solo hashes, y esos fuera del repo;
  - los códigos antiguos dejan de valer;
  - revocar es poner `"revoked": true` o borrar la entrada y redesplegar o reiniciar.
- **Lo que cuesta:** crear o revocar un espacio exige tocar la variable de entorno. Es aceptable para pocos prospectos. Un panel de administración solo tendrá sentido si hay decenas de espacios.
- **Riesgo residual:** no hay límite de intentos. Con 128 bits la fuerza bruta no es práctica, pero se añadirá un límite por IP cuando el despliegue público sea estable.
- **Rutas eliminadas:** `/api/ontology/ask` y `/api/ontology/extract`, que ninguna pantalla usaba. Si la ingesta (Explorar, F5) las necesita, volverán con sesión obligatoria.
