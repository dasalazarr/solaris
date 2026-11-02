---
id: PAT-005
type: pattern
title: "Un cambio, una rama, un PR por repositorio"
status: accepted
owner_role: dev
links: ["[[PAT-001]]", "[[ADR-0008]]", "[[R04]]"]
evidence: ["raw/sessions/2026-11-02_orquestador_despliegue-y-correo.md"]
updated: 2026-11-02
---

# PAT-005 — Un cambio, una rama, un PR

Con tres repositorios (raíz, producto, landing) y PR apilados, Diego perdió la pista de qué estaba fusionado. Reglas:

1. Cada PR apunta a `main`; nada de PR contra ramas de trabajo.
2. Vercel despliega solo `main` de `illariumcore` y `solaris_fronted`. La raíz no se despliega.
3. Orden: producto o landing primero; después, un PR «punteros» en la raíz.
4. Activar «Automatically delete head branches» en los tres repositorios.
5. No seguir comprometiendo en una rama ya fusionada: crear una nueva desde `main`.
6. Una variable `NEXT_PUBLIC_*` solo surte efecto tras un nuevo despliegue.
