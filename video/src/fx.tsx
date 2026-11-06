import React from 'react';
import {AbsoluteFill, Easing, Sequence, interpolate, random, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {Audio} from '@remotion/media';
import {c, f} from './tokens';

export const SALIDA = Easing.bezier(0.16, 1, 0.3, 1);
export const SUAVE = Easing.bezier(0.65, 0, 0.35, 1);

export const tw = (fr: number, a: number, b: number, de = 0, hasta = 1, easing = SALIDA) =>
  interpolate(fr, [a, b], [de, hasta], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing});

export const useFormato = () => {
  const {width, height} = useVideoConfig();
  return {W: width, H: height, vertical: height > width};
};

export const useResorte = (desde: number, damping = 18, mass = 0.8) => {
  const fr = useCurrentFrame();
  const {fps} = useVideoConfig();
  return spring({frame: fr - desde, fps, config: {damping, mass, stiffness: 120}});
};

// ---------- Sonido ----------
export const Sfx: React.FC<{n: string; at: number; v?: number}> = ({n, at, v = 0.5}) => (
  <Sequence from={at} layout="none" durationInFrames={90} name={`sfx ${n}`}>
    <Audio src={staticFile(`sfx/${n}.wav`)} volume={v} />
  </Sequence>
);
export const Teclas: React.FC<{de: number; a: number}> = ({de, a}) => (
  <>
    {Array.from({length: Math.max(0, Math.floor((a - de) / 2))}).map((_, i) =>
      random(`tecla${de}-${i}`) > 0.28 ? (
        <Sfx key={i} n="tick" at={de + i * 2} v={0.1 + random(`vol${de}-${i}`) * 0.1} />
      ) : null,
    )}
  </>
);
export const Fondo_Musical: React.FC<{dur: number; v?: number}> = ({dur, v = 0.16}) => (
  <Audio
    src={staticFile('sfx/pad.wav')}
    loop
    volume={(fr) => interpolate(fr, [0, 45, dur - 60, dur], [0, v, v, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})}
  />
);

// ---------- Fondo: tinta, luz solar lenta, grano y viñeta ----------
const RUIDO = `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='256' height='256'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 0 0 0 .55 0'/%3E%3C/filter%3E%3Crect width='256' height='256' filter='url(%23n)'/%3E%3C/svg%3E")`;

export const Fondo: React.FC<{luz?: number; y?: number}> = ({luz = 1, y = 0.62}) => {
  const fr = useCurrentFrame();
  const {W, H} = useFormato();
  const dx = Math.sin(fr / 90) * W * 0.04;
  const dy = Math.cos(fr / 120) * H * 0.02;
  return (
    <AbsoluteFill style={{background: c.ink}}>
      <AbsoluteFill
        style={{
          opacity: luz,
          background: `radial-gradient(${W * 0.62}px ${H * 0.52}px at ${W / 2 + dx}px ${H * y + dy}px, rgba(242,181,68,.20), rgba(242,181,68,.05) 52%, transparent 74%)`,
        }}
      />
      <AbsoluteFill
        style={{
          opacity: luz * 0.8,
          background: `radial-gradient(${W * 0.45}px ${H * 0.35}px at ${W * 0.12 - dx}px ${H * 0.05}px, rgba(75,58,168,.16), transparent 70%)`,
        }}
      />
    </AbsoluteFill>
  );
};
export const Grano: React.FC = () => {
  const fr = useCurrentFrame();
  const paso = Math.floor(fr / 2);
  return (
    <AbsoluteFill
      style={{
        backgroundImage: RUIDO,
        backgroundPosition: `${Math.floor(random(`gx${paso}`) * 256)}px ${Math.floor(random(`gy${paso}`) * 256)}px`,
        opacity: 0.055,
        mixBlendMode: 'overlay',
        pointerEvents: 'none',
      }}
    />
  );
};
export const Vineta: React.FC = () => (
  <AbsoluteFill style={{background: 'radial-gradient(ellipse at 50% 50%, transparent 72%, rgba(0,0,0,.28) 100%)', pointerEvents: 'none'}} />
);

