/**
 * Cliente API tipado del navegador (M5-T2). Solo habla con el BFF de Next (`/api/...`), nunca con
 * el backend: el JWT vive en una cookie httpOnly que el navegador envía sola (SameSite=Strict).
 *
 * Errores normalizados en `ApiError`:
 * - 401 → la sesión caducó o se cerró: se llama a `onUnauthorized` (por defecto, volver al login).
 * - 403 → el backend deniega la acción para tu rol (o la acción no está permitida aún).
 * - 409 → conflicto de estado/versión (p. ej. el caso ya no está pendiente o cambió).
 * - resto → mensaje genérico en castellano; nunca se muestra un volcado técnico.
 */

import { CSRF_HEADER } from "./bff";

export type ApiErrorKind =
  | "unauthorized"
  | "forbidden"
  | "not_found"
  | "conflict"
  | "validation"
  | "too_large"
  | "rate_limited"
  | "unavailable"
  | "network"
  | "server";

const FALLBACK: Record<ApiErrorKind, string> = {
  unauthorized: "Tu sesión ha caducado. Vuelve a iniciar sesión.",
  forbidden: "Tu rol no tiene permiso para esta acción.",
  not_found: "No se ha encontrado.",
  conflict: "El elemento ha cambiado mientras trabajabas. Recarga para ver la versión actual.",
  validation: "Los datos enviados no son válidos.",
  too_large: "El fichero es demasiado grande.",
  rate_limited: "Demasiadas peticiones seguidas. Espera un minuto y vuelve a intentarlo.",
  unavailable: "El servicio no está disponible ahora mismo. Inténtalo de nuevo en unos segundos.",
  network: "No hay conexión con el servidor.",
  server: "Se ha producido un error inesperado.",
};

export function kindFor(status: number): ApiErrorKind {
  if (status === 401) return "unauthorized";
  if (status === 403) return "forbidden";
  if (status === 404) return "not_found";
  if (status === 409) return "conflict";
  if (status === 413) return "too_large";
  if (status === 415 || status === 422 || status === 400 || status === 411) return "validation";
  if (status === 429) return "rate_limited";
  if (status === 502 || status === 503 || status === 504) return "unavailable";
  return "server";
}

export class ApiError extends Error {
  readonly status: number;
  readonly kind: ApiErrorKind;
  /** Mensaje para mostrar al usuario (el `detail` del backend si es texto legible). */
  readonly userMessage: string;

  constructor(status: number, detail?: string | null) {
    const kind = status === 0 ? "network" : kindFor(status);
    const msg = detail && detail.trim() ? detail.trim() : FALLBACK[kind];
    super(msg);
    this.name = "ApiError";
    this.status = status;
    this.kind = kind;
    this.userMessage = msg;
  }
}

/**
 * Extrae un `detail` legible del cuerpo de error de FastAPI. Solo textos cortos: las listas de
 * validación de Pydantic (que pueden repetir la entrada) se sustituyen por el genérico. Los 5xx
 * siempre usan el genérico.
 */
export function detailFrom(status: number, body: unknown): string | null {
  if (status >= 500 && status !== 503) return null;
  if (typeof body !== "object" || body === null) return null;
  const d = (body as { detail?: unknown }).detail;
  if (typeof d === "string" && d.length > 0 && d.length <= 300) return d;
  return null;
}

export interface ClientOptions {
  fetch?: typeof fetch;
  /** Se llama en un 401 (sesión caducada). Por defecto redirige al login. */
  onUnauthorized?: () => void;
  /** Se llama tras cada respuesta del servidor (renueva el temporizador de inactividad). */
  onActivity?: () => void;
}

export interface RequestOptions {
  method?: "GET" | "POST" | "DELETE";
  json?: unknown;
  form?: FormData;
  signal?: AbortSignal;
}

