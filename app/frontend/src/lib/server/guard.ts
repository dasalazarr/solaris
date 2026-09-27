import "server-only";

import { redirect } from "next/navigation";

import { getSession, readToken, backendFetch, type Principal } from "./session";

/**
 * Sesión obligatoria para las páginas de la app. Sin sesión válida (según el backend) → login.
 * `unavailable` lo gestiona el layout mostrando el error (no se redirige para no crear bucles).
 */
export async function requirePrincipal(): Promise<Principal | null> {
  const s = await getSession();
  if (s.status === "anon") redirect("/login?motivo=sesion");
  return s.status === "ok" ? s.principal : null;
}

export type Probe<T> =
  | { status: "ok"; data: T }
  | { status: "forbidden"; detail: string }
  | { status: "unavailable" };

/**
 * Consulta de solo lectura al backend desde una página de servidor. El backend decide el acceso:
 * su 403 se muestra como "sin permiso" y su 401 lleva al login.
 */
export async function probe<T>(path: string): Promise<Probe<T>> {
  const token = await readToken();
  if (!token) redirect("/login?motivo=sesion");
  let res: Response;
  try {
    res = await backendFetch(path, { token, timeoutMs: 15_000 });
  } catch {
    return { status: "unavailable" };
  }
  if (res.status === 401) redirect("/login?motivo=sesion");
  if (res.status === 403) {
    const body = (await res.json().catch(() => null)) as { detail?: unknown } | null;
    const detail = typeof body?.detail === "string" ? body.detail : "Permiso insuficiente";
    return { status: "forbidden", detail };
  }
  if (!res.ok) return { status: "unavailable" };
  return { status: "ok", data: (await res.json()) as T };
}
