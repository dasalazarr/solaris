import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {c, f} from './tokens';
import {Entorno, Eyebrow, Fondo, Leyendas, Logo, SolGrande, SUAVE, Sfx, Titular, tw, useFormato, useResorte} from './fx';
import {documentos} from './datos';

export const DUR_APERTURA = 220;
export const Apertura: React.FC = () => {
  const fr = useCurrentFrame();
  const {vertical} = useFormato();
  const sol = tw(fr, 4, 70);
  const sube = tw(fr, 108, 150, 0, 1, SUAVE);
  const size = vertical ? 96 : 104;
  return (
    <AbsoluteFill>
      <Fondo luz={sol * 0.8} y={0.5} />
      <SolGrande p={sol * (1 - sube * 0.75)} y={0.3 - sube * 0.04} r={vertical ? 96 : 84} fuerza={1 - sube * 0.5} />
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', padding: 70}}>
        <div style={{position: 'absolute', left: 70, right: 70, top: vertical ? '50%' : '52%', display: 'flex', justifyContent: 'center'}}>
          <Titular texto="Las empresas no necesitan más chatbots." de={34} a={112} size={size} ancho={vertical ? 900 : 1500} />
        </div>
        <div style={{position: 'absolute', left: 70, right: 70, top: vertical ? '48%' : '50%', display: 'flex', justifyContent: 'center'}}>
          <Titular texto="Necesitan que sus procesos tengan *contrato.*" de={124} size={size + 8} ancho={vertical ? 900 : 1500} />
        </div>
      </AbsoluteFill>
      <Sfx n="boom" at={2} v={0.42} />
      <Sfx n="whoosh-soft" at={112} v={0.2} />
    </AbsoluteFill>
  );
};

const HOJAS = [
  {x: 0.16, y: 0.66, z: -120, r: -9, ry: 16},
  {x: 0.34, y: 0.5, z: -420, r: 5, ry: 10},
  {x: 0.5, y: 0.7, z: 40, r: -2, ry: -3},
  {x: 0.68, y: 0.5, z: -340, r: -6, ry: -9},
  {x: 0.85, y: 0.67, z: -80, r: 8, ry: -18},
];

export const DUR_PROBLEMA = 230;
export const Problema: React.FC = () => {
  const fr = useCurrentFrame();
  const {W, H, vertical} = useFormato();
  const roja = 2; // EV-COMP-03: el certificado caducado
  const marca = tw(fr, 150, 172);
  return (
    <AbsoluteFill>
      <Fondo luz={0.65} />
      <AbsoluteFill style={{perspective: 1500}}>
        {documentos.map((d, i) => {
          const h = HOJAS[i];
          const p = tw(fr, 4 + i * 7, 54 + i * 7);
          const deriva = Math.sin(fr / 48 + i * 1.7) * 14;
          const prof = Math.abs(h.z) / 420;
          const es = d.id === 'EV-COMP-03';
          const sheetW = vertical ? 400 : 390;
          const atenua = es ? 0 : marca;
          const yy = vertical ? 0.37 + h.y * 0.5 : h.y;
          return (
            <div
              key={d.id}
              style={{
                position: 'absolute', left: W * h.x - sheetW / 2, top: H * yy - 220 + deriva, width: sheetW, height: 440, padding: 26, borderRadius: 12, background: c.sheet, color: c.ink,
                opacity: p * (1 - atenua * 0.7), filter: `blur(${prof * 4 + atenua * 3}px)`,
                transform: `translateZ(${h.z + fr * 0.5 + (es ? marca * 40 - h.z * marca : 0)}px) translateY(${(1 - p) * 300 - (es ? marca * (vertical ? 60 : 130) : 0)}px) rotateZ(${h.r * (1 - (es ? marca : 0))}deg) rotateY(${h.ry * (1 - (es ? marca : 0))}deg)`,
                boxShadow: es && marca > 0 ? `0 0 0 ${marca * 3}px ${c.arcillaInk}, 0 0 ${marca * 90}px rgba(140,42,31,.8)` : '0 40px 90px -30px rgba(0,0,0,.8)',
                zIndex: es ? 5 : i === roja ? 4 : 1,
              }}
            >
              <div style={{fontFamily: f.ui, fontSize: 21, fontWeight: 600, lineHeight: 1.25}}>{d.documentTitle}</div>
              <div style={{fontFamily: f.mono, fontSize: 14, color: c.muted, marginTop: 8}}>Pág. {d.page}</div>
              <div style={{fontFamily: f.serif, fontSize: 18, lineHeight: 1.45, marginTop: 16, color: 'rgba(13,15,20,.72)'}}>{d.highlightedQuote.slice(0, 210)}</div>
              {es ? (
                <div style={{position: 'absolute', left: 26, bottom: 24, padding: '8px 14px', borderRadius: 8, background: c.arcilla, color: c.arcillaInk, fontFamily: f.mono, fontSize: 17, fontWeight: 500, opacity: marca}}>Caducó el 12/10/2026</div>
              ) : null}
            </div>
          );
        })}
      </AbsoluteFill>
      <Leyendas
        items={[
          {t: 'Tus reglas están claras.', de: 6, a: 72},
          {t: 'Cruzar cada documento a mano consume horas.', de: 78, a: 146},
          {t: 'Y el hueco aparece cuando llega *la auditoría.*', de: 154, a: 226},
        ]}
      />
      <Entorno />
      <Sfx n="whoosh" at={2} v={0.25} />
      <Sfx n="alert" at={150} v={0.42} />
    </AbsoluteFill>
  );
};

