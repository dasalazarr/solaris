import { describe, expect, it } from "vitest";

import {
  CSRF_HEADER,
  backendPath,
  checkSameOrigin,
  forwardRequestHeaders,
  forwardResponseHeaders,
  selfOrigin,
} from "@/lib/bff";

const ORIGIN = "http://localhost:3000";

describe("backendPath (allowlist del proxy)", () => {
  it("permite las rutas del flujo 8D", () => {
    expect(backendPath(["8d"], "POST")).toBe("/8d");
    expect(backendPath(["8d", "123e4567", "events"], "GET")).toBe("/8d/123e4567/events");
    expect(backendPath(["approvals"], "GET")).toBe("/approvals");
    expect(backendPath(["audit", "export.csv"], "GET")).toBe("/audit/export.csv");
  });
  it("rechaza auth, health, rutas desconocidas y métodos no previstos", () => {
    expect(backendPath(["auth", "login"], "POST")).toBeNull();
    expect(backendPath(["auth", "me"], "GET")).toBeNull();
    expect(backendPath(["health"], "GET")).toBeNull();
    expect(backendPath(["docs"], "GET")).toBeNull();
    expect(backendPath(["approvals"], "POST")).toBeNull();
    expect(backendPath([], "GET")).toBeNull();
  });
  it("rechaza traversal y caracteres raros", () => {
    expect(backendPath(["8d", ".."], "GET")).toBeNull();
    expect(backendPath(["8d", "..", "auth"], "GET")).toBeNull();
    expect(backendPath(["8d", "a/b"], "GET")).toBeNull();
    expect(backendPath(["8d", "a%2Fb"], "GET")).toBeNull();
    expect(backendPath(["8d", "a\\b"], "GET")).toBeNull();
    expect(backendPath(["8d", "a b"], "GET")).toBeNull();
  });
});

describe("cabeceras", () => {
  it("no reenvía identidad, cookies ni Authorization del navegador", () => {
    const incoming = new Headers({
      "content-type": "application/json",
      cookie: "solaris_session=abc",
      authorization: "Bearer robado",
      "x-role": "admin",
      "x-user": "jon.it",
      "x-forwarded-for": "1.2.3.4",
    });
    const h = forwardRequestHeaders(incoming, "TOKEN");
    expect(h.get("authorization")).toBe("Bearer TOKEN");
    expect(h.get("content-type")).toBe("application/json");
    for (const n of ["cookie", "x-role", "x-user", "x-forwarded-for"]) expect(h.has(n)).toBe(false);
  });
  it("no reenvía set-cookie del backend y añade nosniff/no-store", () => {
    const h = forwardResponseHeaders(new Headers({ "content-type": "text/event-stream",
                                                   "set-cookie": "x=1", server: "uvicorn" }));
    expect(h.has("set-cookie")).toBe(false);
    expect(h.has("server")).toBe(false);
    expect(h.get("x-content-type-options")).toBe("nosniff");
    expect(h.get("cache-control")).toBe("no-store");
  });
});

describe("checkSameOrigin (CSRF)", () => {
  const good = { origin: ORIGIN, "sec-fetch-site": "same-origin", [CSRF_HEADER]: "1" };
  it("acepta escrituras same-origin con la cabecera", () => {
    expect(checkSameOrigin("POST", new Headers(good), ORIGIN).ok).toBe(true);
  });
  it("rechaza cross-site aunque sea GET", () => {
    expect(checkSameOrigin("GET", new Headers({ "sec-fetch-site": "cross-site" }), ORIGIN).ok)
      .toBe(false);
  });
  it("rechaza escrituras sin Origin, con otro Origin o sin la cabecera CSRF", () => {
    const noOrigin = { "sec-fetch-site": "same-origin", [CSRF_HEADER]: "1" };
    const noCsrf = { origin: ORIGIN, "sec-fetch-site": "same-origin" };
    expect(checkSameOrigin("POST", new Headers(noOrigin), ORIGIN).ok).toBe(false);
    expect(checkSameOrigin("POST", new Headers({ ...good, origin: "https://evil.example" }), ORIGIN).ok)
      .toBe(false);
    expect(checkSameOrigin("DELETE", new Headers(noCsrf), ORIGIN).ok).toBe(false);
  });
});

describe("selfOrigin", () => {
  it("usa la cabecera Host (localhost y 127.0.0.1 son orígenes distintos)", () => {
    expect(selfOrigin(new Headers({ host: "127.0.0.1:3000" }), "http:")).toBe("http://127.0.0.1:3000");
    expect(selfOrigin(new Headers({ host: "localhost:3000" }), "http")).toBe("http://localhost:3000");
  });
  it("sin Host o con Host raro → null (y la escritura se rechaza)", () => {
    expect(selfOrigin(new Headers(), "http:")).toBeNull();
    expect(selfOrigin(new Headers({ host: "evil/..@x" }), "http:")).toBeNull();
    const h = new Headers({ origin: "http://x", [CSRF_HEADER]: "1" });
    expect(checkSameOrigin("POST", h, null).ok).toBe(false);
  });
});
