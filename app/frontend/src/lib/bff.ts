/**
 * Reglas puras del BFF (Route Handlers que hablan con el backend). Sin dependencias de Next para
 * poder probarlas con vitest (`bff.test.ts`).
 *
 * - Solo se reenvían al backend las rutas de la allowlist (nada de `/auth/*`: eso lo gestiona
 *   `/api/session`) y ningún segmento puede escapar de ellas.
 * - Solo se reenvían cabeceras de contenido: nunca `cookie`, `authorization` ni `x-*`. Así el
 *   navegador no puede colar identidad (X-User, X-Role…) aunque el backend ya la ignore.
 * - CSRF: la cookie es SameSite=Strict y, además, toda petición al BFF debe ser same-origin según
 *   Fetch Metadata y las que cambian estado deben traer `Origin` propio y la cabecera
 *   `x-solaris-csrf: 1` (una web ajena no puede enviarla sin preflight CORS, que aquí no existe).
 */

export const CSRF_HEADER = "x-solaris-csrf";

/**
 * Allowlist EXPLÍCITA del proxy (M5-T3): cada ruta del backend que puede usar el navegador, con sus
 * métodos, el tamaño máximo del cuerpo y si es un flujo SSE. `:id` solo acepta un UUID. Refleja
 * `app/backend/tests/test_access_matrix.py::MATRIX` (lo comprueba `bff.test.ts`); una ruta nueva
 * del backend NO queda expuesta hasta que se añade aquí.
 */
export interface RouteRule {
  pattern: readonly string[];
  methods: readonly ("GET" | "POST")[];
  /** Tamaño máximo del cuerpo que se acepta y reenvía (bytes). */
  maxBody?: number;
  /** Respuesta en streaming (SSE): sin timeout, cortada con el `signal` de la petición. */
  stream?: boolean;
}

/** El backend admite 10 MB por fichero + 64 KB de cabeceras del multipart (`MAX_REQUEST_BYTES`). */
export const MAX_UPLOAD_BYTES = 10 * 1024 * 1024 + 64 * 1024;
/** Cuerpos JSON (decisiones HITL ≤ 64 KB en el backend, preguntas…). */
export const MAX_JSON_BYTES = 256 * 1024;

export const ALLOWED_ROUTES: readonly RouteRule[] = [
  { pattern: ["8d"], methods: ["GET", "POST"], maxBody: MAX_UPLOAD_BYTES },
  { pattern: ["8d", ":id"], methods: ["GET"] },
  { pattern: ["8d", ":id", "events"], methods: ["GET"], stream: true },
  { pattern: ["8d", ":id", "approve"], methods: ["POST"] },
  { pattern: ["8d", ":id", "reject"], methods: ["POST"] },
  { pattern: ["8d", ":id", "export"], methods: ["POST"] },
  { pattern: ["approvals"], methods: ["GET"] },
  { pattern: ["audit"], methods: ["GET"] },
  { pattern: ["audit", "export.csv"], methods: ["GET"] },
  { pattern: ["ask"], methods: ["POST"] },
  { pattern: ["complaints", "parse"], methods: ["POST"], maxBody: MAX_UPLOAD_BYTES },
];

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const SEGMENT_RE = /^[A-Za-z0-9._~-]+$/;

export interface MatchedRoute {
  path: string;
  rule: RouteRule;
  maxBody: number;
}

/**
 * Busca la regla de la allowlist para los segmentos del catch-all (ya decodificados por Next).
 * `null` si la ruta o el método no están permitidos. Además de casar la plantilla, cada segmento
 * pasa una allowlist de caracteres (sin `/`, `\`, `%`, espacios) y se rechazan `.` y `..`.
 */
export function matchRoute(segments: readonly string[], method: string): MatchedRoute | null {
  const m = method.toUpperCase();
  if (segments.length === 0 || segments.length > 6) return null;
  for (const seg of segments) {
    if (!SEGMENT_RE.test(seg) || seg === "." || seg === "..") return null;
  }
  for (const rule of ALLOWED_ROUTES) {
    if (rule.pattern.length !== segments.length) continue;
    const ok = rule.pattern.every((p, i) =>
      p === ":id" ? UUID_RE.test(segments[i].toLowerCase()) : p === segments[i]);
    if (!ok) continue;
    if (!(rule.methods as readonly string[]).includes(m)) return null;
    return { path: "/" + segments.join("/"), rule, maxBody: rule.maxBody ?? MAX_JSON_BYTES };
  }
  return null;
}