export function defaultOnUnauthorized(): void {
  if (typeof window === "undefined") return;
  // Navegación completa a propósito: descarta todo el estado de cliente y la caché RSC de la sesión.
  // eslint-disable-next-line @next/next/no-location-assign-relative-destination
  window.location.assign("/login?motivo=sesion");
}

export function createApiClient(opts: ClientOptions = {}) {
  const doFetch = opts.fetch ?? ((...a: Parameters<typeof fetch>) => fetch(...a));
  const onUnauthorized = opts.onUnauthorized ?? defaultOnUnauthorized;

  async function request<T>(url: string, ro: RequestOptions = {}): Promise<T> {
    const method = ro.method ?? (ro.json !== undefined || ro.form ? "POST" : "GET");
    const headers = new Headers({ accept: "application/json" });
    let body: BodyInit | undefined;
    if (method !== "GET") headers.set(CSRF_HEADER, "1");
    if (ro.json !== undefined) {
      headers.set("content-type", "application/json");
      body = JSON.stringify(ro.json);
    } else if (ro.form) {
      body = ro.form; // el navegador pone el boundary de multipart
    }

    let res: Response;
    try {
      res = await doFetch(url, {
        method,
        headers,
        body,
        credentials: "same-origin",
        cache: "no-store",
        signal: ro.signal,
      });
    } catch (e) {
      if (e instanceof DOMException && e.name === "AbortError") throw e;
      throw new ApiError(0);
    }
    opts.onActivity?.();

    if (res.ok) {
      if (res.status === 204) return undefined as T;
      const ct = res.headers.get("content-type") ?? "";
      return (ct.includes("application/json") ? await res.json() : await res.text()) as T;
    }
    const errBody: unknown = await res.json().catch(() => null);
    const err = new ApiError(res.status, detailFrom(res.status, errBody));
    if (res.status === 401) onUnauthorized();
    return Promise.reject(err);
  }

  const backend = <T>(path: string, ro?: RequestOptions) =>
    request<T>(`/api/backend/${path.replace(/^\/+/, "")}`, ro);

  return {
    request,
    backend,
    session: {
      login: (username: string, password: string) =>
        request<SessionInfo>("/api/session", { method: "POST", json: { username, password } }),
      me: () => request<SessionInfo>("/api/session"),
      logout: () => request<void>("/api/session", { method: "DELETE" }),
    },
    approvals: () => backend<ApprovalsPage>("approvals"),
    /** L01: últimos casos 8D (M5-T3, `GET /8d`). */
    cases: () => backend<CaseListPage>("8d"),
    /** L01: extrae los campos de una reclamación sin crear el caso (`POST /complaints/parse`). */
    parseComplaint: (file: File, signal?: AbortSignal) =>
      backend<ComplaintParsed>("complaints/parse", { form: uploadForm(file), signal }),
    /** L01: crea el caso 8D con el mismo fichero y lanza el grafo en segundo plano (202). */
    createCase: (file: File) =>
      backend<CaseCreated>("8d", { form: uploadForm(file) }),
    getCase: (caseId: string, signal?: AbortSignal) =>
      backend<CaseView>(`8d/${encodeURIComponent(caseId)}`, { signal }),
    auditEvents: (params: Record<string, string> = {}) => {
      const qs = new URLSearchParams(params).toString();
      return backend<AuditPage>(`audit${qs ? `?${qs}` : ""}`);
    },
  };
}

/** Multipart con un único campo `file` (el backend rechaza cualquier otro campo). */
export function uploadForm(file: File): FormData {
  const fd = new FormData();
  fd.append("file", file, file.name);
  return fd;
}

export type ApiClient = ReturnType<typeof createApiClient>;

// --- tipos de respuesta del backend (los que usa la UI) -----------------------------------

export interface SessionInfo {
  user: string;
  role: string;
  idle_timeout_s: number;
}

export interface ApprovalItem {
  case_id: string;
  complaint_id: string | null;
  part_ref: string | null;
  customer: string | null;
  created_by: string;
  created_at: string;
  draft: string;
  version: string;
  required_roles: string[];
  can_approve: boolean;
  injection_suspected: boolean;
  warnings: string[];
  elapsed_s: number | null;
}

