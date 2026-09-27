import { describe, expect, it, vi } from "vitest";

import { ApiError, type CaseView } from "@/lib/api-client";
import { parseProgress, watchCase, type EventSourceLike, type WatchUpdate } from "@/lib/case-watch";

class FakeES implements EventSourceLike {
  static last: FakeES | null = null;
  url: string;
  closed = false;
  onerror: ((ev: Event) => void) | null = null;
  listeners = new Map<string, (ev: MessageEvent<string>) => void>();
  constructor(url: string) {
    this.url = url;
    FakeES.last = this;
  }
  addEventListener(t: string, fn: (ev: MessageEvent<string>) => void) {
    this.listeners.set(t, fn);
  }
  emit(t: string, data: unknown) {
    this.listeners.get(t)?.({ data: JSON.stringify(data) } as MessageEvent<string>);
  }
  close() {
    this.closed = true;
  }
}

function view(status: string, nodes: string[] = []): CaseView {
  return { case_id: "c1", complaint_id: "C-OEMN-2026-0312", status, error: null,
           customer: { code: "C-OEMN", name: "OEM Norte" }, complaint: {},
           warnings: [], progress: nodes.map((n) => ({ node: n, outcome: "ok", ms: 1, at: 1 })),
           pending_nodes: [], elapsed_s: 41.2, created_at: "", created_by: "inaki.calidad",
           version: "v" };
}

/** Temporizadores manuales: se ejecutan con `flush()`. */
function timers() {
  const q: (() => void)[] = [];
  return {
    setTimer: (fn: () => void) => { q.push(fn); return q.length; },
    clearTimer: () => undefined,
    async flush() {
      while (q.length) {
        q.shift()!();
        await new Promise((r) => setTimeout(r, 0));
      }
    },
  };
}

const tick = () => new Promise((r) => setTimeout(r, 0));

describe("watchCase", () => {
  it("SSE: progreso por nodo y, al terminar, la vista completa por GET", async () => {
    const updates: WatchUpdate[] = [];
    const getCase = vi.fn(async () => view("pending_approval", ["intake", "D4_root_cause"]));
    const stop = watchCase("c1", { getCase, eventSource: (u) => new FakeES(u) },
                           { onUpdate: (u) => updates.push(u), onError: vi.fn() });
    const es = FakeES.last!;
    expect(es.url).toBe("/api/backend/8d/c1/events");
    es.emit("progress", { node: "intake", outcome: "ok", ms: 900, at: 1 });
    es.emit("progress", { node: "<img src=x>", outcome: "ok" }); // nodo desconocido: se ignora
    expect(updates).toHaveLength(1);
    expect(updates[0]).toMatchObject({ status: "drafting", via: "sse" });
    es.emit("status", { status: "pending_approval", elapsed_s: 41 });
    await tick();
    expect(es.closed).toBe(true);
    expect(getCase).toHaveBeenCalledOnce();
    const last = updates.at(-1)!;
    expect(last.status).toBe("pending_approval");
    expect(last.view?.elapsed_s).toBe(41.2);
    stop();
  });

  it("si el flujo falla, sigue por polling hasta el estado final", async () => {
    const t = timers();
    const seq = [view("drafting", ["intake"]), view("drafting", ["intake", "D1_team"]),
                 view("pending_approval", ["intake", "D1_team"])];
    const getCase = vi.fn(async () => seq.shift()!);
    const updates: WatchUpdate[] = [];
    watchCase("c1", { getCase, eventSource: (u) => new FakeES(u), ...t },
              { onUpdate: (u) => updates.push(u), onError: vi.fn() });
    FakeES.last!.onerror?.(new Event("error"));
    expect(FakeES.last!.closed).toBe(true);
    await tick();
    await t.flush();
    expect(getCase).toHaveBeenCalledTimes(3);
    expect(updates.map((u) => u.status)).toEqual(["drafting", "drafting", "pending_approval"]);
    expect(updates.every((u) => u.via === "polling")).toBe(true);
  });

  it("sin EventSource: polling directo; 403 detiene y avisa", async () => {
    const onError = vi.fn();
    const getCase = vi.fn(async () => {
      throw new ApiError(403, "Permiso insuficiente");
    });
    watchCase("c1", { getCase, eventSource: null }, { onUpdate: vi.fn(), onError });
    await tick();
    expect(onError).toHaveBeenCalledOnce();
    expect(onError.mock.calls[0][0].kind).toBe("forbidden");
  });

  it("los errores transitorios se reintentan con un tope", async () => {
    const t = timers();
    const onError = vi.fn();
    const getCase = vi.fn(async () => {
      throw new ApiError(503);
    });
    watchCase("c1", { getCase, eventSource: null, maxPollErrors: 2, ...t },
              { onUpdate: vi.fn(), onError });
    await tick();
    await t.flush();
    expect(getCase).toHaveBeenCalledTimes(3);
    expect(onError).toHaveBeenCalledOnce();
  });

  it("parseProgress valida el evento", () => {
    expect(parseProgress("no json")).toBeNull();
    expect(parseProgress(JSON.stringify({ node: "D9" }))).toBeNull();
    expect(parseProgress(JSON.stringify({ node: "D2_describe", ms: "x" })))
      .toEqual({ node: "D2_describe", outcome: "ok", ms: 0, at: 0 });
  });
});
