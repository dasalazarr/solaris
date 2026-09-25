---
id: ADR-0006
type: decision
title: "Cierre del demo con promesa de ROI y panel F12 dentro del alcance"
status: accepted
owner_role: product
links: ["[[H02]]", "[[F12]]", "[[P07]]", "[[PAT-001]]"]
evidence: ["raw/sessions/2026-09-25_product_M5-T1.md", "raw/research/IllariumOS.md#L239-L241"]
updated: 2026-09-25
---

# ADR-0006 — Cierre del demo con promesa de ROI y panel F12 dentro del alcance

## Contexto
En M5-T1 el agente de producto propuso cerrar ante Javier (CEO) con el umbral de horas y un "piloto medido", sin prometer ahorro, y aparcar el panel F12. Su argumento: la cuña 8D sola probablemente no justifica ~9.480 €/año.

## Decisión (del fundador, 2026-09-25)
1. **El cierre presenta el ROI del PRD como ahorro esperado:** ~450 h/año (5 h/semana de Calidad + 5 h/semana de jefes de turno) a 35–45 €/h = 16.000–20.000 €/año, con retorno < 12 meses para una planta de 100 empleados (PRD §3.4).
2. **M5-T7 (panel de no conformidades, F12) se mantiene** en el alcance del demo.

## Consecuencias
- Las cifras de ahorro son **[H] sin validar**. Riesgo: un CEO industrial escéptico puede pedir la base del cálculo. Mitigación: el guion cita la fuente (PRD §3.4) y la sesión de validación de M6 mide si el ahorro es creíble (H02). Si las 5 sesiones lo desmienten, se revisa esta decisión.
- Las 450 h/año incluyen jefes de turno (consultas en planta, L04), un uso que el demo no enseña. El guion debe ser coherente con eso.
- F12 añade ~1 tarea de dev (M5-T7) antes del 17/10. El panel puede apoyar visualmente el argumento de ROI (tiempo de ciclo, recurrencia).
