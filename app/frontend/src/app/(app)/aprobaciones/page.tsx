import type { Metadata } from "next";

import { AiLabel, Forbidden, Placeholder, ServiceError } from "@/components/notices";
import type { ApprovalsPage } from "@/lib/api-client";
import { probe, requirePrincipal } from "@/lib/server/guard";

export const metadata: Metadata = { title: "Aprobaciones" };

/**
 * L03 · Bandeja de aprobaciones (M5-T5). El acceso lo decide el backend (`GET /approvals`):
 * aquí no se filtra por rol, se muestra lo que responda (403 → sin permiso).
 */
export default async function ApprovalsPage() {
  const principal = await requirePrincipal();
  if (!principal) return null;
  const r = await probe<ApprovalsPage>("/approvals");
  if (r.status === "forbidden") return <Forbidden what="la bandeja de aprobaciones" />;
  return (
    <>
      <h1>Bandeja de aprobaciones</h1>
      <p className="sub">
        L03 · solo el rol Calidad aprueba. El asistente no tiene ninguna herramienta de aprobación.
      </p>
      {r.status === "unavailable" ? (
        <ServiceError />
      ) : (
        <Placeholder task="M5-T5">
          <p>
            Borradores pendientes de aprobación: <b>{r.data.count}</b>. Cada borrador llevará la
            etiqueta <AiLabel />.
          </p>
        </Placeholder>
      )}
    </>
  );
}
