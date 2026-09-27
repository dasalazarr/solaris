import { cookies } from "next/headers";
import { NextResponse, type NextRequest } from "next/server";

import { checkSameOrigin, selfOrigin } from "@/lib/bff";
import { idleCookieName, sessionCookieName } from "@/lib/server/config";
import {
  backendFetch,
  getSession,
  readToken,
  sessionCookieAttrs,
} from "@/lib/server/session";

/**
 * Sesión del BFF:
 * - `POST /api/session`   login → `POST /auth/login` del backend; guarda el JWT en cookie httpOnly.
 * - `GET /api/session`    usuario y rol según el backend (`GET /auth/me`); renueva la inactividad.
 * - `DELETE /api/session` logout → `POST /auth/logout` y borra la cookie.
 * El token nunca aparece en ninguna respuesta al navegador.
 */

export const dynamic = "force-dynamic";

function sameOrigin(request: NextRequest, method: string): boolean {
  return checkSameOrigin(method, request.headers,
                         selfOrigin(request.headers, request.nextUrl.protocol)).ok;
}

const NO_STORE = { "cache-control": "no-store" };
const MAX_LOGIN_BODY = 2048;

function json(body: unknown, status = 200) {
  return NextResponse.json(body, { status, headers: NO_STORE });
}

function forbiddenCsrf() {
  return json({ detail: "Petición no permitida" }, 403);
}

async function clearCookies() {
  const store = await cookies();
  for (const name of [sessionCookieName(), idleCookieName()]) {
    store.set(name, "", sessionCookieAttrs({ maxAge: 0 }));
  }
}

export async function POST(request: NextRequest) {
  if (!sameOrigin(request, "POST")) return forbiddenCsrf();
  const raw = await request.text();
  if (raw.length > MAX_LOGIN_BODY) return json({ detail: "Petición demasiado grande" }, 413);
  let body: unknown;
  try {
    body = JSON.parse(raw);
  } catch {
    return json({ detail: "Petición no válida" }, 422);
  }
  const { username, password } = (body ?? {}) as Record<string, unknown>;
  if (typeof username !== "string" || typeof password !== "string" || !username || !password) {
    return json({ detail: "Introduce usuario y contraseña" }, 422);
  }

  let res: Response;
  try {
    res = await backendFetch("/auth/login", {
      method: "POST",
      headers: new Headers({ "content-type": "application/json" }),
      body: JSON.stringify({ username: username.trim(), password }),
      timeoutMs: 15_000,
    });
  } catch {
    return json({ detail: "El servidor no responde. Inténtalo de nuevo en unos segundos." }, 503);
  }

  if (!res.ok) {
    // Mensajes genéricos (no revelan si el usuario existe). 422 del backend = formato.
    const detail =
      res.status === 401
        ? "Usuario o contraseña incorrectos"
        : res.status === 429
          ? "Demasiados intentos fallidos. Espera unos minutos y vuelve a intentarlo."
          : res.status === 422
            ? "Usuario o contraseña con formato no válido"
            : "La autenticación no está disponible ahora mismo";
    const status = [401, 422, 429].includes(res.status) ? res.status : 503;
    return json({ detail }, status);
  }

  const data = (await res.json()) as {
    access_token?: unknown;
    expires_in?: unknown;
    idle_timeout_s?: unknown;
    user?: unknown;
    role?: unknown;
  };
  if (typeof data.access_token !== "string" || typeof data.user !== "string" ||
      typeof data.role !== "string") {
    return json({ detail: "La autenticación no está disponible ahora mismo" }, 503);
  }
  const ttl = typeof data.expires_in === "number" && data.expires_in > 0 ? data.expires_in : 1800;
  const idle =
    typeof data.idle_timeout_s === "number" && data.idle_timeout_s > 0 ? data.idle_timeout_s : 900;

  const store = await cookies();
  store.set(sessionCookieName(), data.access_token, sessionCookieAttrs({ maxAge: ttl }));
  store.set(idleCookieName(), String(idle), sessionCookieAttrs({ maxAge: ttl }));
  return json({ user: data.user, role: data.role, idle_timeout_s: idle });
}

export async function GET(request: NextRequest) {
  if (!sameOrigin(request, "GET")) return forbiddenCsrf();
  const s = await getSession();
  if (s.status === "anon") {
    await clearCookies();
    return json({ detail: "Sesión caducada o cerrada" }, 401);
  }
  if (s.status === "unavailable") return json({ detail: "Servicio no disponible" }, 503);
  return json({ ...s.principal, idle_timeout_s: s.idleTimeoutS });
}

export async function DELETE(request: NextRequest) {
  if (!sameOrigin(request, "DELETE")) return forbiddenCsrf();
  const token = await readToken();
  if (token) {
    // Revoca la sesión en el backend; si falla, la cookie se borra igualmente.
    await backendFetch("/auth/logout", { method: "POST", token, timeoutMs: 5_000 }).catch(
      () => null,
    );
  }
  await clearCookies();
  return new NextResponse(null, { status: 204, headers: NO_STORE });
}