/** Ruta del backend o `null` (compatibilidad con M5-T2). */
export function backendPath(segments: readonly string[], method: string): string | null {
  return matchRoute(segments, method)?.path ?? null;
}

export class BodyTooLarge extends Error {}

/**
 * Lee un cuerpo con tope: corta en cuanto se pasa de `max` bytes, sin bufferizar el resto (un
 * cuerpo sin `Content-Length`, o con uno falso, no puede llenar la memoria del BFF).
 */
export async function readCapped(
  body: ReadableStream<Uint8Array> | null,
  max: number,
): Promise<Uint8Array<ArrayBuffer>> {
  if (body === null) return new Uint8Array(new ArrayBuffer(0));
  const reader = body.getReader();
  const chunks: Uint8Array[] = [];
  let total = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    total += value.byteLength;
    if (total > max) {
      await reader.cancel().catch(() => undefined);
      throw new BodyTooLarge();
    }
    chunks.push(value);
  }
  const out = new Uint8Array(total);
  let off = 0;
  for (const c of chunks) {
    out.set(c, off);
    off += c.byteLength;
  }
  return out;
}

const FORWARD_REQUEST = ["content-type", "accept", "last-event-id"] as const;
const FORWARD_RESPONSE = [
  "content-type",
  "content-disposition",
  "cache-control",
  "retry-after",
] as const;

export function pickHeaders(source: Headers, names: readonly string[]): Headers {
  const out = new Headers();
  for (const n of names) {
    const v = source.get(n);
    if (v !== null) out.set(n, v);
  }
  return out;
}

export function forwardRequestHeaders(incoming: Headers, token: string): Headers {
  const h = pickHeaders(incoming, FORWARD_REQUEST);
  h.set("authorization", `Bearer ${token}`);
  return h;
}

export function forwardResponseHeaders(backend: Headers): Headers {
  const h = pickHeaders(backend, FORWARD_RESPONSE);
  h.set("x-content-type-options", "nosniff");
  if (!h.has("cache-control")) h.set("cache-control", "no-store");
  return h;
}

/**
 * Origen propio tal como lo ve el navegador: protocolo + cabecera `Host`. No se usa
 * `nextUrl.origin` porque `next start` lo normaliza a `localhost` y rompería el acceso por
 * `127.0.0.1` (truco del demo para 2 sesiones en paralelo). Un `Host` falso no sirve de nada al
 * atacante: el navegador solo envía nuestra cookie a nuestro host.
 */
export function selfOrigin(headers: Headers, protocol: string): string | null {
  const host = headers.get("host");
  if (!host || !/^[A-Za-z0-9.[\]:-]+$/.test(host)) return null;
  return `${protocol.replace(/:$/, "")}://${host}`;
}

const SAFE_METHODS = new Set(["GET", "HEAD"]);

export type CsrfVerdict = { ok: true } | { ok: false; reason: string };

/**
 * Comprueba que la petición al BFF sale de nuestra propia página.
 * `origin` = origen del propio frontend (p. ej. `http://localhost:3000`).
 */
export function checkSameOrigin(
  method: string,
  headers: Headers,
  origin: string | null,
): CsrfVerdict {
  const site = headers.get("sec-fetch-site");
  if (site !== null && site !== "same-origin") {
    return { ok: false, reason: "cross-site" };
  }
  if (SAFE_METHODS.has(method.toUpperCase())) return { ok: true };
  const reqOrigin = headers.get("origin");
  if (origin === null || reqOrigin === null || reqOrigin !== origin) {
    return { ok: false, reason: "origin" };
  }
  if (headers.get(CSRF_HEADER) !== "1") return { ok: false, reason: "csrf-header" };
  return { ok: true };
}
