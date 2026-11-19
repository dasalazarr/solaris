# Sesión 2026-11-02 · orquestador · equipo de agentes como Proceso

## Tarea
Diego propuso un equipo de agentes «dueños» (landing, producto; después comunicación y diseño) sobre OpenBot, con una plataforma de estado. Pidió criticar la idea y llegar a una síntesis dialéctica.

## Qué se hizo
- Evaluación de OpenBot: `raw/research/2026-11-02_openbot-evaluacion.md`.
- Crítica: licencia no comercial, ejecución sin confirmación por acción, estado fuera del repo; «dueño» sin consecuencias; A/B sin tráfico; retención mal asignada a la landing; insights sin cita; plataforma propia antes de los P0.
- Síntesis aceptada por Diego (ADR-0007): el equipo es un Proceso de Solaris. Runtime = repo + Claude Code; `product` se divide en `landing-steward` y `product-steward`; el tablero será un pack `equipo` dentro del producto (fase 1, tras configurar el despliegue).
- Fase 0 hecha: contratos en `plan/contratos/`, agentes y skills nuevos, reglas `REG-*` en `scripts/wiki_lint.py` con 9 tests en `scripts/test_wiki_lint.py`, O03–O05 en la wiki.

## Qué falló
Nada en el gate. Riesgo abierto: si nadie actualiza `ultima_evidencia`, los contratos se quedan viejos; el lint avisa a los 14 días, pero no bloquea.

## Decisiones
ADR-0007. `owner_role` de la wiki sigue con `product` para los dos administradores, para no tocar todas las páginas.

## Evidencia
`python3 scripts/test_wiki_lint.py` → 9 tests OK. `python3 scripts/wiki_lint.py --write-index` → OK.
