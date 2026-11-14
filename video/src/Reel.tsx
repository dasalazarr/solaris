// Reel comercial «Alta de cliente»: para consultoras e implantadores. 9:16 principal, 16:9 aparte.
import React, {useLayoutEffect, useRef, useState} from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';
import {c, f} from './tokens';
import {Camara, Cursor, Destello, Entorno, Eyebrow, Fondo, Foco, Leyendas, Logo, SUAVE, Sfx, SolGrande, Teclas, Titular, tw, useFormato, useResorte} from './fx';
import {CX, CY, Estado, Ventana} from './ventana';
import {Mascota} from './mascota';
import {bloqueoComercial, casos, definicion, hashVersion, logicaCredito, matriz, reglaCredito, resumenCaso, revisionCredito} from './datos-alta';

const RUTA = 'solaris · Alta de cliente · casos de prueba';
const PIE = `Alta de cliente · ${casos.length} casos`;
const ROTULO: Record<string, string> = {conforme: 'Conforme', incumplida: 'Incumplida', requiere_aprobacion: 'Requiere aprobación', no_aplica: 'No evaluada'};
const tono = (e: string) => (e === 'conforme' ? 'salvia' : e === 'incumplida' ? 'arcilla' : e === 'requiere_aprobacion' ? 'solar' : 'gris') as 'salvia' | 'arcilla' | 'solar' | 'gris';

// ---------------- 1 · Gancho ----------------
export const DUR_GANCHO = 100;
export const Gancho: React.FC = () => {
  const {reel} = useFormato();
  const size = reel ? 132 : 128;
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
      <Fondo luz={0.55} y={0.5} />
      <div style={{position: 'absolute', left: 60, right: 60, top: reel ? '40%' : '40%', display: 'flex', justifyContent: 'center'}}>
        <Titular texto="Implantas el CRM." de={2} a={40} size={size} ancho={reel ? 900 : 1600} paso={3} />
      </div>
      <div style={{position: 'absolute', left: 60, right: 60, top: reel ? '36%' : '34%', display: 'flex', justifyContent: 'center'}}>
        <Titular texto="Las reglas del cliente siguen *en un PDF.*" de={42} size={reel ? 112 : 112} ancho={reel ? 920 : 1600} paso={3} />
      </div>
      <Sfx n="boom" at={0} v={0.5} />
      <Sfx n="whoosh-soft" at={40} v={0.25} />
    </AbsoluteFill>
  );
};

// ---------------- 2 · De la frase al formulario ----------------
type Caja = {x: number; y: number; w: number; h: number};
/** Mide un elemento respecto al lienzo, sin transformaciones: offsetLeft/Top acumulados. */
const medir = (el: HTMLElement | null, raiz: HTMLElement | null): Caja | null => {
  if (!el || !raiz) return null;
  let x = 0;
  let y = 0;
  let n: HTMLElement | null = el;
  while (n && n !== raiz) {
    x += n.offsetLeft;
    y += n.offsetTop;
    n = n.offsetParent as HTMLElement | null;
  }
  return {x, y, w: el.offsetWidth, h: el.offsetHeight};
};