export interface ApprovalsPage {
  items: ApprovalItem[];
  count: number;
}

export interface AuditEvent {
  id: number;
  ts: string;
  event_type: string;
  actor_user: string | null;
  actor_role: string | null;
  case_id: string | null;
  source: string | null;
  payload: unknown;
}

export interface AuditPage {
  items: AuditEvent[];
  next_before_id: number | null;
}

// --- L01 (M5-T3): reclamaciones y casos 8D --------------------------------------------------

export type CaseStatus =
  | "queued"
  | "drafting"
  | "pending_approval"
  | "approved"
  | "rejected"
  | "error";

export type Channel = "visible" | "hidden_text" | "metadata";

export interface DeadlineInfo {
  text: string | null;
  due_date: string | null;
}

export interface CaseListItem {
  case_id: string;
  complaint_id: string | null;
  status: CaseStatus | string;
  customer: string | null;
  customer_name: string | null;
  part_ref: string | null;
  lot_codes: string[];
  qty_affected: number | null;
  issued_date: string | null;
  deadlines: { containment: DeadlineInfo; report_8d: DeadlineInfo };
  filename: string;
  source: string;
  created_by: string;
  created_at: string;
  injection_suspected: boolean;
  injection_channels: string[];
  review_note: boolean;
  warnings: string[];
  elapsed_s: number | null;
}

export interface CaseListPage {
  items: CaseListItem[];
  count: number;
}

export interface InjectionFinding {
  channel: Channel | string;
  location: Record<string, unknown>;
  excerpt: string;
  rule?: string;
}

export interface ReviewNoteItem {
  source: string;
  channel: string;
  location: Record<string, unknown>;
  excerpt: string;
  located?: boolean;
}

/** Aviso genérico del backend. `instruction_ignored` y `model_flagged_text` tienen forma propia. */
export interface BackendWarning {
  type: string;
  message?: string;
  node?: string;
  severity?: string;
  channels?: string[];
  findings?: InjectionFinding[];
  items?: ReviewNoteItem[];
  [k: string]: unknown;
}

export interface ParsedDeadline {
  text: string | null;
  value: number | null;
  unit: string | null;
  due_date: string | null;
}

export interface ComplaintParsed {
  complaint_id: string | null;
  customer_code: string | null;
  part_ref: string | null;
  drawing_no: string | null;
  lot_codes: string[];
  delivery_notes: string[];
  qty_affected: number | null;
  defect_description: string | null;
  requested_deadlines: { containment: ParsedDeadline | null; report_8d: ParsedDeadline | null };
  issued_date: string | null;
  language: string | null;
  template_ref: string | null;
  source: { filename: string; format: string; size: number; pages?: number | null };
  injection_suspected: boolean;
  injection_findings: InjectionFinding[];
  erp_match: { ok: boolean; checked: boolean; mismatches: { field: string }[] };
  field_sources: Record<string, string>;
  warnings: BackendWarning[];
  model: string | null;
  ai_generated: boolean;
}

export interface CaseCreated {
  case_id: string;
  status: string;
  events: string;
}

export interface ProgressEvent {
  node: string;
  outcome: string;
  ms: number;
  at: number;
}

export interface CaseView {
  case_id: string;
  complaint_id: string | null;
  status: CaseStatus | string;
  error: string | null;
  customer: { code: string | null; name: string | null };
  complaint: {
    complaint_id?: string | null;
    part_ref?: string | null;
    lot_codes?: string[] | null;
    qty_affected?: number | null;
    issued_date?: string | null;
    injection_suspected?: boolean | null;
  };
  warnings: BackendWarning[];
  progress: ProgressEvent[];
  pending_nodes: string[];
  elapsed_s: number | null;
  created_at: string;
  created_by: string;
  version: string;
}
