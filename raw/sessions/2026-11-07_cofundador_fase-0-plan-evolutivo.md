# 2026-11-07 · cofundador · Fase 0 del plan evolutivo

**Pedido:** estado del producto frente a un estudio de mercado y plan evolutivo sin sobreingeniería, para tener un espacio listo para mostrarse, usarse y probarse. Después: incluir la experiencia de usuario con el vídeo como referencia, y ejecutar la Fase 0.

**Decisiones de Diego:** el canal de consultora está sin confirmar; to be funcional; procesos en general con foco en la parametrización; el vídeo como referencia no excluyente.

**Hecho:** ADR-0015, `docs/plan-evolutivo.md`, `docs/spec-experiencia.md`, ROADMAP, PRD, nota en Nivel 2, F07, H03, O06. Trabajo sin commit del 05/11 recogido y punteros en `main`.

**Evidencia:** 110 tests del producto; código revisado con un agente; producción recorrida con Chrome en la sesión de Diego (Preguntar, Explorar, Huecos, Revisar y Preguntar a 390 px), con una pregunta libre de prueba y sin aprobar nada; hojas de contacto de los MP4; síntesis en `raw/research/2026-11-07_estudio-mercado-sintesis.md`.

**Qué falló o se corrigió:**
- Dije que la rama del favicon de la landing no tenía PR: era falso. No había hecho fetch en el submódulo y estaba fusionada en solaris_fronted#16.
- Dije que un cortafuegos bloqueaba `illariumcore.vercel.app`: ocurrió en una red; después dejó de reproducirse. Causa desconocida.
- El plan decía guardar el estudio en `raw/research/`. `solaris` es público, así que se guarda solo una síntesis anónima.

**Pendiente:** fusionar el PR; decidir la pregunta libre; confirmar en el PDF del BON las intensidades. La causa exacta del fallo de la pregunta libre no se ha mirado en Vercel: no tocar sin decidir la clave.
