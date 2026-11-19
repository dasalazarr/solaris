# Diagnóstico externo de UX, copy y guion de demo (2026-11-04)

Evidencia en bruto. Texto aportado por Diego, sin editar. **Contiene afirmaciones que el código desmiente:** el contraste y lo que se aceptó o se rechazó están en `raw/sessions/2026-11-04_cofundador_alineamiento-diagnostico.md` y [[ADR-0010]]. No usar este texto como fuente de copy.

Las referencias `image_*.png` son capturas de la landing, el formulario y las vistas Preguntar y Revisar, no archivadas aquí.

---

## Bloque 1 · Diagnóstico y plan por rol

1. Diagnóstico de UX, Atención y Propuesta de Valor (Landing vs. Producto Real)
Al contrastar la landing (`image_324c02.png`), el drawer de contacto (`image_324bbe.png`) y la interfaz real del producto (`image_284bb4.png` e `image_284adf.png`), el diagnóstico es claro: el producto real ya es un motor de gobernanza ontológica completo, pero la landing lo sigue presentando como un buscador de PDFs con esteroides.
A. Análisis de la Animación del Hero: ¿Debería ser más larga?
No debe ser más larga en duración, pero sí debe cerrar el ciclo ontológico completo en el mismo tiempo (6–8 segundos).

* Por qué la animación del Hero se siente más fácil de entender (`image_324c02.png`): Funciona mejor cognitivamente porque tiene foco único y revelación progresiva. A diferencia de la app real (que muestra 3 columnas densas de golpe), el Hero guía el ojo secuencialmente: 1. Pregunta (`¿Por qué está retenido PC-0412?`) $\rightarrow$ 2. Búsqueda (`Buscando en 4 documentos...`) $\rightarrow$ 3. Respuesta con cita + Panel de evidencia lateral.
* Por qué se queda corta en propuesta de valor: Porque se detiene en la Evidencia (Capa Semántica) y omite la Regla y la Acción/Aprobación (Capa Cinética). Si el usuario solo ve «Pregunta $\rightarrow$ Respuesta con cita», su cerebro clasifica a Solaris como un Chat-with-PDF.
* Cómo solucionarlo sin alargar el vídeo: Acelerar el paso inerte de «Buscando en 4 documentos...» (que no aporta valor diferencial) a 0.6 segundos e inyectar al final de la respuesta la tarjeta compacta de acción: `[Regla R-03 activada: > 15.000 €] [Enviar a firma de Dirección Financiera ↗]`. Así, en 7 segundos y con la misma limpieza visual, el usuario ve: Verdad (Cita) + Ley (Regla determinista) + Gobierno (Aprobación humana).

B. Análisis de Atención y Carga Cognitiva en la Landing (`image_324c02.png`)

* Acierto de contraste y ritmo: La alternancia entre bloques oscuros (`#0c0d0e`, que transmiten autoridad, contrato y precisión) y bloques crema cálidos (`#f8f6f0`, que evocan papel editorial y lectura limpia) combinada con la tipografía serif en cursiva («con contrato», «más chatbots», «funciona») y el acento ámbar (`#ebb343`) es impecable.
* Fuga de atención en el Hero: Entre el subtítulo y la ventana de la demo hay un espacio negro vacío excesivo (~140px) que empuja la interfaz hacia abajo en portátiles de 13"-14". Reducir ese margen a 48px hará que el producto sea visible inmediatamente sin hacer scroll.
* Repetición de componente (Hero vs. Sección «Demostración interactiva»): La ventana de la sección «Véalo en un proceso que todos tienen» es visualmente idéntica a la del Hero (misma pregunta `PC-0412`, mismo menú lateral `Preguntar | Huecos | Revisar | Documentos`). Cuando el usuario baja y ve exactamente la misma caja, su atención cae porque cree que ya lo vio.
* El bloque «0 documentos salen de su equipo»: Tiene un impacto visual brutal, pero un copy limitante. Si un director de operaciones o CTO de una empresa mediana lee «de su equipo», piensa en un ejecutable instalado en un PC local. Debe reformularse hacia un lenguaje universal de soberanía: «0 datos salen de su control / perímetro».

2. Mirada Crítica a la UI/UX del Producto (`image_284bb4.png` e `image_284adf.png`)
El diseño de la aplicación real es muy superior a lo que insinúa la landing, pero sufre de sobrecarga de metadatos de ingeniería que compiten por la atención del usuario de negocio.
A. Vista «Preguntar» (`image_284bb4.png`): Competición de 3 columnas

