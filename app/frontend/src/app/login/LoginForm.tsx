"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { ApiError, createApiClient } from "@/lib/api-client";

// En el login un 401 significa "credenciales incorrectas", no "sesión caducada".
const client = createApiClient({ onUnauthorized: () => undefined });

/**
 * Formulario de acceso. Envía usuario y contraseña al BFF (`POST /api/session`), que los pasa al
 * backend y guarda el token en una cookie httpOnly. Aquí no se guarda nada: ni token ni rol.
 */
/** Sincroniza `aria-invalid` con `:user-invalid` (el error se anuncia solo tras interactuar). */
function syncInvalid(ev: { target: EventTarget }) {
  const el = ev.target;
  if (!(el instanceof HTMLInputElement) || el.type === "checkbox") return;
  let invalid = false;
  try {
    invalid = el.matches(":user-invalid");
  } catch {
    invalid = false; // navegador sin :user-invalid: se confía en la validación nativa al enviar
  }
  if (invalid) el.setAttribute("aria-invalid", "true");
  else el.removeAttribute("aria-invalid");
}

export default function LoginForm() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  async function onSubmit(ev: FormEvent<HTMLFormElement>) {
    ev.preventDefault();
    const form = ev.currentTarget;
    const data = new FormData(form);
    setPending(true);
    setError(null);
    try {
      await client.session.login(String(data.get("username") ?? ""),
                                 String(data.get("password") ?? ""));
      router.replace("/");
      router.refresh();
    } catch (e) {
      setError(e instanceof ApiError ? e.userMessage : "No se ha podido iniciar sesión.");
      const pw = form.elements.namedItem("password");
      if (pw instanceof HTMLInputElement) {
        pw.value = "";
        pw.focus();
      }
      setPending(false);
    }
  }

  return (
    <form className="card login-form" method="post" onSubmit={onSubmit}
          onBlurCapture={syncInvalid} onInput={syncInvalid}>
      <div className="field">
        <label htmlFor="username">Usuario</label>
        <input id="username" name="username" type="text" autoComplete="username" required
               autoCapitalize="none" autoCorrect="off" spellCheck={false} maxLength={64}
               enterKeyHint="next" aria-describedby="username-error" />
        <span id="username-error" className="field-error">Introduce tu usuario.</span>
      </div>
      <div className="field">
        <label htmlFor="current-password">Contraseña</label>
        <input id="current-password" name="password" type={showPassword ? "text" : "password"}
               autoComplete="current-password" required maxLength={256} enterKeyHint="done"
               aria-describedby="password-error" />
        <span id="password-error" className="field-error">Introduce tu contraseña.</span>
        <label className="check">
          <input type="checkbox" checked={showPassword}
                 onChange={(e) => setShowPassword(e.target.checked)} />
          Mostrar contraseña
        </label>
      </div>
      <p className="form-error" role="alert" aria-live="assertive">{error}</p>
      <button type="submit" className="btn primary block" disabled={pending}>
        {pending ? "Entrando…" : "Iniciar sesión"}
      </button>
      <p className="note">
        La sesión se cierra tras 15 minutos sin actividad. En un equipo compartido, cierra la
        sesión al terminar.
      </p>
    </form>
  );
}
