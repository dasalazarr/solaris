---
fecha: 2026-11-14
rol: cofundador
tema: Área de contenido y go to market (Fase 0, decisiones)
---

# Contenido y go to market · Fase 0

## Tarea
Diego: plan de contenido y posicionamiento alrededor de Solaris y la mascota (reels, carruseles, imágenes para LinkedIn y X, pruebas A/B, pauta), y explorar un sistema interno de creación de contenido como el de una herramienta comercial que genera una semana de publicaciones a partir de una web. Añadir ElevenLabs y considerar `create-video` de Remotion.

## Qué se encontró
- La herramienta de referencia es un servicio cerrado, sin repositorio público: no hay nada que bifurcar. Se replica el patrón.
- `video/` ya es el motor: Remotion 4, tokens, fuentes, efectos, gate de vocabulario y render en 16:9 y 4:5. Hay un reel 9:16 con mascota sin fusionar en la rama `feat/reel-alta-de-cliente`.
- No hay voz, subtítulos, carrusel ni imagen fija. Tampoco imagen Open Graph en la landing.
- La comunicación estaba aparcada (O03, ADR-0007); ADR-0023 excluía la mascota de `video/`; `REG-AB` impide un A/B en la landing sin línea base.
- Cero entrevistas. El único estudio pone a los despachos en prioridad baja-media.
- La última publicación de la página de empresa describe una ontología distinta a las siete primitivas del producto.
- El instalador de ElevenLabs crea una clave real, instala un SDK y escribe código; el uso comercial exige plan de pago.

## Decisiones de Diego (14/11)
- Objetivo: demostraciones y pilotos. Cuentas: su perfil y la página de Illarium. Pauta: documentada, sin activar. Medio día a la semana.
- Compradores: compras y finanzas, despachos, calidad y cumplimiento. España, en castellano.
- Voz: la suya grabada y una de catálogo; sin clonar. Ya tiene cuenta de pago.
- Sistema: herramienta interna, sin interfaz, en un repositorio privado.
- Mascota: compañera que señala, versión dorada.

## Qué se hizo
- ADR-0024, contrato y agente `contenido`, O03 pasa a `building`.
- `.gitignore`: las pruebas descartadas de la mascota y el personaje negro dejan de poder publicarse por error.
- Tablero con las peticiones a `landing-steward` (imagen Open Graph, UTM, agenda).

## Qué se propuso distinto de lo pedido
- No usar `create-video`: duplicaría proyecto y gates.
- Instalar ElevenLabs en el repositorio privado, no en `video/`.
- El A/B posible hoy es de mensajes en redes; con el alcance actual da señal, no significancia.
- Un comprador por tramo de cuatro semanas en vez de tres a la vez.

## Verificación
- `python3 scripts/wiki_lint.py`.
- Sin código de producto ni de landing en esta fase.

## Pendiente
- Fases 1 a 4: fusionar el motor vertical, crear el repositorio privado, voz y subtítulos, primer lote.
- Supuestos sin confirmar: tamaño del equipo para la licencia de Remotion; cuenta de X; que Umami esté activo en producción.
