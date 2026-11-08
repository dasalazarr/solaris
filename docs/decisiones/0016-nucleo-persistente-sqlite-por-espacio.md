---
id: ADR-0016
type: decision
title: "Un fichero SQLite por espacio y el rol en la sesión firmada"
status: accepted
owner_role: dev
links: ["[[ADR-0010]]", "[[ADR-0015]]", "[[F03]]", "[[R01]]", "[[R02]]"]
evidence: ["raw/sessions/2026-11-07_cofundador_fase-2-nucleo.md"]
updated: 2026-11-07
---

# ADR-0016 · Núcleo persistente: SQLite por espacio y rol en la sesión

- Estado: aceptada por el cofundador (2026-11-07), con la Fase 2 iniciada por Diego. El proveedor de contenedor y el dominio siguen siendo decisión suya.
- Contexto: todo se perdía al recargar y el rol lo elegía el navegador. Sin eso, el principio 3 no se puede demostrar en un piloto.

## Opciones de almacén

1. **Base compartida con filtro por cliente.** Descartada por [[ADR-0010]].
2. **PostgreSQL por cliente.** Aislamiento correcto, pero añade un servicio que operar en cada instalación.
3. **Un fichero SQLite por espacio.** Aislamiento físico, sin servicio aparte y el mismo artefacto en nube y en local.

## Decisión

Opción 3, con estas reglas:

- **`node:sqlite`, no `better-sqlite3`.** Sin dependencia nativa, a cambio de un módulo que Node aún marca como experimental. Queda detrás de la interfaz `Store`, así que cambiarlo cuesta un fichero.
- **`Store` síncrono.** Siempre es un fichero local. Se aparta del borrador de `nivel2-preguntas-y-contrato.md`, que lo proponía asíncrono, porque así la comprobación y la escritura van en una sola transacción.
- **Dos modos.** Solo hay persistencia con código personal y `SOLARIS_DATA_DIR`. Si falta algo, sigue la demostración de siempre, con rol simulado. Por eso se puede fusionar con Vercel desplegando desde `main`.
- **El estado se reproduce.** Lo guardado son decisiones; el estado resulta de aplicarlas sobre el proceso. Objetos y evidencias no se guardan hasta la Fase 4.
- **Pedir cambios no toca lo que se firma.** Está abierto a cualquiera, así que va aparte con su autor, y aprobar exige decir qué texto se aprueba.
- **El registro guarda el id de la persona.** El nombre se resuelve al leer y no queda en filas que no se reescriben.

## Consecuencias

- Hace falta un contenedor con disco, detrás de un proxy con TLS. Una instancia por espacio.
- «Solo anexar» protege de errores de la aplicación, no de quien administra el servidor. No hay cadena de hashes y la interfaz no promete más.
- Sin cifrado en reposo. No entra ningún documento real hasta resolverlo y pasar la revisión de la Fase 5.
- Copias de seguridad sin resolver: se decide con el proveedor.
- Si cambia la política, una aprobación anterior sigue valiendo. Se resuelve con `policy_hash` real en la Fase 3.
