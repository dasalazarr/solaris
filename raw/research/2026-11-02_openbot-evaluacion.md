# Evaluación de OpenBot (openbot.run) · 2026-11-02

Fuente: https://openbot.run/ y https://github.com/nightly-labs/openbot (README), consultadas el 2026-11-02.

## Qué es
App de escritorio (Electron + SolidJS) que ejecuta agentes persistentes en el ordenador. Usa Codex App Server y el Claude Agent SDK por debajo; admite agentes ACP, endpoints compatibles con OpenAI, Ollama y LM Studio.

## Datos relevantes para Solaris
- **Licencia:** PolyForm Noncommercial 1.0.0. El uso comercial exige una licencia aparte (Starter o Team). Las versiones ≤ 0.1.11 siguen bajo Apache-2.0.
- **Permisos:** los agentes corren con `danger-full-access` y `approvalPolicy: never`, sin confirmación por acción.
- **Estado:** agentes, conversaciones, colas y sesiones en `openbot.db` (SQLite, en `userData`); workspaces en `~/OpenBot/Agents/<agent-id>`. No vive en git.
- **Coordinación:** mensajes y transferencias entre agentes, colas FIFO, canales con un responsable por tarea, routines disparadas por webhook.
- **Dashboard:** no se anuncia como función.

## Lectura
No añade un motor que no tengamos (Claude Agent SDK). Choca con el principio 3 (persona en el bucle), con [[ADR-0005]] (el repo es la memoria) y con nuestra naturaleza comercial. Ver ADR-0007.
