---
fecha: 2026-11-07
rol: security
tema: revisión de la Fase 1 antes de dar códigos a prospectos
---

# Revisión de la Fase 1

## Dictamen
APTO con condiciones. Se mantiene el veto a dar códigos hasta cumplirlas. Sin fallos de acceso ni de autenticación.

## Condiciones
1. Clave de Gemini en un proyecto de pago, con tope mensual y alerta. Una clave gratuita no vale para clientes del EEE, según los términos de la API leídos en un resumen automático.
2. Google nombrado en Privacidad y aviso junto al campo. Hecho en PR; falta que alguien cualificado lo valide.
3. Proveedores de muestra sustituidos: un nombre coincidía con una sociedad registrada. Hecho en PR. El historial de git conserva los nombres antiguos; no se reescribe y Diego debe aceptar ese riesgo.
4. Fusionar illariumcore#20, que sustituye a #19.
5. Un código nuevo por prospecto, a 30 días o menos, sin códigos antiguos activos.

Salida rápida: quitar `GEMINI_API_KEY` y volver a desplegar. Las condiciones 1 y 2 dejan de bloquear; las demás siguen.

## Corregido en esta sesión
- illariumcore#20: `maxOutputTokens`, `systemInstruction`, respuesta vacía, fragmento verificado en las citas, aviso de Google, proveedores, foco en diálogos, enlace de salto, contadores y PDF.
- solaris_fronted#17: Privacidad, Bento en futuro y proveedores.

## Aplazado, sin bloquear
Contador global de consultas, dictamen del motor encima del texto del modelo, cabeceras de seguridad, Umami sin SRI, etiquetas de entorno fijas, límites de `rate-limit`, revocación solo con despliegue, `postcss` en `npm audit`, `picsum.photos` en la configuración y aviso de muestra al imprimir otras superficies.

## Qué falló
- axe no se ejecutó: el sistema de permisos bloqueó cargar código externo en la página. Se comprobó el contraste con un script propio.
- Una prueba de código con mayúsculas no entró en un primer intento de esta jornada (ver la traza anterior).

## Evidencia
- Lectura de código, `curl` sin sesión, `npm audit` y `dig`, por el agente de security. Sin descifrar variables ni entrar en producción con código.
- 120 tests, lint y build. Navegador local a 1024 y 375 px con respuestas del modelo simuladas.
- PDF del registro con Chrome sin interfaz: una página, con la etiqueta de muestra.

## Sin comprobar
Lector de pantalla real. Tope de 4.000 tokens con el modelo real. Inyección de prompt contra el modelo. Si la clave actual es de pago y si tiene tope.
