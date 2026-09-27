import type { Metadata } from "next";
import { redirect } from "next/navigation";

import { SynthBand } from "@/components/notices";
import { getSession } from "@/lib/server/session";

import LoginForm from "./LoginForm";

export const metadata: Metadata = { title: "Iniciar sesión" };

const REASONS: Record<string, string> = {
  sesion: "Tu sesión ha caducado o se ha cerrado. Vuelve a iniciar sesión.",
  inactividad: "Se ha cerrado la sesión tras un periodo sin actividad.",
  salida: "Has cerrado la sesión.",
};

export default async function LoginPage({ searchParams }: PageProps<"/login">) {
  const session = await getSession();
  if (session.status === "ok") redirect("/");
  const { motivo } = await searchParams;
  const reason = typeof motivo === "string" ? REASONS[motivo] : undefined;
  return (
    <>
      <SynthBand />
      <main className="login">
        <h1>Solaris · Calidad 8D</h1>
        <p className="sub">Componentes Arga S.L. · demo</p>
        {reason && (
          <p className="alert a-info" role="status">
            {reason}
          </p>
        )}
        <LoginForm />
      </main>
    </>
  );
}
