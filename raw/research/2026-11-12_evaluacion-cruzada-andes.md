# Evaluación cruzada Solaris ↔ Andes (2026-11-12)

Origen: sesión de trabajo en el repositorio de Andes. El documento completo queda fuera de este repositorio.

Andes es otro proyecto de Diego: un agente conversacional por WhatsApp, en producción, con memoria por persona, cola de notificaciones y cobro. No comparte código con Solaris.

## Lo que afecta a Solaris

1. **Sin código compartido.** Despliegues opuestos (instancia local por cliente frente a nube multiusuario) y ningún piloto que lo pida (principio 5).
2. **Finanzas/CFO como plantilla.** `product/lib/templates/compras.json` ya tiene a «Dirección financiera» como responsable. Diego preguntó si un «agente CFO» debía ser un producto aparte; la lectura es que es una plantilla más. Sin demanda comprobada.
3. **Los vencimientos no avisan.** La condición `days_until` de `product/lib/rules-engine.ts` se evalúa al abrir la pantalla. No se encontró nada que la ejecute de forma programada ni un canal de aviso. Andes resuelve lo equivalente con una cola con reintento y clave de idempotencia.
4. **Cambio de modelo sin red.** Andes tuvo tres incidentes en agosto de 2026 por cambios de comportamiento del proveedor de modelo, ninguno detectado por tests. Solaris depende de `GEMINI_MODEL`.
5. **WhatsApp como canal de aviso** choca con «0 documentos salen de tu organización»: el mensaje pasa por Meta. Solo podría viajar el aviso y una referencia.

## Sin comprobar

- No se ejecutaron los tests de Solaris.
- La ausencia de un programador de tareas se dedujo de `product/lib/` y `product/app/api/`; no se revisó `product/scripts/`.
