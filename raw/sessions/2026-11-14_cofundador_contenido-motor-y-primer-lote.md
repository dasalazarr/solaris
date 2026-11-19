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

## Cierre de la sesión (15/11)
- **ElevenLabs conectado** por la vía del navegador: clave en un fichero ignorado por git, SDK instalado, sin descargar el paquete de skills que sugería el instalador. Los permisos incluyeron la clonación de voces, que no usamos.
- **Voz:** `voz.mjs` genera la locución con tiempos por carácter y la convierte a palabras para los subtítulos; con caché por frase y ajustes (estabilidad, velocidad, estilo, semilla). `transcribir.mjs` escrito y sin probar con la API.
- **Pruebas de voz sobre el reel W47 (238 caracteres cada una):** Marta (peninsular), Milena (la ficha dice colombiana) y Marta con `eleven_v3`. No se han oído en la sesión: solo tiempos y sonoridad (−16,2 a −16,3 LUFS).
- **Qué falló en esta parte:** `eleven_v3` rechaza el contexto entre frases (400, sin coste); un parámetro de orden inexistente en la búsqueda de voces; `languageCode` no sirve con `multilingual_v2`; al añadir contexto entre frases cambió la caché y las pruebas anteriores dejaron de contar.
- **Plan del playbook de contenido:** `playbook/PLAN.md` en el repositorio privado, por versiones que esperan a la evidencia (v0 el 22/11, v1 el 13/12).
- **Pendiente de Diego:** oír las tres versiones y elegir voz y modelo; decidir si Milena (colombiana) encaja con un mercado de España; revisar el lote W47; lista de cuentas objetivo; tamaño del equipo para la licencia de Remotion; cuenta de X; crear el remoto privado y abrir el PR de esta rama.
