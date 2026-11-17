// La mascota de Solaris. Geometría y valores de `mascota/Isotipo principal-html/Main.dc.html`:
// esfera achatada (1,10 : 1), dos ojos en tres cuartos y un aro que pasa por detrás y por delante.
// Colores de la versión dorada del kit (`mascota/solaris/tokens`).
import React from 'react';

// Una sola versión: la dorada del kit (ADR-0023, ADR-0024). El personaje negro no se usa.
const p = {
  oro: '#F8C94F', aro: '#FFE08A',
  esfera: ['#FFEDB5', '#F6C54C', '#D69A30'], borde: ['#EDB949', '#DDA63A', '#C98A1E'],
  ojos: '#1A1208', brillo: 0.5,
};

export const Mascota: React.FC<{
  size: number;
  /** Apertura vertical de los ojos: 1 abiertos, 0,12 parpadeo. */
  ojos?: number;
  /** Luz extra del aro, de 0 a 1. */
  luz?: number;
  /** Inclinación extra del aro, en grados. */
  aro?: number;
  /** Chispa que recorre el aro: de 0 a 1 por delante, de 1 a 2 por detrás. */
  chispa?: number;
}> = ({size, ojos = 1, luz = 0, aro = 0, chispa}) => {
  const id = 'm-oro';
  const giro = `translate(0 6) rotate(${-16 + aro})`;
  const ojo = (x: number, y: number, rx: number, ry: number) => (
    <g transform={`translate(${x} ${y}) rotate(-25)`}>
      <ellipse rx={rx} ry={ry * ojos} fill={p.ojos} />
    </g>
  );
  const delante = (chispa ?? 0) % 2 < 1;
  const pos = (chispa ?? 0) % 1;
  return (
    <svg width={size} height={size} viewBox="-200 -200 400 400" style={{display: 'block', overflow: 'visible'}}>
      <defs>
        <radialGradient id={`${id}-sph`} cx="35%" cy="30%" r="75%">
          <stop offset="0" stopColor={p.esfera[0]} />
          <stop offset=".55" stopColor={p.esfera[1]} />
          <stop offset="1" stopColor={p.esfera[2]} />
        </radialGradient>
        <radialGradient id={`${id}-glow`}>
          <stop offset=".5" stopColor={p.oro} stopOpacity=".55" />
          <stop offset="1" stopColor={p.oro} stopOpacity="0" />
        </radialGradient>
        <linearGradient id={`${id}-rim`} x1="85%" y1="5%" x2="15%" y2="95%">
          <stop offset="0" stopColor={p.borde[0]} />
          <stop offset=".45" stopColor={p.borde[1]} />
          <stop offset="1" stopColor={p.borde[2]} />
        </linearGradient>
        <filter id={`${id}-blur`} x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="7" /></filter>
              </defs>
      <circle r={175 + luz * 40} fill={`url(#${id}-glow)`} opacity={0.55 + luz * 0.4} />
      <g transform={giro} fill="none" stroke={p.aro} strokeLinecap="round">
        <path d="M -165 0 A 165 38 0 0 1 165 0" strokeWidth="18" opacity={0.21 + luz * 0.4} filter={`url(#${id}-blur)`} />
        <path d="M -165 0 A 165 38 0 0 1 165 0" strokeWidth="9" opacity="0.85" />
        {chispa !== undefined && !delante ? <path d="M 165 0 A 165 38 0 0 0 -165 0" stroke="#fff" strokeWidth="9" pathLength={1} strokeDasharray="0.1 1" strokeDashoffset={-pos * 0.9} opacity=".8" /> : null}
      </g>
      <ellipse cx="-2.5" cy="2.5" rx="119" ry="109" fill={`url(#${id}-rim)`} />
      <ellipse rx="112" ry="102" fill={`url(#${id}-sph)`} />
      <path d="M -84.6 -27.4 Q -73.2 -56.8 -36.6 -73.1" fill="none" stroke="#fff" strokeWidth="15" strokeLinecap="round" opacity={p.brillo} />
      {ojo(22, -24, 10, 21.5)}
      {ojo(71, -37, 8.5, 21)}
      <g transform={giro} fill="none" stroke={p.aro} strokeLinecap="round">
        <path d="M -165 0 A 165 38 0 0 0 165 0" strokeWidth="19.8" opacity={0.45 + luz * 0.5} filter={`url(#${id}-blur)`} />
        <path d="M -165 0 A 165 38 0 0 0 165 0" strokeWidth="9" />
        {chispa !== undefined && delante ? <path d="M -165 0 A 165 38 0 0 0 165 0" stroke="#fff" strokeWidth="9" pathLength={1} strokeDasharray="0.1 1" strokeDashoffset={-pos * 0.9} opacity=".9" /> : null}
      </g>
    </svg>
  );
};
