import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {c, f} from './tokens';
import {Aparece, Camara, Cursor, Destello, Entorno, Evidencia, Foco, Fondo, Haz, Leyendas, Sfx, Teclas, tw, useResorte} from './fx';
import {CX, CY, Chip, Estado, Ventana} from './ventana';
import {avisoSinFuente, compras, evPolitica, fundamento, pregunta, preguntaSinFuente, respuesta, respuestaSinFuente} from './datos';

export const DUR_CRUZA = 690;

const CLIC = 268;
const CAMBIO = 520;
const regla = compras.rules.find((r) => r.code === 'R-03')!;
const plazo = compras.objects[0].attributes.find((a) => a.key === 'plazo_entrega_estimado')!;

const Burbuja: React.FC<{texto: string; de: number; dur: number; left?: number; top?: number; width?: number}> = ({texto, de, dur, left = 80, top = 22, width = 526}) => {
  const fr = useCurrentFrame();
  const n = Math.floor(tw(fr, de, de + dur, 0, texto.length, (x) => x));
  const caret = fr < de + dur && fr >= de && Math.floor(fr / 8) % 2 === 0;
  return (
    <div style={{position: 'absolute', left, top, width, padding: '14px 20px', borderRadius: '20px 20px 6px 20px', background: c.ink, color: '#fff', fontSize: 20, lineHeight: 1.36, opacity: tw(fr, de - 8, de)}}>
      <span style={{visibility: 'hidden'}}>{texto}</span>
      <span style={{position: 'absolute', left: 20, right: 20, top: 14}}>
        {texto.slice(0, n)}
        {caret ? <span style={{display: 'inline-block', width: 2, height: 21, background: c.solar, marginLeft: 2, verticalAlign: -3}} /> : null}
      </span>
    </div>
  );
};

const FilaCita: React.FC<{n: number; texto: string; top: number; de: number; activa?: boolean}> = ({n, texto, top, de, activa}) => {
  const fr = useCurrentFrame();
  const p = tw(fr, de, de + 18);
  return (
    <div style={{position: 'absolute', left: 28, width: 578, top, height: 50, display: 'flex', alignItems: 'center', gap: 12, padding: '0 12px', borderRadius: 10, opacity: p, transform: `translateY(${(1 - p) * 14}px)`, background: activa ? c.solarSoft : '#fff', border: `1px solid ${activa ? c.solar : c.line}`, fontSize: 17, fontFamily: f.mono, color: 'rgba(13,15,20,.8)', whiteSpace: 'nowrap'}}>
      <Chip n={n} activo={activa} />
      {texto}
    </div>
  );
};