const VUELOS = [
  {palabra: 'límite de crédito', destino: 'Límite de crédito', de: 74},
  {palabra: '20.000\u00a0€', destino: '20.000', de: 98},
  {palabra: 'Riesgos', destino: 'Riesgos', de: 122},
];
export const DUR_REGLA = 250;
export const Regla: React.FC = () => {
  const fr = useCurrentFrame();
  const {W, H, reel} = useFormato();
  const raiz = useRef<HTMLDivElement>(null);
  const origen = useRef<(HTMLSpanElement | null)[]>([]);
  const destino = useRef<(HTMLSpanElement | null)[]>([]);
  const [cajas, setCajas] = useState<{o: (Caja | null)[]; d: (Caja | null)[]}>({o: [], d: []});
  useLayoutEffect(() => {
    const o = origen.current.map((el) => medir(el, raiz.current));
    const d = destino.current.map((el) => medir(el, raiz.current));
    const cambia = JSON.stringify({o, d}) !== JSON.stringify(cajas);
    if (cambia) setCajas({o, d});
  });
  const escala = reel ? (W * 0.9) / 1000 : Math.min(W * 0.62, H - 330) / 1000;
  const frase = reglaCredito.description.replace('20.000 €', '20.000\u00a0€');
  const partes = frase.split(/(límite de crédito|20\.000\u00a0€|Riesgos)/);
  const entra = tw(fr, 4, 30);
  const form = tw(fr, 40, 66);
  const motor = tw(fr, 176, 200);
  const llegado = (i: number) => fr >= VUELOS[i].de + 22;
  const select = fr >= 146;
  const op = fr >= 112;
  const Ranura: React.FC<{i?: number; texto: string; lleno: boolean; ancho?: number; mono?: boolean; color?: 'lavanda' | 'solar'}> = ({i, texto, lleno, ancho, mono, color = 'lavanda'}) => (
    <span
      ref={i === undefined ? undefined : (el) => { destino.current[i] = el; }}
      style={{display: 'inline-flex', alignItems: 'center', minWidth: ancho, height: 62, padding: '0 20px', borderRadius: 12, fontFamily: mono ? f.mono : f.ui, fontSize: 30, fontWeight: 600,
        border: lleno ? 'none' : '2px dashed rgba(13,15,20,.22)', background: lleno ? (color === 'solar' ? c.solarSoft : c.lavanda) : 'transparent', color: lleno ? (color === 'solar' ? c.solarInk : c.lavandaInk) : 'transparent'}}
    >
      {texto}
    </span>
  );
  const Fila: React.FC<{k: string; children: React.ReactNode}> = ({k, children}) => (
    <div style={{display: 'flex', alignItems: 'center', gap: 16, minHeight: 78}}>
      <span style={{width: 250, fontSize: 26, color: c.muted}}>{k}</span>
      <div style={{display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap'}}>{children}</div>
    </div>
  );
  return (
    <AbsoluteFill>
      <Fondo luz={0.8} />
      <div style={{position: 'absolute', left: W / 2 - 500 * escala, top: reel ? 475 : H * 0.6 - 500 * escala, width: 1000, height: 1000, transform: `scale(${escala})`, transformOrigin: '0 0'}}>
        <div ref={raiz} style={{position: 'relative', width: 1000, height: 1000}}>
          <div style={{position: 'absolute', left: 0, right: 0, top: 0, padding: '34px 40px', borderRadius: 26, background: c.ink2, border: '1px solid rgba(255,255,255,.12)', opacity: entra, transform: `translateY(${(1 - entra) * 40}px)`}}>
            <Eyebrow size={22} color="rgba(255,255,255,.6)">Lo que pide tu cliente</Eyebrow>
            <div style={{fontFamily: f.serif, fontSize: 54, lineHeight: 1.3, color: '#fff', marginTop: 16}}>
              «
              {partes.map((p, i) => {
                const v = VUELOS.findIndex((x) => x.palabra === p);
                if (v < 0) return <span key={i}>{p}</span>;
                const luz = tw(fr, VUELOS[v].de - 18, VUELOS[v].de);
                return (
                  <span key={i} ref={(el) => { origen.current[v] = el; }} style={{backgroundImage: `linear-gradient(${c.solar}, ${c.solar})`, backgroundRepeat: 'no-repeat', backgroundPosition: '0 92%', backgroundSize: `${luz * 100}% .2em`, color: luz > 0.5 ? '#fff4d6' : '#fff'}}>
                    {p}
                  </span>
                );
              })}
              »
            </div>
          </div>
          <div style={{position: 'absolute', left: 0, right: 0, top: 380, padding: '30px 40px', borderRadius: 26, background: c.sheet, color: c.ink, opacity: form, transform: `translateY(${(1 - form) * 50}px)`, boxShadow: '0 50px 120px -40px rgba(242,181,68,.35)'}}>
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 10}}>
              <span style={{fontSize: 30, fontWeight: 600}}>Regla {reglaCredito.code} · {reglaCredito.name}</span>
              <span style={{fontFamily: f.mono, fontSize: 20, color: c.muted}}>Contrato</span>
            </div>
            <Fila k="Se aplica a"><Ranura texto={definicion.objectTypes[0].label} lleno /></Fila>
            <Fila k="Exige">
              <Ranura i={0} texto="Límite de crédito" lleno={llegado(0)} ancho={300} />
              <Ranura texto="≤" lleno={op} ancho={62} mono color="solar" />
              <Ranura i={1} texto="20.000" lleno={llegado(1)} ancho={150} mono />
            </Fila>
            <Fila k="Si no se cumple"><Ranura texto="Requiere aprobación" lleno={select} ancho={320} color="solar" /></Fila>
            <Fila k="Decide"><Ranura i={2} texto={reglaCredito.approverRole} lleno={llegado(2)} ancho={170} /></Fila>
          </div>
          <div style={{position: 'absolute', left: 0, right: 0, top: 850, padding: '18px 26px', borderRadius: 16, background: '#05070a', border: `1px solid rgba(242,181,68,.35)`, opacity: motor, transform: `translateY(${(1 - motor) * 20}px)`}}>
            <div style={{fontFamily: f.mono, fontSize: 21, color: c.solar, lineHeight: 1.4}}>{logicaCredito.slice(0, Math.floor(tw(fr, 180, 214, 0, logicaCredito.length, (x) => x)))}</div>
          </div>
          {VUELOS.map((v, i) => {
            const o = cajas.o[i];
            const d = cajas.d[i];
            if (!o || !d || fr < v.de || fr > v.de + 24) return null;
            const p = tw(fr, v.de, v.de + 22, 0, 1, SUAVE);
            const x = o.x + (d.x - o.x) * p;
            const y = o.y + (d.y - o.y) * p - Math.sin(Math.PI * p) * 120;
            const w = o.w + (d.w - o.w) * p;
            const h = o.h + (d.h - o.h) * p;
            return (
              <div key={i} style={{position: 'absolute', left: x, top: y, width: w, height: h, borderRadius: 12, display: 'grid', placeItems: 'center', background: c.solar, color: c.ink, fontFamily: f.ui, fontWeight: 600, fontSize: 30 + (1 - p) * 10, whiteSpace: 'nowrap', overflow: 'hidden', boxShadow: `0 0 ${50 * Math.sin(Math.PI * p) + 10}px rgba(242,181,68,.9)`, transform: `scale(${1 + Math.sin(Math.PI * p) * 0.12})`, zIndex: 10}}>
                {v.palabra}
              </div>
            );
          })}
        </div>
      </div>
      <Entorno />
      <Leyendas
        items={[
          {t: 'Escribe la regla en un formulario. *Sin programar.*', de: 10, a: 166},
          {t: 'Así la lee *el motor.*', de: 176, a: 246},
        ]}
      />
      {VUELOS.map((v) => <Sfx key={v.de} n="whoosh-soft" at={v.de} v={0.3} />)}
      {VUELOS.map((v) => <Sfx key={`p${v.de}`} n="tick" at={v.de + 22} v={0.45} />)}
      <Sfx n="click" at={146} v={0.4} />
      <Teclas de={180} a={214} />
    </AbsoluteFill>
  );
};

