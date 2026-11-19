---
id: R03
type: risk
title: "Trabajo en la nube y copia local divergen"
status: building
owner_role: wiki
links: ["[[PAT-001]]"]
evidence: ["raw/sessions/2026-11-01_orquestador_workspace-y-pendientes.md"]
updated: 2026-11-01
---

# R03 — Divergencia nube/local
Ocurrió el 01/11: el remoto `solaris.git` tenía el espacio de trabajo y la carpeta local era otro proyecto. Mitigación en [[PAT-001]]: fetch al arrancar la sesión y un repo por proyecto.
