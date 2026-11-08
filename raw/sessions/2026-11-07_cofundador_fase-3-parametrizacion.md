---
fecha: 2026-11-07
rol: cofundador
tema: Fase 3, parametrización
---

# Fase 3: parametrización

## Tarea
Que el contrato de un proceso se edite y se publique sin programar, sin cambiar los resultados de hoy.

## Qué se hizo
- `lib/process-definition.ts`, `lib/templates/*.json`, `lib/process-service.ts`, `app/api/process`, `ContractEditor`, `ProcessMatrix`.
- Regresión de oro: fixture de los cuatro procesos capturado antes de migrar.

## Qué falló
La primera versión recibió NO APTO de security. Reproducido por su parte: cambiar la acción aprobada no reabría la revisión; una regla enlazada cerraba su hueco con la firma de otra; una regla llamada `LECTURA` cambiaba quién valida; publicar A, B y A revivía una aprobación; un rol sin personas dejaba el proceso bloqueado. Todo corregido y convertido en tests. El repaso encontró dos fallos abiertos por los arreglos: una revisión reabierta no se podía reaprobar con el mismo texto y una marca falsa de autoaprobación. Corregidos.

También: `video/` dejó de compilar el render por el alias `@/` en las plantillas. Corregido con rutas relativas.

## Decisiones
[[ADR-0017]]. Separación de funciones: solo se marca, decide Diego.

## Evidencia
- 234 tests, lint, build, `npm run gate` y hoja de contacto de `video/`.
- Navegador local: edición, vista previa, publicación, reapertura y registro en escritorio y a 375 px con la primera versión; modo guardado y demostración repetidos en escritorio con la versión final.

## Sin comprobar
- Crear un proceso desde cero: no existe. [[H03]] sin medir.
- Imagen Docker, modelo real con contrato editado y lector de pantalla.
