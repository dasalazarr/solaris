# 2026-11-07 · cofundador · Fase 1 de experiencia

**Pedido:** Diego puso la clave de Gemini y pidió avanzar. Quiere seguir construyendo usabilidad e infraestructura sin esperar a las entrevistas.

**Hecho:** illariumcore#17, modelo configurable y estado HTTP en el log. illariumcore#18, marco con menú lateral, recorrido de 3 pasos, Preguntar en dos zonas, matriz con `matrixFrom`, barra de confianza, Revisar por pasos, Registro con `auditRows` y Contrato. `SolarisWorkspace.tsx` baja de 2274 a 561 líneas.

**Qué falló y se corrigió:**
- Con la clave puesta, producción sigue dando «No puedo responder ahora». El log registra `ApiError` sin estado. Causa probable, sin confirmar: Google limita los modelos 2.5 a quien ya los usaba.
- El recorrido tapaba la decisión en Revisar: ahora va arriba en ese paso.
- El panel de decisión fijo tapaba la cola en móvil y cortaba el botón de aprobar: solo es fijo en escritorio.
- La matriz desbordaba a 375 px: tabla de ancho fijo.

**Decisiones propias, baratas de cambiar:** modelo por defecto `gemini-3.5-flash-lite` (la elección final es de Diego); referencias de IFS sin sección concreta hasta contrastarlas; Umami apagado sin variable.

**Evidencia:** navegador local a 1440 y 375 px con un espacio de prueba desechable, borrado después; consola sin errores; 118 tests.

**Pendiente:** comprobar Gemini tras fusionar #17; revisión de security; impresión a PDF y lector de pantalla; `ProductWindow` y `ventana.tsx` tras fusionar #18.