const Fase1: React.FC = () => {
  const fr = useCurrentFrame();
  const abierto = fr >= CLIC;
  const panel = tw(fr, CLIC, CLIC + 26);
  const enfoqueDoc = Math.min(tw(fr, CLIC + 6, CLIC + 36), 1 - tw(fr, 420, 448));
  const enfoqueRegla = tw(fr, 430, 460);
  return (
    <>
      <Foco d={enfoqueDoc} style={{position: 'absolute', left: 0, top: 0, width: 620, height: 812}}>
        <Burbuja texto={pregunta} de={34} dur={70} />
        {fr >= 106 && fr < 142 ? (
          <div style={{position: 'absolute', left: 28, top: 158, fontFamily: f.mono, fontSize: 18, color: c.muted, opacity: 0.5 + Math.sin(fr / 3) * 0.4}}>Buscando en {Object.keys(compras.evidences).length} documentos…</div>
        ) : null}
        {fr >= 142 ? (
          <div style={{position: 'absolute', left: 28, top: 150, width: 578, fontSize: 22, fontWeight: 500, lineHeight: 1.38}}>
            <Aparece texto={respuesta} de={142} /> <Chip n={1} /> <Chip n={2} activo={abierto} />
          </div>
        ) : null}
        {fr >= 176 ? (
          <div style={{position: 'absolute', left: 28, top: 306, width: 578, fontSize: 17.5, lineHeight: 1.42, color: 'rgba(13,15,20,.78)'}}>
            <Aparece texto={fundamento} de={176} />
          </div>
        ) : null}
        <FilaCita n={1} texto="Solicitud de Pedido PC-0412 · Pág. 1" top={448} de={214} />
        <FilaCita n={2} texto="Política de Compras v3.2 · Pág. 4" top={506} de={222} activa={abierto} />
        <div style={{position: 'absolute', left: 28, top: 574, width: 578, padding: '13px 16px', borderRadius: 12, background: c.solarSoft, border: `1px solid rgba(138,90,0,.3)`, opacity: tw(fr, 232, 250), display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
          <div>
            <div style={{fontFamily: f.mono, fontSize: 17, color: c.solarInk}}>Regla {regla.code} · {regla.thresholdSummary}</div>
            <div style={{fontSize: 19, fontWeight: 600, marginTop: 3}}>Requiere aprobación de {regla.approverRole}</div>
          </div>
        </div>
        <div style={{position: 'absolute', left: 28, top: 668, width: 578, padding: '13px 16px', borderRadius: 12, background: c.ink2, opacity: enfoqueRegla, transform: `translateY(${(1 - enfoqueRegla) * 18}px)`}}>
          <div style={{fontSize: 15, color: 'rgba(255,255,255,.66)', marginBottom: 5}}>Cómo lo evalúa el motor</div>
          <div style={{fontFamily: f.mono, fontSize: 16.5, lineHeight: 1.42, color: c.solar}}>{regla.expression}</div>
        </div>
      </Foco>
      <div style={{position: 'absolute', left: 620, top: 0, width: 584, height: 812, background: '#f6f4ee', borderLeft: `1px solid ${c.line}`}}>
        <div style={{position: 'absolute', left: 0, right: 0, top: 300, textAlign: 'center', fontSize: 18, color: c.muted, opacity: 1 - panel}}>Pulsa una cita para ver el documento</div>
        {abierto ? (
          <div style={{position: 'absolute', left: 24, right: 24, top: 22, bottom: 22, background: c.sheet, border: `1px solid ${c.line}`, borderRadius: 14, padding: '22px 26px', opacity: panel, transform: `translateX(${(1 - panel) * 80}px)`, boxShadow: '0 22px 50px -24px rgba(13,15,20,.3)'}}>
            <div style={{fontSize: 19, fontWeight: 600}}>{evPolitica.documentTitle}</div>
            <div style={{fontFamily: f.mono, fontSize: 15.5, color: c.muted, marginTop: 6}}>Pág. {evPolitica.page} · {evPolitica.section}</div>
            <div style={{fontFamily: f.serif, fontSize: 21, lineHeight: 1.46, marginTop: 20, color: 'rgba(13,15,20,.56)'}}>{evPolitica.precedingText}</div>
            <div style={{fontFamily: f.serif, fontSize: 23, lineHeight: 1.46, marginTop: 14, color: c.ink}}>
              <Evidencia texto={evPolitica.highlightedQuote} de={CLIC + 34} dur={58} />
            </div>
          </div>
        ) : null}
      </div>
      {/* Luz sobre el fragmento citado cuando la barra llega al final */}
      {fr > CLIC + 60 && fr < 430 ? (
        <div style={{position: 'absolute', left: 620, top: 150, width: 584, height: 400, pointerEvents: 'none', mixBlendMode: 'multiply', opacity: tw(fr, CLIC + 60, CLIC + 92) * 0.12, background: `radial-gradient(closest-side, ${c.solar}, transparent)`}} />
      ) : null}
    </>
  );
};

const Fase2: React.FC = () => {
  const fr = useCurrentFrame();
  const local = CAMBIO + 14;
  const aviso = useResorte(local + 92, 15);
  return (
    <div style={{position: 'absolute', inset: 0, opacity: tw(fr, CAMBIO, CAMBIO + 14)}}>
      <Burbuja texto={preguntaSinFuente} de={local} dur={40} left={420} width={750} />
      <div style={{position: 'absolute', left: 60, top: 150, width: 1090, fontSize: 28, fontWeight: 500, lineHeight: 1.34}}>
        {fr >= local + 44 ? <Aparece texto={respuestaSinFuente} de={local + 44} /> : null}
      </div>
      <div style={{position: 'absolute', left: 60, width: 1090, top: 290, padding: '22px 26px', borderRadius: 16, background: c.arcilla, border: '1px solid rgba(140,42,31,.28)', opacity: aviso, transform: `scale(${0.94 + aviso * 0.06})`, boxShadow: `0 0 ${tw(fr, local + 92, local + 120, 70, 0)}px rgba(140,42,31,.5)`}}>
        <Estado tono="arcilla" size={18} style={{background: '#fff', border: '1px solid rgba(140,42,31,.3)'}}>Sin fuente</Estado>
        <div style={{fontSize: 23, fontWeight: 500, color: c.arcillaInk, marginTop: 12, lineHeight: 1.36}}>{avisoSinFuente}</div>
      </div>
      <div style={{position: 'absolute', left: 60, width: 1090, top: 470, padding: '18px 26px', borderRadius: 14, background: '#fff', border: `1px solid ${c.line}`, opacity: tw(fr, local + 108, local + 126), display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 21}}>
        <span>{plazo.label}: <span style={{textDecoration: 'line-through', color: c.muted}}>{plazo.value}</span></span>
        <Estado tono="gris" size={17}>El motor no lo usa</Estado>
      </div>
    </div>
  );
};

export const Cruza: React.FC = () => {
  const fr = useCurrentFrame();
  return (
    <AbsoluteFill>
      <Fondo />
      <Camara
        k={[
          {f: 0, x: 700, y: 480, z: 0.8, rx: 28, ry: -9, rz: 1.5},
          {f: 56, x: 700, y: 430, z: 1},
          {f: 130, x: 500, y: 240, z: 1.42},
          {f: 225, x: 500, y: 340, z: 1.42},
          {f: 262, x: 470, y: 590, z: 1.55},
          {f: 306, x: 1118, y: 300, z: 1.72},
          {f: 420, x: 1118, y: 320, z: 1.82},
          {f: 454, x: 520, y: 720, z: 1.62},
          {f: 512, x: 520, y: 720, z: 1.66},
          {f: 540, x: 800, y: 330, z: 1.22},
          {f: 650, x: 800, y: 400, z: 1.32},
        ]}
      >
        <Ventana activo="Preguntar">
          {fr < CAMBIO + 14 ? <div style={{position: 'absolute', inset: 0, opacity: 1 - tw(fr, CAMBIO, CAMBIO + 14)}}><Fase1 /></div> : null}
          {fr >= CAMBIO ? <Fase2 /> : null}
        </Ventana>
        <Destello de={14} />
        <Destello de={CLIC + 62} dur={40} fuerza={0.3} />
        <Haz de={CLIC + 4} dur={30} a={[CX + 64, CY + 531]} b={[CX + 668, CY + 268]} curva={-170} hasta={CLIC + 80} />
        <Cursor de={236} a={CLIC + 34} escala={0.8} k={[{f: 236, x: 700, y: 800}, {f: 264, x: CX + 240, y: CY + 534}]} clics={[CLIC]} />
      </Camara>
      <Leyendas
        items={[
          {t: 'Pregúntale al proceso.', de: 8, a: 128},
          {t: 'Responde. Y enseña de dónde lo saca.', de: 142, a: 262},
          {t: 'El párrafo exacto. *Página 4, § 2.1.*', de: 286, a: 422},
          {t: 'La regla no la decide el modelo. La evalúa *el código.*', de: 436, a: 516},
          {t: 'Y si no consta, *no lo afirma.*', de: 562, a: 682},
        ]}
      />
      <Entorno />
      <Sfx n="whoosh" at={4} v={0.35} />
      <Teclas de={34} a={104} />
      <Sfx n="whoosh-soft" at={254} v={0.2} />
      <Sfx n="click" at={CLIC} v={0.5} />
      <Sfx n="whoosh" at={CLIC + 4} v={0.28} />
      <Sfx n="ping" at={CLIC + 36} v={0.28} />
      <Sfx n="whoosh-soft" at={428} v={0.22} />
      <Sfx n="whoosh" at={CAMBIO} v={0.22} />
      <Teclas de={CAMBIO + 14} a={CAMBIO + 54} />
      <Sfx n="alert" at={CAMBIO + 106} v={0.4} />
    </AbsoluteFill>
  );
};
