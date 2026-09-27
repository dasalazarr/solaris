import "server-only";

/**
 * Configuración del lado servidor. Nada de esto llega al navegador (sin prefijo NEXT_PUBLIC_ y
 * con `server-only`, que rompe el build si un componente cliente lo importa).
 */

/** URL del backend FastAPI. Solo la usa el servidor de Next; el navegador nunca la ve. */
export function backendUrl(): string {
  const raw = process.env.SOLARIS_BACKEND_URL ?? "http://127.0.0.1:8000";
  const u = new URL(raw);
  if (u.protocol !== "http:" && u.protocol !== "https:") {
    throw new Error("SOLARIS_BACKEND_URL debe ser http(s)");
  }
  return u.origin;
}

/**
 * `Secure` en la cookie. Por defecto sí en producción. Para el demo servido por http en otra
 * máquina que no sea localhost, `SOLARIS_COOKIE_SECURE=false` (localhost ya es contexto seguro).
 */
export function cookieSecure(): boolean {
  const v = process.env.SOLARIS_COOKIE_SECURE;
  if (v === "true") return true;
  if (v === "false") return false;
  return process.env.NODE_ENV === "production";
}

/** Con `Secure`, prefijo `__Host-` (sin Domain, Path=/, solo este host). */
export function sessionCookieName(): string {
  return cookieSecure() ? "__Host-solaris_session" : "solaris_session";
}

export function idleCookieName(): string {
  return cookieSecure() ? "__Host-solaris_idle" : "solaris_idle";
}

/** Valor por defecto de `AUTH_IDLE_TIMEOUT_S` del backend (se sobrescribe con el del login). */
export const DEFAULT_IDLE_TIMEOUT_S = 900;

/** Tiempo máximo de espera al backend para peticiones normales (no para el flujo SSE). */
export const BACKEND_TIMEOUT_MS = 120_000;
