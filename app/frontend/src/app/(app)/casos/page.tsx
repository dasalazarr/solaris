import type { Metadata } from "next";

import { AiLabel, Forbidden, Placeholder } from "@/components/notices";
import { canSee } from "@/lib/roles";
import { requirePrincipal } from "@/lib/server/guard";

export const metadata: Metadata = { title: "Workspace 8D" };

/** L02 · Workspace 8D (M5-T4). Acceso real: `GET /8d/{case_id}` (solo Calidad). */
export default async function CasesPage() {
  const principal = await requirePrincipal();
  if (!principal) return null;
  if (!canSee(principal.role, "casos")) return <Forbidden what="los casos 8D" />;
  return (
    <>
      <h1>Workspace 8D</h1>
      <p className="sub">L02 · borrador D1–D4 con citas, datos del ERP y 8D similares.</p>
      <Placeholder task="M5-T4">
        <p>
          Abre un caso desde Reclamaciones. El borrador D1–D4 se mostrará con la etiqueta{" "}
          <AiLabel /> y cada afirmación con su cita.
        </p>
      </Placeholder>
    </>
  );
}
