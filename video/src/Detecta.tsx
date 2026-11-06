import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {c, f} from './tokens';
import {Camara, Destello, Entorno, Foco, Fondo, Leyendas, Sfx, tw, useResorte} from './fx';
import {CX, CY, Estado, Ventana} from './ventana';
import {compras, evCertificado, huecos, matriz} from './datos';

export const DUR_DETECTA = 610;
const INICIO = 76;
const PASO = 22;
const LISTA = 326;

const COL = [262, 572, 882];
const ANCHO = 296;
const FILA = [190, 400];
const ALTO = 190;

const estilo = (e: string) =>
  ({
    conforme: {bg: c.salvia, fg: c.salviaInk, borde: 'rgba(30,107,58,.25)'},
    incumplida: {bg: c.arcilla, fg: c.arcillaInk, borde: 'rgba(140,42,31,.35)'},
    sin_evidencia: {bg: c.arcilla, fg: c.arcillaInk, borde: 'rgba(140,42,31,.35)'},
    requiere_aprobacion: {bg: c.solarSoft, fg: c.solarInk, borde: 'rgba(138,90,0,.35)'},
  })[e] ?? {bg: '#f1efe9', fg: 'rgba(13,15,20,.66)', borde: 'rgba(13,15,20,.22)'};

const Celda: React.FC<{i: number; rotulo: string; estado: string; x: number; y: number; atenua: number}> = ({i, rotulo, estado, x, y, atenua}) => {
  const fr = useCurrentFrame();
  const de = INICIO + i * PASO;
  const p = useResorte(de + 12, 13, 0.7);
  const s = estilo(estado);
  const barre = fr >= de && fr < de + 18;
  const hueco = ['incumplida', 'sin_evidencia', 'requiere_aprobacion'].includes(estado);
  const onda = tw(fr, de + 12, de + 44);
  return (
    <Foco d={atenua} style={{position: 'absolute', left: x, top: y, width: ANCHO, height: ALTO}}>
      <div style={{position: 'absolute', inset: 0, borderRadius: 16, border: `1px dashed ${c.line}`, background: '#fff'}} />
      {hueco && fr >= de + 12 && onda < 1 ? (
        <div style={{position: 'absolute', inset: 0, borderRadius: 16, border: `3px solid ${s.fg}`, opacity: (1 - onda) * 0.7, transform: `scale(${1 + onda * 0.16})`}} />
      ) : null}
      <div style={{position: 'absolute', inset: 0, borderRadius: 16, background: s.bg, border: `1.5px ${estado === 'no_aplica' ? 'dashed' : 'solid'} ${s.borde}`, opacity: Math.min(1, p), transform: `scale(${0.86 + p * 0.14})`, display: 'grid', placeItems: 'center', padding: 14, textAlign: 'center'}}>
        <span style={{fontSize: 24, fontWeight: 600, lineHeight: 1.2, color: s.fg}}>{rotulo}</span>
      </div>
      {barre ? (
        <div style={{position: 'absolute', inset: -6, borderRadius: 20, overflow: 'hidden', pointerEvents: 'none', boxShadow: `0 0 0 3px ${c.solar}, 0 0 44px rgba(242,181,68,.75)`}}>
          <div style={{position: 'absolute', top: 0, bottom: 0, width: 90, left: `${tw(fr, de, de + 18, -30, 110, (x) => x)}%`, background: 'linear-gradient(90deg, transparent, rgba(242,181,68,.75), transparent)'}} />
        </div>
      ) : null}
    </Foco>
  );
};

