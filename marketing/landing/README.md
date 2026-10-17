# Landing — M7-G3

Página estática sin build: `index.html` + `styles.css`, con los mismos tokens de color que la app. Vista local: `preview_start landing` (puerto 4173) o `python3 -m http.server 4173 --directory marketing/landing`.

## Antes de publicar (checklist)
- [ ] Nombre y dominio decididos (O07).
- [ ] Enlace real de la agenda en el botón `data-agenda-placeholder` (Cal.com/Calendly). Hoy apunta a `#agendar`.
- [ ] Revisión de security: RGPD del embed o enlace de la agenda, cabeceras del hosting y que no haya cookies.
- [ ] Texto de la ayuda foral confirmado en las bases oficiales (`marketing/messaging.md` §3).
- [ ] Cada cifra está en la tabla de claims (`messaging.md` §4).
- [ ] M7-G5: sustituir la maqueta `<figure class="mock">` por el vídeo con póster.

## Despliegue
Netlify o Vercel con la carpeta `marketing/landing/` como raíz publicada (sin comando de build).
