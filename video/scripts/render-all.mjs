// Renderiza todas las piezas. Filtro opcional: node scripts/render-all.mjs Cruza 16x9
import {execFileSync} from 'node:child_process';
import {rmSync} from 'node:fs';
const filtros = process.argv.slice(2);
const piezas = ['Cruza', 'Detecta', 'Firma', 'Pelicula'];
const formatos = ['16x9', '4x5'];
// Reel comercial: 9:16 para TikTok e Instagram, 16:9 para LinkedIn y la web.
const trabajos = [
  ...formatos.flatMap((fm) => piezas.map((p) => [`${p}-${fm}`, `solaris-${p.toLowerCase()}-${fm}`])),
  ['ReelAlta-9x16', 'solaris-reel-alta-de-cliente-9x16'],
  ['ReelAlta-16x9', 'solaris-reel-alta-de-cliente-16x9'],
];
for (const [id, nombre] of trabajos) {
  {
    if (filtros.length && !filtros.every((x) => id.includes(x) || x === id)) continue;
    console.log(`\n>>> ${id}`);
    const salida = `out/${nombre}.mp4`;
    execFileSync('npx', ['remotion', 'render', 'src/index.ts', id, 'out/_crudo.mp4', '--log=error'], {stdio: 'inherit'});
    // Sonoridad para web: -16 LUFS, sin tocar la imagen.
    execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', 'out/_crudo.mp4', '-c:v', 'copy', '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11', '-ar', '48000', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', salida], {stdio: 'inherit'});
  }
}
rmSync('out/_crudo.mp4', {force: true});
