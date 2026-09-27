/**
 * Lógica pura de la bandeja L01 (M5-T3): etiquetas de estado, pasos del progreso, avisos de
 * seguridad y validación del fichero. Sin React ni Next para probarla con vitest (`inbox.test.ts`).
 *
 * Seguridad (R03, PAT-012):
 * - El aviso ROJO sale solo de `injection_suspected` / `instruction_ignored`, que activa el detector
 *   determinista del backend. La señal del LLM sin corroborar (`model_flagged_text`) es una nota
 *   ÁMBAR de revisión y nunca se promociona a rojo aquí.
 * - Los extractos del documento son texto no confiable: se devuelven como `string` y la UI los
 *   pinta como texto (React escapa). Nunca `dangerouslySetInnerHTML`.
 */

import type {
  BackendWarning,
  CaseStatus,
  ComplaintParsed,
  InjectionFinding,
  ProgressEvent,
  ReviewNoteItem,
} from "./api-client";

// --- estado del caso ------------------------------------------------------------------------

export const STATUS_LABEL: Record<CaseStatus, string> = {
  queued: "En cola",
  drafting: "En proceso",
  pending_approval: "Pendiente de aprobación",
  approved: "Aprobado",
  rejected: "Rechazado",
  error: "Error",
};

export type Tone = "info" | "warn" | "ok" | "bad" | "muted";

const STATUS_TONE: Record<CaseStatus, Tone> = {
  queued: "muted",
  drafting: "info",
  pending_approval: "warn",
  approved: "ok",
  rejected: "bad",
  error: "bad",
};

export function statusLabel(status: string): string {
  return Object.hasOwn(STATUS_LABEL, status) ? STATUS_LABEL[status as CaseStatus] : status;
}

export function statusTone(status: string): Tone {
  return Object.hasOwn(STATUS_TONE, status) ? STATUS_TONE[status as CaseStatus] : "muted";
}

/** Estados en los que el grafo ya no avanza solo. */
export function isTerminal(status: string): boolean {
  return status !== "queued" && status !== "drafting";
}

// --- progreso por nodo ----------------------------------------------------------------------

export interface StepDef {
  node: string;
  label: string;
  detail: string;
  /** Nodos que tienen que terminar antes (grafo: intake → D1 ∥ D2 ∥ D3 → D4). */
  after: readonly string[];
}

export const STEPS: readonly StepDef[] = [
  { node: "intake", label: "Leyendo la reclamación", after: [],
    detail: "Extrae los campos y comprueba pieza y lote en el ERP (solo lectura)" },
  { node: "D1_team", label: "D1 · Equipo", after: ["intake"],
    detail: "Propone el equipo según la pieza y el turno" },
  { node: "D2_describe", label: "D2 · Descripción del problema (5W2H)", after: ["intake"],
    detail: "Redacta el 5W2H con citas a la reclamación" },
  { node: "D3_contain", label: "D3 · Contención con datos del ERP", after: ["intake"],
    detail: "Lotes, albaranes y stock afectados (ERP en solo lectura)" },
  { node: "D4_root_cause", label: "D4 · Causa raíz: 8D similares y AMFE",
    after: ["D1_team", "D3_contain"], detail: "Busca 8D antiguos y vincula el AMFE" },
];

export type StepState = "done" | "active" | "pending" | "failed";

export interface StepView extends StepDef {
  state: StepState;
  ms: number | null;
}

/**
 * Estado de cada paso a partir de los eventos de progreso. Un paso está "en curso" cuando sus
 * dependencias han terminado y él no; si el caso acabó en error, los que faltan quedan "fallidos".
 */
export function stepsFor(progress: readonly ProgressEvent[], status: string): StepView[] {
  const done = new Map<string, ProgressEvent>();
  for (const p of progress) done.set(p.node, p);
  const failed = status === "error";
  const finished = isTerminal(status);
  return STEPS.map((s) => {
    const ev = done.get(s.node);
    if (ev) {
      return { ...s, state: ev.outcome === "ok" ? "done" : "failed", ms: ev.ms };
    }
    const ready = s.after.every((n) => done.has(n));
    let state: StepState = "pending";
    if (failed) state = "failed";
    else if (ready && !finished) state = "active";
    return { ...s, state, ms: null };
  });
}

/** Anuncio corto para `aria-live` (lector de pantalla): último paso terminado o estado final. */
export function progressAnnouncement(steps: readonly StepView[], status: string): string {
  if (isTerminal(status)) return `Caso ${statusLabel(status).toLowerCase()}.`;
  const done = steps.filter((s) => s.state === "done").length;
  const active = steps.filter((s) => s.state === "active").map((s) => s.label);
  return `${done} de ${steps.length} pasos terminados.` +
    (active.length ? ` En curso: ${active.join(", ")}.` : "");
}

