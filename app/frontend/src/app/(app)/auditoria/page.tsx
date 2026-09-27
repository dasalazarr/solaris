import type { Metadata } from "next";

import { Forbidden, Placeholder, ServiceError } from "@/components/notices";
import type { AuditPage } from "@/lib/api-client";
import { probe, requirePrincipal } from "@/lib/server/guard";

export const metadata: Metadata = { title: "Auditoría" };

const fmt = new Intl.DateTimeFormat("es-ES", { dateStyle: "short", timeStyle: "medium",
                                              timeZone: "Europe/Madrid" });

/**
 * L07 · Consola de auditoría (M5-T5). Acceso real: `GET /audit` (Auditor y Admin). Solo se
 * muestran fecha, tipo y actor de los últimos eventos; el detalle llega en M5-T5.
 */
export default async function AuditPageView() {
  const principal = await requirePrincipal();
  if (!principal) return null;
  const r = await probe<AuditPage>("/audit?limit=5");
  if (r.status === "forbidden") return <Forbidden what="la consola de auditoría" />;
  return (
    <>
      <h1>Consola de auditoría</h1>
      <p className="sub">L07 · registro de solo anexar con cadena de hash.</p>
      {r.status === "unavailable" ? (
        <ServiceError>El registro de auditoría no está disponible ahora mismo.</ServiceError>
      ) : (
        <Placeholder task="M5-T5">
          <h2>Últimos eventos</h2>
          <div className="tw">
            <table>
              <thead>
                <tr><th>Fecha</th><th>Tipo</th><th>Usuario</th><th>Rol</th></tr>
              </thead>
              <tbody>
                {r.data.items.map((e) => (
                  <tr key={e.id}>
                    <td className="mono">{fmt.format(new Date(e.ts))}</td>
                    <td className="mono">{e.event_type}</td>
                    <td>{e.actor_user ?? "—"}</td>
                    <td>{e.actor_role ?? "—"}</td>
                  </tr>
                ))}
                {r.data.items.length === 0 && (
                  <tr><td colSpan={4}>Sin eventos.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </Placeholder>
      )}
    </>
  );
}
