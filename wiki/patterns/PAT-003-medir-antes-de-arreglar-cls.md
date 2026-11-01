---
id: PAT-003
type: pattern
title: "Medir el origen de un CLS antes de arreglarlo"
status: accepted
owner_role: dev
links: ["[[F06]]", "[[L02]]"]
evidence: ["raw/eval-runs/2026-11-01_lighthouse-landing.md"]
updated: 2026-11-01
---

# PAT-003 — Medir antes de arreglar
## Patrón (éxito)
El estado atribuía el CLS a la animación del hero. El `PerformanceObserver` mostró que era el cambio de fuente (el párrafo pasaba de 3 a 4 líneas). `next/font` con fuente de reserva ajustada lo llevó a 0.
## Cómo aplicarlo
Registrar los `layout-shift` con sus nodos antes de tocar código y comparar contra la rama base con el mismo servidor.
