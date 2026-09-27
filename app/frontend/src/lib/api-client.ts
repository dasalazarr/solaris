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
    auditEvents: (params: Record<string, string> = {}) => {
      const qs = new URLSearchParams(params).toString();
      return backend<AuditPage>(`audit${qs ? `?${qs}` : ""}`);
    },
  };
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
