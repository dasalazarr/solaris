---
fecha: 2026-11-14
rol: cofundador
tema: Inicio vivo, pantallas con el mismo formato y auditoría de experiencia
---

# Inicio vivo y pantallas con el mismo formato

## Tarea
Diego, con capturas de la demo y de ElevenLabs: saludar a Solaris y arreglar el titular de la bienvenida, simplificar «Cómo lo evalúa el motor», dar a todas las pestañas el mismo formato, un Inicio que resuma el estado con la pregunta en primer plano y sensación de sistema vivo, y una auditoría buscando huecos.

## Qué se hizo
- Rama `feat/inicio-vivo` de illariumcore, desde `origin/main`. Un commit local, sin subir.
- `components/workspace/ui.tsx`: cabecera de pantalla, panel, selector, botones, punto vivo y caja de pregunta.
- `InicioSurface.tsx` y `lib/home.ts` (con test): estado del proceso, siguiente decisión, procesos habilitados y última actividad.
- Las seis pantallas usan la cabecera común y se titulan como en el menú.
- `RuleVerdict`: un bloque; la regla en una frase y la lógica real plegada.
- Bienvenida: «Te damos la bienvenida a Solaris»; el nombre del espacio pasa a la línea del entorno; titular en dos líneas.
- ADR-0022 propuesta; `docs/spec-experiencia.md` actualizada.

## Verificación
- 299 tests, lint y build del producto.
- Navegador en local con un código desechable (borrado al terminar): bienvenida, Inicio, las seis pantallas en escritorio, Inicio y Registro a 375 px sin scroll horizontal, recorrido de punta a punta en Compras, y el estado de Inicio pasando de 3 a 2 tras aprobar.
- Pregunta libre desde Inicio: lleva a Preguntar. Sin clave de Gemini en local, respondió «No puedo responder ahora»; la respuesta real no se ha visto.
- Sin probar: Jurídico y Compliance en navegador, espacio que guarda (con persona), lector de pantalla, producción.

## Qué falló
- El foco del campo dibujaba un rectángulo dentro de la caja redonda: el `:focus-visible` global no está en una capa y gana a la utilidad de Tailwind. Se resolvió con una regla propia.
- La línea de estado de Inicio partía el punto a otra línea en móvil.

## Hallazgos de la auditoría sin corregir
- `expression` de R-03 dice una cosa y la lógica evaluada otra; Contrato sigue enseñando `expression`.
- El selector dice «Compras» y la cabecera «Proceso de compra».
- Sin `NEXT_PUBLIC_LANDING_URL`, la puerta enlaza a `illarium.com/solaris`. No se ha comprobado qué vale en Vercel.
- El dictamen repite en parte el motivo que ya da el detalle de Huecos y de Revisar.
- Los botones de dentro de los paneles mezclan radios y tamaños.
- El vídeo rotula «Cómo lo evalúa el motor» y las capturas de la landing son del diseño anterior.

## Cierre
- La rama se subió y illariumcore#30 se fusionó el 14/11 a las 08:05; Vercel marcó el despliegue como completado. No se ha abierto la página en producción.
- La raíz seguía en `docs/vertical-compliance`, ya fusionada y detrás de `main`. Los cambios de raíz se rehicieron sobre `main` en `docs/inicio-vivo`; los punteros de `product` y `landing` quedan en su `main`.
