import { channelLabel, locationLabel, type InjectionNotice, type ReviewNotice } from "@/lib/inbox";

/**
 * Avisos de seguridad de una reclamación (R-L01-4, R-L02-14; R03, PAT-012).
 *
 * - `InjectionBanner` (ROJO): solo cuando el detector determinista del backend lo marca.
 * - `ReviewNote` (ÁMBAR, secundario): señal del LLM sin corroborar. No bloquea ni alarma.
 *
 * Los extractos son texto del documento (no confiable): se pintan como texto dentro de `<q>`, y
 * React lo escapa. No se usa `dangerouslySetInnerHTML` en ningún sitio.
 */

export function InjectionBanner({
  notice,
  complaintId,
}: {
  notice: InjectionNotice;
  complaintId?: string | null;
}) {
  const channels = notice.channels.map(channelLabel);
  return (
    <div className="alert a-bad security" role="alert" data-testid="injection-banner">
      <b>
        {complaintId ? `${complaintId} · ` : ""}Se ignoraron instrucciones incluidas en el
        documento.
      </b>{" "}
      El documento contiene texto dirigido al asistente. Se ha tratado como dato del cliente,{" "}
      <b>no como órdenes</b>: no se ha ejecutado nada y el 8D sigue necesitando aprobación humana.
      {channels.length > 0 && (
        <p className="sec-channels">
          Canales ({channels.length}):{" "}
          {channels.map((c) => (
            <span key={c} className="tag t-bad">
              {c}
            </span>
          ))}
        </p>
      )}
      {notice.findings.length > 0 && (
        <ul className="sec-list">
          {notice.findings.map((f, i) => {
            const where = locationLabel(f.location);
            return (
              <li key={`${f.channel}-${i}`}>
                <span className="sec-where">
                  {channelLabel(String(f.channel))}
                  {where ? ` · ${where}` : ""}
                </span>
                {f.excerpt ? (
                  <>
                    {": "}
                    <q className="excerpt">{f.excerpt}</q>
                  </>
                ) : null}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

export function ReviewNote({ notice }: { notice: ReviewNotice }) {
  return (
    <div className="alert a-warn review-note" role="note" data-testid="review-note">
      <b>Nota de revisión.</b> {notice.message}
      {notice.items.length > 0 && (
        <ul className="sec-list">
          {notice.items.map((it, i) => {
            const where = locationLabel(it.location);
            return (
              <li key={`${it.source}-${i}`}>
                <span className="sec-where">
                  {where || "documento"}
                  {it.located === false ? " · inicio del fragmento" : " · frase señalada"}
                </span>
                {": "}
                <q className="excerpt">{it.excerpt}</q>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
