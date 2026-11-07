import React from 'react';
import {c, f} from './tokens';
import {VENTANA} from './fx';

// El mismo menú que product/components/workspace/Shell.tsx.
const NAV = ['Preguntar', 'Explorar', 'Huecos', 'Revisar'];
const NAV_SECUNDARIO = ['Contrato', 'Registro'];
const ICONO: Record<string, React.ReactNode> = {
  Preguntar: <path d="M3 4h14v10H8l-5 4z" />,
  Explorar: <><ellipse cx="10" cy="5" rx="7" ry="3" /><path d="M3 5v10c0 1.7 3 3 7 3s7-1.3 7-3V5M3 10c0 1.7 3 3 7 3s7-1.3 7-3" /></>,
  Huecos: <path d="M10 3l8 14H2zM10 8v4M10 14.6v.1" />,
  Revisar: <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v12a1 1 0 01-1 1H4a1 1 0 01-1-1zM7 10l2 2 4-4" />,
  Contrato: <path d="M10 5C8.5 3.8 6 3 3 3v12c3 0 5.5.8 7 2 1.5-1.2 4-2 7-2V3c-3 0-5.5.8-7 2zM10 5v12" />,
  Registro: <path d="M5 2h7l4 4v12H5zM12 2v4h4M10.5 9.5v3l2 1" />,
};
export const CX = 196;
export const CY = 48;
export const CW = VENTANA.w - CX;
export const CH = VENTANA.h - CY;

/** Reproduce el marco de `landing/src/components/ProductWindow.tsx`, a escala de vídeo. */
export const Ventana: React.FC<{activo: string; children: React.ReactNode; extra?: React.ReactNode; cuenta?: React.ReactNode}> = ({activo, children, extra, cuenta}) => (
  <div style={{position: 'absolute', inset: 0, borderRadius: 22, background: c.sheet, color: c.ink, fontFamily: f.ui, boxShadow: '0 0 0 1px rgba(255,255,255,.14), 0 60px 160px -40px rgba(242,181,68,.34), 0 40px 90px -20px rgba(0,0,0,.7)'}}>
    <div style={{position: 'absolute', inset: 0, borderRadius: 22, overflow: 'hidden'}}>
      <div style={{position: 'absolute', left: 0, right: 0, top: 0, height: CY, background: '#f1efe9', borderBottom: `1px solid ${c.line}`, display: 'flex', alignItems: 'center', padding: '0 20px'}}>
        <div style={{display: 'flex', gap: 8}}>{[0, 1, 2].map((i) => <span key={i} style={{width: 13, height: 13, borderRadius: 99, background: 'rgba(13,15,20,.15)'}} />)}</div>
        <div style={{margin: '0 auto', padding: '5px 16px', borderRadius: 8, background: 'rgba(255,255,255,.7)', fontFamily: f.mono, fontSize: 15, color: c.muted}}>solaris · caso de muestra · Proceso de compra</div>
        <span style={{fontFamily: f.mono, fontSize: 14, color: c.muted}}>Demo en la nube · datos de muestra</span>
      </div>
      <div style={{position: 'absolute', left: 0, top: CY, bottom: 0, width: CX, background: '#f7f6f2', borderRight: `1px solid ${c.line}`, padding: 14, display: 'flex', flexDirection: 'column', gap: 4}}>
        <div style={{display: 'flex', alignItems: 'center', gap: 10, padding: '8px 10px 18px'}}>
          <span style={{width: 18, height: 18, borderRadius: 99, background: c.solar}} />
          <span style={{fontSize: 19, fontWeight: 600}}>Solaris</span>
        </div>
        {NAV.map((n) => (
          <div key={n} style={{display: 'flex', alignItems: 'center', gap: 10, padding: '10px', borderRadius: 9, fontSize: 18, fontWeight: n === activo ? 600 : 400, color: n === activo ? c.ink : c.muted, background: n === activo ? '#fff' : 'transparent', boxShadow: n === activo ? '0 1px 3px rgba(13,15,20,.1), 0 0 0 1px rgba(13,15,20,.06)' : undefined}}>
            <svg width="19" height="19" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" strokeLinecap="round">{ICONO[n]}</svg>
            <span style={{flex: 1}}>{n}</span>
            {n === 'Huecos' ? cuenta : null}
          </div>
        ))}
        <div style={{margin: '8px 0', borderTop: `1px solid ${c.line}`}} />
        {NAV_SECUNDARIO.map((n) => (
          <div key={n} style={{display: 'flex', alignItems: 'center', gap: 10, padding: '10px', fontSize: 18, color: c.muted}}>
            <svg width="19" height="19" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" strokeLinecap="round">{ICONO[n]}</svg>
            <span>{n}</span>
          </div>
        ))}
        <div style={{marginTop: 'auto', padding: '8px 10px', borderRadius: 8, background: c.salvia, color: c.salviaInk, fontFamily: f.mono, fontSize: 14}}>Proceso de compra · 5 docs</div>
      </div>
      <div style={{position: 'absolute', left: CX, top: CY, right: 0, bottom: 0, overflow: 'hidden'}}>{children}</div>
      {extra}
    </div>
  </div>
);

export const Chip: React.FC<{n: number | string; activo?: boolean; style?: React.CSSProperties}> = ({n, activo, style}) => (
  <span style={{display: 'inline-flex', alignItems: 'center', justifyContent: 'center', minWidth: 28, height: 28, padding: '0 6px', borderRadius: 7, fontFamily: f.mono, fontSize: 16, fontWeight: 500, verticalAlign: 3, background: activo ? c.solar : c.solarSoft, color: activo ? c.ink : c.solarInk, ...style}}>{n}</span>
);

export const Estado: React.FC<{tono: 'solar' | 'arcilla' | 'salvia' | 'niebla' | 'gris'; children: React.ReactNode; size?: number; style?: React.CSSProperties}> = ({tono, children, size = 16, style}) => {
  const m = {
    solar: [c.solarSoft, c.solarInk], arcilla: [c.arcilla, c.arcillaInk], salvia: [c.salvia, c.salviaInk], niebla: [c.niebla, c.nieblaInk], gris: ['#eceae4', 'rgba(13,15,20,.68)'],
  }[tono];
  return <span style={{display: 'inline-block', padding: '5px 12px', borderRadius: 8, fontFamily: f.mono, fontSize: size, fontWeight: 500, background: m[0], color: m[1], ...style}}>{children}</span>;
};
