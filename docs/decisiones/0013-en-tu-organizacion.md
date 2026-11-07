---
id: ADR-0013
type: decision
title: "Decimos «en tu organización», y «En tu piloto» en vez de «Siguiente»"
status: accepted
owner_role: product
links: ["[[ADR-0009]]", "[[ADR-0010]]", "[[ADR-0012]]", "[[F06]]"]
evidence: ["docs/spec-landing-claridad.md"]
updated: 2026-11-05
---

# ADR-0013 · «En tu organización» y «En tu piloto»

- Estado: «en tu organización» lo aprueba Diego (2026-11-05). «En tu piloto» es propuesta del cofundador, aplicada porque es barata de cambiar y pendiente de su visto bueno.
- Contexto: «tu equipo» se lee como máquina o como personas; el producto lo usa como personas (`SolarisOnboarding.tsx`). Una auditoría externa propuso «Vive en tu infraestructura» o «En tu propio entorno». Además, «Siguiente» contaba lo que le falta al producto más que lo que recibe el cliente.

## Opciones para el lugar de instalación

1. **«Tu equipo».** Es lo que había, y es ambiguo.
2. **«Tu infraestructura» o «tu entorno».** Suenan sólidas, pero sugieren una nube propia, y VPC no se promete ([[ADR-0010]]).
3. **«Tu organización».** Ya es la cifra de la página, y no prejuzga dónde corre: sigue abierto (`nivel2-preguntas-y-contrato.md`, H1).

## Decisión

- **Opción 3.** «Equipo» queda solo cuando se habla de una máquina («un equipo de tu organización»).
- **La columna «Siguiente» pasa a «En tu piloto»**, con la nota «Lo preparamos contigo para el primer piloto». Solo admite lo comprometido, como antes.
- **La Visión sigue rotulada como hipótesis.** «En desarrollo» se descartó porque es falso.

## Consecuencias

- Toda frase nueva de landing y producto sigue este vocabulario.
- El estado real se sigue diciendo, una vez, en esa columna.
- Si Nivel 2 se redefine con otro lugar de instalación, se revisa este ADR.