// ---------------- 3 · Contrato: reglas, casos, vista previa y publicar ----------------
export const DUR_CONTRATO = 330;
const PUBLICA = 236;
const Contrato: React.FC = () => {
  const fr = useCurrentFrame();
  const fMatriz = 92;
  const dIzq = Math.min(tw(fr, 84, 104), 1 - tw(fr, 214, 230));
  const publicada = fr >= PUBLICA;
  return (
    <>
      <Foco d={dIzq} style={{position: 'absolute', left: 26, top: 20, width: 600}}>
        <div style={{fontFamily: f.mono, fontSize: 16, color: c.muted}}>Contrato · borrador</div>
        <div style={{fontSize: 32, fontWeight: 600, letterSpacing: '-.02em', marginTop: 2}}>{definicion.name}</div>
        <div style={{display: 'flex', gap: 8, marginTop: 10}}>{definicion.roles.map((r) => <Estado key={r} tono="niebla" size={16}>{r}</Estado>)}</div>
        <div style={{fontSize: 18, fontWeight: 600, marginTop: 22}}>Reglas ({definicion.rules.length})</div>
        {definicion.rules.map((r, i) => {
          const p = tw(fr, 10 + i * 10, 34 + i * 10);
          return (
            <div key={r.code} style={{marginTop: 10, padding: '14px 16px', borderRadius: 12, background: '#fff', border: `1px solid ${c.line}`, opacity: p, transform: `translateY(${(1 - p) * 20}px)`}}>
              <div style={{display: 'flex', justifyContent: 'space-between'}}>
                <span style={{fontSize: 20, fontWeight: 600}}>{r.code} · {r.name}</span>
                <Estado tono="gris" size={14}>Sin fuente</Estado>
              </div>
              <div style={{fontSize: 16, color: c.muted, marginTop: 4}}>{r.thresholdSummary} · Decide: {r.approverRole}</div>
            </div>
          );
        })}
        <div style={{fontSize: 18, fontWeight: 600, marginTop: 22}}>Casos de prueba ({casos.length})</div>
        {casos.map((k, i) => {
          const p = tw(fr, 40 + i * 8, 62 + i * 8);
          return (
            <div key={k.id} style={{marginTop: 8, padding: '10px 14px', borderRadius: 10, background: '#fff', border: `1px dashed rgba(13,15,20,.2)`, opacity: p}}>
              <div style={{fontSize: 17, fontWeight: 600}}><span style={{fontFamily: f.mono}}>{k.id}</span> · {k.title}</div>
              <div style={{fontFamily: f.mono, fontSize: 13.5, color: c.muted, marginTop: 2}}>{resumenCaso(k)}</div>
            </div>
          );
        })}
        <div style={{fontSize: 14, color: c.muted, marginTop: 10, fontStyle: 'italic'}}>Casos escritos a mano, sin documento detrás.</div>
      </Foco>
      <div style={{position: 'absolute', left: 648, top: 20, width: 534}}>
        <div style={{fontSize: 18, fontWeight: 600, opacity: tw(fr, fMatriz - 20, fMatriz)}}>Vista previa · antes de publicar</div>
        <div style={{display: 'grid', gridTemplateColumns: '120px 1fr 1fr', gap: 10, marginTop: 14, opacity: tw(fr, fMatriz - 16, fMatriz)}}>
          <span />
          {definicion.rules.map((r) => <span key={r.code} style={{fontFamily: f.mono, fontSize: 18, fontWeight: 500, textAlign: 'center'}}>{r.code}</span>)}
          {matriz.map((fila, a) => (
            <React.Fragment key={fila.objectId}>
              <span style={{fontFamily: f.mono, fontSize: 18, alignSelf: 'center'}}>{fila.objectId}</span>
              {fila.cells.map((celda, b) => {
                const de = fMatriz + (a * 2 + b) * 9;
                const p = tw(fr, de, de + 14);
                const s = tono(celda.estado);
                const hueco = celda.estado !== 'conforme';
                const onda = tw(fr, de + 6, de + 34);
                return (
                  <div key={b} style={{position: 'relative', height: 74, borderRadius: 12, border: '1px dashed rgba(13,15,20,.15)'}}>
                    {hueco && p > 0 && onda < 1 ? <div style={{position: 'absolute', inset: 0, borderRadius: 12, border: `3px solid ${s === 'arcilla' ? c.arcillaInk : c.solarInk}`, opacity: (1 - onda) * 0.7, transform: `scale(${1 + onda * 0.18})`}} /> : null}
                    <Estado tono={s} size={17} style={{position: 'absolute', inset: 0, display: 'grid', placeItems: 'center', textAlign: 'center', borderRadius: 12, opacity: p, transform: `scale(${0.8 + p * 0.2})`}}>{ROTULO[celda.estado]}</Estado>
                  </div>
                );
              })}
            </React.Fragment>
          ))}
        </div>
        <div style={{marginTop: 20, padding: '12px 16px', borderRadius: 12, background: '#fff', border: `1px solid ${c.line}`, fontSize: 15.5, lineHeight: 1.4, color: 'rgba(13,15,20,.75)', opacity: tw(fr, 160, 180)}}>
          Sin fuente: {definicion.rules.map((r) => r.code).join(', ')}. La regla se evalúa, pero no podrá citar de dónde sale.
        </div>
        <div style={{marginTop: 20, display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: 12, opacity: tw(fr, 190, 206)}}>
          {publicada ? (
            <div style={{textAlign: 'right'}}>
              <Estado tono="salvia" size={19} style={{padding: '12px 18px', borderRadius: 99, transform: `scale(${tw(fr, PUBLICA, PUBLICA + 12, 0.7, 1)})`}}>Versión publicada</Estado>
              <div style={{fontFamily: f.mono, fontSize: 14.5, color: c.muted, marginTop: 10, opacity: tw(fr, PUBLICA + 14, PUBLICA + 30)}}>{hashVersion.slice(0, 23)}…</div>
            </div>
          ) : (
            <span style={{display: 'inline-flex', alignItems: 'center', height: 54, padding: '0 26px', borderRadius: 99, background: c.solar, fontSize: 19, fontWeight: 700, transform: `scale(${fr >= PUBLICA - 3 ? 0.95 : 1})`, boxShadow: `0 0 ${22 + Math.sin(fr / 6) * 8}px rgba(242,181,68,.7)`}}>Publicar versión</span>
          )}
        </div>
      </div>
    </>
  );
};
export const ContratoEscena: React.FC = () => {
  const fr = useCurrentFrame();
  const bloom = fr >= PUBLICA ? 1 - tw(fr, PUBLICA, PUBLICA + 30) : 0;
  return (
    <AbsoluteFill>
      <Fondo luz={1 + bloom} />
      <Camara
        k={[
          {f: 0, x: 700, y: 480, z: 0.82, rx: 24, ry: 9, rz: -1.5},
          {f: 40, x: 330, y: 330, z: 1.12, zv: 2.35},
          {f: 84, x: 330, y: 560, z: 1.15, zv: 2.35},
          {f: 112, x: 1110, y: 300, z: 1.32, zv: 2.6},
          {f: 196, x: 1110, y: 330, z: 1.34, zv: 2.62},
          {f: 226, x: 1110, y: 470, z: 1.42, zv: 2.6},
          {f: 320, x: 1110, y: 480, z: 1.46, zv: 2.66},
        ]}
      >
        <Ventana activo="Contrato" ruta={RUTA} pie={PIE}><Contrato /></Ventana>
        <Destello de={10} />
        <Destello de={PUBLICA} dur={32} fuerza={0.6} />
        <Cursor de={196} a={PUBLICA + 10} escala={0.8} k={[{f: 196, x: 1100, y: 800}, {f: 230, x: CX + 1110, y: CY + 455}]} clics={[PUBLICA]} />
      </Camara>
      {bloom > 0 ? <AbsoluteFill style={{mixBlendMode: 'screen', opacity: bloom * 0.45, background: 'radial-gradient(circle at 50% 58%, rgba(255,226,165,.95), rgba(242,181,68,.35) 34%, transparent 72%)'}} /> : null}
      <Leyendas
        items={[
          {t: 'Pruébala con casos *antes de publicar.*', de: 10, a: 214},
          {t: 'Publicas una versión. *Queda registrada.*', de: 226, a: 326},
        ]}
      />
      <Entorno />
      <Sfx n="whoosh" at={2} v={0.35} />
      {matriz.flatMap((fila, a) => fila.cells.map((celda, b) => <Sfx key={`${a}${b}`} n={celda.estado === 'conforme' ? 'tick' : 'alert'} at={92 + (a * 2 + b) * 9 + 4} v={celda.estado === 'conforme' ? 0.35 : 0.4} />))}
      <Sfx n="click" at={PUBLICA} v={0.55} />
      <Sfx n="chime" at={PUBLICA + 1} v={0.45} />
    </AbsoluteFill>
  );
};

