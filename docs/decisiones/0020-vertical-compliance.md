---
id: ADR-0020
type: decision
title: "La vertical Compliance empieza por prevención del blanqueo en despachos y asesorías"
status: accepted
owner_role: product
links: ["[[ADR-0011]]", "[[ADR-0015]]", "[[ADR-0017]]", "[[O01]]", "[[O06]]", "[[O07]]", "[[H04]]"]
evidence: ["raw/research/2026-11-10_compliance-vertical.md", "docs/caso-de-estudio-compliance.md"]
updated: 2026-11-10
---

# ADR-0020 · Vertical Compliance

- Estado: aceptada por Diego (2026-11-10): ámbito de prevención del blanqueo y plantilla en el producto. Siguen abiertos el nombre y quién revisa las reglas.
- Contexto: Diego pide investigar y estructurar una vertical de Compliance con su caso de estudio, incluida la plantilla en el producto. El estudio de mercado pide «una obligación regulatoria» como motivo de urgencia ([[O06]]) y [[ADR-0011]] dejó abierto un proceso nuevo para consultoras. El alcance está congelado ([[ADR-0015]]).

## Opciones de ámbito

Comparadas con fuentes en `raw/research/2026-11-10_compliance-vertical.md`.

1. **Prevención del blanqueo (Ley 10/2010).** Obligaciones por expediente de cliente, con fechas próximas. Solo sirve a sujetos obligados.
2. **Compliance penal (art. 31 bis CP, UNE 19601).** Sirve a la industria mediana, pero sin fecha que obligue y en terreno de las suites GRC.
3. **Diligencia de terceros.** La reforma europea de 2026 la deja para grupos muy grandes.
4. **Protección de datos.** Mercado maduro.
5. **Canal de denuncias.** Datos demasiado sensibles para una demo.

## Opciones de alcance

- **A. No hacerla.** No desplaza nada. Deja sin respuesta la pregunta del canal.
- **B. Solo documento.** Investigación y caso de estudio, para enseñar en entrevistas.
- **C. Documento y plantilla.** Lo pedido por Diego. Quinta plantilla en el producto.

## Decisión

Ámbito 1 y alcance C, en dos entregas:

1. Investigación, caso de estudio y esta nota. Hecho el 10/11.
2. Plantilla `pbc` en el producto, con el caso de `docs/caso-de-estudio-compliance.md`. Construida el 10/11 en la rama `feat/plantilla-compliance` de illariumcore, por fusionar.

El proceso es «alta y seguimiento de clientes». Se nombra «Compliance · Alta de clientes». Compliance penal queda como segundo proceso posible, sin fecha.

## Por qué

- Es el único ámbito con fechas cercanas: cambio del reglamento en octubre de 2026 y reglamento europeo en julio de 2027 (fuente secundaria, por confirmar en el texto).
- Las obligaciones son condiciones sobre un expediente con documentos. Caben en los operadores actuales sin tocar el motor ([[ADR-0017]]).
- El despacho de [[O01]] y las asesorías del canal son ellos mismos sujetos obligados: el primer usuario puede ser el propio aliado.

## Consecuencias

- **Desplaza la Fase 4** uno o dos días de trabajo por la plantilla.
- **No valida demanda.** [[H04]] se mide en las entrevistas. Si se debilita, la plantilla se queda como muestra y no se profundiza.
- **No encaja con el cliente ideal del estudio** (industria mediana). Es una apuesta por el canal, no por ese cliente.
- **Cambia el ROADMAP:** de cuatro plantillas a cinco. IFS y EUDR siguen sin profundizarse.
- **Landing:** no nombra Compliance hasta que la plantilla esté fusionada. Entonces se propone el cambio.
- **Texto obligatorio en la plantilla:** no es asesoramiento jurídico ni certifica cumplimiento.
- **Antes de un piloto real:** revisión de las reglas por alguien cualificado, lectura de los artículos sin comprobar, Nivel 2, encargo de tratamiento y veto de `security`.
- **Fuera:** examen especial, comunicación al SEPBLAC, verificación de identidad y consulta de registros externos.

## Abierto para Diego

1. ¿El identificador `pbc` y el nombre «Compliance · Alta de clientes»?
2. ¿Quién revisa las reglas antes de enseñarlas a un despacho?