1. Columna Izquierda (El Contrato y KPIs): Es una joya de producto. Ver el Contrato del Proceso arriba (Responsable, Alcance, Umbrales `R-03`, `R-02`, `R-01`) y los KPIs del proceso e histórico abajo (`91.4% conformes`, `3.2h tiempo medio`) materializa la ontología al instante.
   * Crítica UX: Las barras amarillas de los gráficos de Mayo a Octubre parecen tener todas exactamente la misma altura, lo que les da aspecto de placeholder estático. Además, el pie `Esquema: Pydantic v2 · 2026.4 · sha256:9f4c2b81...` debe ocultarse bajo un tooltip de «Ver certificado técnico del contrato» para no ensuciar la lectura ejecutiva.
2. Columna Central (Interacción y Respuesta):
   * Crítica UX (Fricción de scroll): La mitad superior está ocupada por el selector de idioma (`ES | FR | EN`), las 3 preguntas sugeridas y el input de búsqueda. Eso empuja lo más valioso —el dictamen en caja negra, los chips morados de `Objetos de Ontología consultados` (`PC-0412`, `PROV-018`), las `Reglas deterministas evaluadas` (`Regla R-03`, `Regla R-02`) y el botón ámbar `Abrir en Revisar ↗`— hacia el borde inferior de la pantalla.
   * Solución: Una vez que hay una respuesta activa, colapsar las preguntas sugeridas en un desplegable o píldora compacta para que la respuesta, las reglas evaluadas y el botón de acción suban 180px.
3. Columna Derecha (Visor de Evidencia):
   * Crítica UX: Las pestañas superiores (`EV-COMP-01 (Pág. 4)`, `EV-COMP-02 (Pág. 1)`) usan códigos internos. Un director financiero no sabe qué es `EV-COMP-01`, pero sí entiende `[1] Política de Compras (Pág. 4)` y `[2] Pedido PC-0412 (Pág. 1)`, haciendo match directo con el `[1]` y `[2]` amarillos del texto central.
4. Cabecera superior derecha: El badge `Nivel 1: Nube Demo (Muestra) | Nivel 2 (previsto)` transmite que el producto está a medio hacer. Cámbialo por un indicador de entorno limpio: `Entorno: Demo Interactiva (Datos de muestra)` con un botón secundario `Ver arquitectura VPC / Local`.

B. Vista «Revisar» (`image_284adf.png`): Bandeja HITL y Registro de Auditoría

1. El mayor acierto oculto: El selector arriba a la derecha `Rol firmante activo: [Dirección financiera v]`. Ese selector demuestra en vivo el paradigma «mismo modelo, diferentes roles/fronts», pero pasa visualmente desapercibido porque parece un filtro gris más. Debe tener un borde destacado o un icono de perfil/llave que invite al usuario en la demo a cambiar de rol (ej. probar qué pasa si intenta aprobar siendo Comprador vs. Dirección Financiera).
2. Exceso de códigos internos en títulos: Títulos como `EVIDENCIA EN DOCUMENTO ORIGINAL (R4)` (`image_284bb4.png`) o `Registro Inmutable de Auditoría del Espacio (R8 / R16)` (`image_284adf.png`) exponen la numeración de requisitos internos de tu backlog (`R4`, `R8`, `R16`, `R15`). Elimina esos códigos entre paréntesis de la interfaz de usuario.
3. Jerga cruda en la cabecera de aprobación: En `image_284adf.png`, esquina superior derecha de la tarjeta blanca, aparece `step_id: step_emit_pc_0412` y `args_hash: arg_8831f09a2b1c` en texto plano. Agrupa eso dentro de un badge elegante con icono de escudo: `✓ Sello de idempotencia activo` (que al pasar el ratón muestre el `step_id` y `args_hash`).

3. Rediseño del Drawer «Solicitar demostración» (`image_324bbe.png`)
Tienes toda la razón: el modal lateral actual cumple funcionalmente, pero se siente como un formulario SaaS genérico («más del montón») y desaprovecha el contexto de quien acaba de interactuar con una ontología de procesos.
Cómo transformarlo en una experiencia de conversión diferencial («Configurador de Sesión de Diagnóstico»):

