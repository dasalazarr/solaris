// Falla si un texto de las escenas usa palabras vetadas o nombres de proveedor (ADR-0010, ADR-0012, H7).
import {readdirSync, readFileSync} from 'node:fs';
import {VETADAS} from './vocabulario.mjs';

let fallos = 0;
for (const fichero of readdirSync('src').filter((x) => x.endsWith('.tsx'))) {
  readFileSync(`src/${fichero}`, 'utf8').split('\n').forEach((linea, i) => {
    const m = linea.match(VETADAS);
    if (m) {
      fallos++;
      console.error(`src/${fichero}:${i + 1} «${m[0]}»: ${linea.trim().slice(0, 100)}`);
    }
  });
}
if (fallos) {
  console.error(`${fallos} palabra(s) vetada(s). Si ya son ciertas, cambia antes ADR-0010.`);
  process.exit(1);
}
console.log('Vocabulario OK');
