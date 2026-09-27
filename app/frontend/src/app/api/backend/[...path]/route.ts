import { cookies } from "next/headers";
import { NextResponse, type NextRequest } from "next/server";

import {
  BodyTooLarge,
  checkSameOrigin,
  matchRoute,
  readCapped,
  forwardRequestHeaders,
  forwardResponseHeaders,
  selfOrigin,
} from "@/lib/bff";
import { idleCookieName, sessionCookieName } from "@/lib/server/config";
import { backendFetch, readToken, sessionCookieAttrs } from "@/lib/server/session";

/**
 * Proxy BFF hacia el backend FastAPI: `/api/backend/<ruta>` → `<SOLARIS_BACKEND_URL>/<ruta>`.
 *
 * El navegador nunca habla con el backend ni ve el JWT: aquí se lee de la cookie httpOnly y se
 * envía como `Authorization: Bearer`. Solo rutas de la allowlist (`lib/bff.ts`), solo cabeceras
 * de contenido y comprobación same-origin/CSRF. La autorización la decide el backend: sus 401,
 * 403 y 409 se devuelven tal cual (con su `detail` genérico).
 */

export const dynamic = "force-dynamic";

function sameOrigin(request: NextRequest, method: string): boolean {
  return checkSameOrigin(method, request.headers,
                         selfOrigin(request.headers, request.nextUrl.protocol)).ok;
}

function error(detail: string, status: number) {
  return NextResponse.json({ detail }, { status, headers: { "cache-control": "no-store" } });
}

async function handle(request: NextRequest, ctx: RouteContext<"/api/backend/[...path]">) {
  const method = request.method.toUpperCase();
  if (!sameOrigin(request, method)) {
    return error("Petición no permitida", 403);
  }
  const { path } = await ctx.params;
  const route = matchRoute(path, method);
  if (route === null) return error("Ruta no encontrada", 404);

  const token = await readToken();
  if (!token) return error("No autenticado", 401);

  // Cuerpo con tope por ruta (subidas: 10 MB + 64 KB, como el backend; JSON: 256 KB). Se corta
  // al pasarse aunque falte o mienta el Content-Length.
  let body: Uint8Array<ArrayBuffer> | null = null;
  if (method !== "GET" && method !== "HEAD") {
    const tooLarge = route.maxBody > 1024 * 1024
      ? "Fichero demasiado grande (máximo 10 MB)"
      : "Cuerpo demasiado grande";
    const declared = Number(request.headers.get("content-length") ?? "0");
    if (!Number.isFinite(declared) || declared > route.maxBody) return error(tooLarge, 413);
    try {
      body = await readCapped(request.body, route.maxBody);
    } catch (e) {
      if (e instanceof BodyTooLarge) return error(tooLarge, 413);
      return error("Petición no válida", 400);
    }
  }

  const target = route.path;
  const isStream = route.rule.stream === true;
  let res: Response;
  try {
    res = await backendFetch(target + request.nextUrl.search, {
      method,
      token,
      headers: forwardRequestHeaders(request.headers, token),
      body,
      signal: request.signal,
      timeoutMs: isStream ? null : undefined,
    });
  } catch {
    return error("Servicio no disponible temporalmente", 503);
  }

  if (res.status === 401) {
    // Sesión caducada o revocada en el backend: se borra la cookie para no reintentar con ella.
    const store = await cookies();
    for (const name of [sessionCookieName(), idleCookieName()]) {
      store.set(name, "", sessionCookieAttrs({ maxAge: 0 }));
    }
  }
  if (res.status >= 300 && res.status < 400) return error("Respuesta no válida del servidor", 502);

  return new NextResponse(res.body, {
    status: res.status,
    headers: forwardResponseHeaders(res.headers),
  });
}

export const GET = handle;
export const POST = handle;
