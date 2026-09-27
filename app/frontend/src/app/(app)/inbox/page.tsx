import type { Metadata } from "next";

import { AiLabel, Forbidden, Placeholder } from "@/components/notices";
import { canSee } from "@/lib/roles";
import { requirePrincipal } from "@/lib/server/guard";

export const metadata: Metadata = { title: "Reclamaciones" };

/** L01 · Inbox de reclamaciones (M5-T3). Acceso real: `POST /8d` (solo Calidad). */
export default async function InboxPage() {
  const principal = await requirePrincipal();
  if (!principal) return null;
  if (!canSee(principal.role, "inbox")) return <Forbidden what="las reclamaciones" />;
  return (
    <>
      <h1>Reclamaciones abiertas</h1>
      <p className="sub">L01 · subir PDF o EML, crear el caso 8D y ver el progreso.</p>
      <Placeholder task="M5-T3">
        <p>
          Aquí aparecerán la lista de reclamaciones, la zona para soltar el PDF o el correo y el
          progreso por pasos. Cada resultado del asistente llevará la etiqueta <AiLabel />.
        </p>
      </Placeholder>
    </>
  );
}
