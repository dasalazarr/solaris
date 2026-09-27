"use client";

import { createApiClient } from "./api-client";

/**
 * Instancia del cliente API para los componentes cliente. Cada respuesta del servidor cuenta como
 * actividad (el backend también renueva la sesión con cada petición autenticada).
 */

type Listener = () => void;
const listeners = new Set<Listener>();

export function onServerContact(fn: Listener): () => void {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

export const api = createApiClient({
  onActivity: () => listeners.forEach((fn) => fn()),
});