// ---------- Tipografía de presentación ----------
export const Titular: React.FC<{
  texto: string; de: number; a?: number; size?: number; ancho?: number; paso?: number; color?: string; align?: 'center' | 'left'; peso?: number;
}> = ({texto, de, a, size = 96, ancho, paso = 3, color = '#fff', align = 'center', peso = 600}) => {
  const fr = useCurrentFrame();
  let cursiva = false;
  const palabras = texto.split(' ').map((p) => {
    const abre = p.startsWith('*');
    if (abre) cursiva = true;
    const it = cursiva;
    if (p.replace(/[.,]$/, '').endsWith('*')) cursiva = false;
    return {t: p.replace(/\*/g, ''), it};
  });
  const salida = a === undefined ? 0 : tw(fr, a - 14, a, 0, 1, SUAVE);
  return (
    <div
      style={{
        fontFamily: f.ui, fontWeight: peso, fontSize: size, lineHeight: 1.08, letterSpacing: '-0.035em', color,
        textAlign: align, maxWidth: ancho, opacity: 1 - salida,
        filter: salida > 0 ? `blur(${salida * 16}px)` : undefined,
        transform: `translateY(${-salida * 22}px)`,
      }}
    >
      {palabras.map((w, i) => {
        const p = tw(fr, de + i * paso, de + i * paso + 26);
        return (
          <span
            key={i}
            style={{
              display: 'inline-block', marginRight: '0.26em', opacity: p,
              filter: p < 1 ? `blur(${(1 - p) * 14}px)` : undefined,
              transform: `translateY(${(1 - p) * size * 0.34}px) scale(${0.97 + p * 0.03})`,
              ...(w.it
                ? {
                    fontFamily: f.serif, fontStyle: 'italic', fontWeight: 400, letterSpacing: '-0.02em', paddingRight: '.06em',
                    background: `linear-gradient(100deg, ${c.solarHover}, ${c.solar} 55%, #ffdf9e)`,
                    WebkitBackgroundClip: 'text', backgroundClip: 'text', color: 'transparent',
                  }
                : {}),
            }}
          >
            {w.t}
          </span>
        );
      })}
    </div>
  );
};

/** Leyenda de cada plano: arriba, con velo para que se lea sobre la ventana. */
export const Leyendas: React.FC<{items: {t: string; de: number; a: number}[]}> = ({items}) => {
  const fr = useCurrentFrame();
  const {H, vertical} = useFormato();
  const activa = items.some((x) => fr >= x.de - 6 && fr <= x.a + 4);
  const velo = activa ? 1 : 0;
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <div style={{position: 'absolute', inset: 0, height: H * (vertical ? 0.25 : 0.25), opacity: velo, background: `linear-gradient(${c.ink} 62%, rgba(13,15,20,.7) 82%, transparent)`}} />
      {items.map((x, i) =>
        fr >= x.de - 2 && fr <= x.a + 2 ? (
          <div key={i} style={{position: 'absolute', top: vertical ? 74 : 62, left: 0, right: 0, display: 'flex', justifyContent: 'center', padding: '0 64px'}}>
            <Titular texto={x.t} de={x.de} a={x.a} size={vertical ? 66 : 64} ancho={vertical ? 960 : 1780} paso={2} />
          </div>
        ) : null,
      )}
    </AbsoluteFill>
  );
};

export const Eyebrow: React.FC<{children: React.ReactNode; color?: string; size?: number}> = ({children, color = c.solar, size = 26}) => (
  <div style={{fontFamily: f.mono, fontSize: size, fontWeight: 500, letterSpacing: '.14em', textTransform: 'uppercase', color}}>{children}</div>
);

