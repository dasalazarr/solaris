---
id: ADR-0012
type: decision
title: "Tratamos al lector de tú y le hablamos de procesos, no de packs"
status: accepted
owner_role: product
links: ["[[ADR-0010]]", "[[ADR-0011]]", "[[F06]]"]
evidence: []
updated: 2026-11-05
---

# ADR-0012 · Tuteo, y «proceso» en vez de «pack»

- Estado: el tuteo lo decide Diego (2026-11-05). Pidió buscar alternativas a «pack»; «proceso» es propuesta del cofundador, aplicada porque es barata de cambiar y pendiente de su visto bueno.
- Contexto: el PRD trataba al lector de usted. Diego presenta a dueños de consultoras e implantadores y pide «tus». «Pack» es jerga nuestra y no dice qué se compra.

## Opciones para «pack»

1. **Proceso.** Las tarjetas ya son procesos y es una primitiva de la ontología. Riesgo: «Jurídico» agrupa más de un proceso.
2. **Módulo.** Se entiende, pero suena a software por piezas, y el motor es uno.
3. **Plantilla.** Fácil de entender, pero suena a algo estático y barato.
4. **Caso de uso.** Natural para implantadores, largo en botones y sin carácter.
5. **Contrato de proceso.** El más propio de la tesis, pero se confunde con los contratos de Jurídico.

## Decisión

- **Al lector, de tú.** Solo cambia la segunda persona: «las empresas necesitan que sus procesos…» se queda.
- **Al lector, «proceso».** Titular: «Un motor. Un contrato por proceso.» «Pack» sigue siendo el término interno en código, PRD y este repositorio.
- **Las páginas legales siguen de usted** hasta que las valide alguien cualificado.

## Consecuencias

- Toda frase nueva de landing y producto va de tú y sin «pack».
- «Véalo» pasa a «Míralo», porque «velo» se lee como otra palabra.
- El ancla pública pasa de `#packs` a `#procesos`; un enlace antiguo abre la portada sin saltar a la sección.
- Si se añade un caso comercial ([[ADR-0011]]), se presenta como un proceso más.
