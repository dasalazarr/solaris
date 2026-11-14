---
fecha: 2026-11-14
rol: cofundador
tema: Área de contenido (Fases 1 a 4): motor vertical, repositorio privado y primer lote
---

# Contenido y go to market · motor vertical y primer lote

## Tarea
Ejecutar el plan aprobado por Diego tras ADR-0024: fusionar el reel vertical con la mascota dorada, crear el área de contenido en un repositorio privado, añadir voz y subtítulos, y producir el primer lote.

## Qué se hizo
- `video/`: el reel «Alta de cliente» en 9:16 queda con una sola variante, la dorada. La mascota abre y cierra; ya no acompaña los planos de producto. El vocabulario vetado pasa a un módulo (`video/scripts/vocabulario.mjs`) que también usa el área de contenido.
- Skills `video-funcional` y `direccion-visual`: regla de la mascota en piezas sociales.
- Repositorio privado del área (fuera de esta raíz): estrategia, lista de mensajes permitidos, generador de carrusel, imagen y reel sobre el motor de `video/`, gate propio y primer lote en borrador para compras y finanzas.
- Instalador de ElevenLabs ejecutado hasta el paso de autorización. No se autorizó en la sesión.

## Qué falló
- La mascota del reel tapaba el rótulo «Demo en la nube · datos de muestra» en un plano de producto. Se vio en la hoja de contacto, no en el gate.
- Al describirle a Diego la opción de la mascota dije que el reel ya dejaba los planos de producto sin ella. No era cierto: la acompañaba todo el reel. Se cambió el reel para que coincida con lo decidido.
- Con voz, la locución se adelantaba a la imagen: cada plano tiene una duración mínima y la voz no esperaba. Se detectó con una voz de borrador del sistema.
- El primer carrusel tenía el cuerpo de texto demasiado pequeño para móvil.
- El instalador de ElevenLabs pide permisos mucho más amplios de lo necesario, incluida la clonación de voces, que Diego había descartado. Se le avisó antes de autorizar.

## Verificación
- `npm run gate` en `video/` con el producto en su `main`; hojas de contacto del reel en 9:16 y regresión en 16:9 y 4:5.
- `python3 scripts/wiki_lint.py`.
- En el repositorio privado: gate en verde, y en rojo con una palabra vetada y un mensaje inexistente; carruseles, imágenes y reel renderizados y vistos en hoja de contacto; reel a −16,1 LUFS.
- Sin hacer: ver los vídeos a tiempo real y oírlos; voz de catálogo; transcripción de una grabación de Diego; enlace con UTM comprobado en la analítica.

## Pendiente
- Diego: autorizar ElevenLabs o poner una clave restringida; revisar el lote; confirmar tamaño del equipo (licencia de Remotion) y la cuenta de X.
- landing-steward: imagen Open Graph, convención de UTM, comprobar la analítica en producción.