export const Entorno: React.FC = () => {
  const {vertical} = useFormato();
  return (
    <div style={{position: 'absolute', left: vertical ? 36 : 44, bottom: vertical ? 36 : 36, display: 'flex', alignItems: 'center', gap: 12, padding: '10px 18px', borderRadius: 999, background: 'rgba(21,24,33,.86)', border: '1px solid rgba(255,255,255,.14)', fontFamily: f.mono, fontSize: 20, color: 'rgba(255,255,255,.86)'}}>
      <span style={{width: 10, height: 10, borderRadius: 99, background: c.solar}} />
      Demo en la nube · datos de muestra
    </div>
  );
};

// ---------- Cámara virtual sobre la ventana de producto ----------
export const VENTANA = {w: 1400, h: 860};
export type Clave = {f: number; x: number; y: number; z: number; zv?: number; rx?: number; ry?: number; rz?: number};

export const Camara: React.FC<{k: Clave[]; children: React.ReactNode; centro?: number}> = ({k, children, centro}) => {
  const fr = useCurrentFrame();
  const {W, H, vertical} = useFormato();
  const fs = k.map((x) => x.f);
  const v = (g: (x: Clave) => number) => (k.length < 2 ? g(k[0]) : interpolate(fr, fs, k.map(g), {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: SUAVE}));
  const ajuste = vertical ? (W * 0.94) / VENTANA.w : (W * 0.74) / VENTANA.w;
  const cy = centro ?? (vertical ? 0.61 : 0.62);
  const deriva = 1 + Math.sin(fr / 70) * 0.004;
  return (
    <AbsoluteFill style={{perspective: 2600, perspectiveOrigin: `50% ${cy * 100}%`}}>
      <div
        style={{
          position: 'absolute', left: 0, top: 0, width: VENTANA.w, height: VENTANA.h, transformOrigin: '0 0',
          transform: `translate(${W / 2}px, ${H * cy}px) rotateX(${v((x) => x.rx ?? 0)}deg) rotateY(${v((x) => x.ry ?? 0)}deg) rotateZ(${v((x) => x.rz ?? 0)}deg) scale(${v((x) => (vertical ? x.zv ?? x.z : x.z)) * ajuste * deriva}) translate(${-v((x) => x.x)}px, ${-v((x) => x.y)}px)`,
        }}
      >
        {children}
      </div>
    </AbsoluteFill>
  );
};

/** Barrido de luz sobre el cristal de la ventana. */
export const Destello: React.FC<{de: number; dur?: number; fuerza?: number}> = ({de, dur = 46, fuerza = 0.5}) => {
  const fr = useCurrentFrame();
  if (fr < de || fr > de + dur) return null;
  const p = tw(fr, de, de + dur, -40, 140, SUAVE);
  return (
    <div style={{position: 'absolute', inset: 0, pointerEvents: 'none', mixBlendMode: 'screen', background: `linear-gradient(112deg, transparent ${p - 16}%, rgba(255,240,205,${fuerza}) ${p}%, transparent ${p + 16}%)`}} />
  );
};

/** Profundidad de campo: lo que no importa se aleja. */
export const Foco: React.FC<{d: number; style?: React.CSSProperties; children: React.ReactNode}> = ({d, style, children}) => (
  <div style={{...style, opacity: 1 - d * 0.62, filter: d > 0.01 ? `blur(${d * 3.5}px) saturate(${1 - d * 0.4})` : undefined}}>{children}</div>
);