1. Conservar el contexto dinámico: Si el usuario hace clic en «Solicitar demostración» desde el Pack Calidad IFS Food o mientras revisa el pedido `PC-0412` en la demo, el drawer debe abrirse con el chip `Calidad` o `Compras` ya preseleccionado y un mensaje contextual arriba: «Configurando sesión para el proceso de Compras».
2. Sustituir el campo frío «Comentario (Opcional)» por «¿Qué fricción quiere resolver primero?» con chips seleccionables en 1 clic:
   * `[ ] Pedidos o contratos que se aprueban sin cumplir toda la norma`
   * `[ ] Demasiado tiempo cruzando PDFs, anexos y el ERP a mano`
   * `[ ] Auditorías (IFS, EUDR, ISO) con huecos documentales`
   * `[ ] Evaluar despliegue de IA privada sin fugas de datos`(Esto reduce a cero el esfuerzo de escribir en móvil o escritorio y te entrega un lead ultra-cualificado antes de la llamada).
3. Añadir «Qué ocurrirá en los 30 minutos» (Micro-agenda de valor): Justo encima del botón ámbar, reemplaza el vacío por 3 checks muy breves:
   * Min 0–10: Mapeo rápido de las reglas y documentos de su proceso.
   * Min 10–25: Prueba en vivo sobre el motor de Solaris (citas, huecos y flujo de firma).
   * Min 25–30: Definición de arquitectura (Local / VPC) y estimación de piloto.
4. Doble vía de cierre: En lugar de prometer únicamente «Le respondemos en un día laborable» (que enfría el impulso del comprador), permite que el botón principal sea `Continuar y elegir hora (30 min) →` (integrando Cal.com/Calendly embebido en el paso 2 del mismo drawer) o un enlace secundario debajo: «Prefiero que me escriban por correo primero».

4. Copy Universal y Directo para la Landing
El objetivo de este ajuste es que cualquier director general, de operaciones, financiero o de IT entienda el valor en el primer impacto, sin que suene a nicho técnico ni a simple lector de PDFs:

* Pre-título (Eyebrow):
   * Actual: `IA PRIVADA PARA PROCESOS`
   * Propuesto: `GOBERNANZA Y EJECUCIÓN DE PROCESOS CON IA PRIVADA`
* Titular (H1):
   * Actual: Sus procesos, con contrato. (Mantener: es potente, memorable y único).
* Subtítulo del Hero (Universal y completo):
   * Actual: «Solaris responde con la cita exacta de sus documentos, detecta lo que incumple sus reglas y no ejecuta nada sin su aprobación.»
   * Propuesto: «Solaris convierte sus normativas y documentos en reglas vivas: audita cada expediente con la cita exacta, bloquea lo que incumple y exige la firma del responsable antes de ejecutar cualquier paso.»
* Sección El Problema (Subtítulo de cierre):
   * Actual: «Necesitan que sus procesos tengan contrato: reglas escritas, respuestas con fuente y una persona que aprueba.»
   * Propuesto: «Necesitan que sus procesos operen bajo contrato: reglas que el código evalúa siempre igual, evidencia verificable en un clic y decisiones firmadas con trazabilidad total.»
* Sección La Ontología de Procesos (Subtítulo explicativo):
   * Actual: «Siete primitivas: Proceso, Objeto, Relación, Evidencia, Regla, Acción y Revisión. El motor es el mismo en cada sector; cada pack define sus tipos.»
   * Propuesto: «Un lenguaje universal para cualquier operación. Solaris estructura su negocio en siete piezas conectadas —Proceso, Objeto, Relación, Evidencia, Regla, Acción y Revisión— donde la IA lee los documentos, pero el código determinista evalúa las reglas y las personas gobiernan la decisión.»
* Sección «0 documentos salen de su equipo»:
   * Actual: `0 documentos salen de su equipo. En la instalación local. La demostración usa datos de muestra en la nube.`
   * Propuesto: `0 datos fuera de su perímetro.` Despliegue Solaris en su propia infraestructura local o nube privada (VPC). Sus documentos y decisiones nunca entrenan modelos externos.

5. Plan de Acción Operativo (Handoff por Rol)
Puedes copiar y entregar directamente estos dos bloques de tareas a cada responsable:
Bloque A: Plan de Acción para el Dueño de la Landing (`solaris.dasalazarr.com`)

