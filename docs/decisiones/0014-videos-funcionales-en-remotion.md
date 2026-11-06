---
id: ADR-0014
type: decision
title: "Vídeos funcionales en Remotion, con los datos del producto"
status: accepted
owner_role: product
links: ["[[ADR-0010]]", "[[ADR-0012]]", "[[F01]]", "[[F03]]", "[[F04]]", "[[F06]]"]
evidence: ["raw/sessions/2026-11-06_cofundador_videos-remotion.md"]
updated: 2026-11-06
---

# ADR-0014 · Vídeos funcionales en Remotion

- Estado: aceptada la herramienta (2026-11-06, Diego pidió Remotion). El resultado y su publicación quedan pendientes de su visto bueno.
- Contexto: hacen falta piezas para redes y para presentar a consultoras. Una grabación de pantalla envejece con cada cambio de interfaz, y un guion copiado a mano puede acabar afirmando lo que el producto no hace.

## Opciones

1. **Grabar la demo.** Es barato y fiel, pero no admite el acabado pedido y hay que repetirlo con cada cambio.
2. **Remotion con datos copiados.** Tiene el acabado, pero el guion y el producto pueden divergir.
3. **Remotion en `video/`, importando `product/lib`.** Las escenas leen el caso de muestra y el motor; el render falla si los huecos del guion dejan de ser los del motor.

## Decisión

Opción 3. La interfaz del vídeo es una recreación, no una captura: reproduce textos y datos del producto, a mayor tamaño.

## Consecuencias

- `video/` es una carpeta de la raíz, sin ningún papel en el despliegue de `product` ni de `landing`.
- Los proveedores salen solo por identificador hasta resolver H7.
- Del post de partida no pasan a los vídeos: «pack», «sellado», «se ejecutan solas», «se auditan solos», «en un clic» y «cientos de expedientes». Chocan con [[ADR-0010]] y [[ADR-0012]], o no están medidos.
- Licencia de Remotion: gratis hasta 3 empleados. Illarium debe revisarlo al contratar al cuarto.
