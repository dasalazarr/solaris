---
fecha: 2026-11-07
rol: cofundador
tema: la landing y el vídeo enseñan el menú real del producto
---

# Menú real en landing y vídeo

## Tarea
Alinear `ProductWindow` y `video/src/ventana.tsx` con el menú de la Fase 1 y volver a renderizar.

## Qué se hizo
- Landing (solaris_fronted#17): Contrato y Registro, iconos de la app y «Proceso de compra».
- Vídeo: lo mismo; 8 MP4 en `video/out/` (no se versionan).

## Qué falló
Nada. Dos capturas del navegador no llegaron y se repitieron.

## Decisiones
- El título «IA privada para procesos con contrato» de la landing no se toca: es mensaje y SEO, y lo decide Diego.

## Evidencia
- `pnpm lint` (solo los 3 avisos conocidos) y `pnpm build`. Navegador local a 1024 px y comprobación a 375 px sin scroll horizontal.
- `npm run gate`. Hojas de contacto de Película 16:9 y Firma 4:5, además de Cruza y Detecta. Duraciones sin cambios y sonoridad de −16,2 a −16,7 LUFS.

## Sin comprobar
- Audio y ritmo a tiempo real: los debe ver una persona con sonido.
- Hero de la landing por encima de 1024 px.
