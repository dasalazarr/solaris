# Sesión 2026-11-04 · cofundador · alineamiento a partir de un diagnóstico externo

## Tarea
Diego aporta un diagnóstico externo (`raw/research/2026-11-04_diagnostico-ux-externo.md`) y pide alinear landing y producto. Decide: no prometer VPC, agenda con enlace tras enviar, alcance completo.

## Qué se hizo
- Contraste del diagnóstico con el código. Plan aprobado por Diego.
- Producto, apilados: illariumcore#9 (rol y Revisar) → #10 (Preguntar) → #11 (Huecos y Explorar) → #12 (datos).
- Landing, apilados: solaris_fronted#9 (copy) → #10 (hero) → #11 (demo) → #12 (formulario).
- Raíz: [[ADR-0010]], `docs/guion-demo-90s.md`, PRD, `fundacional.md` §6 y este registro.

## Qué se descubrió
- **Cualquiera podía aprobar:** el rol era texto libre y nadie lo comprobaba. El diagnóstico lo describía como un desplegable que demostraba el modelo.
- Confirmar el bloqueo de PC-0419 lo marcaba como «Validado / Aprobado» y validaba sus atributos con el certificado aún caducado.
- Aprobar PC-0412 no cerraba su hueco.
- Falsos o inexistentes en el diagnóstico: registro inmutable, huella criptográfica, evaluación en segundo plano, Pydantic en ejecución, «Cumple R-01» en PC-0412 (el motor da `no_aplica`), § 1.4 de la política, expediente de PROV-018 y Huecos 1:1 con Revisar.
- Premisas erróneas con arreglo más barato: el espacio del hero era 80 px, no 140; «Buscando» ya duraba 0,7 s; Revisar ya estaba en la demo; el enlace de agenda ya existía; los KPI ya variaban y el problema era la escala.
- Aceptado: quitar jerga, plegar preguntas, destacar el rol, cerrar el hero en la regla, contexto y fricciones en el formulario.

## Qué falló
- Un comando encadenado con `;` publicó el commit de P2 aunque un test nuevo fallaba, y el cuerpo del PR ya decía que pasaban. El fallo estaba en el test (id `EXP-M219`, no `AV-9041`). Se corrigió en el siguiente commit. Aprendizaje: encadenar gate y commit con `&&`.
- La barra del hero desbordaba 51 px en móvil. Se detectó midiendo y se arregló antes del PR.

## Decisión a revisar
Añadir el certificado de PROV-018 sube Compras a 5 documentos. Es más cierto que retirar la afirmación, pero landing y producto deben publicarse a la vez.

## Evidencia
- Producto: `npm test` 101, lint, `tsc`, `next build`. Navegador local con un espacio de prueba efímero: rol bloqueado sin entrada en el registro, PC-0419 sigue bloqueado, Huecos 3 → 2, recorrido de Huecos y Revisar en los 4 packs, 375 px sin scroll horizontal.
- Landing: lint con solo los 3 avisos previos, build, `out/` sin errores de consola. Hero a 1366×768 asoma 154 px y a 375 px ocupa 480 de 480 px. Preselección desde los 4 packs.

## Sin probar
- Envío real del formulario: se interceptó la petición para no generar correo.
- Lighthouse en URL publicada; preview conjunta.
- Navegación con flechas en la pestaña Explorar de la demo.
- Vista Preguntar en navegador con Jurídico, IFS y EUDR (código genérico; sí se recorrieron Huecos y Revisar).

## Revisión de security (añadido el mismo día)
- No veta. Sin secretos, XSS ni datos personales hacia la analítica.
- H1 (media): un rol sin firma podía pedir cambios sobre una aprobación firmada. security lo vio leyendo código; se reprodujo con 3 tests en rojo, se corrigió en illariumcore#9 y se comprobó en navegador. Es un fallo que introduje al dejar «Pedir cambios» abierto sin mirar el estado.
- Corregidos después, a petición de Diego: H2, H3 y H5. security no ha revisado estos arreglos. Sin corregir: H6 (en `plan/STATUS.md`). Condición H4 antes de activar la agenda. H7: nombres de empresa sin comprobar en el Registro Mercantil.
- security no comprobó en navegador, ni build, ni variables de Vercel, ni HTML publicado.
