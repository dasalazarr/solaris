---
fecha: 2026-11-19
rol: cofundador
tema: Implementación de las correcciones C1, C5 y C8 de la plantilla cfo
---

# Correcciones de la plantilla cfo

## Tarea
Diego eligió «las tres recomendadas» de la auditoría (`raw/research/2026-11-19_cfo-pyme-procesos-ecuador.md`, sección D).

## Hecho
- Rama `feat/cfo-correcciones-auditoria` de illariumcore, cortada desde `feat/motor-linear-cfo` (sin PR).
- R-MAR-03 mide sobre `ingresos_operativos`; R-BAN-05 (comprobante de más de 500 $ pagado por el sistema financiero, atributo `forma_pago`); `action` con borrador de plan de caja en R-LIQ-01.
- Golden de `cfo` regenerado: solo cambia esa entrada. 332 tests, eslint y `next build` pasan.

## Correcciones a la auditoría
- C8 era menos grave de lo dicho: R-LIQ-01 ya tenía una revisión escrita a mano (REV-CFO-01, plan de caja). La acción nueva solo actúa en cierres nuevos que fallen. La auditoría original no se edita (RAW es inmutable); la corrección vive en O08.

## Sin comprobar
- No se revisó en el navegador.
- Los valores de `forma_pago` (`sistema_financiero`, `efectivo`) son nuestros, no los códigos del SRI.
- La muestra no tiene préstamos ni pagos en efectivo: C1 y C5 se prueban con casos de prueba, no con un hueco nuevo en la demo (octubre conserva sus tres huecos).

## Tropiezo
- `timeout` no existe en macOS y un `cat > fichero` sin entrada colgó un comando; se paró y se borró el fichero.
