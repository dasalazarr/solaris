import "server-only";

import { cookies } from "next/headers";
import { cache } from "react";

import {
  BACKEND_TIMEOUT_MS,
  DEFAULT_IDLE_TIMEOUT_S,
  backendUrl,
  cookieSecure,
  idleCookieName,
  sessionCookieName,
} from "./config";

/**
 * Sesión del lado servidor (BFF). El JWT del backend vive SOLO en una cookie httpOnly; el
 * navegador nunca lo lee. El rol lo devuelve siempre el backend (`GET /auth/me`, PAT-008).
 */

export interface Principal {
  user: string;
  role: string;
}

export type SessionState =
  | { status: "ok"; principal: Principal; idleTimeoutS: number }
  | { status: "anon" }
  | { status: "unavailable" };

export async function readToken(): Promise<string | null> {
  const store = await cookies();
  const v = store.get(sessionCookieName())?.value;
  return v && v.length < 4096 ? v : null;
}

export async function readIdleTimeout(): Promise<number> {
  const store = await cookies();
  const n = Number(store.get(idleCookieName())?.value);
  return Number.isInteger(n) && n >= 60 && n <= 86_400 ? n : DEFAULT_IDLE_TIMEOUT_S;
}

export interface BackendInit {
  method?: string;
  token?: string | null;
  headers?: Headers;
  body?: BodyInit | null;
  signal?: AbortSignal;
  timeoutMs?: number | null;
}

/** Llamada al backend desde el servidor de Next. Nunca se cachea. */
export async function backendFetch(path: string, init: BackendInit = {}): Promise<Response> {
  const headers = init.headers ?? new Headers();
  if (init.token) headers.set("authorization", `Bearer ${init.token}`);
  const signals: AbortSignal[] = [];
  if (init.signal) signals.push(init.signal);
  const timeout = init.timeoutMs === undefined ? BACKEND_TIMEOUT_MS : init.timeoutMs;
  if (timeout !== null) signals.push(AbortSignal.timeout(timeout));
  return fetch(backendUrl() + path, {
    method: init.method ?? "GET",
    headers,
    body: init.body ?? null,
    cache: "no-store",
    redirect: "manual",
    signal: signals.length ? AbortSignal.any(signals) : undefined,
  });
}

/**
 * Usuario de la sesión actual según el backend. Memorizado por petición (React `cache`).
 * Cada llamada renueva la inactividad en el backend, igual que cualquier otra petición.
 */
export const getSession = cache(async (): Promise<SessionState> => {
  const token = await readToken();
  if (!token) return { status: "anon" };
  let res: Response;
  try {
    res = await backendFetch("/auth/me", { token, timeoutMs: 10_000 });
  } catch {
    return { status: "unavailable" };
  }
  if (res.status === 401) return { status: "anon" };
  if (!res.ok) return { status: "unavailable" };
  const body: unknown = await res.json().catch(() => null);
  if (!isPrincipal(body)) return { status: "unavailable" };
  return {
    status: "ok",
    principal: { user: body.user, role: body.role },
    idleTimeoutS: await readIdleTimeout(),
  };
});

function isPrincipal(v: unknown): v is Principal {
  return (
    typeof v === "object" &&
    v !== null &&
    typeof (v as Principal).user === "string" &&
    typeof (v as Principal).role === "string"
  );
}

export interface SessionCookieOptions {
  maxAge: number;
}

export function sessionCookieAttrs({ maxAge }: SessionCookieOptions) {
  return {
    httpOnly: true,
    secure: cookieSecure(),
    sameSite: "strict" as const,
    path: "/",
    maxAge,
  };
}
