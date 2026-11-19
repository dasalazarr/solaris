---
type: session
rol: landing-steward
fecha: 2026-11-03
tarea: "ADR-0009 (tres audiencias), PR 1 copy sin respaldo y propuesta de estructura del PR 2"
---

# 2026-11-03 · landing-steward · visión y audiencias

## Tarea
Decisión de Diego (03/11): la landing da visión (ontología de procesos), enseña la demo y vende a clientes, aliados e inversores. Un relato, tres salidas. Orden: ADR-0009 + PRD → PR 1 (O1 de la auditoría) → propuesta del PR 2 sin código.

## Qué se hizo
- `docs/decisiones/0009-landing-tres-audiencias.md`; `docs/prd-landing.md` §1 (propósito, salidas, regla de copy) y §3 (fila Inversor) con nota de cambio fechada.
- PR 1 · dasalazarr/solaris_fronted#5 (`fix/copy-sin-respaldo`, commit `ae10ec4`): IFS «Demo disponible bajo petición»; fuera la sección del diario y su enlace del menú; Bento «Un motor, muchos procesos»; título unificado.
- Hallazgo: `dasalazarr.com/diario`, `/ensayos` y `/blog` devuelven 404 (curl, 03/11). No hay entradas publicadas: la sección se oculta (no se pregunta a Diego, el 404 lo responde) y se quita la columna «Recursos» del pie.
- Propuesta de estructura del PR 2 (abajo), pendiente del visto bueno de Diego.

## Evidencia
- `pnpm lint` OK (3 avisos previos de oxlint); `pnpm build` OK.
- `out/` servido en local: título nuevo, `noindex, nofollow`, sin `#diario` ni enlaces a diario/ensayos.
- 375 px: `scrollWidth` 375. Capturas de escritorio (Chrome headless, movimiento reducido) y de móvil (panel del navegador).

## Qué falló / aprendido
- El worktree nació de un commit antiguo de la raíz (`b43e70a`), sin `plan/` ni `fundacional.md`; hubo que moverlo a `origin/main`. Comprobar la base del worktree antes de leer (PAT-001).
- Chrome headless no baja de unos 500 px de ancho: la captura a 375 sale recortada. Para móvil, usar el panel con emulación.
- El panel oculto da `innerWidth` 0: medir desbordamiento solo con un tamaño emulado.
- En el producto, `approvalThresholds` dice que R-02 aplica «entre 6.000 y 15.000 €», pero la regla R-02 dice «≥ 6.000 €» y se aplica a PC-0412 (18.450 €). Incoherencia para product-steward.

## Propuesta PR 2 · `feat/vision-y-audiencias` (sin código hasta el visto bueno)
Orden de secciones (cambios en negrita):
1. Nav (añade «Visión») · 2. Hero · 3. Tesis · 4. **La ontología de procesos** (sustituye a El bucle) · 5. Qué hace · 6. Cifra · 7. Demo · 8. Packs · 9. **Hoy · Siguiente · Visión** · 10. Dos formas · 11. Cómo trabajamos (**salida aliados**) · 12. Preguntas · 13. Cierre con **tres salidas** · Pie.

- **Ontología:** las 7 primitivas sobre PC-0412 con los datos del producto: Proceso «Compras» (`policy_hash`, responsable Dirección financiera) · Objeto PC-0412, 18.450,00 €, Suministros Industriales del Norte S.L. · Relación PC-0412 → PROV-018 · Evidencia «Política Corporativa de Compras y Gasto v3.2», pág. 4, § 2.1 · Regla R-03 (> 15.000 € ⇒ firma DF) · Acción: borrador de emisión del pedido · Revisión: Dirección financiera aprueba → registro. Reutiliza el scroll del Bucle.
- **Consecuencia de copiar el producto:** en el producto PC-0412 ya tiene 3 ofertas; el hueco es la firma de DF, no «solo 2 ofertas». Cambia el relato de la demo de la landing (Huecos y Revisar) y la cita del hero.
- **Hoy · Siguiente · Visión:** tres columnas a partir de fundacional §6. Hoy: cita en un clic (respuestas predefinidas), huecos como interfaz, persona en el bucle con exportación. Siguiente: motor de reglas evaluado por código, validar citas libres, persistencia de Revisar, instalación local. Visión · hipótesis: modelos por proceso, federación entre procesos, portal de proveedores.
- **Formulario:** campo «Perfil» (cliente/aliado/inversor) en radios, como «Proceso»; «Proceso» obligatorio solo para cliente. `track('form_enviado', { perfil, proceso, section })`. Bloqueado por `perfil` en `/api/solicitud` (product-steward).
- **Inversores:** botón «Material para inversores» abre el formulario con perfil preseleccionado. No se publica material.