1. Ajuste del Hero y su Animación (Prioridad Alta):
   * Reducir el padding vertical entre los botones del Hero (`Solicitar demostración` / `Ver cómo funciona`) y el borde superior del mockup de la demo de ~140px a 48px para que la interfaz entre en el above the fold.
   * Actualizar el loop de la animación del Hero: mantener la simplicidad actual de 2 paneles, reducir el estado `Buscando en 4 documentos...` a 0.6s y añadir al final del mensaje de respuesta una barra de acción clara: `Regla R-03 activada (> 15.000 €) · Requiere firma de Dirección Financiera [Revisar y firmar →]`.
   * Aplicar el nuevo subtítulo del Hero y el ajuste del bloque `0 datos fuera de su perímetro`.
2. Diferenciación entre el Hero y la Sección «Demostración interactiva» (Prioridad Alta):
   * Mientras el Hero muestra la simplicidad del flujo de consulta, la sección inferior («Véalo en un proceso que todos tienen») debe mostrar la potencia del producto real (`image_284bb4.png` / `image_284adf.png`): incluir una pestaña o vista donde el usuario haga clic en `Revisar (3)` y vea la bandeja de aprobación con el borrador editable y el botón de `Aprobar y confirmar`.
3. Limpieza de jerga en la sección «Cómo funciona» (Prioridad Media):
   * En la tarjeta `6. Registro` de la línea de tiempo oscura, cambiar el texto «Aprobación registrada con step_id, args_hash y la evidencia enlazada» por: «Aprobación sellada con huella única de auditoría, versión del contrato y evidencia enlazada (impide pagos o acciones duplicadas)».
4. Reestructuración de «Hoy · Siguiente · Visión» (Prioridad Media):
   * Eliminar de la columna Siguiente el punto «Registro de aprobaciones que se conserva entre sesiones» (ya que en la captura `image_284adf.png` ya tienes el Registro Inmutable de Auditoría funcionando) y pasarlo a Hoy. En Siguiente, colocar: «Conectores directos con su ERP/CRM y despliegue en su infraestructura privada (VPC o servidor propio)».
5. Evolución del Drawer de «Solicitar demostración» (Prioridad Media):
   * Preseleccionar automáticamente el chip de `Proceso que le interesa` según la sección desde donde el usuario abrió el modal.
   * Reemplazar el textarea abierto `Comentario` por 3–4 chips seleccionables de dolor de negocio + un campo corto opcional, e integrar selección de fecha/hora en un segundo paso del mismo drawer.

Bloque B: Plan de Acción para el Dueño de la Demo / Producto (`app`)

1. Simplificación de densidad visual en la vista «Preguntar» (`image_284bb4.png`) (Prioridad Alta):
   * Hacer que el bloque de Consultas verificadas sobre este contrato (las 3 preguntas sugeridas) se colapse automáticamente o ocupe una sola línea deslizable una vez que hay una ejecución activa, subiendo el dictamen negro y la barra ámbar (`Acción propuesta sujeta a decisión humana -> Abrir en Revisar`) al primer plano sin requerir scroll.
   * Renombrar las pestañas del visor derecho de `EV-COMP-01 (Pág. 4)` a `[1] Política Compras (Pág. 4)` y `[2] Pedido PC-0412 (Pág. 1)` para que el usuario conecte instantáneamente las citas `[1]` y `[2]` del texto con el documento original.
2. Purga de etiquetas internas de ingeniería (Prioridad Alta):
   * Eliminar los códigos de requisito `(R4)`, `(R15)`, `(R8 / R16)` de los encabezados de las tarjetas en `Preguntar` y `Revisar`.
   * Ocultar los hashes crudos (`sha256:9f4c2b81...`, `step_id: step_emit_pc_0412`, `args_hash: arg_8831f09a2b1c`) detrás de un badge limpio con tooltip: `✓ Trazabilidad criptográfica verificada`.
   * Cambiar el badge superior derecho `Nivel 1: Nube Demo (Muestra) | Nivel 2 (previsto)` por `Modo: Demo Interactiva (Datos de muestra)`.
3. Protagonismo al selector de Rol en la vista «Revisar» (`image_284adf.png`) (Prioridad Media):
   * Destacar visualmente el selector `Rol firmante activo: Dirección financiera` en la esquina superior derecha. Añadir en el desplegable un segundo rol de prueba (ej. `Solicitante / Compras (Sin permiso R-03)`) que, al seleccionarlo, deshabilite el botón `Aprobar y confirmar` con un aviso: «El contrato del proceso exige el rol Dirección Financiera para importes > 15.000 €». Esa micro-interacción demuestra el poder de la ontología en 3 segundos mejor que cualquier párrafo explicativo.
