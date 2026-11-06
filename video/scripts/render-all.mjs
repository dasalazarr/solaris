// Renderiza todas las piezas. Filtro opcional: node scripts/render-all.mjs Cruza 16x9
import {execFileSync} from 'node:child_process';
import {rmSync} from 'node:fs';
const filtros = process.argv.slice(2);
const piezas = ['Cruza', 'Detecta', 'Firma', 'Pelicula'];
const formatos = ['16x9', '4x5'];
for (const fm of formatos) {
  for (const p of piezas) {
    const id = `${p}-${fm}`;
    if (filtros.length && !filtros.every((x) => id.includes(x))) continue;
    console.log(`\n>>> ${id}`);
    const salida = `out/solaris-${p.toLowerCase()}-${fm}.mp4`;
    execFileSync('npx', ['remotion', 'render', 'src/index.ts', id, 'out/_crudo.mp4', '--log=error'], {stdio: 'inherit'});
    // Sonoridad para web: -16 LUFS, sin tocar la imagen.
    execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', 'out/_crudo.mp4', '-c:v', 'copy', '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11', '-ar', '48000', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', salida], {stdio: 'inherit'});
  }
}
rmSync('out/_crudo.mp4', {force: true});
