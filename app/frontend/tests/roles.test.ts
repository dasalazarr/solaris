import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

import { SCREENS, canSee, roleLabel, screensFor } from "@/lib/roles";

describe("navegación por rol", () => {
  it("cada rol del demo ve su menú", () => {
    const keys = (r: string) => screensFor(r).map((s) => s.key);
    expect(keys("calidad")).toEqual(["inbox", "casos", "aprobaciones"]);
    expect(keys("planta")).toEqual([]);
    expect(keys("auditor")).toEqual(["auditoria"]);
    expect(keys("admin")).toEqual(["auditoria"]);
  });
  it("un rol desconocido no ve nada (falla cerrado)", () => {
    expect(screensFor("superadmin")).toEqual([]);
    expect(screensFor("__proto__")).toEqual([]);
    expect(canSee("constructor", "auditoria")).toBe(false);
    expect(roleLabel("otro")).toBe("otro");
  });
});

/**
 * El menú refleja la matriz de acceso del backend. Si alguien cambia
 * `app/backend/tests/test_access_matrix.py::MATRIX`, este test avisa.
 */
describe("coherencia con la matriz del backend", () => {
  const src = readFileSync(
    fileURLToPath(new URL("../../backend/tests/test_access_matrix.py", import.meta.url)),
    "utf8",
  );
  function rolesOf(method: string, path: string): string[] {
    const re = new RegExp(
      `\\("${method}", "${path.replace(/[{}/]/g, (c) => `\\${c}`)}"\\): (\\{[^}]*\\}|ALL)`,
    );
    const m = src.match(re);
    if (!m) throw new Error(`No encuentro ${method} ${path} en MATRIX`);
    if (m[1] === "ALL") return ["admin", "auditor", "calidad", "planta"];
    return [...m[1].matchAll(/"(\w+)"/g)].map((x) => x[1]).sort();
  }
  it.each(SCREENS.map((s) => [s.key, s.backend] as const))("%s ↔ %s", (key, backend) => {
    const [method, path] = backend.split(" ");
    const screen = SCREENS.find((s) => s.key === key)!;
    expect([...screen.roles].sort()).toEqual(rolesOf(method, path));
  });
});
