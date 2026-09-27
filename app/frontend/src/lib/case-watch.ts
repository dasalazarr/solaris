/**
 * Seguimiento del progreso de un caso 8D (L01, M5-T3).
 *
 * 1. SSE: `GET /api/backend/8d/{id}/events` (el BFF lo reenvía en streaming). Eventos `progress`
 *    (un nodo terminado) y `status` (estado final, o corte a los 300 s del backend).
 * 2. Si el navegador no tiene `EventSource`, el flujo falla o se corta sin estado final: polling
 *    de `GET /8d/{id}` cada `pollMs` (1,5 s por defecto).
 * Al terminar siempre se pide `GET /8d/{id}` para tener los avisos (inyección, nota de revisión).
 *
 * Los datos del flujo se validan antes de usarlos: solo se aceptan `node` de la lista conocida y
 * números; nada del flujo se pinta como HTML.
 */

import { ApiError, type CaseView, type ProgressEvent } from "./api-client";
import { STEPS, isTerminal } from "./inbox";

export interface WatchUpdate {
  progress: ProgressEvent[];
  status: string;
  /** Vista completa del caso cuando se ha pedido (al terminar o en cada sondeo). */
  view?: CaseView;
  /** "sse" o "polling": útil para la traza y los tests. */
  via: "sse" | "polling";
}

export interface EventSourceLike {
  addEventListener(type: string, fn: (ev: MessageEvent<string>) => void): void;
  close(): void;
  onerror: ((ev: Event) => void) | null;
}

export interface WatchDeps {
  getCase: (caseId: string, signal?: AbortSignal) => Promise<CaseView>;
  /** Constructor de EventSource (inyectable en tests). `null` = forzar polling. */
  eventSource?: ((url: string) => EventSourceLike) | null;
  pollMs?: number;
  /** Errores seguidos tolerados en el polling antes de rendirse (red, 503…). */
  maxPollErrors?: number;
  setTimer?: (fn: () => void, ms: number) => unknown;
  clearTimer?: (t: unknown) => void;
}

export interface WatchHandlers {
  onUpdate: (u: WatchUpdate) => void;
  onError: (e: ApiError) => void;
}

const KNOWN_NODES = new Set([...STEPS.map((s) => s.node), "await_approval", "hitl_gate"]);

export function parseProgress(data: string): ProgressEvent | null {
  let v: unknown;
  try {
    v = JSON.parse(data);
  } catch {
    return null;
  }
  if (typeof v !== "object" || v === null) return null;
  const o = v as Record<string, unknown>;
  if (typeof o.node !== "string" || !KNOWN_NODES.has(o.node)) return null;
  return {
    node: o.node,
    outcome: typeof o.outcome === "string" ? o.outcome : "ok",
    ms: typeof o.ms === "number" ? o.ms : 0,
    at: typeof o.at === "number" ? o.at : 0,
  };
}

function parseStatus(data: string): string | null {
  try {
    const v = JSON.parse(data) as { status?: unknown };
    return typeof v.status === "string" ? v.status : null;
  } catch {
    return null;
  }
}

const STOP_KINDS = new Set(["unauthorized", "forbidden", "not_found"]);

/** Empieza a seguir el caso. Devuelve la función para pararlo (al desmontar el componente). */
export function watchCase(caseId: string, deps: WatchDeps, h: WatchHandlers): () => void {
  const pollMs = deps.pollMs ?? 1500;
  const maxErrors = deps.maxPollErrors ?? 5;
  const setTimer = deps.setTimer ?? ((fn, ms) => setTimeout(fn, ms));
  const clearTimer = deps.clearTimer ?? ((t) => clearTimeout(t as ReturnType<typeof setTimeout>));
  const ctrl = new AbortController();
  let stopped = false;
  let timer: unknown = null;
  let es: EventSourceLike | null = null;
  let progress: ProgressEvent[] = [];
  let errors = 0;

  const stop = () => {
    stopped = true;
    es?.close();
    es = null;
    if (timer !== null) clearTimer(timer);
    ctrl.abort();
  };

  const fail = (e: unknown) => {
    if (stopped) return;
    if (e instanceof DOMException && e.name === "AbortError") return;
    const err = e instanceof ApiError ? e : new ApiError(0);
    if (STOP_KINDS.has(err.kind) || ++errors > maxErrors) {
      stop();
      h.onError(err);
      return;
    }
    timer = setTimer(poll, pollMs);
  };

  async function poll() {
    timer = null;
    if (stopped) return;
    try {
      const v = await deps.getCase(caseId, ctrl.signal);
      if (stopped) return;
      errors = 0;
      progress = v.progress ?? [];
      h.onUpdate({ progress, status: v.status, view: v, via: "polling" });
      if (isTerminal(v.status)) stop();
      else timer = setTimer(poll, pollMs);
    } catch (e) {
      fail(e);
    }
  }

  const factory = deps.eventSource === undefined
    ? (typeof EventSource === "undefined" ? null
      : (url: string) => new EventSource(url) as unknown as EventSourceLike)
    : deps.eventSource;

  if (!factory) {
    void poll();
    return stop;
  }

  const toPolling = () => {
    es?.close();
    es = null;
    if (!stopped && timer === null) void poll();
  };

  try {
    es = factory(`/api/backend/8d/${encodeURIComponent(caseId)}/events`);
  } catch {
    void poll();
    return stop;
  }
  es.addEventListener("progress", (ev) => {
    const p = parseProgress(ev.data);
    if (!p || stopped) return;
    progress = [...progress.filter((x) => x.node !== p.node), p];
    h.onUpdate({ progress, status: "drafting", via: "sse" });
  });
  es.addEventListener("status", (ev) => {
    const status = parseStatus(ev.data);
    es?.close();
    es = null;
    if (stopped) return;
    if (status && isTerminal(status)) h.onUpdate({ progress, status, via: "sse" });
    // Estado final o corte del backend: la vista completa (avisos) llega por GET.
    void poll();
  });
  // Error de red, 4xx del BFF o `event: error` del backend → seguir por polling.
  es.onerror = () => toPolling();
  return stop;
}
