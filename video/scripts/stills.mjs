// Hoja de contacto: node scripts/stills.mjs "Comp:f1,f2,f3;Comp2:f4" salida
import {bundle} from '@remotion/bundler';
import {renderStill, selectComposition, openBrowser} from '@remotion/renderer';
import {execFileSync} from 'node:child_process';
import {mkdirSync, rmSync} from 'node:fs';
import path from 'node:path';

const [spec, salida = 'contacto'] = process.argv.slice(2);
const dir = path.resolve('out/stills', salida);
rmSync(dir, {recursive: true, force: true});
mkdirSync(dir, {recursive: true});
const serveUrl = await bundle({entryPoint: path.resolve('src/index.ts')});
const browser = await openBrowser('chrome');
let i = 0;
for (const parte of spec.split(';')) {
  const [id, fs] = parte.split(':');
  const composition = await selectComposition({serveUrl, id, puppeteerInstance: browser});
  for (const frame of fs.split(',').map(Number)) {
    await renderStill({serveUrl, composition, frame, output: `${dir}/${String(i++).padStart(3, '0')}.jpg`, imageFormat: 'jpeg', jpegQuality: 88, scale: 0.5, puppeteerInstance: browser});
  }
}
await browser.close({silent: true});
const cols = Math.min(6, i);
execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-pattern_type', 'glob', '-i', `${dir}/*.jpg`, '-vf', `scale=720:900:force_original_aspect_ratio=decrease,pad=720:900:(ow-iw)/2:(oh-ih)/2,tile=${cols}x${Math.ceil(i / cols)}:padding=6`, '-frames:v', '1', '-q:v', '3', `out/stills/${salida}.jpg`]);
console.log(`out/stills/${salida}.jpg`, i);