export function formatElapsed(seconds: number): string {
  const s = Math.max(0, Math.floor(seconds));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

// --- avisos de seguridad --------------------------------------------------------------------

const CHANNEL_LABEL: Record<string, string> = {
  visible: "texto visible",
  hidden_text: "texto oculto",
  metadata: "metadatos",
};

export function channelLabel(channel: string): string {
  return CHANNEL_LABEL[channel] ?? channel;
}

/** Ubicación legible: `{page: 2}` → "p. 2"; `{field: "pdf_metadata.keywords"}` → "campo …". */
export function locationLabel(location: Record<string, unknown> | null | undefined): string {
  if (!location) return "";
  const parts: string[] = [];
  const page = location.page;
  if (typeof page === "number" || (typeof page === "string" && /^\d+$/.test(page))) {
    parts.push(`p. ${page}`);
  }
  const field = location.field;
  if (typeof field === "string" && field) parts.push(`campo ${field}`);
  const header = location.header;
  if (typeof header === "string" && header) parts.push(`cabecera ${header}`);
  return parts.join(" · ");
}

export interface InjectionNotice {
  channels: string[];
  findings: InjectionFinding[];
}

export interface ReviewNotice {
  message: string;
  items: ReviewNoteItem[];
}

const REVIEW_DEFAULT =
  "El modelo señaló un fragmento como posible instrucción, pero el detector no lo confirma. " +
  "Revísalo; no se ha ejecutado nada.";

function uniq(xs: readonly string[]): string[] {
  return [...new Set(xs)].sort();
}

/**
 * Aviso rojo: SOLO si el backend lo marca con su detector determinista (`injection_suspected`
 * o un aviso `instruction_ignored`). `findings` puede venir en el parseo (`injection_findings`)
 * o dentro del aviso del caso 8D (`warnings[].findings`).
 */
export function injectionNotice(input: {
  injection_suspected?: boolean | null;
  injection_findings?: readonly InjectionFinding[] | null;
  warnings?: readonly BackendWarning[] | null;
}): InjectionNotice | null {
  const ws = (input.warnings ?? []).filter((w) => w.type === "instruction_ignored");
  const findings: InjectionFinding[] = [
    ...(input.injection_findings ?? []),
    ...ws.flatMap((w) => (Array.isArray(w.findings) ? w.findings : [])),
  ];
  if (!input.injection_suspected && ws.length === 0) return null;
  const channels = uniq([
    ...findings.map((f) => String(f.channel)),
    ...ws.flatMap((w) => (Array.isArray(w.channels) ? w.channels.map(String) : [])),
  ]);
  // Sin duplicados (el parseo y el aviso pueden traer el mismo hallazgo).
  const seen = new Set<string>();
  const unique = findings.filter((f) => {
    const k = `${f.channel}|${JSON.stringify(f.location)}|${f.excerpt}`;
    if (seen.has(k)) return false;
    seen.add(k);
    return true;
  });
  return { channels, findings: unique };
}

/** Nota ámbar de revisión (PAT-012): señal del LLM no corroborada. Nunca activa el rojo. */
export function reviewNotice(warnings: readonly BackendWarning[] | null | undefined):
  ReviewNotice | null {
  const ws = (warnings ?? []).filter((w) => w.type === "model_flagged_text");
  if (ws.length === 0) return null;
  const items = ws.flatMap((w) => (Array.isArray(w.items) ? w.items : []));
  const message = typeof ws[0].message === "string" && ws[0].message ? ws[0].message
    : REVIEW_DEFAULT;
  return { message, items };
}

/** Otros avisos del parseo que conviene enseñar (sin los de seguridad, que tienen su banner). */
export function otherWarnings(warnings: readonly BackendWarning[] | null | undefined): string[] {
  const out: string[] = [];
  for (const w of warnings ?? []) {
    if (w.type === "instruction_ignored" || w.type === "model_flagged_text") continue;
    if (typeof w.message === "string" && w.message) out.push(w.message);
  }
  return uniq(out);
}

// --- vista previa del parseo ----------------------------------------------------------------

export interface PreviewRow {
  label: string;
  value: string;
  mono?: boolean;
}

function dash(v: unknown): string {
  if (v === null || v === undefined || v === "") return "—";
  if (Array.isArray(v)) return v.length ? v.join(", ") : "—";
  return String(v);
}

function deadline(d: ComplaintParsed["requested_deadlines"]["containment"]): string {
  if (!d) return "—";
  const due = d.due_date ? formatDate(d.due_date) : null;
  if (d.text && due) return `${d.text} (${due})`;
  return d.text ?? due ?? "—";
}

export function previewRows(p: ComplaintParsed): PreviewRow[] {
  return [
    { label: "Reclamación", value: dash(p.complaint_id), mono: true },
    { label: "Cliente", value: dash(p.customer_code), mono: true },
    { label: "Pieza", value: dash(p.part_ref), mono: true },
    { label: "Lotes", value: dash(p.lot_codes), mono: true },
    { label: "Albaranes", value: dash(p.delivery_notes), mono: true },
    { label: "Piezas afectadas", value: dash(p.qty_affected) },
    { label: "Emitida", value: p.issued_date ? formatDate(p.issued_date) : "—" },
    { label: "Contención", value: deadline(p.requested_deadlines?.containment ?? null) },
    { label: "Informe 8D", value: deadline(p.requested_deadlines?.report_8d ?? null) },
  ];
}

// --- fechas y fichero -----------------------------------------------------------------------

/** `2026-09-22` o ISO completo → `22/09/2026` (sin depender de la zona horaria del navegador). */
export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(value);
  return m ? `${m[3]}/${m[2]}/${m[1]}` : value;
}

/** Límite por fichero del backend (`MAX_FILE_BYTES`). */
export const MAX_FILE_BYTES = 10 * 1024 * 1024;
const ALLOWED_EXT = /\.(pdf|eml)$/i;

/** Comprobación previa (solo UX): el backend vuelve a validar extensión, firma y tamaño. */
export function checkFile(file: { name: string; size: number }): string | null {
  if (!ALLOWED_EXT.test(file.name)) return "Solo se admiten reclamaciones en PDF o correo (.eml).";
  if (file.size === 0) return "El fichero está vacío.";
  if (file.size > MAX_FILE_BYTES) return "El fichero supera el máximo de 10 MB.";
  return null;
}