// ---------- Cursor con clics ----------
export const Cursor: React.FC<{k: {f: number; x: number; y: number}[]; clics?: number[]; de?: number; a?: number; escala?: number}> = ({k, clics = [], de = 0, a = 1e6, escala = 1}) => {
  const fr = useCurrentFrame();
  const fs = k.map((x) => x.f);
  const x = interpolate(fr, fs, k.map((p) => p.x), {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: SUAVE});
  const y = interpolate(fr, fs, k.map((p) => p.y), {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: SUAVE});
  const o = Math.min(tw(fr, de, de + 12), 1 - tw(fr, a - 10, a));
  if (o <= 0) return null;
  const pulsa = clics.reduce((m, cf) => Math.max(m, fr >= cf - 3 && fr <= cf + 5 ? 1 - Math.abs(fr - cf) / 5 : 0), 0);
  return (
    <div style={{position: 'absolute', left: 0, top: 0, width: 0, height: 0, opacity: o, zIndex: 40}}>
      {clics.map((cf) => {
        if (fr < cf || fr > cf + 26) return null;
        const p = tw(fr, cf, cf + 26);
        return <div key={cf} style={{position: 'absolute', left: x - 40, top: y - 40, width: 80, height: 80, borderRadius: 99, border: `3px solid ${c.solar}`, opacity: 1 - p, transform: `scale(${0.2 + p * 1.3})`}} />;
      })}
      <svg width="38" height="46" viewBox="0 0 19 23" style={{position: 'absolute', left: x, top: y, transformOrigin: '0 0', transform: `scale(${escala * (1 - pulsa * 0.16)})`, filter: 'drop-shadow(0 4px 8px rgba(0,0,0,.4))'}}>
        <path d="M1 1 L1 18 L5.6 14 L8.7 21 L12 19.6 L8.9 12.8 L15 12.5 Z" fill="#0d0f14" stroke="#fff" strokeWidth="1.5" strokeLinejoin="round" />
      </svg>
    </div>
  );
};

/** Haz de luz entre una cita y su fuente. */
export const Haz: React.FC<{de: number; dur?: number; a: [number, number]; b: [number, number]; curva?: number; hasta?: number}> = ({de, dur = 26, a, b, curva = -120, hasta = 1e6}) => {
  const fr = useCurrentFrame();
  if (fr < de) return null;
  const p = tw(fr, de, de + dur, 0, 1, SUAVE);
  const fuera = 1 - tw(fr, hasta - 16, hasta);
  const mx = (a[0] + b[0]) / 2;
  const my = (a[1] + b[1]) / 2 + curva;
  const d = `M${a[0]} ${a[1]} Q${mx} ${my} ${b[0]} ${b[1]}`;
  const q = (s: number) => [(1 - s) ** 2 * a[0] + 2 * (1 - s) * s * mx + s ** 2 * b[0], (1 - s) ** 2 * a[1] + 2 * (1 - s) * s * my + s ** 2 * b[1]];
  const [px, py] = q(p);
  return (
    <svg width={VENTANA.w} height={VENTANA.h} style={{position: 'absolute', inset: 0, zIndex: 30, overflow: 'visible', pointerEvents: 'none', opacity: fuera}}>
      <defs>
        <filter id="halo" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="7" /></filter>
      </defs>
      <path d={d} fill="none" stroke={c.solar} strokeWidth="9" pathLength={1} strokeDasharray={`${p} 1`} opacity=".45" filter="url(#halo)" />
      <path d={d} fill="none" stroke={c.solar} strokeWidth="2.5" pathLength={1} strokeDasharray={`${p} 1`} />
      <circle cx={px} cy={py} r={p < 1 ? 7 : 5} fill="#fff4d6" />
      <circle cx={px} cy={py} r="18" fill={c.solar} opacity=".55" filter="url(#halo)" />
    </svg>
  );
};

// ---------- Marca ----------
export const Logo: React.FC<{size?: number; color?: string}> = ({size = 48, color = '#fff'}) => (
  <div style={{display: 'flex', alignItems: 'center', gap: size * 0.3}}>
    <svg width={size} height={size} viewBox="0 0 26 26">
      <circle cx="13" cy="13" r="12" fill="none" stroke={c.solar} strokeOpacity=".55" strokeWidth="1" />
      <circle cx="13" cy="13" r="7.5" fill={c.solar} />
    </svg>
    <span style={{fontFamily: f.ui, fontWeight: 600, fontSize: size * 0.95, letterSpacing: '-0.02em', color}}>Solaris</span>
  </div>
);

