import IdleGuard from "@/components/IdleGuard";
import LogoutButton from "@/components/LogoutButton";
import NavLinks from "@/components/NavLinks";
import { AiNotice, ServiceError, SynthBand } from "@/components/notices";
import { roleLabel, screensFor } from "@/lib/roles";
import { getSession } from "@/lib/server/session";
import { redirect } from "next/navigation";

/**
 * Layout de la app autenticada: cabecera con usuario y rol (los dice el backend en `/auth/me`),
 * navegación según el rol, aviso de IA (art. 50, F11) y banda de datos sintéticos (ADR-0004).
 */
export default async function AppLayout({ children }: LayoutProps<"/">) {
  const session = await getSession();
  if (session.status === "anon") redirect("/login?motivo=sesion");
  if (session.status === "unavailable") {
    return (
      <main className="narrow">
        <h1>Solaris</h1>
        <ServiceError>
          No se puede comprobar tu sesión con el servidor. Recarga la página en unos segundos.
        </ServiceError>
      </main>
    );
  }
  const { principal, idleTimeoutS } = session;
  const nav = screensFor(principal.role).map(({ href, code, label }) => ({ href, code, label }));

  return (
    <>
      <a className="skip" href="#contenido">Saltar al contenido</a>
      <header className="top">
        <div className="bar">
          <span className="brand">Solaris · Calidad 8D</span>
          <span className="tag plant">Componentes Arga S.L. · Orkoien</span>
          <span className="user">
            <span className="user-name">{principal.user}</span>{" "}
            <span className="tag role" title="Rol asignado por el servidor">
              {roleLabel(principal.role)}
            </span>
          </span>
          <LogoutButton />
        </div>
        <AiNotice />
        <SynthBand />
        <NavLinks items={nav} />
      </header>
      <main id="contenido">{children}</main>
      <IdleGuard idleTimeoutS={idleTimeoutS} />
    </>
  );
}
