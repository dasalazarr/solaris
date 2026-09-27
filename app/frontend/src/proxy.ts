import { NextResponse, type NextRequest } from "next/server";

/**
 * Proxy de Next (antes "middleware"):
 * 1. CSP con nonce por petición (script-src sin 'unsafe-inline'): mitiga XSS. El token ya está en
 *    una cookie httpOnly, pero un XSS podría usar la sesión desde la propia página.
 * 2. Sin cookie de sesión, las páginas de la app redirigen al login. Es solo UX: la sesión real
 *    la valida el backend en cada petición (layout → `/auth/me`).
 * Las rutas `/api/*` hacen sus propias comprobaciones (same-origin, CSRF, cookie).
 */

const SESSION_COOKIES = ["solaris_session", "__Host-solaris_session"];

function csp(nonce: string): string {
  const dev = process.env.NODE_ENV === "development";
  return [
    "default-src 'self'",
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'${dev ? " 'unsafe-eval'" : ""}`,
    // En desarrollo Next inyecta estilos sin nonce (HMR); en producción, solo con nonce.
    dev ? "style-src 'self' 'unsafe-inline'" : `style-src 'self' 'nonce-${nonce}'`,
    "img-src 'self' blob: data:",
    "font-src 'self'",
    "connect-src 'self'",
    "object-src 'none'",
    "base-uri 'none'",
    "form-action 'self'",
    "frame-ancestors 'none'",
  ].join("; ");
}

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const hasSession = SESSION_COOKIES.some((n) => request.cookies.has(n));
  if (!hasSession && pathname !== "/login") {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    url.search = pathname === "/" ? "" : "?motivo=sesion";
    return NextResponse.redirect(url);
  }

  const nonce = Buffer.from(crypto.randomUUID()).toString("base64");
  const policy = csp(nonce);
  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-nonce", nonce);
  requestHeaders.set("content-security-policy", policy);
  const response = NextResponse.next({ request: { headers: requestHeaders } });
  response.headers.set("content-security-policy", policy);
  return response;
}

export const config = {
  matcher: [
    {
      // Páginas: todo menos API, estáticos y ficheros públicos; sin prefetches.
      source: "/((?!api|_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|ico|txt)$).*)",
      missing: [
        { type: "header", key: "next-router-prefetch" },
        { type: "header", key: "purpose", value: "prefetch" },
      ],
    },
  ],
};
