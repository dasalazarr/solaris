"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { api, onServerContact } from "@/lib/api";
import { ApiError } from "@/lib/api-client";

/**
 * Cierre de sesión por inactividad (E1-US4, coherente con `AUTH_IDLE_TIMEOUT_S` del backend).
 *
 * - Actividad = interacción del usuario (teclado, puntero, rueda, táctil) o respuesta del servidor.
 * - Con actividad y más de PING_EVERY_MS sin hablar con el servidor, se hace `GET /api/session`
 *   para que el backend renueve la sesión (su reloj de inactividad solo cuenta peticiones).
 * - Un minuto antes del límite se avisa; al llegar al límite se cierra la sesión y se vuelve al
 *   login. El backend cierra la sesión por su cuenta aunque este componente no llegue a actuar.
 * - Las pestañas de la misma sesión comparten actividad y cierre (BroadcastChannel).
 */

const PING_EVERY_MS = 60_000;
const WARN_BEFORE_MS = 60_000;
const TICK_MS = 5_000;
const CHANNEL = "solaris-session";

export default function IdleGuard({ idleTimeoutS }: { idleTimeoutS: number }) {
  const idleMs = idleTimeoutS * 1000;
  const minutes = Math.max(1, Math.round(idleTimeoutS / 60));
  const lastActivity = useRef(0);
  const lastContact = useRef(0);
  const closing = useRef(false);
  const channel = useRef<BroadcastChannel | null>(null);
  const dialog = useRef<HTMLDialogElement>(null);
  const [remainingS, setRemainingS] = useState<number | null>(null);

  const close = useCallback(async (reason: "inactividad" | "salida", broadcast = true) => {
    if (closing.current) return;
    closing.current = true;
    if (broadcast) channel.current?.postMessage({ type: "logout", reason });
    await api.session.logout().catch(() => undefined);
    // Navegación completa a propósito: descarta todo el estado de cliente y la caché RSC de la sesión.
    // eslint-disable-next-line @next/next/no-location-assign-relative-destination
    window.location.assign(`/login?motivo=${reason}`);
  }, []);

  const ping = useCallback(() => {
    lastContact.current = Date.now();
    api.session.me().catch((e: unknown) => {
      // 401 ya redirige al login desde el cliente API; el resto se ignora (el siguiente
      // intento o el backend decidirán).
      if (!(e instanceof ApiError)) throw e;
    });
  }, []);

  const markActivity = useCallback(
    (fromOtherTab = false) => {
      const now = Date.now();
      lastActivity.current = now;
      if (!fromOtherTab) {
        channel.current?.postMessage({ type: "activity", at: now });
        if (now - lastContact.current > PING_EVERY_MS) ping();
      }
    },
    [ping],
  );

  useEffect(() => {
    const now = Date.now();
    lastActivity.current = now;
    lastContact.current = now;
    if ("BroadcastChannel" in window) {
      channel.current = new BroadcastChannel(CHANNEL);
      channel.current.onmessage = (ev: MessageEvent) => {
        const msg = ev.data as { type?: string; reason?: string; at?: number };
        if (msg?.type === "activity") markActivity(true);
        if (msg?.type === "logout") {
          void close(msg.reason === "salida" ? "salida" : "inactividad", false);
        }
      };
    }
    let lastEvent = 0;
    const onUser = () => {
      const t = Date.now();
      if (t - lastEvent < 1000) return; // como mucho un registro por segundo
      lastEvent = t;
      markActivity();
    };
    const events = ["pointerdown", "keydown", "wheel", "touchstart"] as const;
    events.forEach((e) => window.addEventListener(e, onUser, { passive: true }));
    const stopContact = onServerContact(() => {
      lastContact.current = Date.now();
      lastActivity.current = Date.now();
    });
    const onLogoutRequest = () => void close("salida");
    window.addEventListener("solaris:logout", onLogoutRequest);

    const timer = window.setInterval(() => {
      const idle = Date.now() - lastActivity.current;
      if (idle >= idleMs) {
        void close("inactividad");
      } else if (idle >= idleMs - WARN_BEFORE_MS) {
        setRemainingS(Math.ceil((idleMs - idle) / 1000));
      } else {
        setRemainingS(null);
      }
    }, TICK_MS);

    return () => {
      window.clearInterval(timer);
      events.forEach((e) => window.removeEventListener(e, onUser));
      window.removeEventListener("solaris:logout", onLogoutRequest);
      stopContact();
      channel.current?.close();
      channel.current = null;
    };
  }, [idleMs, markActivity, close]);

  useEffect(() => {
    const d = dialog.current;
    if (!d) return;
    if (remainingS !== null && !d.open) d.showModal();
    if (remainingS === null && d.open) d.close();
  }, [remainingS]);

  return (
    <dialog ref={dialog} className="idle-dialog" aria-labelledby="idle-title"
            onCancel={() => { markActivity(); setRemainingS(null); }}>
      <h2 id="idle-title">Tu sesión va a cerrarse</h2>
      <p>
        Por seguridad, la sesión se cierra tras {minutes} {minutes === 1 ? "minuto" : "minutos"}{" "}
        sin actividad. Quedan <b>{remainingS ?? 0} s</b>.
      </p>
      <div className="row">
        <button type="button" className="btn primary" autoFocus
                onClick={() => { markActivity(); setRemainingS(null); }}>
          Seguir conectado
        </button>
        <button type="button" className="btn" onClick={() => void close("salida")}>
          Cerrar sesión
        </button>
      </div>
    </dialog>
  );
}
