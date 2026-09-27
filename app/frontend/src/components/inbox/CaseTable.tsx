import Link from "next/link";

import type { CaseListItem, DeadlineInfo } from "@/lib/api-client";
import { channelLabel, formatDate, statusLabel, statusTone } from "@/lib/inbox";

function deadline(d: DeadlineInfo | undefined): string {
  if (!d) return "—";
  if (d.due_date) return formatDate(d.due_date);
  return d.text ?? "—";
}

/** Tabla de casos 8D de la bandeja L01 (R-L01-3/4). Solo metadatos; ningún texto del documento. */
export function CaseTable({ items }: { items: readonly CaseListItem[] }) {
  return (
    <div className="tw">
      <table>
        <caption className="visually-hidden">Casos 8D, del más reciente al más antiguo</caption>
        <thead>
          <tr>
            <th scope="col">Reclamación</th>
            <th scope="col">Cliente</th>
            <th scope="col">Pieza</th>
            <th scope="col">Lote</th>
            <th scope="col">Emitida</th>
            <th scope="col">Contención</th>
            <th scope="col">8D</th>
            <th scope="col">Estado</th>
          </tr>
        </thead>
        <tbody>
          {items.map((x) => (
            <tr key={x.case_id} className={x.injection_suspected ? "hot" : undefined}>
              <td className="mono">
                <Link href={`/casos/${x.case_id}`}>
                  <b>{x.complaint_id ?? x.filename}</b>
                </Link>
                {x.injection_suspected && (
                  <>
                    <br />
                    <span
                      className="tag t-bad"
                      title={`Instrucciones ignoradas en: ${x.injection_channels
                        .map(channelLabel).join(", ")}`}
                    >
                      ⚠ Aviso de seguridad
                      {x.injection_channels.length ? ` · ${x.injection_channels.length}` : ""}
                    </span>
                  </>
                )}
                {x.review_note && (
                  <>
                    <br />
                    <span className="tag t-warn">Nota de revisión</span>
                  </>
                )}
              </td>
              <td>{x.customer_name ?? x.customer ?? "—"}</td>
              <td className="mono">{x.part_ref ?? "—"}</td>
              <td className="mono">{x.lot_codes.length ? x.lot_codes.join(", ") : "—"}</td>
              <td>{formatDate(x.issued_date)}</td>
              <td>{deadline(x.deadlines?.containment)}</td>
              <td>{deadline(x.deadlines?.report_8d)}</td>
              <td>
                <span className={`tag tone-${statusTone(x.status)}`}>{statusLabel(x.status)}</span>
                <br />
                <span className="note">
                  {formatDate(x.created_at)} · {x.created_by}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
