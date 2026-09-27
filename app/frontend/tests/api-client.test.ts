import { describe, expect, it, vi } from "vitest";

import { ApiError, createApiClient, detailFrom, kindFor } from "@/lib/api-client";
import { CSRF_HEADER } from "@/lib/bff";

function fakeFetch(status: number, body: unknown, contentType = "application/json") {
  return vi.fn<(url: RequestInfo | URL, init?: RequestInit) => Promise<Response>>(
    async () =>
      new Response(status === 204 ? null : JSON.stringify(body), {
        status,
        headers: { "content-type": contentType },
      }),
  );
}

describe("createApiClient", () => {
  it("solo habla con el BFF y manda la cabecera CSRF en las escrituras", async () => {
    const f = fakeFetch(202, { case_id: "x" });
    const api = createApiClient({ fetch: f as unknown as typeof fetch });
    await api.backend("/8d", { json: { complaint_id: "C-1" } });
    const [url, init] = f.mock.calls[0];
    expect(url).toBe("/api/backend/8d");
    const h = new Headers(init?.headers);
    expect(init?.method).toBe("POST");
    expect(h.get(CSRF_HEADER)).toBe("1");
    expect(h.get("authorization")).toBeNull(); // el token nunca pasa por el navegador
    expect(init?.credentials).toBe("same-origin");
  });

  it("los GET no llevan cabecera CSRF", async () => {
    const f = fakeFetch(200, { items: [], count: 0 });
    const api = createApiClient({ fetch: f as unknown as typeof fetch });
    await expect(api.approvals()).resolves.toEqual({ items: [], count: 0 });
    expect(new Headers(f.mock.calls[0][1]?.headers).has(CSRF_HEADER)).toBe(false);
  });

  it("401 → llama a onUnauthorized (volver al login) y lanza ApiError", async () => {
    const onUnauthorized = vi.fn();
    const api = createApiClient({
      fetch: fakeFetch(401, { detail: "No autenticado" }) as unknown as typeof fetch,
      onUnauthorized,
    });
    const err = await api.approvals().catch((e: unknown) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect((err as ApiError).kind).toBe("unauthorized");
    expect(onUnauthorized).toHaveBeenCalledOnce();
  });

  it("403 → forbidden con el detail del backend y sin redirigir", async () => {
    const onUnauthorized = vi.fn();
    const api = createApiClient({
      fetch: fakeFetch(403, { detail: "Permiso insuficiente" }) as unknown as typeof fetch,
      onUnauthorized,
    });
    const err = (await api.auditEvents().catch((e: unknown) => e)) as ApiError;
    expect(err.kind).toBe("forbidden");
    expect(err.userMessage).toBe("Permiso insuficiente");
    expect(onUnauthorized).not.toHaveBeenCalled();
  });

  it("409 → conflict", async () => {
    const api = createApiClient({
      fetch: fakeFetch(409, { detail: "El caso no está pendiente de aprobación" }) as unknown as typeof fetch,
    });
    const err = (await api.backend("8d/abc/approve", { json: { version: "0" } })
      .catch((e: unknown) => e)) as ApiError;
    expect(err.kind).toBe("conflict");
    expect(err.status).toBe(409);
    expect(err.userMessage).toMatch(/no está pendiente/);
  });

  it("500 → mensaje genérico, nunca el volcado del servidor", async () => {
    const api = createApiClient({
      fetch: fakeFetch(500, { detail: "Traceback (most recent call last): secret" }) as unknown as typeof fetch,
    });
    const err = (await api.approvals().catch((e: unknown) => e)) as ApiError;
    expect(err.kind).toBe("server");
    expect(err.userMessage).not.toMatch(/Traceback|secret/);
  });

  it("error de red → kind network", async () => {
    const f = vi.fn(async () => { throw new TypeError("fetch failed"); });
    const api = createApiClient({ fetch: f as unknown as typeof fetch });
    const err = (await api.approvals().catch((e: unknown) => e)) as ApiError;
    expect(err.kind).toBe("network");
  });

  it("onActivity se llama tras cada respuesta", async () => {
    const onActivity = vi.fn();
    const api = createApiClient({ fetch: fakeFetch(204, null) as unknown as typeof fetch, onActivity });
    await api.session.logout();
    expect(onActivity).toHaveBeenCalledOnce();
  });

  it("la respuesta de login no expone token (lo guarda el BFF)", async () => {
    const f = fakeFetch(200, { user: "inaki.calidad", role: "calidad", idle_timeout_s: 900 });
    const api = createApiClient({ fetch: f as unknown as typeof fetch });
    const s = await api.session.login("inaki.calidad", "x".repeat(20));
    expect(s).not.toHaveProperty("access_token");
    expect(f.mock.calls[0][0]).toBe("/api/session");
  });
});

describe("normalización de errores", () => {
  it("kindFor", () => {
    expect(kindFor(401)).toBe("unauthorized");
    expect(kindFor(403)).toBe("forbidden");
    expect(kindFor(409)).toBe("conflict");
    expect(kindFor(422)).toBe("validation");
    expect(kindFor(429)).toBe("rate_limited");
    expect(kindFor(503)).toBe("unavailable");
  });
  it("detailFrom ignora listas de Pydantic y textos largos", () => {
    expect(detailFrom(422, { detail: [{ msg: "x", input: "<script>" }] })).toBeNull();
    expect(detailFrom(403, { detail: "a".repeat(301) })).toBeNull();
    expect(detailFrom(403, { detail: "Permiso insuficiente" })).toBe("Permiso insuficiente");
  });
});