/** El sol del logo a escala de escenario: anillo, núcleo, halo y destello anamórfico. */
export const SolGrande: React.FC<{p: number; x?: number; y?: number; r?: number; fuerza?: number}> = ({p, x = 0.5, y = 0.5, r = 120, fuerza = 1}) => {
  const {W, H} = useFormato();
  const fr = useCurrentFrame();
  const respira = 1 + Math.sin(fr / 26) * 0.012;
  const cx = W * x;
  const cy = H * y;
  const anillo = r * 1.6 * (0.6 + p * 0.4);
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <div style={{position: 'absolute', left: cx - W, top: cy - W, width: W * 2, height: W * 2, opacity: p * 0.8 * fuerza, background: `radial-gradient(circle, rgba(242,181,68,.42), rgba(242,181,68,.12) 16%, transparent 40%)`, mixBlendMode: 'screen'}} />
      <div style={{position: 'absolute', left: cx - W * 0.6, top: cy - 3, width: W * 1.2, height: 6, opacity: p * 0.6 * fuerza, background: 'linear-gradient(90deg, transparent, rgba(255,226,165,.85), transparent)', filter: 'blur(3px)', transform: `scaleX(${0.3 + p * 0.7})`}} />
      <div style={{position: 'absolute', left: cx - anillo, top: cy - anillo, width: anillo * 2, height: anillo * 2, borderRadius: '50%', border: `2px solid rgba(242,181,68,${0.55 * p})`, transform: `scale(${respira})`}} />
      <div style={{position: 'absolute', left: cx - r, top: cy - r, width: r * 2, height: r * 2, borderRadius: '50%', opacity: p, transform: `scale(${(0.2 + p * 0.8) * respira})`, background: `radial-gradient(circle at 42% 38%, #ffe6ad, ${c.solar} 58%, #e29f28)`, boxShadow: `0 0 ${r * 0.9}px rgba(242,181,68,.75), 0 0 ${r * 2.4}px rgba(242,181,68,.35)`}} />
    </AbsoluteFill>
  );
};

/** Entrada y salida de cada escena: fundido con desenfoque y un leve empuje de cámara. */
export const Fundido: React.FC<{dur: number; children: React.ReactNode; entrada?: number; salida?: number}> = ({dur, children, entrada = 14, salida = 14}) => {
  const fr = useCurrentFrame();
  const a = entrada ? tw(fr, 0, entrada, 0, 1, SUAVE) : 1;
  const b = salida ? 1 - tw(fr, dur - salida, dur, 0, 1, SUAVE) : 1;
  const o = Math.min(a, b);
  return (
    <AbsoluteFill style={{opacity: o, filter: o < 1 ? `blur(${(1 - o) * 12}px)` : undefined, transform: `scale(${1 + (1 - b) * 0.035 - (1 - a) * 0.02})`}}>
      {children}
    </AbsoluteFill>
  );
};

/** Texto que entra palabra a palabra, para las respuestas dentro de la interfaz. */
export const Aparece: React.FC<{texto: string; de: number; paso?: number; style?: React.CSSProperties}> = ({texto, de, paso = 1, style}) => {
  const fr = useCurrentFrame();
  return (
    <span style={style}>
      {texto.split(' ').map((w, i) => {
        const p = tw(fr, de + i * paso, de + i * paso + 12);
        return <span key={i} style={{opacity: p, filter: p < 1 ? `blur(${(1 - p) * 5}px)` : undefined}}>{w} </span>;
      })}
    </span>
  );
};

/** Firma de marca: la barra solar de 0,42 em bajo el fragmento citado, barrida palabra a palabra. */
export const Evidencia: React.FC<{texto: string; de: number; dur?: number; style?: React.CSSProperties}> = ({texto, de, dur = 50, style}) => {
  const fr = useCurrentFrame();
  const w = texto.split(' ');
  return (
    <span style={style}>
      {w.map((t, i) => {
        const a = de + (i / w.length) * dur;
        const p = tw(fr, a, a + 6, 0, 1, Easing.linear);
        return (
          <span key={i} style={{backgroundImage: `linear-gradient(${c.solar}, ${c.solar})`, backgroundRepeat: 'no-repeat', backgroundPosition: '0 88%', backgroundSize: `${p * 100}% .42em`}}>
            {t}{' '}
          </span>
        );
      })}
    </span>
  );
};