4. Realismo en el widget de KPIs (`image_284bb4.png`) (Prioridad Baja):
   * Ajustar las alturas de las barras de los meses `May - Oct` en la tarjeta KPIs del proceso e histórico para que reflejen una variación realista (ej. evolución desde 78% hasta 91.4% y reducción de tiempos de 5.1h a 3.2h), reforzando visualmente el retorno de inversión del proceso gobernado.

## Bloque 2 · Vistas Huecos y Explorar

Para que las pestañas `Explorar (4)` y `Huecos (3)` cierren el círculo con `Preguntar` y `Revisar (3)`, ambas vistas deben mantener la misma limpieza ejecutiva (cero códigos de backlog como `R4`/`R8` y cero hashes crudos en primer plano) y demostrar la separación entre la Capa Semántica (el mapa de objetos, relaciones y documentos) y la Capa Cinética (el motor determinista que detecta brechas antes de una auditoría).
1. Vista `Huecos (3)` — El Radar Preventivo de Incumplimientos
Propósito ontológico y de UX: En la landing prometes: «Cruza sus reglas con cada expediente y marca el hueco antes de que llegue a auditoría». Cuando el usuario hace clic en `Huecos (3)`, no debe ver una tabla técnica de logs, sino un diagnóstico accionable de qué falta, qué regla lo exige y cómo resolverlo en un clic.
Además, para que exista coherencia total (1:1) con las 3 tarjetas que ya tienes en `Revisar (3)` (`PC-0412`, `PC-0419` y `FAC-2026-889`), los 3 huecos deben corresponder exactamente a esos mismos objetos.
A. Cabecera y Filtros de la Vista `Huecos (3)`

* Título de la sección: `Brechas y Huecos Detectados contra el Contrato`
* Subtítulo: `Solaris cruza de forma continua cada expediente activo con la Política de Compras v3.2. Nada avanza al ERP mientras exista un hueco abierto.`
* Píldoras de resumen (arriba a la izquierda):
   * `[Todos (3)]` · `[Falta firma (1)]` · `[Documento caducado (1)]` · `[Dato dudoso en documento (1)]`
* Indicador de estado (arriba a la derecha):
   * Badge limpio: `✓ Evaluación determinista activa · Política v3.2` (Tooltip al pasar el ratón: `Hash de política: sha256:9f4c2b8...`).

B. Micro-copy de las 3 Tarjetas de Huecos (Columna Principal)
Tarjeta 1 — Hueco de Aprobación (Conectado a Regla R-03)

* Badge de severidad: `[FALTA FIRMA EXPRESA · REGLA R-03]` (Color ámbar)
* Objeto afectado: `Pedido PC-0412 · Suministros Industriales del Norte S.L. (18.450,00 €)`
* Qué falta (El Hueco): `El pedido adjunta las 3 ofertas comparativas exigidas, pero supera el umbral de 15.000,00 € y carece de la firma registrada de Dirección Financiera.`
* Evidencia normativa (Clicable al visor derecho): `Cita [1]: Política de Compras v3.2 · Pág. 4 (§ 2.1 Umbrales de autorización)`
* CTA directo: `[Resolver en Revisar →]` (Al hacer clic, lleva directo a la tarjeta de aprobación de `PC-0412` en la pestaña Revisar).

Tarjeta 2 — Hueco Documental Crítico (Conectado a Regla R-01)

* Badge de severidad: `[BLOQUEO PREVENTIVO · REGLA R-01]` (Color rojo suave)
* Objeto afectado: `Pedido PC-0419 · Logística Delta S.A. (PROV-024)`
* Qué falta (El Hueco): `El certificado de estar al corriente con la AEAT del proveedor venció hace 14 días. El contrato del proceso prohíbe comprometer gasto con certificados caducados.`
* Evidencia normativa (Clicable al visor derecho): `Cita [3]: Política de Compras v3.2 · Pág. 2 (§ 1.4 Homologación y vigencia legal)`
* CTA directo: `[Ver bloqueo y reclamar al proveedor →]`

Tarjeta 3 — Hueco de Verificación de Evidencia (Conectado a Ingesta/Confianza)

