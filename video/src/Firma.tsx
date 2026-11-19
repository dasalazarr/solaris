import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {c, f} from './tokens';
import {Camara, Cursor, Destello, Entorno, Foco, Fondo, Leyendas, SUAVE, Sfx, Teclas, tw, useFormato, useResorte} from './fx';
import {CX, CY, Estado, Ventana} from './ventana';
import {borrador, huecos, motivoBloqueo, revision, rolSinFirma} from './datos';

export const DUR_FIRMA = 720;
const CLIC_NO = 112;
const CLIC_ROL = 232;
const SEL = 286;
const CLIC_SI = 452;
const FINAL = 596;

const ANTES = 'Verificadas';
const DESPUES = 'Comprobadas';
if (!borrador.includes(ANTES)) throw new Error('El borrador del producto ya no contiene la palabra que se edita en el vídeo');

const Borrador: React.FC = () => {
  const fr = useCurrentFrame();
  const [a, b] = borrador.split(ANTES);
  const sel = fr >= SEL && fr < SEL + 22;
  const n = Math.floor(tw(fr, SEL + 22, SEL + 56, 0, DESPUES.length, (x) => x));
  const palabra = fr < SEL + 22 ? ANTES : DESPUES.slice(0, n);
  const caret = fr >= SEL + 22 && fr < SEL + 90 && Math.floor(fr / 8) % 2 === 0;
  return (
    <div style={{whiteSpace: 'pre-wrap', fontFamily: f.mono, fontSize: 18, lineHeight: 1.5, color: 'rgba(13,15,20,.86)'}}>
      {a}
      <span style={{background: sel ? c.solar : fr >= SEL + 22 ? c.solarSoft : 'transparent', borderRadius: 3}}>{palabra}</span>
      {caret ? <span style={{display: 'inline-block', width: 2, height: 21, background: c.ink, verticalAlign: -4}} /> : null}
      {b}
    </div>
  );
};

const Boton: React.FC<{children: React.ReactNode; style?: React.CSSProperties}> = ({children, style}) => (
  <span style={{display: 'inline-flex', alignItems: 'center', height: 50, padding: '0 20px', borderRadius: 10, fontSize: 18, fontWeight: 600, whiteSpace: 'nowrap', ...style}}>{children}</span>
);

