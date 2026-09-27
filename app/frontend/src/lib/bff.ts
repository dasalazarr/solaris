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

/** Primer segmento permitido → métodos permitidos. Refleja la matriz del backend. */
export const ALLOWED_ROUTES: Readonly<Record<string, readonly string[]>> = {
  "8d": ["GET", "POST"],
  approvals: ["GET"],
  audit: ["GET"],
  ask: ["POST"],
  complaints: ["POST"],
};

const SEGMENT_RE = /^[A-Za-z0-9._~-]+$/;

/**
 * Construye la ruta del backend a partir de los segmentos del catch-all. `null` si no está
 * permitida. Los segmentos ya vienen decodificados por Next: se validan con una allowlist de
 * caracteres (sin `/`, `\`, `%`, espacios) y se rechazan `.` y `..`.
 */
export function backendPath(segments: readonly string[], method: string): string | null {
  if (segments.length === 0 || segments.length > 6) return null;
  const allowed = ALLOWED_ROUTES[segments[0]];
  if (!allowed || !allowed.includes(method.toUpperCase())) return null;
  for (const seg of segments) {
    if (!SEGMENT_RE.test(seg) || seg === "." || seg === "..") return null;
  }
  return "/" + segments.join("/");
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
