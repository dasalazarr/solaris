---
id: ADR-0028
type: decision
title: "El código abre el vertical: tres tipos de espacio"
status: accepted
owner_role: security
links: ["[[ADR-0003]]", "[[ADR-0021]]", "[[ADR-0026]]", "[[F05]]"]
evidence: ["product/lib/space-admin.ts", "product/tests/space-admin.test.ts"]
updated: 2026-11-18
---

# ADR-0028 · El código abre el vertical: tres tipos de espacio

- Fecha: 2026-11-18
- Estado: aceptada (Diego, 18/11/2026)

## Contexto

Solaris tiene una sola puerta. Detrás hay varios verticales: compras, jurídico, finanzas (CFO), prevención del blanqueo, IFS y EUDR. El mecanismo ya existía ([[ADR-0003]]): cada código abre un espacio, y ese espacio abre una lista cerrada de procesos (`packIds`). Pero cada alta se hacía a mano, con procesos, días y nombre elegidos en el momento. El resultado era un onboarding distinto en cada caso, y la puerta intentaba compensarlo repitiendo la tesis de la landing.

## Opciones

1. **Seguir como estaba.** Altas a mano con `--procesos`.
2. **Una puerta o una URL por vertical.** Equivale a un listado público de espacios, y el PRD lo prohíbe (R1).
3. **Tipos de espacio en el script de alta.** Cada tipo trae sus valores por defecto. Ni el motor ni el servidor cambian.

## Decisión

Opción 3. El código decide qué vertical se ve. Un vertical es un proceso de plantilla y no es una entidad nueva del motor.

| Tipo | Para quién | Procesos | Personas con rol | Caducidad por defecto |
|---|---|---|---|---|
| `demo` | prospecto | exactamente uno (`--vertical`) | no | 14 días |
| `piloto` | cliente | los suyos (al menos uno) | sí, con `persona` después del alta | 90 días |
| `interno` | Diego, para enseñar | todos | no | 30 días |

- `npm run espacio -- alta --tipo demo --vertical cfo`
- `npm run espacio -- alta --tipo piloto --procesos juridico` y después `persona <id> --nombre … --roles …`
- `npm run espacio -- alta --tipo interno`

`--dias` y `--nombre` siguen mandando sobre los valores por defecto. Si no se indica `--tipo`, el alta se hace a mano como antes.

La puerta tiene un solo trabajo: pegar el código de la invitación y entrar. Después, el primer uso lo marca el proceso ([[ADR-0021]]).

## Consecuencias

- **Se gana:** cada prospecto recibe lo mismo, con la etiqueta «Demo · Finanzas» y la misma invitación. El tipo no es un permiso nuevo; solo decide qué `packIds` y qué caducidad se guardan. Un vertical nuevo exige añadir su nombre a `VERTICAL_NAMES`, y el compilador avisa si falta.
- **Cuesta:** el tipo no se guarda en `SOLARIS_SPACES`, así que `lista` lo deja ver por la etiqueta y no por un campo. Guardarlo obligaría a tocar la validación del servidor. No compensa hasta que haya decenas de espacios.
- **Sin cambio de seguridad:** el código sigue teniendo 128 bits, se guarda como hash, caduca, se revoca y tiene límite de intentos ([[F05]]).
- **Pendiente:** un enlace con el código tras `#` para no tener que copiar y pegar. Toca el acceso, así que necesita su propia nota y la revisión de security.
