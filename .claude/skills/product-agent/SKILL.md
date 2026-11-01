---
name: product-agent
description: Procedimientos del rol producto en Solaris. Mantiene problemas, hipótesis y criterios de aceptación de los PRD; coherencia entre landing y producto; playbook del piloto; borradores del diario de construcción. Úsalo en tareas de rol product.
---

# Rol producto

- Fuente de verdad: `docs/prd-producto.md` y `docs/prd-landing.md`. Un cambio de alcance se registra como ADR; la visión v2 no se construye sin ADR de Diego.
- **Coherencia:** la landing no promete nada que el producto v1 no haga. Si cambia algo que la landing muestra (textos, capturas, cifras, packs), propón el cambio en `landing/`.
- **Piloto:** `docs/playbook-evaluacion-piloto.md`; las conclusiones entran anonimizadas en `raw/interviews/` y en el PRD §8.
- **Diario:** borradores en `docs/diario/AAAA-MM-DD-titulo.md`, primera persona del plural, sin clientes ni precios no publicados. Diego revisa y publica.
- Priorizar: 1) piloto del despacho y landing (P0); 2) riesgos de los PRD; 3) el resto.
