---
id: PAT-006
type: pattern
title: "Un generador sintético se congela cuando otro artefacto cita sus IDs"
status: accepted
owner_role: dev
links: ["[[ADR-0004]]", "[[PAT-004]]", "[[R05]]"]
evidence: ["raw/sessions/2026-09-25_product_M1-T2.md", "raw/sessions/2026-09-24_dev_M1-T3.md", "raw/sessions/2026-09-25_product_M1-T4.md"]
updated: 2026-09-25
---

# PAT-006 — Un generador sintético se congela cuando otro artefacto cita sus IDs

## Patrón (fallo evitado)
El corpus (M1-T2) cita 104 lotes, 48 lotes de material y 124 albaranes **generados** por el seed del ERP (M1-T3). Los códigos dependen del flujo del generador aleatorio. Cualquier cambio en `erp/generate_seed.py` que consuma el RNG de otra forma (aunque solo sea para "arreglar" cantidades irreales) renumera los códigos y rompe en silencio el corpus y, después, el golden set.

## Evidencia (trazas en raw/)
M1-T2 detectó irrealismos en el seed: lotes de hilo de 13–24 t y albaranes no cronológicos. **No se corrigen** para no romper las referencias.

## Cómo aplicarlo / workaround
- Tras M1-T2, `generate_seed.py` está **congelado**. Las correcciones se hacen como **post-proceso que no toca el RNG** (p. ej. reescalar `qty` de los lotes de hilo después de generarlos) y siempre se vuelven a ejecutar `check_corpus.py` y `smoke.sql`.
- Todo generador aguas abajo (corpus → reclamaciones → golden set) lee los IDs de la fuente (ERP o manifest), nunca los recalcula.
- Cadena de validación tras cualquier cambio de datos: `smoke.sql` → `check_corpus.py` → (M1-T5) validador del golden set.

## Irrealismos conocidos del seed (aceptados, no se corrigen)
- Lotes de hilo de 13–24 t.
- Albaranes no estrictamente cronológicos (AL-26-00573 es anterior a AL-26-00572).
- Numeración de reclamaciones no monótona (C-LEIZ-2026-0088 frente a 0107).
- Lotes `released` parcialmente expedidos (ver F05).
- El hilo S-GOIE-260117 también alimenta CR-02 (AR-1005/1009/1010), algo coherente con la planta y útil para el distractor #3.

Si un validador de cliente lo señala en M6, se explica como "datos sintéticos"; no justifica romper las referencias.
