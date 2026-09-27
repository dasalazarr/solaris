import { redirect } from "next/navigation";

import { roleLabel, screensFor } from "@/lib/roles";
import { requirePrincipal } from "@/lib/server/guard";

/** Inicio: lleva a la primera pantalla del rol. Sin pantallas (p. ej. Planta) → aviso. */
export default async function Home() {
  const principal = await requirePrincipal();
  if (!principal) return null;
  const first = screensFor(principal.role)[0];
  if (first) redirect(first.href);
  return (
    <>
      <h1>Hola, {principal.user}</h1>
      <p className="sub">Rol: {roleLabel(principal.role)}</p>
      <div className="card">
        <p>
          Tu rol no tiene acceso a las pantallas del flujo 8D de este demo (reclamaciones,
          workspace, aprobaciones ni auditoría). El acceso lo decide el servidor según tu rol.
        </p>
      </div>
    </>
  );
}
