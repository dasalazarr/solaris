import './fonts';
import React from 'react';
import {AbsoluteFill, Composition, Series} from 'remotion';
import {FPS, c} from './tokens';
import {Fondo_Musical, Fundido, Grano, Vineta} from './fx';
import {Cruza, DUR_CRUZA} from './Cruza';
import {DUR_DETECTA, Detecta} from './Detecta';
import {DUR_FIRMA, Firma} from './Firma';
import {DUR_PLANTILLA, Plantilla} from './Plantilla';
import {Companero, CierreReel, ContratoEscena, DUR_CIERRE_REEL, DUR_CONTRATO, DUR_DECIDE, DUR_GANCHO, DUR_REGLA, Decide, Gancho, Regla} from './Reel';
import {Apertura, Capitulo, Cierre, DUR_APERTURA, DUR_CAPITULO, DUR_CIERRE, DUR_PROBLEMA, Problema} from './Titulos';

const SOLAPE = 12;

type Plano = {dur: number; el: React.ReactNode};
const cap = (n: string, palabra: string, titulo: string): Plano => ({dur: DUR_CAPITULO, el: <Capitulo n={n} palabra={palabra} titulo={titulo} />});
const CAP1 = cap('01', 'Cruza', 'Responde con *la fuente.*');
const CAP2 = cap('02', 'Detecta', 'Encuentra *lo que falta.*');
const CAP3 = cap('03', 'Firma', 'Decide *una persona.*');
const CRUZA: Plano = {dur: DUR_CRUZA, el: <Cruza />};
const DETECTA: Plano = {dur: DUR_DETECTA, el: <Detecta />};
const FIRMA: Plano = {dur: DUR_FIRMA, el: <Firma />};
const CIERRE: Plano = {dur: DUR_CIERRE, el: <Cierre />};

const duracion = (p: Plano[]) => p.reduce((s, x) => s + x.dur, 0) - SOLAPE * (p.length - 1);

const Montaje: React.FC<{planos: Plano[]; sobre?: React.ReactNode}> = ({planos, sobre}) => (
  <AbsoluteFill style={{background: c.ink}}>
    <Series>
      {planos.map((p, i) => (
        <Series.Sequence key={i} durationInFrames={p.dur} offset={i ? -SOLAPE : 0}>
          <Fundido dur={p.dur} entrada={i ? SOLAPE : 10} salida={i === planos.length - 1 ? 16 : SOLAPE}>{p.el}</Fundido>
        </Series.Sequence>
      ))}
    </Series>
    {sobre}
    <Vineta />
    <Grano />
    <Fondo_Musical dur={duracion(planos)} />
  </AbsoluteFill>
);

const PIEZAS: Record<string, Plano[]> = {
  Pelicula: [{dur: DUR_APERTURA, el: <Apertura />}, {dur: DUR_PROBLEMA, el: <Problema />}, CAP1, CRUZA, CAP2, DETECTA, CAP3, FIRMA, CIERRE],
  Cruza: [CAP1, CRUZA, CIERRE],
  Detecta: [CAP2, DETECTA, CIERRE],
  Firma: [CAP3, FIRMA, CIERRE],
  // Base para piezas nuevas (src/Plantilla.tsx). render:all no la renderiza.
  Plantilla: [{dur: DUR_PLANTILLA, el: <Plantilla />}],
};
// Reel comercial: va aparte porque sus formatos son 9:16 y 16:9.
const REEL: Plano[] = [
  {dur: DUR_GANCHO, el: <Gancho />},
  {dur: DUR_REGLA, el: <Regla />},
  {dur: DUR_CONTRATO, el: <ContratoEscena />},
  {dur: DUR_DECIDE, el: <Decide />},
  {dur: DUR_CIERRE_REEL, el: <CierreReel />},
];
// En 9:16 la mascota dorada acompaña todo el reel (ADR-0024).
const INICIOS_REEL = REEL.map((_, i) => REEL.slice(0, i).reduce((t, p) => t + p.dur - SOLAPE, 0));
const FORMATOS_REEL: {id: string; width: number; height: number; mascota?: boolean}[] = [
  {id: 'ReelAlta-9x16', width: 1080, height: 1920, mascota: true},
  {id: 'ReelAlta-16x9', width: 1920, height: 1080},
];
const FORMATOS = [
  {id: '16x9', width: 1920, height: 1080},
  {id: '4x5', width: 1080, height: 1350},
];

export const Root: React.FC = () => (
  <>
    {FORMATOS_REEL.map((fm) => {
      const Pieza: React.FC = () => <Montaje planos={REEL} sobre={fm.mascota ? <Companero inicios={INICIOS_REEL} fin={duracion(REEL)} /> : undefined} />;
      return <Composition key={fm.id} id={fm.id} component={Pieza} durationInFrames={duracion(REEL)} fps={FPS} width={fm.width} height={fm.height} />;
    })}
    {Object.entries(PIEZAS).flatMap(([nombre, planos]) =>
      FORMATOS.map((fm) => {
        const Pieza: React.FC = () => <Montaje planos={planos} />;
        return <Composition key={`${nombre}-${fm.id}`} id={`${nombre}-${fm.id}`} component={Pieza} durationInFrames={duracion(planos)} fps={FPS} width={fm.width} height={fm.height} />;
      }),
    )}
  </>
);