* Badge de severidad: `[DATO SIN EVIDENCIA CLARA · CONFIANZA 74%]` (Color violeta/azul)
* Objeto afectado: `Factura FAC-2026-889 · Recargo de transporte (680,00 €)`
* Qué falta (El Hueco): `La factura incluye un recargo de transporte por 680,00 € que no figura en el pedido original ni alcanza el umbral de certeza de lectura (80%). Solaris nunca asume un dato dudoso.`
* Evidencia normativa (Clicable al visor derecho): `Cita [4]: Factura FAC-2026-889 · Pág. 1 (Línea 4 de desglose)`
* CTA directo: `[Inspeccionar documento y decidir →]`

2. Vista `Explorar (4)` — El Mapa de la Ontología y sus Documentos
Propósito ontológico y de UX: En la versión de la landing, esta pestaña se llamaba simplemente `Documentos` (`Pack Compras · 4 docs`), y en la aplicación evolucionó a `Explorar (4)`. Ese cambio de nombre es un gran acierto: en un sistema ontológico no solo ves «4 archivos PDF sueltos», sino cómo esos 4 documentos se convierten en Objetos, Relaciones y Reglas estructuradas (la Capa Semántica de Pydantic v2 en acción).
A. Estructura de 2 Paneles (Lista de Fuentes y Objetos a la izquierda + Visor Ontológico a la derecha)

* Título de la sección: `Explorador del Proceso: Documentos, Objetos y Reglas`
* Subtítulo: `Las 4 fuentes verificadas que alimentan este expediente y las entidades extraídas bajo el esquema del contrato.`
* Conmutador de vista rápida (Arriba):
   * `Vista por Documentos (4)` | `Vista por Objetos de Ontología (5)`

B. Micro-copy de los 4 Documentos (Panel Izquierdo)
En lugar de mostrar nombres de archivo informáticos (`Politica_Compras_v3_2_2026.pdf` o `EV-COMP-01`), preséntalos con jerarquía de negocio clara:

1. `[1] Política Corporativa de Compras y Gasto v3.2`
   * Rol en la ontología: `NORMATIVA MAESTRA`
   * Resumen extraído: `Define 3 reglas activas (R-01, R-02, R-03) y los umbrales de firma de Dirección Financiera.`
   * Estado: `✓ Vigente · Verificado`
2. `[2] Solicitud de Pedido PC-0412 (Válvulas DN80 INOX)`
   * Rol en la ontología: `OBJETO DE PROCESO · 18.450,00 €`
   * Resumen extraído: `12 uds. válvula neumática INOX 316L. Vinculado a 3 ofertas comparativas.`
   * Estado: `⚠ Retenido en Regla R-03 (Falta firma)`
3. `[3] Expediente de Homologación — Suministros Industriales del Norte (PROV-018)`
   * Rol en la ontología: `RELACIÓN / PROVEEDOR`
   * Resumen extraído: `Certificado AEAT en vigor y 3 ofertas técnicas adjuntas verificadas.`
   * Estado: `✓ Conforme (Cumple R-01 y R-02)`
4. `[4] Expediente Logística Delta S.A. (PC-0419) y Factura FAC-2026-889`
   * Rol en la ontología: `EXPEDIENTES CON INCIDENCIA`
   * Resumen extraído: `Contiene certificado AEAT vencido (PC-0419) y cargo de transporte no pactado (680,00 €).`
   * Estado: `✕ Bloqueado por contrato (2 huecos)`

C. Panel Derecho en `Explorar (4)` (La Ficha Ontológica del Documento Seleccionado)
Cuando el usuario selecciona, por ejemplo, el documento `[2] Solicitud de Pedido PC-0412`, encima del visor del PDF aparece una Cinta de Extracción Ontológica muy visual y limpia (sin mostrar código JSON crudo):

* Objeto identificado: `Pedido PC-0412`
* Relación vinculada: `Emitido a → Suministros Industriales del Norte S.L. (PROV-018)`
* Atributos validados por esquema: `Importe neto: 18.450,00 €` · `Ofertas adjuntas: 3 / 3` · `Partida: Válvulas DN80 INOX`
* Cruce con el contrato: `Cumple R-01 (Homologación) ✓` · `Cumple R-02 (3 Ofertas) ✓` · `Exige R-03 (Firma > 15.000 €) ⏳`