// ---------------- 4 · Decide una persona ----------------
export const DUR_DECIDE = 250;
const NO = 70;
const ROL = 140;
const SI = 178;
const Decision: React.FC = () => {
  const fr = useCurrentFrame();
  const {reel} = useFormato();
  const A = reel ? 720 : 1144;
  const Y = reel ? {rol: 116, razon: 196, borrador: 290, aviso: 430, botones: 556, audit: 636} : {rol: 24, razon: 128, borrador: 186, aviso: 310, botones: 400, audit: 500};
  const conRol = fr >= ROL;
  const aprobado = fr >= SI;
  const giro = tw(fr, ROL, ROL + 14, 0, 1, SUAVE);
  const temblor = fr >= NO && fr < NO + 16 ? Math.sin((fr - NO) * 1.9) * (16 - (fr - NO)) * 0.9 : 0;
  const aviso = Math.min(tw(fr, NO, NO + 12), 1 - tw(fr, ROL, ROL + 10));
  const audit = tw(fr, SI + 18, SI + 44);
  return (
    <>
      <div style={{position: 'absolute', left: 30, top: 24, width: reel ? A : 720}}>
        <div style={{fontFamily: f.mono, fontSize: 17, color: c.muted}}>Revisión · Regla {revisionCredito.ruleCode} · {revisionCredito.targetObjectId}</div>
        <div style={{fontSize: 34, fontWeight: 600, letterSpacing: '-.02em', marginTop: 4}}>{revisionCredito.title}</div>
      </div>
      <div style={reel ? {position: 'absolute', left: 30, top: Y.rol} : {position: 'absolute', right: 30, top: 24, textAlign: 'right'}}>
        <div style={{fontSize: 15, color: c.muted, marginBottom: 4}}>Actúas como</div>
        <div style={{display: 'inline-block', padding: '8px 16px', borderRadius: 10, background: conRol ? c.lavanda : '#fff', color: conRol ? c.lavandaInk : c.ink, border: `1px solid ${c.line}`, fontSize: 20, fontWeight: 500, overflow: 'hidden'}}>
          <span style={{display: 'block', opacity: giro > 0.5 ? (giro - 0.5) * 2 : 1 - giro * 2, transform: `translateY(${giro < 0.5 ? -giro * 20 : (1 - giro) * 20}px)`}}>{giro > 0.5 ? revisionCredito.requiredRole : 'Comercial'}</span>
        </div>
      </div>
      <div style={{position: 'absolute', left: 30, top: Y.razon, width: A, fontSize: 21, lineHeight: 1.44, color: 'rgba(13,15,20,.8)'}}>{revisionCredito.reasonSummary}</div>
      <div style={{position: 'absolute', left: 30, top: Y.borrador, width: A}}>
        <div style={{fontSize: 17, fontWeight: 600, marginBottom: 8}}>Borrador de la acción</div>
        <div style={{padding: '16px 20px', borderRadius: 12, border: '1.5px solid rgba(13,15,20,.2)', background: '#fafaf8', fontFamily: f.mono, fontSize: 20}}>{revisionCredito.proposedDraft}</div>
      </div>
      {aviso > 0 ? (
        <div style={{position: 'absolute', left: 30, width: A, top: Y.aviso, padding: '14px 18px', borderRadius: 12, background: c.arcilla, border: '1px solid rgba(140,42,31,.3)', fontSize: 22, fontWeight: 500, color: c.arcillaInk, opacity: aviso, transform: `translateY(${(1 - aviso) * 12}px)`}}>{bloqueoComercial}</div>
      ) : null}
      <div style={{position: 'absolute', left: 30, width: A, top: Y.botones, display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: `1px solid ${c.line}`, paddingTop: 16}}>
        <div style={{fontFamily: f.mono, fontSize: 17, color: c.muted}}>Decide: <b>{revisionCredito.requiredRole}</b></div>
        {aprobado ? (
          <Estado tono="salvia" size={20} style={{padding: '12px 18px', transform: `scale(${tw(fr, SI, SI + 12, 0.7, 1)})`}}>Aprobada por {revisionCredito.requiredRole}</Estado>
        ) : (
          <span style={{display: 'inline-flex', alignItems: 'center', height: 54, padding: '0 24px', borderRadius: 99, background: c.solar, fontSize: 19, fontWeight: 700, opacity: conRol ? 1 : 0.42, transform: `translateX(${temblor}px) scale(${fr >= SI - 3 ? 0.95 : 1})`, boxShadow: conRol ? `0 0 ${24 + Math.sin(fr / 7) * 10}px rgba(242,181,68,.7)` : undefined}}>Aprobar y confirmar</span>
        )}
      </div>
      {audit > 0 ? (
        <div style={{position: 'absolute', left: 30, width: A, top: Y.audit, padding: '18px 22px', background: '#fff', borderRadius: 14, border: `1px solid ${c.line}`, opacity: audit, transform: `translateY(${(1 - audit) * 40}px)`, boxShadow: '0 14px 40px -20px rgba(13,15,20,.4)'}}>
          <div style={{fontSize: 21, fontWeight: 600}}>Registro</div>
          <div style={{display: 'grid', gridTemplateColumns: reel ? '1fr 1fr' : '1fr 1.2fr .8fr 1.4fr', gap: reel ? 12 : 18, marginTop: 14}}>
            {[
              ['Quién', revisionCredito.requiredRole],
              ['Decisión', 'Revisión aprobada'],
              ['Regla', `${revisionCredito.ruleCode} · ${revisionCredito.targetObjectId}`],
              ['Versión', `${hashVersion.slice(0, 15)}…`],
            ].map(([k, v], i) => (
              <div key={k} style={{opacity: tw(fr, SI + 26 + i * 6, SI + 42 + i * 6)}}>
                <div style={{fontFamily: f.mono, fontSize: 15, color: c.muted}}>{k}</div>
                <div style={{fontSize: 20, fontWeight: 500, marginTop: 6, fontFamily: k === 'Versión' ? f.mono : f.ui}}>{v}</div>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </>
  );
};
export const Decide: React.FC = () => {
  const fr = useCurrentFrame();
  const {reel} = useFormato();
  // En 9:16 la tarjeta es estrecha: el botón y el rol cambian de sitio.
  const boton = reel ? {x: CX + 640, y: CY + 582} : {x: CX + 1080, y: CY + 430};
  const rol = reel ? {x: CX + 120, y: CY + 150} : {x: CX + 1060, y: CY + 70};
  const bloom = fr >= SI ? 1 - tw(fr, SI, SI + 30) : 0;
  return (
    <AbsoluteFill>
      <Fondo luz={1 + bloom} />
      <Camara
        k={[
          {f: 0, x: 700, y: 400, z: 0.84, rx: 22, ry: -8, rz: 1.5},
          {f: 36, x: reel ? 600 : 798, y: reel ? 360 : 330, z: 1.32, zv: 1.85},
          {f: 66, x: reel ? 600 : 900, y: reel ? 560 : 420, z: 1.5, zv: 1.9},
          {f: 130, x: reel ? 600 : 900, y: reel ? 560 : 420, z: 1.5, zv: 1.9},
          {f: 150, x: reel ? 600 : 1080, y: reel ? 240 : 160, z: 1.6, zv: 2.1},
          {f: 170, x: reel ? 600 : 1000, y: reel ? 560 : 440, z: 1.6, zv: 1.95},
          {f: 200, x: reel ? 600 : 798, y: reel ? 700 : 560, z: 1.4, zv: 1.85},
          {f: 250, x: reel ? 600 : 798, y: reel ? 710 : 570, z: 1.42, zv: 1.88},
        ]}
      >
        <Ventana activo="Revisar" ruta={RUTA} pie={PIE}><Decision /></Ventana>
        <Destello de={8} />
        <Destello de={SI} dur={30} fuerza={0.6} />
        <Cursor de={40} a={SI + 8} escala={0.8} k={[{f: 40, x: 800, y: 760}, {f: 66, ...boton}, {f: 120, ...boton}, {f: 138, ...rol}, {f: 156, ...rol}, {f: 175, ...boton}]} clics={[NO, ROL, SI]} />
      </Camara>
      {bloom > 0 ? <AbsoluteFill style={{mixBlendMode: 'screen', opacity: bloom * 0.5, background: 'radial-gradient(circle at 50% 56%, rgba(255,226,165,.95), rgba(242,181,68,.35) 34%, transparent 72%)'}} /> : null}
      <Leyendas
        items={[
          {t: 'Si la regla pide Riesgos, *Comercial no aprueba.*', de: 8, a: 140},
          {t: 'Riesgos decide. *Queda en el registro.*', de: 152, a: 246},
        ]}
      />
      <Entorno />
      <Sfx n="whoosh" at={2} v={0.35} />
      <Sfx n="click" at={NO} v={0.4} />
      <Sfx n="deny" at={NO + 2} v={0.42} />
      <Sfx n="click" at={ROL} v={0.5} />
      <Sfx n="click" at={SI} v={0.6} />
      <Sfx n="chime" at={SI + 1} v={0.5} />
      <Sfx n="boom" at={SI} v={0.25} />
    </AbsoluteFill>
  );
};

// ---------------- 5 · Cierre comercial ----------------
export const DUR_CIERRE_REEL = 170;
export const CierreReel: React.FC = () => {
  const fr = useCurrentFrame();
  const {reel} = useFormato();
  const s = useResorte(reel ? 84 : 66, 20);
  if (reel) {
    // La mascota llega desde su esquina (ver Companero) y se queda como logo.
    const marca = tw(fr, 24, 46);
    return (
      <AbsoluteFill>
        <Fondo luz={0.9} y={0.26} />
        <div style={{position: 'absolute', left: 0, right: 0, top: 632, textAlign: 'center', fontFamily: f.ui, fontWeight: 600, fontSize: 88, letterSpacing: '-0.02em', color: '#fff', opacity: marca, transform: `translateY(${(1 - marca) * 16}px)`}}>Solaris</div>
        <div style={{position: 'absolute', left: 80, right: 80, top: 790, display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center'}}>
          <Titular texto="Tú aportas el proceso." de={30} size={92} ancho={900} />
          <div style={{marginTop: 8}}>
            <Titular texto="Illarium aporta *el contrato.*" de={46} size={92} ancho={900} />
          </div>
        </div>
        <div style={{position: 'absolute', left: 0, right: 0, top: 1236, opacity: s, transform: `translateY(${(1 - s) * 18}px)`, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 22}}>
          <div style={{fontFamily: f.ui, fontSize: 36, color: 'rgba(255,255,255,.8)'}}>Para consultoras e implantadores de CRM</div>
          <div style={{padding: '14px 30px', borderRadius: 99, background: c.solar, color: c.ink, fontFamily: f.ui, fontWeight: 700, fontSize: 34}}>Pide una demo · solaris.dasalazarr.com</div>
        </div>
        <div style={{position: 'absolute', top: 1420, left: 0, right: 0, textAlign: 'center', fontFamily: f.mono, fontSize: 21, color: 'rgba(255,255,255,.62)', opacity: tw(fr, 80, 104)}}>Caso ficticio · casos de prueba escritos a mano</div>
        <Sfx n="boom" at={0} v={0.36} />
        <Sfx n="ping" at={24} v={0.3} />
        <Sfx n="chime" at={84} v={0.3} />
      </AbsoluteFill>
    );
  }
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
      <Fondo luz={0.9} y={0.5} />
      <SolGrande p={tw(fr, 0, 50) * 0.26} y={reel ? 0.4 : 0.42} r={reel ? 220 : 190} fuerza={0.7} />
      <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', padding: reel ? '0 80px' : 60, textAlign: 'center', transform: `translateY(${reel ? -90 : -30}px)`}}>
        <Titular texto="Tú aportas el proceso." de={4} size={reel ? 96 : 104} ancho={reel ? 900 : 1600} />
        <div style={{marginTop: 10}}>
          <Titular texto="Illarium aporta *el contrato.*" de={22} size={reel ? 96 : 104} ancho={reel ? 900 : 1600} />
        </div>
        <div style={{marginTop: reel ? 64 : 48, opacity: s, transform: `translateY(${(1 - s) * 18}px)`, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 18}}>
          <div style={{fontFamily: f.ui, fontSize: reel ? 38 : 34, color: 'rgba(255,255,255,.8)'}}>Para consultoras e implantadores de CRM</div>
          <Logo size={reel ? 62 : 54} />
          <div style={{marginTop: 6, padding: '14px 30px', borderRadius: 99, background: c.solar, color: c.ink, fontFamily: f.ui, fontWeight: 700, fontSize: reel ? 34 : 28}}>Pide una demo · solaris.dasalazarr.com</div>
        </div>
      </div>
      <div style={{position: 'absolute', bottom: reel ? 470 : 38, left: 0, right: 0, textAlign: 'center', fontFamily: f.mono, fontSize: reel ? 22 : 18, color: 'rgba(255,255,255,.62)', opacity: tw(fr, 60, 84)}}>Caso ficticio · casos de prueba escritos a mano</div>
      <Sfx n="boom" at={0} v={0.36} />
      <Sfx n="chime" at={66} v={0.3} />
    </AbsoluteFill>
  );
};

// ---------------- El compañero: la mascota abre y cierra el reel 9:16 ----------------
// Aparece en el gancho y vuelve en el cierre (ADR-0024). En los planos de producto no está:
// ahí mandan la cita y el rótulo de entorno, y quien decide en pantalla es una persona (principios 3 y 4).
export const Companero: React.FC<{inicios: number[]; fin: number}> = ({inicios, fin}) => {
  const fr = useCurrentFrame();
  const {reel} = useFormato();
  const entra = useResorte(14, 13, 0.9);
  if (!reel) return null;
  const [, regla, contrato, decide, cierre] = inicios;
  const marcas = [0, regla - 4, regla + 24, cierre - 2, cierre + 28];
  const v = (vals: number[]) => interpolate(fr, marcas, vals, {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: SUAVE});
  const x = 540;
  const y = v([1250, 1250, 1250, 468, 468]);
  const size = v([440, 440, 440, 450, 450]);
  // Fuera de plano mientras se ve el producto.
  const presente = 1 - tw(fr, regla - 6, regla + 10) + tw(fr, cierre + 2, cierre + 22);

  const tras = (t: number, dur: number) => (fr >= t && fr < t + dur ? (fr - t) / dur : -1);
  const max = (ts: number[], dur: number, g: (p: number) => number) => ts.reduce((m, t) => { const p = tras(t, dur); return p < 0 ? m : Math.max(m, g(p)); }, 0);
  const suma = (ts: number[], dur: number, g: (p: number) => number) => ts.reduce((m, t) => { const p = tras(t, dur); return p < 0 ? m : m + g(p); }, 0);

  const llegadas = [...VUELOS.map((w) => regla + w.de + 22), regla + 146];
  const avisos = matriz.flatMap((fila, a) => fila.cells.map((celda, b) => (celda.estado === 'conforme' ? -1 : contrato + 92 + (a * 2 + b) * 9 + 6))).filter((t) => t > 0);
  const alegrias = [contrato + PUBLICA, decide + SI, cierre + 28];
  const negacion = [decide + NO];

  const pulso = max(llegadas, 14, (p) => 1 - p);
  const salto = max(alegrias, 24, (p) => Math.sin(Math.PI * p));
  const destello = max(alegrias, 34, (p) => 1 - p);
  const rot = suma(negacion, 22, (p) => Math.sin(p * 22 * 1.15) * 12 * (1 - p)) + suma(avisos, 16, (p) => -9 * Math.sin(Math.PI * p));
  const parpadeo = (fr + 37) % 113 < 4 || tras(decide + ROL, 4) >= 0;
  const ojos = parpadeo ? 0.12 : max(negacion, 26, () => 0.5) || (max(avisos, 16, () => 1) ? 1.16 : 1);

  const flota = Math.sin(fr / 29) * size * 0.022;
  const escala = (0.55 + 0.45 * entra) * (1 + pulso * 0.13 + salto * 0.08);
  const o = Math.min(entra * 1.4, 1, 1 - tw(fr, fin - 16, fin)) * presente;
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <div style={{position: 'absolute', left: x - size / 2, top: y - size / 2 + flota - salto * size * 0.2 + (1 - entra) * 240, width: size, height: size, opacity: o, transform: `scale(${escala}) rotate(${rot}deg)`}}>
        <Mascota size={size} ojos={ojos} luz={Math.max(pulso * 0.8, destello)} aro={Math.sin(fr / 41) * 2.5 + salto * 9} chispa={(fr / 46) % 2} />
      </div>
    </AbsoluteFill>
  );
};
