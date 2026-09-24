# Solaris — Skill & feature impact tracker

> Registro de auditoría de **cada propuesta de cambio** atómica (a una skill, una feature o el código de un hito) y de su resultado en el gate. Equivale a `skill-impact.md` en WikiSkill.
> **Solo se anexa.** Las propuestas rechazadas también se registran, porque la wiki persiste y sirve para no repetir errores.

| # | Fecha | Rol | Objetivo (skill / feature / tarea) | Cambio (resumen o enlace a commit) | Gate | Resultado del gate | Decisión |
|---|---|---|---|---|---|---|---|
| 0 | 2026-09-24 | product | Repo (M0) | Scaffolding WikiSkill, wiki sembrada, 5 skills, 4 agentes, plan M0–M6 | `wiki_lint.py` | OK | **Accepted** |
| 1 | 2026-09-24 | product | M1-T1 Ficha de la planta ficticia | `app/data/synthetic/PLANT.md` + `acl.json` (3 líneas, 12 referencias, 6 proveedores, 3 clientes, 4 usuarios/roles, 9 carpetas, 2 familias de recurrencia, 5 casos de test de ACL). En la revisión se renombra el cliente "Ebro…" → "Ribera Chassis Systems" (Ebro es una marca real de vehículos) | Contraste con las personas §3.2 + consistencia PLANT.md ↔ acl.json (script) | 9/9 carpetas coinciden; 4 personas cubiertas | **Accepted** |