export const DUR_CAPITULO = 74;
export const Capitulo: React.FC<{n: string; palabra: string; titulo: string}> = ({n, palabra, titulo}) => {
  const fr = useCurrentFrame();
  const {vertical} = useFormato();
  const linea = tw(fr, 2, 34);
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
      <Fondo luz={0.7} y={0.5} />
      <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 28, padding: 60, textAlign: 'center'}}>
        <div style={{opacity: tw(fr, 2, 18), transform: `translateY(${tw(fr, 2, 22, 14, 0)}px)`}}>
          <Eyebrow size={vertical ? 36 : 36}>{n} · {palabra}</Eyebrow>
        </div>
        <div style={{width: 280 * linea, height: 2, background: `linear-gradient(90deg, transparent, ${c.solar}, transparent)`}} />
        <Titular texto={titulo} de={8} size={vertical ? 108 : 124} ancho={vertical ? 940 : 1600} />
      </div>
      <Sfx n="boom" at={0} v={0.24} />
      <Sfx n="whoosh-soft" at={0} v={0.18} />
    </AbsoluteFill>
  );
};

export const DUR_CIERRE = 170;
export const Cierre: React.FC = () => {
  const fr = useCurrentFrame();
  const {vertical} = useFormato();
  const s = useResorte(70, 20);
  const sol = tw(fr, 0, 50);
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
      <Fondo luz={0.9} y={0.5} />
      <SolGrande p={sol * 0.28} y={0.42} r={190} fuerza={0.75} />
      <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', padding: 60, textAlign: 'center', transform: 'translateY(-30px)'}}>
        <Titular texto="Procesos *con contrato.*" de={4} size={vertical ? 118 : 136} ancho={vertical ? 940 : 1600} />
        <div style={{marginTop: 22}}>
          <Titular texto="Nada se aprueba a ciegas." de={26} size={vertical ? 50 : 52} peso={400} color="rgba(255,255,255,.76)" paso={2} />
        </div>
        <div style={{marginTop: 66, opacity: s, transform: `translateY(${(1 - s) * 18}px)`, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16}}>
          <Logo size={vertical ? 58 : 54} />
          <div style={{fontFamily: f.mono, fontSize: 21, color: 'rgba(255,255,255,.6)'}}>un producto de Illarium · solaris.dasalazarr.com</div>
        </div>
      </div>
      <div style={{position: 'absolute', bottom: 38, left: 0, right: 0, textAlign: 'center', fontFamily: f.mono, fontSize: 18, color: 'rgba(255,255,255,.62)', opacity: tw(fr, 60, 84)}}>Caso ficticio con datos de muestra</div>
      <Sfx n="boom" at={0} v={0.32} />
      <Sfx n="chime" at={70} v={0.26} />
    </AbsoluteFill>
  );
};
export {Entorno};
