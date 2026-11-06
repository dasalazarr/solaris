import {continueRender, delayRender, staticFile} from 'remotion';
import {loadFont} from '@remotion/fonts';

const lista: [string, string, string, string][] = [
  ['Schibsted Grotesk', 'schibsted-grotesk-latin-400-normal', '400', 'normal'],
  ['Schibsted Grotesk', 'schibsted-grotesk-latin-500-normal', '500', 'normal'],
  ['Schibsted Grotesk', 'schibsted-grotesk-latin-600-normal', '600', 'normal'],
  ['Schibsted Grotesk', 'schibsted-grotesk-latin-700-normal', '700', 'normal'],
  ['Newsreader', 'newsreader-latin-400-normal', '400', 'normal'],
  ['Newsreader', 'newsreader-latin-500-normal', '500', 'normal'],
  ['Newsreader', 'newsreader-latin-400-italic', '400', 'italic'],
  ['Newsreader', 'newsreader-latin-500-italic', '500', 'italic'],
  ['JetBrains Mono', 'jetbrains-mono-latin-400-normal', '400', 'normal'],
  ['JetBrains Mono', 'jetbrains-mono-latin-500-normal', '500', 'normal'],
];

const espera = delayRender('Cargando tipografías');
Promise.all(
  lista.map(([family, file, weight, style]) =>
    loadFont({family, url: staticFile(`fonts/${file}.woff2`), weight, style}),
  ),
).then(() => continueRender(espera));
