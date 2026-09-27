import type { Metadata } from "next";

import InboxClient from "@/components/inbox/InboxClient";
import { Forbidden } from "@/components/notices";
import type { CaseListPage } from "@/lib/api-client";
import { canSee } from "@/lib/roles";
import { probe, requirePrincipal } from "@/lib/server/guard";

export const metadata: Metadata = { title: "Reclamaciones" };

/**
 * L01 · Inbox de reclamaciones (M5-T3). El acceso lo decide el backend: `GET /8d` (lista),
 * `POST /complaints/parse` y `POST /8d` son solo del rol Calidad; `roles.ts` solo oculta el menú.
 */
export default async function InboxPage() {
  const principal = await requirePrincipal();
  if (!principal) return null;
  if (!canSee(principal.role, "inbox")) return <Forbidden what="las reclamaciones" />;
  const r = await probe<CaseListPage>("/8d");
  if (r.status === "forbidden") return <Forbidden what="las reclamaciones" detail={r.detail} />;
  const initial = r.status === "ok"
    ? { status: "ok" as const, items: r.data.items }
    : { status: "error" as const, forbidden: false,
        message: "El servicio no está disponible ahora mismo. Pulsa Actualizar en unos segundos." };
  return (
    <>
      <h1>Reclamaciones</h1>
      <p className="sub">
        L01 · sube la reclamación del cliente, revisa los campos y genera el borrador 8D. Nada sale
        de aquí sin aprobación humana.
      </p>
      <InboxClient initial={initial} />
    </>
  );
}