const Matriz: React.FC = () => {
  const fr = useCurrentFrame();
  const foco = Math.min(tw(fr, 232, 256), 1 - tw(fr, 300, 322));
  const reglas = ['R-01', 'R-02', 'R-03'].map((id) => compras.rules.find((r) => r.code === id)!);
  return (
    <div style={{position: 'absolute', inset: 0, opacity: 1 - tw(fr, LISTA - 6, LISTA + 12), transform: `scale(${1 - tw(fr, LISTA - 6, LISTA + 18) * 0.05})`}}>
      <Foco d={foco} style={{position: 'absolute', inset: 0}}>
        <div style={{position: 'absolute', left: 32, top: 26, fontSize: 30, fontWeight: 600, letterSpacing: '-.02em'}}>Cruce de reglas y objetos</div>
        {reglas.map((r, i) => (
          <div key={r.code} style={{position: 'absolute', left: COL[i], width: ANCHO, top: 92, textAlign: 'center', opacity: tw(fr, 22 + i * 5, 42 + i * 5)}}>
            <div style={{fontFamily: f.mono, fontSize: 26, fontWeight: 500}}>{r.code}</div>
            <div style={{fontSize: 17, color: c.muted, marginTop: 4}}>{r.thresholdSummary}</div>
          </div>
        ))}
        {matriz.map((m, i) => (
          <div key={m.id} style={{position: 'absolute', left: 32, top: FILA[i] + 56, opacity: tw(fr, 30 + i * 6, 50 + i * 6)}}>
            <div style={{fontFamily: f.mono, fontSize: 26, fontWeight: 500}}>{m.id}</div>
            <div style={{fontSize: 19, color: c.muted, marginTop: 4}}>{m.detalle}</div>
          </div>
        ))}
      </Foco>
      {matriz.flatMap((m, a) =>
        m.celdas.map((x, b) => (
          <Celda key={`${m.id}${x.regla}`} i={a * 3 + b} rotulo={x.rotulo} estado={x.estado} x={COL[b]} y={FILA[a]} atenua={a === 0 && b === 0 ? 0 : foco} />
        )),
      )}
    </div>
  );
};

const Tarjeta: React.FC<{i: number; objeto: string; codigo: string; titulo: string; texto: string; tono: 'solar' | 'arcilla'; estado: string; atenua: number}> = ({i, objeto, codigo, titulo, texto, tono, estado, atenua}) => {
  const fr = useCurrentFrame();
  const p = tw(fr, LISTA + 8 + i * 9, LISTA + 40 + i * 9);
  return (
    <Foco d={atenua} style={{position: 'absolute', left: 32, width: 1140, top: 96 + i * 142, height: 128, opacity: p * (1 - atenua * 0.62), transform: `translateY(${(1 - p) * 60}px)`, filter: p < 1 ? `blur(${(1 - p) * 10}px)` : atenua > 0.01 ? `blur(${atenua * 3}px)` : undefined}}>
      <div style={{position: 'absolute', inset: 0, background: '#fff', borderRadius: 16, border: `1px solid ${c.line}`, padding: '16px 22px', boxShadow: '0 10px 28px -18px rgba(13,15,20,.35)'}}>
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
          <span style={{fontFamily: f.mono, fontSize: 18, color: c.muted}}>Regla {codigo} · {objeto}</span>
          <Estado tono={tono} size={17}>{estado}</Estado>
        </div>
        <div style={{fontSize: 25, fontWeight: 600, marginTop: 4, letterSpacing: '-.01em'}}>{titulo}</div>
        <div style={{fontSize: 19, color: 'rgba(13,15,20,.72)', marginTop: 2}}>{texto}</div>
      </div>
    </Foco>
  );
};

const Lista: React.FC = () => {
  const fr = useCurrentFrame();
  const foco = tw(fr, 452, 480);
  const n = Math.floor(tw(fr, LISTA + 8, LISTA + 40, 0, huecos.open.length + 0.01));
  const falta = huecos.open.find((g) => g.rule.code === 'R-02')!;
  const dato = compras.objects.find((o) => o.id === 'FAC-2026-889')!.attributes.find((a) => a.key === 'recargo_transporte')!;
  const barra = tw(fr, 480, 530, 0, dato.confidence);
  return (
    <div style={{position: 'absolute', inset: 0, opacity: tw(fr, LISTA, LISTA + 12)}}>
      <Foco d={foco} style={{position: 'absolute', left: 32, top: 24, right: 32}}>
        <div style={{display: 'flex', alignItems: 'baseline', gap: 12, fontSize: 32, fontWeight: 600, letterSpacing: '-.02em'}}>
          <span style={{fontFamily: f.mono, color: c.arcillaInk}}>{n}</span> huecos abiertos
        </div>
      </Foco>
      <Tarjeta i={0} atenua={foco} objeto="PC-0412" codigo="R-03" tono="solar" estado="Requiere aprobación" titulo="Falta la aprobación de Dirección financiera" texto="El importe neto (18.450,00 €) supera el umbral de 15.000,00 € · Política de Compras, pág. 4" />
      <Tarjeta i={1} atenua={foco} objeto="PC-0419" codigo="R-01" tono="arcilla" estado="Incumplida" titulo="Certificado AEAT caducado el 12/10/2026" texto={`Expediente de homologación de PROV-024 · pág. ${evCertificado.page}`} />
      <Tarjeta i={2} atenua={foco} objeto="PC-0419" codigo="R-02" tono="arcilla" estado="Falta evidencia" titulo="Tres ofertas comparativas sin evidencia" texto={`No consta evidencia de: ${falta.pendientes.map((k) => k.replace(/_/g, ' ')).join(', ')}`} />
      <div style={{position: 'absolute', left: 32, width: 1140, top: 530, height: 240, borderRadius: 16, border: `1.5px dashed rgba(138,90,0,.45)`, background: '#fffaf0', padding: '20px 26px', opacity: tw(fr, 430, 456), transform: `translateY(${tw(fr, 430, 456, 40, 0)}px)`}}>
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
          <span style={{fontSize: 21, fontWeight: 600}}>Datos por validar ({huecos.pendingData.length})</span>
          <Estado tono="solar" size={17}>No cuenta como hueco</Estado>
        </div>
        <div style={{fontFamily: f.mono, fontSize: 19, color: c.muted, marginTop: 10}}>FAC-2026-889 · {dato.label}: {dato.value}</div>
        <div style={{position: 'relative', height: 16, borderRadius: 99, background: '#efe9db', marginTop: 34}}>
          <div style={{position: 'absolute', left: 0, top: 0, bottom: 0, width: `${barra * 100}%`, borderRadius: 99, background: c.solar}} />
          <div style={{position: 'absolute', left: '80%', top: -10, bottom: -10, width: 3, background: c.ink}} />
          <div style={{position: 'absolute', left: '80%', top: -38, transform: 'translateX(-50%)', fontFamily: f.mono, fontSize: 17}}>mínimo 0,80</div>
          <div style={{position: 'absolute', left: `${barra * 100}%`, top: 24, transform: 'translateX(-50%)', fontFamily: f.mono, fontSize: 20, fontWeight: 500, color: c.solarInk}}>{barra.toFixed(2).replace('.', ',')}</div>
        </div>
      </div>
    </div>
  );
};

