/**
 * Pantallas del demo y roles que las ven (M5-T2).
 *
 * SOLO para la experiencia de usuario: decide qué enlaces se muestran. La autorización real es
 * siempre la del backend (PAT-008): cada pantalla llama a endpoints que devuelven 401/403 por sí
 * mismos. Este mapa refleja `app/backend/tests/test_access_matrix.py::MATRIX`; si cambia la
 * matriz, cambia aquí (lo comprueba `roles.test.ts`).
 */

export type Role = "calidad" | "planta" | "auditor" | "admin";

export type ScreenKey = "inbox" | "casos" | "aprobaciones" | "auditoria";

export interface Screen {
  key: ScreenKey;
  code: string; // página L de la wiki
  href: `/${string}`;
  label: string;
  roles: readonly Role[];
  /** Endpoint del backend que decide el acceso (documental). */
  backend: string;
}

export const SCREENS: readonly Screen[] = [
  { key: "inbox", code: "L01", href: "/inbox", label: "Reclamaciones", roles: ["calidad"],
    backend: "POST /8d" },
  { key: "casos", code: "L02", href: "/casos", label: "Workspace 8D", roles: ["calidad"],
    backend: "GET /8d/{case_id}" },
  { key: "aprobaciones", code: "L03", href: "/aprobaciones", label: "Aprobaciones",
    roles: ["calidad"], backend: "GET /approvals" },
  { key: "auditoria", code: "L07", href: "/auditoria", label: "Auditoría",
    roles: ["auditor", "admin"], backend: "GET /audit" },
];

const ROLE_LABELS: Record<Role, string> = {
  calidad: "Calidad",
  planta: "Planta",
  auditor: "Auditoría externa",
  admin: "Administración",
};

export function isRole(value: unknown): value is Role {
  return typeof value === "string" && Object.hasOwn(ROLE_LABELS, value);
}

/** Etiqueta legible del rol que devuelve el backend. Un rol desconocido se muestra tal cual. */
export function roleLabel(role: string): string {
  return isRole(role) ? ROLE_LABELS[role] : role;
}

/** Pantallas visibles para un rol. Un rol desconocido no ve ninguna (falla cerrado). */
export function screensFor(role: string): Screen[] {
  return isRole(role) ? SCREENS.filter((s) => s.roles.includes(role)) : [];
}

export function canSee(role: string, key: ScreenKey): boolean {
  return screensFor(role).some((s) => s.key === key);
}

export function screen(key: ScreenKey): Screen {
  const s = SCREENS.find((x) => x.key === key);
  if (!s) throw new Error(`Pantalla desconocida: ${key}`);
  return s;
}
