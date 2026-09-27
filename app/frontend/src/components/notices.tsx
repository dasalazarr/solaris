import type { ReactNode } from "react";

/**
 * Avisos comunes. El aviso de IA (art. 50 del AI Act, F11) es obligatorio en toda pantalla con
 * salida de IA: `AiNotice` va en el layout de la app (todas las pantallas autenticadas) y
 * `AiLabel` marca cada bloque concreto generado por IA (lo usan L01–L03 desde M5-T3).
 */

export const AI_LABEL_TEXT = "Generado por IA · revisar antes de usar";

export function AiNotice() {
  return (
    <div className="ai-notice" role="note" aria-label="Aviso de sistema de IA">
      <b>Sistema de IA.</b> Los borradores, resúmenes e hipótesis de esta aplicación los genera un
      modelo de IA. Revísalos antes de usarlos; nada se envía sin aprobación humana (AI Act,
      art. 50).
    </div>
  );
}

export function AiLabel() {
  return <span className="tag t-info ai-label">{AI_LABEL_TEXT}</span>;
}

export function SynthBand() {
  return (
    <div className="synth">
      Datos sintéticos · demo. Empresa, clientes, personas y códigos ficticios.
    </div>
  );
}

export function Forbidden({ what, detail }: { what: string; detail?: string }) {
  return (
    <div className="alert a-bad" role="alert">
      <b>No tienes permiso para ver {what}.</b>
      <br />
      {detail ?? "El servidor ha denegado el acceso para tu rol."} Si crees que deberías tenerlo,
      pide al administrador que revise tu rol.
    </div>
  );
}

export function ServiceError({ children }: { children?: ReactNode }) {
  return (
    <div className="alert a-warn" role="alert">
      <b>El servicio no está disponible ahora mismo.</b>
      <br />
      {children ?? "Inténtalo de nuevo en unos segundos. Si persiste, avisa al administrador."}
    </div>
  );
}

export function Placeholder({ task, children }: { task: string; children?: ReactNode }) {
  return (
    <div className="card placeholder">
      <p className="note">
        Pantalla en construcción · se completa en <b>{task}</b>.
      </p>
      {children}
    </div>
  );
}