3. Resumen del Flujo de Navegación para el Desarrollador de la Demo
Con estos textos, las 4 pestañas superiores de la aplicación (`Preguntar` | `Explorar (4)` | `Huecos (3)` | `Revisar (3)`) cuentan una historia sin fisuras para cualquier cliente que entre a probarla:

1. `Preguntar`: El usuario consulta en lenguaje natural y comprueba que Solaris responde con la cita literal y señala qué regla bloquea el pedido.
2. `Explorar (4)`: El usuario ve que detrás no hay un chatbot adivinando texto, sino 4 documentos transformados en Objetos, Relaciones y Reglas verificadas.
3. `Huecos (3)`: El usuario descubre que no hace falta siquiera hacer preguntas: Solaris ya auditó todos los expedientes en segundo plano y aisló las 3 brechas exactas.
4. `Revisar (3)`: El usuario asume el rol de Dirección Financiera, edita o valida el borrador y firma la acción dejando una huella de auditoría inmutable.

## Bloque 3 · Guion de 90 segundos

Aquí tienes el guion de recorrido comercial de 90 segundos estructurado exactamente sobre las cuatro pestañas principales de la demo (`Preguntar`, `Explorar`, `Huecos` y `Revisar`). Este guion conecta la Capa Semántica (datos y contratos) con la Capa Cinética (reglas, brechas y aprobación humana) y está diseñado para guiar al cliente con claridad en una reunión de 30 minutos:
Guion de Demostración de Solaris (90 Segundos)
1. Pestaña `Preguntar` (Segundos 0 – 30)

* Acción en pantalla: El demostrador entra a la vista principal y teclea o selecciona la pregunta clave: «¿Por qué está retenido el pedido PC-0412 y qué exige el contrato del proceso para emitirlo?»
* Discurso comercial:
«Imagine que un auditor o un director de operaciones necesita saber por qué un pedido crítico de 18.450 € está detenido. En lugar de buscar entre PDFs y correos, le preguntamos directamente a Solaris. Como ve, el sistema no adivina: responde de forma instantánea y nos muestra la cita exacta de la Política de Compras v3.2. Lo más importante: al fondo de la respuesta, el sistema detecta que se activa la Regla R-03 (importes mayores a 15.000 €) y nos indica que la acción está congelada a la espera de una persona autorizada.»

2. Pestaña `Explorar (4)` (Segundos 30 – 50)

* Acción en pantalla: Se hace clic en la pestaña `Explorar (4)` para mostrar el mapa de documentos, objetos y reglas del contrato.
* Discurso comercial:
«Detrás de esta respuesta no hay un chatbot suelto, sino una ontología operativa estructurada en Pydantic v2. En esta pestaña Explorar, Solaris nos muestra las cuatro fuentes maestras de este expediente —la política corporativa, el pedido, la homologación del proveedor y las facturas— convertidas en objetos, relaciones y reglas vivas. El sistema lee y cruza los documentos de su organización de forma 100% determinista.»

3. Pestaña `Huecos (3)` (Segundos 50 – 70)

* Acción en pantalla: Se hace clic en la pestaña `Huecos (3)` para mostrar el panel preventivo con los 3 expedientes con incidencias (`PC-0412`, `PC-0419` y `FAC-2026-889`).
* Discurso comercial:
«Pero lo verdaderamente potente es que su equipo no tiene que preguntar para encontrar problemas. La pestaña Huecos actúa como un radar preventivo continuo: Solaris cruza todas las reglas del contrato contra todos los expedientes activos en segundo plano y aísla exactamente dónde falta una firma, qué certificado del proveedor ha caducado o qué dato no encaja, antes de que llegue la auditoría externa o el error escale al ERP.»

4. Pestaña `Revisar (3)` (Segundos 70 – 90)

* Acción en pantalla: Se hace clic en `Revisar (3)`, se muestra el selector de rol (`Rol firmante activo: Dirección financiera`), se revisa el borrador y se pulsa `Aprobar y confirmar`.
* Discurso comercial:
«Por último, llegamos al núcleo de gobierno: la bandeja Revisar. Aquí es donde el humano toma el control. Supongamos que asumimos el rol de Dirección Financiera. Solaris ya preparó el borrador de emisión y nos muestra la evidencia. El sistema nunca ejecuta nada por su cuenta: el responsable revisa los parámetros, valida la excepción y pulsa aprobar. En ese instante, la acción queda sellada en el Registro Inmutable de Auditoría con una huella criptográfica única, garantizando trazabilidad total y cero duplicidades para su organización.»
