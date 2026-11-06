// Punto de partida para una función nueva. Copia este fichero, cambia los datos y añade la pieza a PIEZAS en Root.tsx.
// Regla: ningún dato escrito a mano. Se lee de product/lib a través de datos.ts.
import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {c, f} from './tokens';
import {Camara, Destello, Entorno, Fondo, Leyendas, Sfx, tw} from './fx';
import {Estado, Ventana} from './ventana';
import {compras} from './datos';

export const DUR_PLANTILLA = 240;

export const Plantilla: React.FC = () => {
  const fr = useCurrentFrame();
  const regla = compras.rules[0];
  return (
    <AbsoluteFill>
      <Fondo />
      {/* x e y son coordenadas de la ventana (1400 × 860); z = 1 la encaja en el ancho. zv solo aplica en 4:5. */}
      <Camara
        k={[
          {f: 0, x: 700, y: 480, z: 0.8, rx: 26, ry: -8, rz: 1.5},
          {f: 56, x: 700, y: 430, z: 1},
          {f: 200, x: 700, y: 300, z: 1.4, zv: 1.25},
        ]}
      >
        <Ventana activo="Huecos">
          <div style={{position: 'absolute', left: 32, top: 32, right: 32, opacity: tw(fr, 40, 62)}}>
            <div style={{fontFamily: f.mono, fontSize: 18, color: c.muted}}>Regla {regla.code}</div>
            <div style={{fontSize: 30, fontWeight: 600, margin: '6px 0 14px'}}>{regla.name}</div>
            <Estado tono="solar" size={18}>{regla.thresholdSummary}</Estado>
          </div>
        </Ventana>
        <Destello de={14} />
      </Camara>
      {/* Una idea por leyenda, de tú. Entre asteriscos va la cursiva solar. */}
      <Leyendas items={[{t: 'Una idea por plano. *Sin más.*', de: 8, a: 228}]} />
      {/* Obligatoria en todo plano de producto (principio 4). */}
      <Entorno />
      <Sfx n="whoosh" at={4} v={0.35} />
    </AbsoluteFill>
  );
};