export const Detecta: React.FC = () => {
  const fr = useCurrentFrame();
  return (
    <AbsoluteFill>
      <Fondo />
      <Camara
        k={[
          {f: 0, x: 700, y: 480, z: 0.8, rx: 26, ry: 8, rz: -1.5},
          {f: 56, x: 760, y: 430, z: 1.06},
          {f: 215, x: 780, y: 440, z: 1.12},
          {f: 256, x: CX + COL[0] + 148, y: CY + FILA[0] + 90, z: 1.85},
          {f: 306, x: CX + COL[0] + 148, y: CY + FILA[0] + 90, z: 1.95},
          {f: 336, x: 790, y: 330, z: 1.2},
          {f: 440, x: 790, y: 345, z: 1.26},
          {f: 482, x: 798, y: 690, z: 1.48, zv: 1.3},
          {f: 600, x: 798, y: 695, z: 1.54, zv: 1.32},
        ]}
      >
        <Ventana
          activo="Huecos"
          cuenta={fr >= LISTA ? <span style={{fontFamily: f.mono, fontSize: 14, padding: '1px 8px', borderRadius: 99, background: c.arcilla, color: c.arcillaInk}}>{huecos.open.length}</span> : null}
        >
          {fr < LISTA + 14 ? <Matriz /> : null}
          {fr >= LISTA ? <Lista /> : null}
        </Ventana>
        <Destello de={14} />
      </Camara>
      <Leyendas
        items={[
          {t: 'No hace falta preguntar.', de: 8, a: 88},
          {t: 'Al abrir el proceso, cruza cada regla con cada objeto.', de: 96, a: 222},
          {t: 'Lo que no ha comprobado, *no lo da por cumplido.*', de: 236, a: 318},
          {t: 'Tres huecos. Cada uno, con su regla y *su fuente.*', de: 338, a: 446},
          {t: 'Una lectura dudosa no cuenta hasta que *la validas.*', de: 468, a: 600},
        ]}
      />
      <Entorno />
      <Sfx n="whoosh" at={4} v={0.35} />
      {matriz.flatMap((m, a) =>
        m.celdas.map((x, b) => (
          <Sfx key={`${a}${b}`} n={['incumplida', 'sin_evidencia', 'requiere_aprobacion'].includes(x.estado) ? 'alert' : 'tick'} at={INICIO + (a * 3 + b) * PASO + 12} v={['incumplida', 'sin_evidencia', 'requiere_aprobacion'].includes(x.estado) ? 0.38 : 0.4} />
        )),
      )}
      <Sfx n="whoosh-soft" at={232} v={0.22} />
      <Sfx n="whoosh" at={LISTA - 6} v={0.26} />
      <Sfx n="whoosh-soft" at={456} v={0.2} />
    </AbsoluteFill>
  );
};
