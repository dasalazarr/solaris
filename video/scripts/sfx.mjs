// Diseño de sonido sintetizado aquí mismo: sin bibliotecas ni licencias de terceros.
import {mkdirSync, writeFileSync} from 'node:fs';

mkdirSync(new URL('../public/sfx/', import.meta.url), {recursive: true});

const SR = 44100;
let seed = 7;
const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647) * 2 - 1;

const wav = (name, chans) => {
  const n = chans[0].length;
  const peak = Math.max(...chans.map((c) => c.reduce((m, v) => Math.max(m, Math.abs(v)), 0))) || 1;
  const buf = Buffer.alloc(44 + n * 4);
  buf.write('RIFF', 0); buf.writeUInt32LE(36 + n * 4, 4); buf.write('WAVEfmt ', 8);
  buf.writeUInt32LE(16, 16); buf.writeUInt16LE(1, 20); buf.writeUInt16LE(2, 22);
  buf.writeUInt32LE(SR, 24); buf.writeUInt32LE(SR * 4, 28); buf.writeUInt16LE(4, 32); buf.writeUInt16LE(16, 34);
  buf.write('data', 36); buf.writeUInt32LE(n * 4, 40);
  for (let i = 0; i < n; i++) {
    buf.writeInt16LE(Math.round((chans[0][i] / peak) * 0.89 * 32767), 44 + i * 4);
    buf.writeInt16LE(Math.round((chans[chans.length - 1][i] / peak) * 0.89 * 32767), 46 + i * 4);
  }
  writeFileSync(new URL(`../public/sfx/${name}.wav`, import.meta.url), buf);
};
const make = (s, fn) => { const a = new Float64Array(Math.floor(s * SR)); for (let i = 0; i < a.length; i++) a[i] = fn(i / SR, i / a.length); return a; };

// Tecla: chasquido corto de ruido filtrado.
let lp = 0;
wav('tick', [make(0.05, (t) => { lp += 0.5 * (rnd() - lp); return (rnd() - lp) * Math.exp(-t * 130) * 0.7 + Math.sin(2 * Math.PI * 1900 * t) * Math.exp(-t * 200) * 0.2; })]);

// Clic de interfaz.
wav('click', [make(0.09, (t) => Math.sin(2 * Math.PI * (900 - 3000 * t) * t) * Math.exp(-t * 70))]);

// Barrido: ruido con paso bajo que abre y cierra, y paneo.
for (const [name, dur, top] of [['whoosh', 0.9, 0.42], ['whoosh-soft', 0.6, 0.2]]) {
  let f = 0;
  const m = make(dur, (t, p) => { const c = 0.015 + top * Math.sin(Math.PI * p) ** 2; f += c * (rnd() - f); return f * Math.sin(Math.PI * p) ** 1.5; });
  wav(name, [m.map((v, i) => v * (1 - (i / m.length) * 0.5)), m.map((v, i) => v * (0.5 + (i / m.length) * 0.5))]);
}

// Impacto grave para los títulos.
wav('boom', [make(2.2, (t) => (Math.sin(2 * Math.PI * (38 + 34 * Math.exp(-t * 9)) * t) * Math.exp(-t * 2.3)) + 0.25 * Math.sin(2 * Math.PI * 76 * t) * Math.exp(-t * 3.5))]);

// Campana limpia: confirmación y cita.
const bell = (f0, dec = 3) => make(2.2, (t) => [[1, 1], [2.0, 0.45], [3.01, 0.22], [4.2, 0.09]].reduce((s, [k, a]) => s + a * Math.sin(2 * Math.PI * f0 * k * t) * Math.exp(-t * dec * k), 0) * Math.min(1, t * 400));
const sum = (a, b, off) => { const o = Math.floor(off * SR); const r = Float64Array.from(a); for (let i = 0; i + o < r.length; i++) r[i + o] += b[i]; return r; };
wav('chime', [sum(bell(659.25), bell(987.77), 0.11)]);
wav('ping', [bell(1318.5, 7)]);

// Aviso de hueco: nota grave y apagada. Rechazo: dos notas descendentes.
wav('alert', [make(0.6, (t) => (Math.sin(2 * Math.PI * 196 * t) + 0.35 * Math.sin(2 * Math.PI * 392 * t)) * Math.exp(-t * 8) * Math.min(1, t * 300))]);
wav('deny', [sum(make(0.7, (t) => Math.sin(2 * Math.PI * 233 * t) * Math.exp(-t * 11) * Math.min(1, t * 300)), make(0.7, (t) => Math.sin(2 * Math.PI * 174.6 * t) * Math.exp(-t * 9) * Math.min(1, t * 300)), 0.13)]);

// Fondo: acorde abierto de senos desafinados, respiración lenta y bucle de 40 s.
const D = 40;
const chord = [73.42, 110, 146.83, 220, 277.18, 329.63];
const pad = (det) => make(D, (t) => {
  let s = 0;
  chord.forEach((f, k) => {
    const cycles = Math.round((f + det * (k + 1) * 0.03) * D); // ciclos enteros: el bucle no chasquea
    const breath = 0.6 + 0.4 * Math.sin((2 * Math.PI * (k + 1) * t) / D + k * 1.7);
    s += (Math.sin((2 * Math.PI * cycles * t) / D) * breath) / (1 + k * 0.45);
  });
  return s;
});
wav('pad', [pad(-1), pad(1)]);
