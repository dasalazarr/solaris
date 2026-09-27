"use client";

/** Cierra la sesión. La lógica vive en IdleGuard (avisa también a las otras pestañas). */
export default function LogoutButton() {
  return (
    <button
      type="button"
      className="btn"
      onClick={() => window.dispatchEvent(new Event("solaris:logout"))}
    >
      Cerrar sesión
    </button>
  );
}
