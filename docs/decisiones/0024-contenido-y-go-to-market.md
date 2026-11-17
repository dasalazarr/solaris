---
id: ADR-0024
type: decision
title: "Contenido y go to market: se reactiva la comunicación, con límites"
status: validating
owner_role: product
links: ["[[ADR-0007]]", "[[ADR-0014]]", "[[ADR-0023]]", "[[ADR-0010]]", "[[ADR-0018]]", "[[O03]]", "[[F06]]"]
evidence: ["raw/sessions/2026-11-14_cofundador_contenido-go-to-market.md"]
updated: 2026-11-14
---

# ADR-0024 · Contenido y go to market

- Estado: propuesta. Diego decidió el 14/11 las opciones de abajo y aprobó el plan; falta ver el primer lote de piezas.
- Contexto: Solaris necesita su primer piloto de pago y no tiene canal. La comunicación estaba aparcada ([[O03]], [[ADR-0007]]) hasta tener ritmo de diario, condición que no se cumple. Diego pide un área de contenido (posicionamiento, plan editorial, pruebas de mensaje, reels, carruseles, imágenes y pauta) y un sistema interno que produzca las piezas.

## Opciones decididas

| Pregunta | Elegido | Descartado |
|---|---|---|
| Para qué sirve el contenido | Conseguir demostraciones y pilotos | Crecer audiencia; atraer canal; solo validar mensajes |
| Quién habla | El perfil de Diego (tesis y diario) y la página de Illarium (dolor, prueba y casos) | Cuentas propias de Solaris; solo marca; solo persona |
| Sistema | Herramienta interna sobre el motor de `video/`, sin interfaz | Panel con calendario; producto vendible (Visión v2) |
| Dónde vive | Repositorio privado aparte: estrategia, calendario, guiones, piezas y medición | La raíz pública |
| Mascota en piezas sociales | Compañera que señala: gancho, cierre y reacciones con sus estados. No habla. Versión dorada | Narradora con voz; solo firma |
| Voz | Diego grabado y una voz sintética de catálogo. No se clona a nadie | Clon de voz; sin voz |
| Pauta | Se documenta y no se activa | Presupuesto mensual desde el primer día |

## Decisión

1. **Se reactiva [[O03]] sin esperar al ritmo de diario.** Sus límites siguen: todo es borrador hasta que Diego lo aprueba, y publicar lo hace una persona. No hay publicación automática.
2. **El área vive en un repositorio privado.** Importa tokens, fuentes y efectos de `video/src` por alias, como `video/` importa `product/lib` ([[ADR-0014]]). El motor reutilizable (formato vertical, mascota por fotograma) se queda en `video/`.
3. **Toda afirmación de una pieza sale de una lista de mensajes permitidos**, cada uno con su referencia al PRD o a una decisión y su estado: Hoy, En tu piloto o Visión. Solo «Hoy» va en presente ([[ADR-0018]]). El vocabulario vetado ([[ADR-0010]]) se comprueba también sobre el texto del post y el guion de la voz.
4. **La mascota entra en piezas sociales.** Esto matiza la línea de [[ADR-0023]] que la excluía de `video/`: aparece en el gancho y en el cierre, nunca en un plano de producto ni junto a una cita, y una vez por plano como mucho.
5. **La prueba A/B es de mensajes en redes, no de la landing.** Un mismo dolor con dos ganchos, medido por `utm_content`. `REG-AB` sigue en pie: no hay experimento en la landing sin línea base de tráfico en `raw/eval-runs/`.
6. **Un comprador por tramo de cuatro semanas:** compras y finanzas, despachos, calidad y cumplimiento. El foco se revisa con las solicitudes por perfil.
7. **Rol nuevo, `contenido`,** con contrato en `plan/contratos/contenido.md`.

## Consecuencias

- Cuesta unos cinco días de construcción que salen de la Fase 4 (documentos reales).
- No se usa `create-video`: ya hay un proyecto de Remotion y un segundo duplicaría configuración y gates.
- Los guiones de la voz sintética salen a un tercero. Solo llevan texto público y datos de muestra.
- Si el equipo pasa de tres personas, Remotion exige licencia de empresa.
- La landing necesita imagen Open Graph, una convención de UTM y el enlace de agenda para que los enlaces de las piezas conviertan. Se propone a `landing-steward`; no se cambia aquí.
- Calidad y cumplimiento solo se cuenta como caso de uso: sus plantillas no reciben funciones nuevas.
- Sin entrevistas, los dolores de las piezas son hipótesis. Las respuestas que generen se anotan, anonimizadas, como evidencia.
