# Solaris — Roadmap al demo validable

**Objetivo:** un demo funcional del flujo **reclamación del OEM → borrador 8D D1–D4 con citas, ERP trazado y aprobación humana**. Debe poder validarse con 5 responsables de calidad y servir para vender pilotos antes del cierre de la ayuda foral (**06/11/2026**, ver [O04](../wiki/opportunities/O04-ayuda-foral-2026.md)).

**Alcance congelado.** Cualquier cosa fuera de esta tabla se registra en la wiki como `idea` o `parked`, no se implementa ([PAT-001](../wiki/patterns/PAT-001-demo-una-cuna.md)).

| Hito | Fechas objetivo | Rol líder | Features | Gate de salida |
|---|---|---|---|---|
| [M0 Repo vivo](milestones/M0.md) | 24/09 ✅ | product + wiki | — | `wiki_lint.py` OK; cada F enlaza P y L; STATUS con la siguiente tarea de cada rol |
| [M1 Planta sintética + golden set](milestones/M1.md) | 25/09 – 30/09 | product → dev | datos para F01–F05 | Corpus y ERP mock cargables; golden set revisado; caso de inyección aprobado por security |
| [M2 Ingesta + RAG citado con ACL](milestones/M2.md) | 29/09 – 03/10 | dev | F01, F02, F03 | Precisión de citas ≥90%; "no encontrado" correcto; test ACL negativo = 0; p95 < 8 s |
| [M3 Agente 8D D1–D4](milestones/M3.md) | 03/10 – 09/10 | dev (+security) | F04, F05, F06, F10 | Borrador < 3 min; ≥3 similares; ≥2 hipótesis ligadas al AMFE; HITL no saltable; comparativa de ≥3 modelos |
| [M4 Trust Layer](milestones/M4.md) | 06/10 – 10/10 | security | F08, F09, F11 | Suite red-team 6/6 en verde; audit de solo anexar; RBAC on-behalf-of |
| [M5 UI del demo](milestones/M5.md) | 08/10 – 14/10 | dev + product | F07, F12, L01–L03, L07 | El guion corre de principio a fin sin intervención manual |
| [M6 Demo validable](milestones/M6.md) | 14/10 – 17/10 (demo listo) → validación hasta 31/10 | product + security | — | `make demo` reproducible; 5 sesiones de validación en `raw/interviews/`; H01–H04 actualizadas |

M3 y M4 se solapan: seguridad empieza el RBAC y el audit mientras dev construye el grafo 8D.

## Dependencias

```
M0 ─► M1 ─► M2 ─► M3 ─► M5 ─► M6
             │     ▲     ▲
             └──► M4 ────┘   (M4 necesita el esquema de BD de M2; M5 necesita el audit y el RBAC de M4)
```

## Fuera de alcance del demo (parked)
- Pasarela OT OPC UA/MQTT ([L08](../wiki/places/L08-borde-ot.md)).
- Keycloak y OpenFGA (en el demo, auth simple con roles; ver ADR-0002).
- GraphRAG.
- Vertical agro IFS/BRC.
- Euskera/ALIA.
- Autonomía L3.
- WikiSkill dentro del producto ([O02](../wiki/opportunities/O02-wikiskill-en-producto.md), v2).
- Conectores reales de SAP B1, Dynamics y Odoo (tras validar [H03](../wiki/hypotheses/H03-erp-pymes.md)).

## Después del demo (orientativo)
Preparar 3–5 expedientes de la ayuda foral con pilotos. Construir la ruta de modelos solo UE antes de usar datos reales ([R01](../wiki/risks/R01-soberania-vs-openrouter-deepseek.md)). Hacer el primer conector ERP real según H03. Experimentar con O02.
