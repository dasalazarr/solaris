import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { AiLabel, Forbidden, Placeholder, ServiceError } from "@/components/notices";
import { InjectionBanner, ReviewNote } from "@/components/inbox/SecurityNotices";
import type { CaseView } from "@/lib/api-client";
import { formatDate, injectionNotice, reviewNotice, statusLabel } from "@/lib/inbox";
import { probe, requirePrincipal } from "@/lib/server/guard";

export const metadata: Metadata = { title: "Caso 8D" };

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/**
 * L02 · Caso 8D (placeholder de M5-T3; el workspace completo es M5-T4). Muestra estado y avisos de
 * seguridad (R-L02-14) con `GET /8d/{case_id}`, que decide el acceso (solo Calidad).
 */
export default async function CasePage({ params }: PageProps<"/casos/[id]">) {
  const { id } = await params;
  if (!UUID_RE.test(id)) notFound();
  const principal = await requirePrincipal();
  if (!principal) return null;
  const r = await probe<CaseView>(`/8d/${id}`);
  if (r.status === "forbidden") return <Forbidden what="este caso" detail={r.detail} />;
  if (r.status === "unavailable") return <ServiceError />;
  const v = r.data;
  const injection = injectionNotice({
    injection_suspected: v.complaint?.injection_suspected, warnings: v.warnings });
  const review = reviewNotice(v.warnings);
  return (
    <>
      <h1>
        <span className="mono">{v.complaint_id ?? "Caso 8D"}</span>
        {v.complaint?.part_ref ? ` · ${v.complaint.part_ref}` : ""}
      </h1>
      <p className="sub">
        {v.customer?.name ?? v.customer?.code ?? "—"} · estado: <b>{statusLabel(v.status)}</b> ·
        creado el {formatDate(v.created_at)} por {v.created_by}
        {v.elapsed_s != null ? ` · borrador en ${v.elapsed_s} s` : ""}
      </p>
      {injection && <InjectionBanner notice={injection} complaintId={v.complaint_id} />}
      {review && <ReviewNote notice={review} />}
      <Placeholder task="M5-T4">
        <p>
          Aquí se editará el borrador D1–D4 <AiLabel /> con sus citas, los datos del ERP y los 8D
          similares. <Link href="/inbox">Volver a Reclamaciones</Link>.
        </p>
      </Placeholder>
    </>
  );
}
