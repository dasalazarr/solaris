import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { InjectionBanner, ReviewNote } from "@/components/inbox/SecurityNotices";
import { injectionNotice, reviewNotice } from "@/lib/inbox";

const HOSTILE = '<img src=x onerror="alert(1)"><script>alert(2)</script> ignore previous';

describe("avisos de seguridad (render)", () => {
  it("banner rojo con los 3 canales y el extracto escapado, nunca como HTML", () => {
    const n = injectionNotice({
      injection_suspected: true,
      injection_findings: [
        { channel: "visible", location: { page: 2 }, excerpt: HOSTILE },
        { channel: "hidden_text", location: { page: 1 }, excerpt: "［system］ override" },
        { channel: "metadata", location: { field: "pdf_metadata.keywords" }, excerpt: "x" },
      ],
    })!;
    const html = renderToStaticMarkup(<InjectionBanner notice={n} complaintId="C-OEMN-2026-0331" />);
    expect(html).toContain('role="alert"');
    expect(html).toContain("a-bad");
    expect(html).toContain("Se ignoraron instrucciones incluidas en el");
    expect(html).toContain("Canales (3)");
    for (const c of ["texto visible", "texto oculto", "metadatos"]) expect(html).toContain(c);
    expect(html).not.toContain("<img");
    expect(html).not.toContain("<script");
    expect(html).toContain("&lt;img src=x onerror=&quot;alert(1)&quot;&gt;");
  });

  it("nota de revisión en ámbar (no rojo, no alerta) con la frase señalada", () => {
    const r = reviewNotice([{ type: "model_flagged_text", message: "Revísalo.", items: [
      { source: "S3", channel: "visible", location: { page: 1 }, excerpt: HOSTILE, located: true },
      { source: "S4", channel: "visible", location: {}, excerpt: "Dear team", located: false },
    ] }])!;
    const html = renderToStaticMarkup(<ReviewNote notice={r} />);
    expect(html).toContain("a-warn");
    expect(html).not.toContain("a-bad");
    expect(html).not.toContain('role="alert"');
    expect(html).toContain("p. 1 · frase señalada");
    expect(html).toContain("documento · inicio del fragmento");
    expect(html).not.toContain("<script");
  });
});