const Tarea: React.FC = () => {
  const fr = useCurrentFrame();
  const conRol = fr >= CLIC_ROL;
  const aprobado = fr >= CLIC_SI;
  const temblor = fr >= CLIC_NO && fr < CLIC_NO + 16 ? Math.sin((fr - CLIC_NO) * 1.9) * (16 - (fr - CLIC_NO)) * 0.9 : 0;
  const aviso = Math.min(tw(fr, CLIC_NO, CLIC_NO + 14), 1 - tw(fr, CLIC_ROL, CLIC_ROL + 12));
  const fNotice = Math.min(tw(fr, CLIC_NO + 6, CLIC_NO + 30), 1 - tw(fr, CLIC_ROL - 26, CLIC_ROL - 6));
  const fDraft = Math.min(tw(fr, SEL - 26, SEL - 4), 1 - tw(fr, CLIC_SI - 54, CLIC_SI - 30));
  const d = Math.max(fNotice * 0.8, fDraft);
  const audit = tw(fr, CLIC_SI + 24, CLIC_SI + 54);
  const prensa = fr >= CLIC_SI - 3 && fr <= CLIC_SI + 6 ? 0.95 : 1;
  const giro = tw(fr, CLIC_ROL, CLIC_ROL + 14, 0, 1, SUAVE);
  return (
    <>
      <Foco d={d} style={{position: 'absolute', left: 30, top: 22, width: 720}}>
        <div style={{fontFamily: f.mono, fontSize: 17, color: c.muted}}>Revisión · Regla {revision.ruleCode} · {revision.targetObjectId}</div>
        <div style={{fontSize: 30, fontWeight: 600, letterSpacing: '-.02em', marginTop: 4}}>{revision.title}</div>
      </Foco>
      <div style={{position: 'absolute', right: 30, top: 22, textAlign: 'right'}}>
        <div style={{fontSize: 15, color: c.muted, marginBottom: 4}}>Actúas como</div>
        <div style={{display: 'inline-block', padding: '8px 16px', borderRadius: 10, background: conRol ? c.lavanda : '#fff', color: conRol ? c.lavandaInk : c.ink, border: `1px solid ${c.line}`, fontSize: 18, fontWeight: 500, overflow: 'hidden'}}>
          <span style={{display: 'block', opacity: giro > 0.5 ? (giro - 0.5) * 2 : 1 - giro * 2, transform: `translateY(${giro < 0.5 ? -giro * 20 : (1 - giro) * 20}px)`}}>
            {giro > 0.5 ? revision.requiredRole : rolSinFirma}
          </span>
        </div>
      </div>
      <Foco d={d} style={{position: 'absolute', left: 30, top: 118, width: 1144, fontSize: 19, lineHeight: 1.44, color: 'rgba(13,15,20,.8)'}}>
        {revision.reasonSummary}
      </Foco>
      <Foco d={fNotice * 0.8} style={{position: 'absolute', left: 30, top: 226, width: 1144}}>
        <div style={{display: 'flex', justifyContent: 'space-between', fontSize: 17, marginBottom: 8}}>
          <span style={{fontWeight: 600}}>Borrador editable de la acción</span>
          <span style={{fontFamily: f.mono, fontSize: 15, color: c.muted}}>Se registra la versión editada y aprobada</span>
        </div>
        <div style={{padding: '14px 18px', borderRadius: 12, border: `1.5px solid ${fDraft > 0.3 ? c.solar : 'rgba(13,15,20,.2)'}`, background: fDraft > 0.3 ? '#fff' : '#fafaf8', boxShadow: fDraft > 0.3 ? `0 0 0 4px rgba(242,181,68,.2)` : undefined, height: 182}}>
          <Borrador />
        </div>
      </Foco>
      {aviso > 0 ? (
        <div style={{position: 'absolute', left: 30, width: 1144, top: 454, padding: '14px 18px', borderRadius: 12, background: c.arcilla, border: '1px solid rgba(140,42,31,.3)', fontSize: 22, fontWeight: 500, color: c.arcillaInk, opacity: aviso, transform: `translateY(${(1 - aviso) * 12}px)`}}>
          {motivoBloqueo}
        </div>
      ) : null}
      <Foco d={fDraft} style={{position: 'absolute', left: 30, width: 1144, top: 526, display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: `1px solid ${c.line}`, paddingTop: 14}}>
        <div style={{fontFamily: f.mono, fontSize: 16, color: c.muted}}>Rol requerido: <b>{revision.requiredRole}</b></div>
        <div style={{display: 'flex', gap: 10, alignItems: 'center'}}>
          {aprobado ? (
            <Estado tono="salvia" size={19} style={{padding: '12px 18px', transform: `scale(${tw(fr, CLIC_SI, CLIC_SI + 12, 0.7, 1)})`}}>Aprobada por {revision.requiredRole}</Estado>
          ) : (
            <>
              <Boton style={{background: conRol ? c.arcilla : '#f4f1ec', color: conRol ? c.arcillaInk : 'rgba(13,15,20,.4)'}}>Rechazar</Boton>
              <Boton style={{background: '#fff', border: '1px solid rgba(13,15,20,.2)'}}>Pedir cambios</Boton>
              <Boton
                style={{
                  borderRadius: 99, background: c.solar, color: c.ink, opacity: conRol ? 1 : 0.42, transform: `translateX(${temblor}px) scale(${prensa})`,
                  boxShadow: conRol ? `0 0 ${24 + Math.sin(fr / 7) * 10}px rgba(242,181,68,.7)` : undefined,
                }}
              >
                Aprobar y confirmar
              </Boton>
            </>
          )}
        </div>
      </Foco>
      {audit > 0 ? (
        <div style={{position: 'absolute', left: 30, width: 1144, top: 604, height: 192, background: '#fff', borderRadius: 14, border: `1px solid ${c.line}`, padding: '16px 22px', opacity: audit, transform: `translateY(${(1 - audit) * 50}px)`, boxShadow: '0 14px 40px -20px rgba(13,15,20,.4)'}}>
          <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
            <span style={{fontSize: 21, fontWeight: 600}}>Registro de auditoría · esta sesión</span>
            <span style={{padding: '6px 14px', borderRadius: 8, border: '1px solid rgba(13,15,20,.2)', fontSize: 16, fontWeight: 600}}>Exportar CSV</span>
          </div>
          <div style={{display: 'grid', gridTemplateColumns: '1.1fr 1fr 1.2fr .9fr', gap: 18, marginTop: 18}}>
            {[
              ['Quién', revision.requiredRole],
              ['Decisión', 'Revisión aprobada'],
              ['Versión', 'Borrador editado'],
              ['Evidencia', 'Política, pág. 4'],
            ].map(([k, v], i) => (
              <div key={k} style={{opacity: tw(fr, CLIC_SI + 34 + i * 7, CLIC_SI + 52 + i * 7)}}>
                <div style={{fontFamily: f.mono, fontSize: 15, color: c.muted}}>{k}</div>
                <div style={{fontSize: 21, fontWeight: 500, marginTop: 6}}>{v}</div>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </>
  );
};

/** El contador cae de 3 a 2, con desenfoque de movimiento vertical. */
const Contador: React.FC = () => {
  const fr = useCurrentFrame();
  const {W, H, vertical} = useFormato();
  const entra = tw(fr, FINAL, FINAL + 18);
  const pill = useResorte(FINAL + 54, 16);
  if (fr < FINAL) return null;
  const roll = tw(fr, FINAL + 36, FINAL + 58, 0, 1, SUAVE);
  const size = vertical ? 400 : 380;
  const vel = Math.sin(roll * Math.PI);
  return (
    <AbsoluteFill style={{background: `rgba(13,15,20,${entra * 0.95})`, backdropFilter: `blur(${entra * 22}px)`, alignItems: 'center', justifyContent: 'center', paddingTop: 120}}>
      <div style={{width: W, height: H * 0.55, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', opacity: entra}}>
        <div style={{height: size * 1.04, overflow: 'hidden', position: 'relative', width: size, filter: vel > 0.02 ? `blur(${vel * 6}px)` : undefined}}>
          {['3', '2'].map((n, i) => (
            <div key={n} style={{position: 'absolute', inset: 0, display: 'grid', placeItems: 'center', fontFamily: f.ui, fontWeight: 600, fontSize: size, lineHeight: 1, letterSpacing: '-.04em', color: i ? c.solar : '#fff', transform: `translateY(${(i - roll) * 100}%)`, textShadow: i ? '0 0 80px rgba(242,181,68,.55)' : undefined}}>{n}</div>
          ))}
        </div>
        <div style={{fontFamily: f.ui, fontWeight: 500, fontSize: vertical ? 50 : 46, color: 'rgba(255,255,255,.9)', letterSpacing: '-.02em', marginTop: 10}}>huecos abiertos</div>
        <div style={{marginTop: 30, opacity: pill, transform: `translateY(${(1 - pill) * 20}px)`}}>
          <Estado tono="salvia" size={vertical ? 26 : 24} style={{padding: '12px 22px', borderRadius: 99}}>{`PC-0412 · R-03 · Aprobado por ${revision.requiredRole}`}</Estado>
        </div>
      </div>
    </AbsoluteFill>
  );
};

if (huecos.open.length !== 3) throw new Error('El contador del vídeo asume 3 huecos abiertos antes de aprobar');

export const Firma: React.FC = () => {
  const fr = useCurrentFrame();
  const bloom = fr >= CLIC_SI ? 1 - tw(fr, CLIC_SI, CLIC_SI + 34) : 0;
  return (
    <AbsoluteFill>
      <Fondo luz={1 + bloom} />
      <Camara
        k={[
          {f: 0, x: 700, y: 480, z: 0.8, rx: 26, ry: -8, rz: 1.5},
          {f: 56, x: 760, y: 410, z: 1.04},
          {f: 96, x: 940, y: 560, z: 1.2},
          {f: 142, x: 798, y: 540, z: 1.5, zv: 1.27},
          {f: 196, x: 798, y: 550, z: 1.5, zv: 1.27},
          {f: 226, x: 1090, y: 200, z: 1.42},
          {f: 262, x: 798, y: 360, z: 1.46, zv: 1.3},
          {f: 330, x: 798, y: 400, z: 1.6, zv: 1.32},
          {f: 398, x: 798, y: 400, z: 1.62, zv: 1.34},
          {f: 430, x: 1020, y: 620, z: 1.55, zv: 1.4},
          {f: 468, x: 1020, y: 620, z: 1.6, zv: 1.42},
          {f: 512, x: 798, y: 730, z: 1.42, zv: 1.28},
          {f: FINAL, x: 798, y: 730, z: 1.46, zv: 1.3},
        ]}
      >
        <Ventana activo="Revisar"><Tarea /></Ventana>
        <Destello de={14} />
        <Destello de={CLIC_SI} dur={34} fuerza={0.7} />
        <Cursor
          de={80}
          a={CLIC_SI + 26}
          k={[
            {f: 80, x: 760, y: 780},
            {f: 108, x: CX + 1060, y: CY + 566},
            {f: 200, x: CX + 1060, y: CY + 566},
            {f: 228, x: CX + 1040, y: CY + 66},
            {f: 262, x: CX + 1040, y: CY + 90},
            {f: 282, x: CX + 240, y: CY + 368},
            {f: 396, x: CX + 240, y: CY + 368},
            {f: 448, x: CX + 1070, y: CY + 566},
          ]}
          clics={[CLIC_NO, CLIC_ROL, CLIC_SI]}
          escala={0.8}
        />
      </Camara>
      {bloom > 0 ? <AbsoluteFill style={{mixBlendMode: 'screen', opacity: bloom * 0.55, background: 'radial-gradient(circle at 50% 58%, rgba(255,226,165,.95), rgba(242,181,68,.4) 34%, transparent 72%)'}} /> : null}
      <Contador />
      <Leyendas
        items={[
          {t: 'Aquí decide *una persona.*', de: 8, a: 96},
          {t: 'Si tu rol no es el que exige la regla, *no puedes aprobar.*', de: 118, a: 214},
          {t: 'Con el rol correcto, revisas el borrador. Y lo editas.', de: 262, a: 404},
          {t: 'Solaris no envía nada por su cuenta.', de: 416, a: 500},
          {t: 'Queda registrado quién, qué versión y *qué evidencia.*', de: 510, a: FINAL - 6},
          {t: 'Y el hueco *se cierra.*', de: FINAL + 6, a: 712},
        ]}
      />
      <Entorno />
      <Sfx n="whoosh" at={4} v={0.35} />
      <Sfx n="click" at={CLIC_NO} v={0.4} />
      <Sfx n="deny" at={CLIC_NO + 2} v={0.42} />
      <Sfx n="click" at={CLIC_ROL} v={0.5} />
      <Sfx n="ping" at={CLIC_ROL + 8} v={0.2} />
      <Sfx n="tick" at={SEL} v={0.35} />
      <Teclas de={SEL + 22} a={SEL + 56} />
      <Sfx n="click" at={CLIC_SI} v={0.6} />
      <Sfx n="chime" at={CLIC_SI + 1} v={0.5} />
      <Sfx n="boom" at={CLIC_SI} v={0.28} />
      <Sfx n="whoosh" at={FINAL} v={0.25} />
      <Sfx n="whoosh-soft" at={FINAL + 36} v={0.3} />
      <Sfx n="chime" at={FINAL + 56} v={0.34} />
    </AbsoluteFill>
  );
};
