import type { StepView } from "@/lib/inbox";

const ICON: Record<StepView["state"], string> = {
  done: "✓",
  active: "…",
  pending: "○",
  failed: "✕",
};

const STATE_TEXT: Record<StepView["state"], string> = {
  done: "terminado",
  active: "en curso",
  pending: "pendiente",
  failed: "no completado",
};

/** Lista de pasos del grafo 8D (intake → D1 ∥ D2 ∥ D3 → D4 → pendiente de aprobación). */
export function ProgressSteps({ steps, finalLabel, finalDone }: {
  steps: readonly StepView[];
  finalLabel: string;
  finalDone: boolean;
}) {
  return (
    <ol className="steps" data-testid="progress-steps">
      {steps.map((s) => (
        <li key={s.node} className={`step s-${s.state}`}>
          <span className="step-icon" aria-hidden="true">{ICON[s.state]}</span>
          <span>
            <b>{s.label}</b>
            <span className="visually-hidden">: {STATE_TEXT[s.state]}</span>
            {s.ms !== null && <span className="step-ms"> · {(s.ms / 1000).toFixed(1)} s</span>}
            <br />
            <span className="note">{s.detail}</span>
          </span>
        </li>
      ))}
      <li className={`step ${finalDone ? "s-done" : "s-pending"}`}>
        <span className="step-icon" aria-hidden="true">{finalDone ? "✓" : "○"}</span>
        <span>
          <b>{finalLabel}</b>
          <span className="visually-hidden">: {finalDone ? "terminado" : "pendiente"}</span>
        </span>
      </li>
    </ol>
  );
}
