# Traza de sesión — 2026-09-24 → 2026-09-27 · orquestador · cierre

Una sesión larga de orquestación: el orquestador lanza y reanuda agentes por rol (product, dev, security), repite cada gate, consolida la wiki y hace un commit por tarea.

## Qué se hizo
- **M0:** brainstorm → repositorio vivo WikiSkill (raw/wiki/skills), 5 skills, 4 agentes, plan M0–M6 y `wiki_lint.py`.
- **M1 (cerrado):** planta ficticia, ERP mock determinista, corpus de 41 documentos, 5 reclamaciones (distractor + inyección), golden set de 50 Q&A y 5 casos 8D, revisión de security.
- **M2 (gate abierto):** backend, `llm.route()`, esquema RAG con ACL en SQL, ingesta, recuperación híbrida, `POST /ask` y runner de evals. Precisión de citas 93 %, "no encontrado" 4/5, p95 fuera de objetivo.
- **M3 (cerrado):** MCP del ERP de solo lectura, parser de reclamaciones, grafo 8D (5/5 casos en ~27 s), HITL, comparativa de modelos (ADR-0007) y revisión de security con red-team (APPROVE con condiciones).
- **M4 (adelantado):** audit de solo anexar con cadena de hash, auth JWT + on-behalf-of + `solaris_app`, revisión de M2.
- **M5 (en curso):** guion del demo v0 y wireframes; esqueleto Next.js con BFF. **M5-T3 a medias, sin commit.**

## Decisiones del fundador
- Solaris es el nombre en clave de Illarium; la cuña del demo es el 8D en automoción; stack objetivo reducido.
- LLM vía OpenRouter, por calidad-precio → **ADR-0007:** config mixta (Gemini 2.5 Flash en Vertex UE con ZDR para el 8D; DeepSeek para la respuesta citada).
- **ADR-0006:** cierre del demo con promesa de ROI; panel F12 dentro del alcance.
- Adelantar la comparativa de modelos (M3-T5) para resolver la latencia.
- Detuvo 3 agentes (M2-T7 y M4-T5 el 25/09, M5-T3 el 27/09). Su trabajo parcial quedó sin commit o fue incluido en sus commits "first commit".

## Aprendizajes de orquestación (para la próxima sesión)
- **Límites de sesión de la API:** hubo 4 cortes con agentes en paralelo. Un agente pesado a la vez es más fiable, y los cortados se reanudan con su contexto.
- **Consolidación con scripts:** 3 veces un `patch()` falló por un anclaje con `**` que no estaba en el texto y el commit salió incompleto. Solución aplicada: encadenar `python … && lint && git commit`, de modo que un fallo aborte el commit.
- **Commits por rutas de la tarea**, nunca `git add -A` con agentes activos: evita mezclar trabajo en curso.
- **El orquestador repite siempre el gate** antes de aceptar. Los agentes no editan `wiki/`, `plan/` ni `CLAUDE.md`; lo hace el orquestador.

## Patrones creados en la sesión
PAT-001 a PAT-012 (ver `wiki/index.md`).

## Estado al cerrar
Ver `plan/STATUS.md`. Último commit estable antes del cierre: `c98e5b1` (M5-T2). Servidores de preview detenidos al cerrar.
