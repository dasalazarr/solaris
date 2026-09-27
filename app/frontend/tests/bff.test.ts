import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

import {
  ALLOWED_ROUTES,
  BodyTooLarge,
  CSRF_HEADER,
  MAX_JSON_BYTES,
  MAX_UPLOAD_BYTES,
  backendPath,
  matchRoute,
  readCapped,
  checkSameOrigin,
  forwardRequestHeaders,
  forwardResponseHeaders,
  selfOrigin,
} from "@/lib/bff";

const ORIGIN = "http://localhost:3000";
const ID = "123e4567-e89b-42d3-a456-426614174000";

describe("backendPath (allowlist del proxy)", () => {
  it("permite las rutas del flujo 8D", () => {
    expect(backendPath(["8d"], "POST")).toBe("/8d");
    expect(backendPath(["8d", ID, "events"], "GET")).toBe(`/8d/${ID}/events`);
    expect(backendPath(["8d"], "GET")).toBe("/8d");
    expect(backendPath(["complaints", "parse"], "POST")).toBe("/complaints/parse");
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

describe("allowlist explícita (M5-T3)", () => {
  it("`:id` solo acepta un UUID y cada subruta tiene sus métodos", () => {
    expect(backendPath(["8d", "123e4567", "events"], "GET")).toBeNull();
    expect(backendPath(["8d", ID], "POST")).toBeNull();
    expect(backendPath(["8d", ID, "events"], "POST")).toBeNull();
    expect(backendPath(["8d", ID, "otra"], "GET")).toBeNull();
    expect(backendPath(["8d", ID, "approve"], "GET")).toBeNull();
    expect(backendPath(["8d", ID, "approve"], "POST")).toBe(`/8d/${ID}/approve`);
    expect(backendPath(["complaints"], "POST")).toBeNull();
    expect(backendPath(["complaints", "parse"], "GET")).toBeNull();
    expect(backendPath(["complaints", "otra"], "POST")).toBeNull();
    expect(backendPath(["audit", "x.csv"], "GET")).toBeNull();
  });
  it("SSE solo en /events y límites de cuerpo coherentes con el backend", () => {
    expect(matchRoute(["8d", ID, "events"], "GET")?.rule.stream).toBe(true);
    expect(matchRoute(["8d", ID], "GET")?.rule.stream).toBeFalsy();
    // backend: MAX_FILE_BYTES (10 MB) + 64 KB de cabeceras del multipart
    expect(MAX_UPLOAD_BYTES).toBe(10 * 1024 * 1024 + 64 * 1024);
    expect(matchRoute(["complaints", "parse"], "POST")?.maxBody).toBe(MAX_UPLOAD_BYTES);
    expect(matchRoute(["8d"], "POST")?.maxBody).toBe(MAX_UPLOAD_BYTES);
    expect(matchRoute(["8d", ID, "approve"], "POST")?.maxBody).toBe(MAX_JSON_BYTES);
    expect(matchRoute(["ask"], "POST")?.maxBody).toBe(MAX_JSON_BYTES);
  });

  /** Cada ruta del proxy existe en la matriz de acceso del backend con ese método. */
  it("cruza la allowlist con `test_access_matrix.py::MATRIX`", () => {
    const src = readFileSync(
      fileURLToPath(new URL("../../backend/tests/test_access_matrix.py", import.meta.url)),
      "utf8",
    );
    const matrix = new Set(
      [...src.matchAll(/\("(GET|POST|DELETE)", "([^"]+)"\):/g)].map((m) => `${m[1]} ${m[2]}`),
    );
    for (const r of ALLOWED_ROUTES) {
      const path = "/" + r.pattern.map((p) => (p === ":id" ? "{case_id}" : p)).join("/");
      for (const m of r.methods) expect(matrix, `${m} ${path}`).toContain(`${m} ${path}`);
    }
    expect(matrix).not.toContain("GET /auth/me/x");
  });
});

function streamOf(chunks: number[]): ReadableStream<Uint8Array> {
  return new ReadableStream({
    start(c) {
      for (const n of chunks) c.enqueue(new Uint8Array(n));
      c.close();
    },
  });
}

describe("readCapped", () => {
  it("devuelve el cuerpo completo si cabe", async () => {
    const out = await readCapped(streamOf([3, 4]), 10);
    expect(out.byteLength).toBe(7);
    expect((await readCapped(null, 10)).byteLength).toBe(0);
  });
  it("corta en cuanto se pasa del tope (sin Content-Length fiable)", async () => {
    let pulled = 0;
    const endless = new ReadableStream<Uint8Array>({
      pull(c) {
        pulled++;
        c.enqueue(new Uint8Array(1024));
      },
    });
    await expect(readCapped(endless, 4096)).rejects.toBeInstanceOf(BodyTooLarge);
    expect(pulled).toBeLessThan(10);
  });
});
