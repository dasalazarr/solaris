---
fecha: 2026-11-10
rol: cofundador
tema: plantilla Compliance en el producto
---

# Plantilla Compliance (alta de clientes, PBC)

## Tarea
Diego aceptó ADR-0020 y pidió construir la plantilla.

## Qué se hizo
- `product/lib/templates/pbc.json` y `product/lib/seeds/pbc.ts`: asesoría ficticia, 6 clientes, 3 titulares reales, 5 reglas, 4 revisiones y 3 preguntas de muestra.
- Las reglas citan el manual interno ficticio, no la ley.
- Registro en `solaris-data.ts`, etiqueta en `SolarisWorkspace.tsx`, `metadata.json` y `scripts/nuevo-codigo.mjs`.
- Entrada de oro nueva en `tests/fixtures/golden-packs.json`; las cuatro anteriores, idénticas.
- En la raíz: ADR-0020 aceptada, ROADMAP, PRD §4 y caso de estudio alineado con la plantilla.

## Qué falló
- `nuevo-codigo.mjs` rechazaba `pbc`: tenía su propia lista de procesos.
- Un test fijaba en 4 el número de procesos.
- La muestra contaba 8 documentos y la plantilla 7: la copia escaneada de CL-0355 era un fichero aparte. Unificado.
- El primer volcado del fixture cambió la sangría de todo el fichero. Rehecho con el formato original.

## Evidencia
- 266 tests, lint y build.
- Navegador local con un código desechable, ya borrado: matriz con los cinco estados; el Representante no puede aprobar R-PBC-03 y el Socio director sí; tras aprobar, la celda pasa a «Aprobada» y los huecos de 5 a 4; 375 px sin scroll horizontal; consola sin errores.

## Sin comprobar
- Lector de pantalla. Pregunta libre con el modelo real sobre este proceso.
- En móvil, con cinco columnas el texto de las celdas se aprieta. No se tocó.
- Ninguna regla la ha revisado alguien cualificado.
