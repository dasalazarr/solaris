# Illarium Industrial OS: investigación de mercado, arquitectura y PRD del MVP para pymes industriales de Navarra y País Vasco

La tesis tiene mercado en Navarra, pero no como "Sistema Operativo de IA" horizontal. La versión que Illarium puede vender es un **copiloto de conocimiento y calidad para planta**, desplegable en nube UE o en local, que empiece por proveedores de automoción (Tier 2/3 de Volkswagen Navarra) y por la agroalimentación de transformación. Debe venderse como servicio de implantación más suscripción y financiarse en parte con la línea foral de fomento de la empresa digital (hasta 30.000 €). Si compite con Microsoft Copilot en productividad de oficina, pierde. Si resuelve la documentación técnica, las no conformidades y el acceso seguro a datos de ERP/MES/OT, gana.

## TL;DR

- **Mercado [V/I]:** la industria pesa entre el 25,8% y el 31% del PIB/VAB navarro, según la fuente y la base de cálculo. Los tres sectores prioritarios son **automoción** (unas 120 empresas, 6.500 M€, más de 13.000 empleos, 6% del PIB), **agroalimentación** (7,5% del VAB, 28.700 empleos) y **renovables** (más de 110 empresas, 10% del empleo industrial, 5% del PIB). La adopción de IA en empresas navarras de 10 o más empleados es del 20,5%, frente al 21,1% de España y el 17,5% de la industria española. El hueco existe, pero la industria navarra está en contracción: la producción industrial cayó un 7,7% en el primer semestre de 2026, frente a un crecimiento del 3,8% en el conjunto del Estado (Noticias de Navarra, 27/08/2026), y el 10,5% de los afiliados industriales estuvo en ERTE en 2025. Eso obliga a vender ahorro y cumplimiento, no innovación.
- **Producto [I]:** el MVP debe limitarse a tres épicas: (1) Knowledge Hub industrial con RAG citado y permisos heredados; (2) agente de Calidad/No Conformidades (8D, reclamaciones, auditorías IATF/IFS) con *human-in-the-loop*; (3) capa de conectores y gobierno (ERP/MES en solo lectura, pasarela *edge* OPC UA/MQTT, auditoría, RBAC y transparencia del art. 50 del AI Act). La pila recomendada es LangGraph + MCP, PostgreSQL/pgvector, Keycloak, Langfuse, vLLM con modelos *open-weight* y opción de nube UE (AWS Aragón, Azure Madrid).
- **Negocio [H]:** pricing híbrido. Consiste en una implantación de 6.000–18.000 € subvencionable y tres niveles de suscripción: "Planta" (≈790 €/mes), "Industrial" (≈1.690 €/mes) y "Enterprise/On-prem" (desde ≈36.000 €/año). La métrica de valor son los flujos y agentes activos, no los asientos. Freemium solo como *sandbox* limitado. Los riesgos principales son cuatro: la "trampa de la consultoría", la competencia subvencionada de centros tecnológicos (NAITEC ya ofrece asistentes de IA generativa sobre conocimiento propio), el empaquetado de Copilot y la contracción industrial.

**Leyenda epistémica:** **[V]** dato verificado con fuente nombrada · **[I]** inferencia propia a partir de datos · **[H]** hipótesis a validar con clientes.

---

## 1. Investigación de mercado y ecosistema navarro

### 1.1 Contexto macro: una economía muy industrial en fase de ajuste

- **Peso industrial [V, con conflicto de fuentes].** Noticias de Navarra (junio 2025) sitúa el peso industrial en el 25,8% del PIB, "el mayor entre todas las comunidades autónomas". Institución Futuro (2026) lo sitúa "en torno al 26,7%", con mínimo decenal en 2024. El consejero Mikel Irujo habló en 2025 de "en torno al 30%". El Plan de Industria 2021-2025 del Gobierno de Navarra recoge un VAB industrial del 31,0% en 2021 (Nastat), con objetivo del 32% en 2025. **Interpretación [I]:** la discrepancia se debe a la base (PIB o VAB, con o sin energía, año). En cualquier caso, Navarra está entre las regiones más industriales de España y el peso industrial está bajando, no subiendo.
- **Empleo industrial [V].** Hubo 74.595 afiliados a la Seguridad Social en el sector industrial en 2025 (Institución Futuro, abril 2026). El empleo manufacturero alcanzó una media de 71.650 cotizantes en mayo de 2025, "casi un 23% del total de ocupados" (Irujo, Parlamento de Navarra). La última cifra oficial localizada de empresas industriales es de 3.337 (Nastat, 2021), con 174 medianas empresas industriales.
- **Ciclo [V].** El 10,5% de los afiliados industriales estuvo en ERTE en 2025, el porcentaje más alto de España frente al 2,2% nacional (Institución Futuro). La producción industrial cayó un 7,7% en el primer semestre de 2026, "frente a un crecimiento del 3,8% en el conjunto del Estado", y las exportaciones un 5,9% en 2025 (Noticias de Navarra, 27/08/2026). El Gobierno foral prepara un Plan de Reactivación Industrial y un Plan Industrial 2026-2030. Hubo cierres y ajustes relevantes: BSH en Esquíroz (660 trabajadores, ERE de cierre), ajustes en KYBSE y ZF-TRW.
- **Implicación para el producto [I].** En un ciclo de contracción, el comprador industrial no compra "transformación con IA"; compra reducción de coste de no calidad, horas de ingeniería y riesgo de auditoría. El discurso comercial tiene que ser de ROI a 6–12 meses.

### 1.2 Los tres sectores prioritarios

| Sector | Datos clave [V] | Tractoras y tejido | Por qué encaja con un OS de IA [I] |
|---|---|---|---|
| **Automoción y movilidad** | Unas 120 empresas, 6.500 M€ de facturación, más de 13.000 empleos (4,5% del empleo), 6% del PIB y cerca del 46% de las exportaciones de mercancías (Invest in Navarra/SODENA vía COPE, 2025) | VW Navarra en Landaben (5.300 empleados actuales según el comité de empresa, recogido por Actualidad Motor, y más de 6.000 en 2027), que pasará de 225.000 vehículos en 2025 a 360.000–370.000 en 2027, con un nuevo turno de fin de semana desde el 8/1/2027. Un estudio de ACAN sobre 14 proveedores estima hasta 1.300 contrataciones adicionales | Presión IATF 16949 y VDA, PPAP, APQP, 8D; rotación y onboarding masivo de operarios (1.050 personas en formación); documentación técnica densa (AMFE, planes de control, instrucciones de trabajo) |
| **Agroalimentación** | 7,5% del VAB y 28.700 empleos (9,2% del empleo regional), de los que 16.000 están en transformación, que genera el 12% de las exportaciones. Navarra produce el 40% de la verdura congelada de España (Navarra Capital). Según un recuento industrial de 2024, 406 empresas, de ellas 12 con más de 250 empleados, 4.500 M€ de volumen de negocio y 5% del PIB (Noticias de Navarra). Las exportaciones agroalimentarias crecen un 5,9% y las cárnicas un 22,1% (Laboral Kutxa, 2025) | Grupo AN, Florette, Grupo Apex, Tutti Food Group, Foodys, Exkal. Nagrifood (clúster, con 102 asociados tras la incorporación de cinco nuevas empresas anunciada en su Asamblea General en San Adrián, según Navarra Capital), CNTA y la Ciudad Agroalimentaria de Tudela | Seguridad alimentaria (APPCC, IFS/BRC), trazabilidad, fichas técnicas cliente/retailer, gestión de alérgenos, reclamaciones, estacionalidad. Es el sector más estable del ciclo actual |
| **Energías renovables / bienes de equipo** | Más de 110 empresas, 10% del empleo industrial, 4.500 M€ de facturación, 5% del PIB y segundo sector exportador (Invest in Navarra) | Siemens Gamesa, Nordex-Acciona Windpower, Acciona Energía, Ingeteam; Enercluster; CENER | Documentación de O&M, SCADA de parques, análisis de incidencias y *field service*, licitaciones técnicas. Las tractoras tienen TI corporativa propia; la oportunidad está en ingenierías y proveedores (Nabrawind, Laulagun, Eosol…) |

**Por qué no metalmecánica genérica como sector separado [I]:** en Navarra la metalmecánica y la maquinaria son sobre todo la base de proveedores de automoción y renovables. Tratarla como vertical propio diluye el mensaje. Es mejor segmentar por **proceso** (calidad, mantenimiento, ingeniería de oferta) que por CNAE.

**Casos de uso concretos por sector [I, priorizados por viabilidad y ROI]:**

- **Automoción (Tier 2/3):**
  - Borrador 8D a partir de una reclamación de cliente, con recuperación de 8D históricos, AMFE y planes de control.
  - Asistente de instrucciones de trabajo para onboarding de operarios nuevos (multilingüe).
  - Preparación de auditorías IATF.
  - Respuesta a RFQ técnicos con consulta a ERP (costes y rutas).
- **Agroalimentación:**
  - Generación y actualización de fichas técnicas y especificaciones para retailers.
  - Asistente APPCC y alérgenos.
  - Análisis de reclamaciones de consumidor.
  - Preparación de auditorías IFS/BRC.
  - Consulta en lenguaje natural sobre la trazabilidad de lotes (ERP/MES).
- **Renovables y bienes de equipo:**
  - Asistente de O&M sobre manuales y el histórico de órdenes de trabajo.
  - Triaje de alarmas SCADA con contexto documental.
  - Generación de documentación de ofertas y licitaciones.

### 1.3 Adopción tecnológica y de IA: el dato de partida

- **Navarra [V]:** el 20,5% de las empresas de 10 o más empleados usa IA, frente al 20,6% del País Vasco, el 21,1% de España, el 30,1% de Madrid y el 25,6% de Cataluña (INE, Encuesta TIC en empresas 2024-1T2025, datos definitivos del 22/10/2025). En la industria española la cifra baja al 17,5%. La edición 2025-1T2026 todavía no está publicada; se espera hacia finales de octubre de 2026 y utilizará la CNAE-2025, lo que puede romper la serie.
- **UE [V]:** el 20,0% de las empresas de 10 o más empleados usó IA en 2025 (13,5% en 2024), con el 55,0% entre las grandes empresas y el 17,3% en manufactura. Dinamarca lidera con un 42,0% (Eurostat, diciembre 2025).
- **Lectura [I]:** Navarra está en la media, no rezagada. Pero la métrica INE cuenta cualquier uso (incluido ChatGPT para textos) y no la integración en procesos. El hueco real está en la **IA integrada con datos operativos**, que según la experiencia de campo está muy por debajo del 20%. **[H] a validar:** menos del 5% de las pymes industriales navarras tiene un RAG o agente en producción conectado a ERP/MES.
- **Barreras locales [I, con apoyo parcial de fuentes]:**
  1. **Escasez de talento:** ACAN estima 1.300 contrataciones solo en 14 proveedores y el foco del Servicio Navarro de Empleo está en perfiles de operario, no digitales. El responsable de TI de una pyme de 50–150 empleados suele ser una sola persona.
  2. **Decisión fuera de Navarra:** muchas plantas medianas pertenecen a grupos (alemanes, japoneses, vascos) con TI corporativa que impone su pila (a menudo Microsoft 365 + SAP).
  3. **Cultura de ingeniería prudente:** exigen demostración en planta y referencias locales.
  4. **Datos no preparados:** SharePoint o servidores de ficheros con permisos caóticos. La consultora Summum IA (blog del 12/03/2026, no Microsoft) estima que sanear los permisos antes de activar Copilot "puede llevar entre 20 y 80 horas de trabajo técnico".
  5. **Ciclo económico:** las empresas en ERTE congelan el gasto discrecional.

### 1.4 Competencia indirecta y sustitutos

| Tipo | Actores | Amenaza | Lectura crítica [I] |
|---|---|---|---|
| **Plataformas horizontales** | Microsoft 365 Copilot; Copilot Business a 18,20 €/usuario/mes en contrato anual (15,60 € en promoción) sobre un plan Business; M365 Copilot completo, 26,00 €/usuario/mes en contrato anual (27,30 € mes a mes) según Summum IA, o 26,43 € en promoción y 29,03 € con tarifa habitual sobre Business Standard según Javadex. Otros: Google Gemini for Workspace, ChatGPT Enterprise | **Alta** en oficina | Ya está en la factura de muchas plantas. No se debe competir en correo, Word o Teams, sino en planta, calidad, ERP/MES/OT y control del dato (en local) |
| **Plataformas de agentes europeas** | Dust (París): tras su cambio de precios de mediados de 2026, Pro a 30 $/asiento/mes (24 $ anual) con 8.000 créditos y Max a 150 $; plan gratuito con 500 créditos | Media | Muy buena para pymes tecnológicas y SaaS. Débil en OT, en local y en castellano industrial. Es la referencia de precios y de UX |
| **Centros tecnológicos (SINAI/ADItech)** | **NAITEC** (ofrece expresamente "asistentes inteligentes que trabajan con el conocimiento propio de la empresa", conectividad MQTT/OPC-UA con MES/SCADA/ERP y ciberseguridad industrial), **CNTA** (agroalimentario), **CENER** (energía), **AIN**, Lurederra | **Alta y subestimada** | Tienen marca, relación con el Gobierno de Navarra y capacidad para preparar las ayudas. Pero venden proyectos, no productos mantenidos. **Estrategia: aliarse, no competir**, con Illarium como producto que ellos pueden implantar o recomendar |
| **Polo IRIS / IRIS EDIH** | Coordinado por ADItech, consorcio de 25 entidades, especializado en IA, supercomputación y medicina personalizada; servicios sin coste para pymes | Media (sustituto de la fase de diagnóstico) | Canal de *top of funnel*: el diagnóstico gratuito de IRIS puede acabar en la implantación de Illarium |
| **Consultoras e integradores locales** | NAXIA (Pamplona, agentes de IA para pymes), asociados de ATANA (70 empresas asociadas, de ellas 61 pymes, según su gerente Cristina García a ANIMSA), integradores de ERP y MES | Media | Compiten en precio y cercanía. Diferenciación: producto reutilizable con gobierno, frente a proyectos a medida |
| **Consultoras nacionales** | Accenture, NTT Data, Seidor, Telefónica Tech, Minsait | Baja en pymes | Relevantes en tractoras; posible canal a medio plazo |
| **ERP/MES con IA embebida** | SAP Business One/S4 (Joule), Microsoft Dynamics 365 (Copilot), Sage, Odoo, a3ERP; MES tipo Aquiles/propietarios | Media–creciente | Los fabricantes de ERP añadirán copilotos nativos. La ventaja de Illarium es cruzar sistemas (ERP + documentos + OT), algo que ningún ERP hace bien |

**[H] a validar:** las pymes navarras de 50–250 empleados usan mayoritariamente SAP Business One, Microsoft Dynamics o ERP nacionales (Sage, a3, Ekon), y el MES suele ser una hoja de cálculo o un desarrollo propio. Esto es crítico para priorizar conectores y debe validarse en 15–20 entrevistas.

### 1.5 Ayudas y marco institucional (estado a 24/09/2026)

**Estrategia regional [V]:** la S4 (Estrategia de Especialización Inteligente para la Sostenibilidad, 2021-2027), coordinada por SODENA, tiene seis prioridades verticales: movilidad eléctrica y conectada, alimentación saludable y sostenible, industria de la energía verde, medicina personalizada, industria audiovisual y turismo sostenible. La transición digital es transversal. Las ayudas a proyectos estratégicos de I+D se articulan en retos: VOLTA (movilidad), AERO (energía verde), GEMA (medicina), ALPES (alimentación) e IRIS (innovación digital en sectores S4). **[I]** Dos de los tres sectores objetivo (automoción y agroalimentación) y el tercero (energía verde) coinciden con prioridades S4, lo que facilita el encaje en convocatorias.

| Instrumento | Estado y condiciones [V] | Uso para Illarium [I] |
|---|---|---|
| **Ayudas para el fomento de la empresa digital 2026 (Gobierno de Navarra)** | Dotación de 1,7 M€. Hasta 30.000 € en proyectos tipo A/B (implantación de soluciones; soluciones del Plan de Transformación Digital o del Plan de Ciberseguridad) y tipo C (asesoramiento y formación). Plazo del 19/05/2026 al 06/11/2026. Proyectos ejecutados desde el 22/11/2025. **Por primera vez abiertas también a grandes empresas.** Concesión por orden de presentación hasta agotar crédito. 185 empresas beneficiarias en la convocatoria anterior | **Palanca principal de venta en 2026.** Empaquetar la implantación como proyecto tipo A. Ojo: el plazo cierra el 6/11/2026 y el crédito es limitado (1,7 M€ equivale a unas 57 ayudas de 30.000 €), así que la prioridad comercial inmediata es presentar solicitudes en octubre |
| **Ayudas a la contratación de transferencia de conocimiento (pymes)** | 60% del gasto con un máximo de 10.000 € (pymes) y 70% con un máximo de 16.000 € (UIE) para actuaciones con universidades, centros tecnológicos o IRIS LAB. Plazo enero–febrero de 2026 | Vía para proyectos conjuntos con NAITEC o CNTA (Illarium como subcontratista o proveedor de plataforma) |
| **Ayudas a la inversión en pymes industriales 2026** | Línea foral activa (se desconocen los detalles de la intensidad TIC) | Posible encaje de hardware *edge*/GPU en local; hay que verificar en las bases |
| **Proyectos de I+D / estratégicos (Gobierno de Navarra)** | Convocatorias anuales I+D+i 2026; retos S4 | Proyecto de I+D sobre agentes para OT con un cliente tractor y un centro tecnológico |
| **Kit Consulting (Red.es)** | Bonos de 12.000–24.000 € según tamaño (10–249 empleados); servicio de IA de hasta 6.000 €. **Plazo para formalizar acuerdos cerrado el 31/05/2026**; sin nueva convocatoria confirmada | No contar con él en 2026; si se reabre, sirve como puerta de diagnóstico. Requiere que Illarium esté adherido como asesor digital |
| **Kit Digital (Red.es)** | **Información contradictoria.** Algunas fuentes citan la Orden TDF/39/2026 y un catálogo ampliado con IA sin plazos abiertos; otras afirman que ya no admite solicitudes | No construir el plan de negocio sobre Kit Digital; es, como mucho, un complemento |
| **RedIA (Red.es, FEDER 2021-2027)** | 130 M€ (47 M€ para regiones más desarrolladas, incluida Navarra); proyectos de desarrollo experimental de 400.000 € a 5 M€; intensidad del 45%/35%/25% (pequeña/mediana/resto). En Navarra: Kunak Technologies y Uraphex (656.045 € entre ambas) y Nanogrow Biotech (más de 454.000 €, RedIA Salud), unos 1,1 M€ en total | El umbral de 400.000 € está fuera del alcance de Illarium en solitario. Posible como socio tecnológico de un cliente mediano |
| **SPRI "Inteligencia Artificial 2026" (País Vasco)** | Hasta 100.000 €/año en proyectos de adopción de IA en empresas vascas | **Muy relevante para el GTM vasco**: el País Vasco tiene un programa específico de IA más generoso que Navarra |
| **IRIS EDIH** | Servicios de digitalización sin coste para pymes; alianzas con 13 EDIH (6 nacionales, 7 europeos), con al menos el 50% de los costes financiados en servicios de hubs aliados | Canal de generación de demanda y de credibilidad |
| **Next Generation EU** | Kit Digital y Kit Consulting se financian con el MRR (Componente 13); el horizonte del Plan de Recuperación termina en 2026 | **Riesgo:** la financiación NGEU se acaba. Diseñar el negocio para que sobreviva sin ella |

**[H] no verificado:** varias webs comerciales mencionan un programa estatal de 40 M€ para que las pymes accedan a la IA mediante "al menos 15 modelos generales y plataformas SaaS". No se ha encontrado fuente primaria; hay que vigilar el BOE y Red.es, porque podría ser un canal de financiación de plataformas como Illarium.

**Marco regulatorio [V]:**

- **AI Act (Reglamento UE 2024/1689).** Prohibiciones y alfabetización en IA (art. 4) vigentes desde febrero de 2025. El **Digital Omnibus sobre IA** (acuerdo político del 7/5/2026, aprobado por el Parlamento en junio y adoptado por el Consejo el 29/6/2026) aplaza las obligaciones de alto riesgo del Anexo III al **2/12/2027** y las de la IA integrada en productos regulados (Anexo I, p. ej. maquinaria) al **2/8/2028**. Las obligaciones de transparencia del art. 50 (avisar de que se interactúa con una IA, marcar contenido sintético) aplican desde el 2/8/2026, aunque algunas fuentes indican plazos específicos posteriores para el marcado legible por máquina. Hay que verificar en el texto publicado en el DOUE.
  - **[I]** Un asistente de conocimiento o calidad no es de alto riesgo en el Anexo III. Pero si Illarium llegara a controlar funciones de seguridad de maquinaria, entraría en el régimen del Anexo I (2028). **Decisión de producto: los agentes nunca actúan en lazo cerrado sobre OT en el MVP.**
- **NIS2.** España no ha completado la transposición. El Anteproyecto de Ley de Coordinación y Gobernanza de la Ciberseguridad fue aprobado el 14/1/2025 y seguía en tramitación en julio de 2026. La Comisión emitió un dictamen motivado en mayo de 2025. Mientras tanto aplica el RDL 12/2018. La directiva alcanza a entidades de 50 o más empleados o más de 10 M€ de facturación en sus sectores; la fabricación de vehículos, maquinaria y equipos eléctricos y la producción y transformación de alimentos figuran como sectores "importantes" (Anexo II) y la energía como "esenciales" (Anexo I).
  - **[I]** Muchos clientes medianos (proveedores de automoción, alimentarias de más de 50 empleados) serán sujetos obligados. Illarium será **proveedor en su cadena de suministro** y le pedirán evidencias de seguridad: ENS o ISO 27001 a medio plazo, notificación de incidentes en 24 h/72 h.
- **RGPD.** Aplica sobre todo a datos de empleados (turnos, incidencias con nombre, formación) y a correos. Es necesario un DPA, un registro de actividades y, en su caso, una evaluación de impacto.
- **ENS.** Solo es obligatorio si se sirve al sector público. **[I]** No es prioritario en el MVP, pero el ENS nivel medio es una ventaja comercial en empresas públicas forales y en ciertos clientes del sector energético.

---

## 2. Infraestructura técnica y arquitectura

### 2.1 Principios de arquitectura [I]

1. **Soberanía por defecto:** los datos y la inferencia se quedan en la UE; hay opción 100% en local para OT y documentación sensible (planos, recetas, AMFE).
2. **IT primero, OT en solo lectura:** el MVP lee de MES/SCADA/historiadores, pero nunca escribe en PLC ni SCADA. La escritura en ERP (p. ej. crear una no conformidad) siempre pasa por una aprobación humana.
3. **Modelo intercambiable:** una capa de abstracción de LLM (API UE u *open-weight* en local) permite no depender de un proveedor.
4. **Despliegue en tres modalidades con el mismo código:** SaaS UE multiinquilino, nube dedicada del cliente e instalación en local o *edge*.

### 2.2 Cloud, en local y edge: decisión por tipo de carga

| Carga | Recomendación | Justificación |
|---|---|---|
| Plano de control (UI, orquestación, metadatos, facturación) | SaaS en región española: **AWS Europa (España), en Aragón**, con 3 zonas de disponibilidad desde noviembre de 2022 [V]; **Azure Spain Central, en Madrid** [V]; Google Cloud Madrid [V]. Alternativas soberanas europeas: OVHcloud, Scaleway, IONOS, STACKIT | Latencia baja desde Pamplona y Bilbao; la residencia en España simplifica la conversación sobre RGPD. **[I]** Para el cliente que tema la CLOUD Act, ofrecer un proveedor europeo |
| Inferencia LLM general | API UE con cero retención (Mistral La Plateforme, Azure OpenAI con residencia UE, Bedrock en la región UE) o inferencia propia | La calidad de los modelos frontera en razonamiento sobre documentación compleja sigue siendo superior |
| Inferencia sobre datos sensibles u OT | **En local**: servidor con 1–2 GPU de 48 GB (clase L40S/RTX 6000 Ada) con **vLLM** y modelos *open-weight* de 7B–32B cuantizados; o *appliance* ligero con 1 GPU de 24 GB en plantas pequeñas | **[I]** Muchas plantas no dejarán salir planos, recetas ni datos de proceso. El servidor en local también encaja como inversión subvencionable |
| Conectividad OT | **Pasarela *edge*** (IPC industrial) en la DMZ entre IT y OT según el modelo de zonas y conductos de **IEC 62443**. Lee **OPC UA** y **MQTT** (preferiblemente Sparkplug B) y, si existe, un *Unified Namespace* o historiador; publica hacia la capa IT solo por salida | Respeta la segmentación de red; ningún puerto entrante hacia OT |

**Modelos europeos y *open-weight* [V + I]:**

- **ALIA** (BSC, Gobierno de España): ALIA-40B, Salamandra-7B y Salamandra-2B, en 35 lenguas europeas con peso reforzado del castellano y las cooficiales, incluido el **euskera** [V]. Sin embargo, investigadores de la Universidad de Valencia, recogidos por Xataka, concluyeron que "en exámenes de matemáticas tipo test puntuó peor que el resto de LLMs, e incluso puntuó peor que si hubiera tratado de adivinar las respuestas". Multiverse Computing (vasca) publica versiones comprimidas [V].
  - **[I]** Usar ALIA como opción de "soberanía" y para tareas ligeras (clasificación, traducción al euskera), no como motor principal de razonamiento en el MVP.
- **Mistral** (Francia): modelos *open-weight* pequeños y medianos, además de API UE. **[I]** Es la mejor opción de "modelo europeo" para tareas agénticas.
- **Otros *open-weight*** (Qwen, Llama, Gemma): son competitivos en local. **[I]** Hay que revisar las licencias (la de Llama tiene restricciones) y el riesgo reputacional o geopolítico de los modelos de origen chino ante clientes con TI corporativa alemana. Conviene documentar la procedencia del modelo en la ficha de cada agente.

### 2.3 Pila tecnológica recomendada (con trade-offs)

| Capa | Elección MVP | Alternativas descartadas o diferidas | Trade-off [I] |
|---|---|---|---|
| **Orquestación de agentes** | **LangGraph** (grafos de estado, *checkpoints* persistentes, *interrupts* nativos para *human-in-the-loop*) | CrewAI (menos control de estado), AutoGen (orientado a investigación), n8n (bueno para integraciones, pobre para razonamiento con estado) | LangGraph da trazabilidad y reanudación de flujos largos (un 8D dura días). Coste: curva de aprendizaje y dependencia del ecosistema LangChain. Mitigación: lógica de dominio en Python puro, LangGraph solo como motor de estado |
| **Protocolo de herramientas** | **MCP (Model Context Protocol)** para exponer conectores (ERP, SharePoint, MES, OPC UA vía pasarela) como servidores MCP | Integraciones *ad hoc* por agente | MCP convierte cada conector en un **activo reutilizable** y, por tanto, en el "OS modular". Es el foso técnico si se construye una librería de conectores para ERP españoles. Riesgo: seguridad de los servidores MCP (inyección de prompts, permisos excesivos). Hay que aplicar una lista de herramientas permitidas y *scopes* por rol |
| **Integración** | Conectores propios para SAP B1 (Service Layer), Dynamics 365 (OData), Odoo (XML-RPC), a3/Sage (vía BD o API); SharePoint/OneDrive (Graph); servidores de ficheros SMB | Plataformas iPaaS (Make, Zapier) | En la industria los ERP son locales y heterogéneos. Los conectores son el trabajo más lento y la mayor barrera de entrada para competidores |
| **Base vectorial** | **PostgreSQL + pgvector** (con *pgvectorscale*/HNSW) y búsqueda híbrida con BM25 (`pg_search`/`tsvector`) | Qdrant (se incorpora si se superan unos 10–50 M de vectores por inquilino o hace falta filtrado avanzado a gran escala); Weaviate; Milvus (excesivo para pymes) | Una sola base de datos para metadatos, ACL y vectores simplifica copias, cifrado y despliegue en local, algo crítico para un fundador en solitario. El volumen de una pyme industrial (10⁴–10⁶ fragmentos) cabe holgadamente |
| **Ingesta y RAG** | Docling o Unstructured para PDF, planos y tablas; *chunking* estructural (por secciones o celdas de AMFE); *embeddings* multilingües (BGE-M3 o multilingual-e5, en local); *reranker* (bge-reranker); citas obligatorias con página; herencia de ACL desde el origen | GraphRAG completo (diferido a la v2 para relaciones pieza–proceso–defecto) | La calidad del RAG industrial depende del análisis de tablas y planos, no de la base vectorial. Hay que invertir ahí |
| **Observabilidad y evaluación** | **Langfuse** autoalojado (trazas, coste y latencia por agente), OpenTelemetry, **Ragas/DeepEval** con conjuntos de evaluación dorados por cliente (50–100 preguntas validadas por Calidad) | LangSmith (SaaS en EE. UU., peor encaje de soberanía) | Sin evaluación continua no se puede demostrar el ROI ni detectar regresiones al cambiar de modelo |
| **Identidad y autorización** | **Keycloak** (OIDC/SAML, federación con Entra ID o AD local); RBAC más ABAC por planta, línea o documento; **OpenFGA** para ACL finas heredadas | Auth0/Clerk (SaaS en EE. UU.) | Autoalojable y válido en local. El agente actúa siempre **en nombre del usuario** (*on-behalf-of*) y nunca con una superidentidad |
| **Seguridad** | TLS 1.3; cifrado en reposo (AES-256) con KMS o Vault; aislamiento por inquilino (*schema* o BD dedicada); registro de auditoría inmutable (solo anexar) de cada prompt, herramienta invocada, dato recuperado y aprobación; filtros contra inyección de prompts y DLP; *sandbox* para la ejecución de código | — | Diseñado para responder a los cuestionarios de proveedor NIS2 y a una futura certificación ISO 27001/ENS |
| **Human-in-the-loop** | *Interrupts* de LangGraph y bandeja de aprobaciones: cualquier escritura en ERP, envío externo o cierre de 8D exige aprobación de un rol designado; niveles de autonomía configurables por agente (L0 sugiere, L1 redacta, L2 ejecuta con aprobación, L3 ejecuta y notifica, esta última no disponible en el MVP) | — | Requisito comercial (cultura prudente) y regulatorio (transparencia y supervisión humana) |
| **Despliegue** | Contenedores; Kubernetes ligero (k3s) en local; Helm; GitOps | — | Una sola distribución para las tres modalidades |

---

## 3. PRD – MVP "Illarium Planta" v1.0

### 3.1 Problem Statement

> Las pymes industriales de Navarra y el País Vasco (50–500 empleados) pierden horas de ingeniería y calidad y asumen riesgo de auditoría porque su conocimiento operativo (procedimientos, AMFE, 8D, fichas técnicas, manuales de máquina, histórico de incidencias) está disperso entre servidores de ficheros, ERP, MES y la cabeza de personas veteranas. Las herramientas de IA genéricas (Copilot, ChatGPT) no acceden de forma segura a sus datos de planta, no respetan permisos ni la segmentación OT y no generan entregables con formato de su sistema de calidad. Por eso la IA se queda en usos de oficina y no reduce el coste de no calidad ni el tiempo de respuesta a clientes y auditores.

**Hipótesis de valor [H]:**

- Reducir un 40% el tiempo de elaboración de un 8D o de una respuesta a una reclamación.
- Reducir un 50% el tiempo de búsqueda de información técnica.
- Reducir un 30% el tiempo de onboarding de un operario o técnico.

Todo ello con un retorno de la inversión inferior a 12 meses para una planta de 100 empleados.

### 3.2 User Personas

| Persona | Contexto | Jobs-to-be-done | Pains | Criterios de compra |
|---|---|---|---|---|
| **Iñaki – Responsable de Calidad** (Tier 2 de automoción, 180 empleados, Landaben/Orkoien) | IATF 16949; 30–60 reclamaciones al año; auditorías de cliente y de tercera parte | "Cuando llega una reclamación, quiero contener, analizar la causa raíz y responder en 24 h/10 días con un 8D sólido" | Buscar 8D antiguos y AMFE en carpetas; redactar en inglés o alemán; presión por los plazos del cliente (VW) | Calidad del borrador, trazabilidad de fuentes, formato del cliente, cero fugas de información. **Usuario principal y *champion*** |
| **Maite – Gerente de Operaciones/Planta** (alimentaria de 4.ª gama, Ribera, 250 empleados) | Estacionalidad, rotación, auditorías IFS, presión de márgenes de la distribución | "Quiero que un operario nuevo sea productivo en días y que los jefes de turno resuelvan dudas sin llamarme" | Conocimiento en veteranos; manuales desactualizados; incidencias repetidas | Adopción real en planta (móvil o tableta, castellano sencillo), ROI en horas, mínima carga para TI. **Presupuesto operativo** |
| **Jon – Director de IT/OT** (fabricante de bienes de equipo, 120 empleados, Gipuzkoa/Navarra) | Una o dos personas en TI; ERP SAP B1 o Dynamics; red OT segmentada a medias; cuestionarios NIS2 de clientes | "Quiero habilitar IA sin abrir agujeros en OT ni crear otra isla de datos" | Miedo a la "IA en la sombra"; permisos caóticos; falta de tiempo | Despliegue en local u opción UE, SSO con Entra/AD, auditoría, OT en solo lectura, documentación de seguridad (lista para ISO 27001/NIS2). **Poder de veto** |
| **Javier – Gerente/CEO de pyme** (empresa familiar, 60–150 empleados) | Márgenes presionados, posible ERTE, relación con AIN, la cámara y el clúster | "Quiero mejorar la productividad sin un proyecto que me coma el año" | Desconfianza hacia las consultoras; experiencias previas de software que no se usa | Precio cerrado, subvención gestionada, referencia de otra empresa navarra, piloto en 30–60 días. **Firma** |
| *Secundaria:* técnico de mantenimiento o jefe de turno | Usuario final en planta | "Dime cómo se resuelve esta alarma o este cambio de formato" | Manuales en PDF de 400 páginas | Rapidez, respuesta con la página del manual |

### 3.3 Épicas core del MVP

#### ÉPICA 1 — Knowledge Hub industrial (RAG con permisos y citas)

**Objetivo:** una única fuente de respuesta fiable sobre la documentación técnica y de calidad, respetando los permisos de origen.

| ID | User Story | Criterios de aceptación |
|---|---|---|
| E1-US1 | Como Director de IT/OT, quiero conectar SharePoint/OneDrive y un servidor de ficheros SMB para que el sistema indexe los documentos **heredando sus ACL** | La sincronización inicial de 50.000 documentos se completa en menos de 24 h. Un cambio de permisos en origen se refleja en menos de 1 h. Una prueba con un usuario sin acceso a una carpeta devuelve 0 fragmentos de esa carpeta (test automatizado) |
| E1-US2 | Como técnico, quiero preguntar en lenguaje natural (castellano, euskera o inglés) y recibir la respuesta **con cita a documento, versión y página** | El 100% de las respuestas incluye al menos una cita navegable. Si no hay evidencia, el sistema responde "no encontrado" en lugar de inventar. Precisión de citas de al menos el 90% sobre el conjunto de evaluación dorado del cliente. Latencia p95 inferior a 8 s |
| E1-US3 | Como Responsable de Calidad, quiero que el sistema entienda **tablas de AMFE, planes de control e instrucciones de trabajo** | La extracción estructurada de AMFE (modo de fallo, causa, control, S/O/D) tiene una exactitud de al menos el 85% por campo en 20 AMFE reales del piloto |
| E1-US4 | Como Gerente de Planta, quiero usarlo desde tableta o móvil en planta | UI responsive; modo "respuesta corta con pasos". El SSO funciona en dispositivos compartidos con cierre de sesión por inactividad |
| E1-US5 | Como usuario, quiero saber que interactúo con una IA y poder valorar la respuesta | Aviso visible de sistema de IA (art. 50 del AI Act). Botón de valoración (útil o no útil) con motivo que alimenta el panel de calidad |

#### ÉPICA 2 — Agente de Calidad y No Conformidades (8D / reclamaciones / auditorías)

**Objetivo:** el primer flujo agéntico con ROI medible y alto dolor, que actúa como cuña comercial.

| ID | User Story | Criterios de aceptación |
|---|---|---|
| E2-US1 | Como Responsable de Calidad, quiero **subir una reclamación de cliente** (PDF o correo) y obtener un borrador de D1–D4 (equipo, descripción, contención, causa raíz candidata) | El borrador se genera en menos de 3 min. Recupera al menos 3 8D o incidencias históricas similares con enlace. Propone al menos 2 hipótesis de causa raíz vinculadas a modos de fallo del AMFE. Todo el contenido es editable |
| E2-US2 | Como Responsable de Calidad, quiero que el agente **consulte el ERP/MES** (lotes, fechas, proveedor, líneas) para acotar el alcance de la contención | Consultas en solo lectura vía servidor MCP. Cada dato del ERP se muestra con la consulta ejecutada (trazabilidad). Si el conector falla, el agente lo indica y no se inventa datos |
| E2-US3 | Como Responsable de Calidad, quiero **aprobar cada paso** antes de que el 8D avance o se envíe | *Interrupt* obligatorio antes de D5–D8 y antes de cualquier envío externo. El registro de auditoría guarda quién aprobó, cuándo y qué versión. Sin aprobación no hay acción (test) |
| E2-US4 | Como Responsable de Calidad, quiero exportar en la **plantilla del cliente** (p. ej. el formato 8D del OEM o la plantilla interna) y en su idioma (ES/EN/DE) | Exportación a DOCX/XLSX con la plantilla cargada por el cliente, con al menos el 95% de los campos mapeados correctamente. Traducción revisable |
| E2-US5 | Como Gerente, quiero un **panel de no conformidades** (tiempo de ciclo, recurrencia, causas principales) | El panel se actualiza a diario. Tiempo medio de cierre antes y después de Illarium, calculado desde la fecha de alta |
| E2-US6 *(variante agro)* | Como Responsable de Calidad alimentaria, quiero preparar una auditoría IFS/BRC con una **lista de verificación de evidencias** trazada a documentos | El 100% de los requisitos seleccionados tiene evidencia enlazada o se marca como "sin evidencia" |

#### ÉPICA 3 — Conectores, gobierno y confianza ("Trust Layer")

**Objetivo:** lo que convence al Director de IT/OT y convierte el producto en un "OS modular" y no en un chatbot.

| ID | User Story | Criterios de aceptación |
|---|---|---|
| E3-US1 | Como Director de IT/OT, quiero **SSO con Entra ID o AD local** y roles por planta, departamento y documento | OIDC/SAML operativo. Roles predefinidos (Admin, Calidad, Operaciones, Planta, Auditor). El agente actúa *on-behalf-of* el usuario (test de escalado de privilegios negativo) |
| E3-US2 | Como Director de IT/OT, quiero instalar una **pasarela *edge*** que lea tags OPC UA/MQTT de un historiador o *broker* **sin puertos entrantes hacia OT** | Instalación documentada en DMZ (IEC 62443). Solo conexiones salientes. Solo lectura verificada (el intento de escritura es rechazado y registrado). Al menos 1 fuente OT conectada en el piloto |
| E3-US3 | Como Director de IT/OT, quiero un **registro de auditoría exportable** de prompts, fuentes recuperadas, herramientas invocadas y aprobaciones | El registro es inmutable (solo anexar), se exporta a CSV o SIEM (syslog) y su retención es configurable (por defecto 1 año) |
| E3-US4 | Como Director de IT/OT, quiero elegir **dónde se ejecuta el modelo** (API UE con cero retención o modelo en local) por espacio de trabajo o por agente | El cambio de proveedor de modelo se configura sin despliegue. Ficha de agente con modelo, versión, proveedor y región. Evaluación de regresión automática con el conjunto dorado al cambiar de modelo |
| E3-US5 | Como Admin, quiero **catálogo de conectores MCP** (SharePoint, SMB, SAP B1, Dynamics 365, Odoo, correo) activables por módulo | Al menos 4 conectores en GA para la v1. Cada conector con *scopes* mínimos documentados |
| E3-US6 | Como Gerente, quiero **documentación de cumplimiento** lista para entregar (DPA RGPD, descripción de medidas de seguridad, nota de alfabetización en IA del art. 4, ficha de transparencia) | Paquete descargable desde la consola; revisión legal previa al lanzamiento |

**Fuera del alcance del MVP (explícito) [I]:** escritura en PLC/SCADA, mantenimiento predictivo con ML sobre series temporales (lo hacen mejor NAITEC o especialistas), agentes autónomos L3, marketplace de agentes de terceros, visión artificial.

### 3.4 Modelo de pricing

**Benchmarks [V]:**

| Herramienta | Precio | Métrica |
|---|---|---|
| Microsoft 365 Copilot Business | 18,20 €/usuario/mes en contrato anual (15,60 € en promoción) sobre un plan M365 Business; M365 Copilot completo, 26,00 €/usuario/mes en contrato anual (27,30 € mes a mes) según Summum IA, o 26,43 € en promoción y 29,03 € con tarifa habitual sobre Business Standard según Javadex | Asiento |
| Dust (Business, desde mediados de 2026) | Pro a 30 $/mes (24 $ anual) con 8.000 créditos; Max a 150 $/mes (120 $ anual); gratuito con 500 créditos | Asiento más créditos |
| Coste orientativo de Copilot para 30 usuarios | Unos 6.552 €/año solo en el complemento, a precio de lista y sin la promoción vigente hasta el 30/09/2026 (Summum IA) | — |
| Proyectos de implantación de copilotos para pymes en España | Consultores nacionales anuncian proyectos cerrados desde 5.000 €; saneamiento de permisos (1.000–3.000 €) y formación (1.500–4.000 €) | Proyecto |

**Lectura [I]:** el mercado está migrando de "asiento ilimitado" a **asiento más consumo** (el caso Dust de 2026). En planta, cobrar por asiento penaliza la adopción (muchos operarios con uso esporádico). **Métrica de valor recomendada: plantas/espacios de trabajo más agentes o flujos activos, con usuarios de consulta ilimitados y un paquete de ejecuciones agénticas incluido.**

**Propuesta de tiers [H, a validar con 10 entrevistas de disposición a pagar y 3 pilotos]:**

| Tier | Precio | Incluye | Público |
|---|---|---|---|
| **Sandbox (freemium)** | 0 € durante 30 días o de forma permanente con límites | 1 espacio de trabajo en SaaS UE, 3 usuarios, 500 documentos, solo el Knowledge Hub, sin conectores ERP/OT | Generación de *leads* y prueba de calidad del RAG. **No es un freemium clásico**: el B2B industrial no se autoservirá, así que funciona como demo con sus propios documentos |
| **Planta** | **≈790 €/mes** (facturación anual, ≈9.480 €/año) | 1 planta, usuarios de consulta ilimitados, Knowledge Hub + 1 agente (Calidad), 2 conectores (SharePoint/SMB + 1 ERP), 2.000 ejecuciones agénticas al mes, SaaS UE | Pymes de 50–150 empleados |
| **Industrial** | **≈1.690 €/mes** (≈20.280 €/año) | Hasta 3 plantas, todos los agentes del catálogo, pasarela *edge* OT, SSO y auditoría avanzada, 10.000 ejecuciones al mes, nube dedicada UE, SLA del 99,5% | 150–500 empleados, NIS2 "importantes" |
| **Enterprise / On-prem** | **Desde ≈36.000 €/año** más hardware | Instalación en local o *edge* completa con modelos *open-weight*, conectores a medida, soporte 8×5 con respuesta en 4 h | Plantas de grupos o datos muy sensibles |
| **Implantación (obligatoria)** | **6.000 € (Planta) – 18.000 € (Industrial)** | Saneamiento de permisos, ingesta, conjunto de evaluación dorado, configuración de plantillas 8D/IFS, formación (alfabetización en IA del art. 4) | **Empaquetada como proyecto subvencionable** |

**Encaje con ayudas [I]:** un proyecto típico Planta en el primer año (implantación de 6.000 € más 12 meses de licencia de 9.480 €, unos 15.500 €) cabe dentro del techo de 30.000 € de la línea foral de fomento de la empresa digital. La intensidad varía por modalidad, así que hay que confirmarla en las bases. **Regla de negocio: el precio debe ser rentable sin ayuda.** La ayuda acelera la decisión, pero no puede sostener el margen. En el País Vasco, la línea SPRI de IA (hasta 100.000 €/año) permite vender el tier Industrial más la implantación.

**Comparación de valor [I]:** Copilot para 30 usuarios cuesta unos 6.552 €/año a precio de lista (Summum IA) y no toca planta. Illarium Planta cuesta unos 9.480 €/año con usuarios ilimitados. Si ahorra 5 h/semana al Responsable de Calidad y 5 h/semana entre jefes de turno (unas 450 h/año a 35–45 €/h, es decir, 16.000–20.000 €), el retorno es inferior a 12 meses. **Esto tiene que medirse en el piloto, no suponerse.**

### 3.5 Métricas de éxito del MVP

**North Star Metric [I]:** **Tareas operativas resueltas y aceptadas por semana por planta** (respuestas del Knowledge Hub valoradas como útiles con cita más borradores de 8D o auditoría aprobados por un humano). Captura el valor entregado y la confianza, no solo el uso.

| KPI | Objetivo a 6 meses [H] |
|---|---|
| Plantas de pago | 5–8 (al menos 3 de automoción, 2 de agroalimentación, 1 en el País Vasco) |
| Tiempo hasta el primer valor (primera respuesta citada útil) | Menos de 10 días desde la firma |
| Precisión de citas sobre el conjunto dorado | Al menos el 90% |
| Tasa de alucinación (afirmación sin soporte) | Menos del 3% en la evaluación mensual |
| Aceptación de borradores 8D (editados menos del 30%) | Al menos el 60% |
| Reducción del tiempo de ciclo de 8D o reclamación | Al menos el 30% frente a la línea base del cliente |
| Usuarios activos semanales / usuarios habilitados | Al menos el 40% |
| Retención de clientes a 12 meses / NRR | Al menos el 90% / al menos el 110% (expansión a más agentes o plantas) |
| Margen bruto de la suscripción (con coste de inferencia) | Al menos el 70% |
| Horas de servicio no facturables por cliente y mes tras la implantación | Menos de 6 h (indicador clave de la "trampa de la consultoría") |
| Proporción de acuerdos cofinanciados con ayudas | Registrar sin objetivo; alerta si supera el 80% (dependencia) |

### 3.6 Riesgos principales y feedback crítico

| # | Riesgo / debilidad de la tesis | Severidad | Mitigación |
|---|---|---|---|
| 1 | **"OS de IA modular" es una visión, no un producto vendible.** Un fundador en solitario no puede construir un sistema operativo horizontal frente a Microsoft, Dust o los ERP. El comprador industrial no compra "OS", compra "8D en 2 días" | **Crítica** | Posicionar como *vertical agent suite* para calidad y conocimiento de planta. El "OS" es la arquitectura interna (MCP, conectores, gobierno), no el mensaje comercial |
| 2 | **Trampa de la consultoría:** cada cliente pide conectores y flujos a medida y el producto se convierte en servicios con margen bajo | **Crítica** | Catálogo cerrado de conectores; cualquier desarrollo a medida se factura y se convierte en conector del catálogo; límite de horas no facturables (KPI) |
| 3 | **Competencia subvencionada de centros tecnológicos:** NAITEC ya anuncia asistentes de IA generativa sobre conocimiento propio y la integración MQTT/OPC-UA con MES/SCADA/ERP, además de ayudar a preparar las ayudas | Alta | Convertirlos en canal: acuerdo de "plataforma recomendada" o subcontratación en proyectos de transferencia; Illarium aporta producto mantenido y ellos I+D y marca |
| 4 | **Empaquetado de Copilot:** el Director de TI dirá "ya tenemos Copilot" | Alta | No competir en oficina; ofrecer coexistencia (conector para Teams más adelante); demostrar lo que Copilot no hace: OT, ERP local, plantillas 8D, ejecución en local |
| 5 | **Ciclo industrial adverso** (producción -7,7% en el primer semestre de 2026 frente al +3,8% estatal, según Noticias de Navarra; 10,5% de afiliados en ERTE en 2025) y cierres | Alta | Vender ahorro y cumplimiento (NIS2, auditorías) con ROI inferior a 12 meses; priorizar agroalimentación (más estable) y proveedores con aumento de carga por el eléctrico de VW |
| 6 | **Dependencia de ayudas y fin de NGEU** (Kit Consulting cerrado, Kit Digital incierto, crédito foral limitado a 1,7 M€ y por orden de llegada) | Media–alta | Precio rentable sin ayuda; calendario comercial alineado con las convocatorias; diversificar hacia el País Vasco (SPRI) |
| 7 | **Decisión fuera de Navarra** en plantas de grupos multinacionales | Media | Segmentar hacia empresas de capital local o vasco con decisión en la región; en multinacionales, entrar como piloto local con aprobación de TI del grupo |
| 8 | **Riesgo técnico del RAG industrial** (planos, tablas escaneadas, AMFE en Excel mal estructurados) | Media | Conjunto de evaluación dorado desde el día 1; rechazar clientes cuyo corpus no alcance la calidad mínima (criterios de calificación en preventa) |
| 9 | **Seguridad agéntica** (inyección de prompts vía documentos o correos de clientes, abuso de herramientas MCP) | Media | Solo lectura por defecto, lista de herramientas permitidas, *human-in-the-loop* en escrituras, *red-teaming* antes de producción |
| 10 | **Capacidad de un fundador autónomo** (ventas, preventa, desarrollo, soporte y seguridad a la vez); los clientes NIS2 exigirán continuidad y evidencias | Alta | Limitar a 5–8 clientes en el año 1; socio técnico o comercial; valorar SL y seguro de RC/ciber; ISO 27001 en el año 2 |
| 11 | **Regulación en movimiento** (fechas del AI Act según el Omnibus, NIS2 sin transponer) | Baja–media | Diseñar para el nivel más exigente plausible (transparencia, supervisión humana, registros); revisar trimestralmente |

### 3.7 Recomendaciones de ejecución (próximos 90 días) [I]

1. **Semanas 1–3: descubrimiento.** 15–20 entrevistas (8 de Calidad en automoción vía ACAN, 6 en agroalimentación vía Nagrifood/CNTA, 4 de TI/OT). Validar la pila de ERP y MES, el volumen de 8D y la disposición a pagar.
2. **Semanas 2–6: alianzas.** Reuniones con IRIS/ADItech (canal de diagnóstico), NAITEC y CNTA (modelo de colaboración), AIN y ATANA.
3. **Antes del 6/11/2026: ayudas.** Preparar 3–5 expedientes de la línea foral de fomento de la empresa digital (tipo A) con pilotos. Es el cuello de botella temporal más importante del año.
4. **Semanas 4–12: construcción.** Épica 1 completa, Épica 2 (D1–D4 y aprobaciones) y Épica 3 mínima (SSO, auditoría, SharePoint/SMB y 1 ERP). La pasarela OT, solo en el piloto que la requiera.
5. **Criterio de continuidad a los 6 meses:** al menos 5 plantas de pago, NSM creciente, precisión de citas de al menos el 90% y menos de 6 h/mes no facturables por cliente. Si no se cumple, volver a un modelo de consultoría con aceleradores (IP reutilizable) en lugar de SaaS.

---

## Caveats

- **Cifras sectoriales:** proceden sobre todo de Invest in Navarra/SODENA, clústeres y prensa regional (Noticias de Navarra, Navarra Capital, COPE), con años de referencia distintos (2023–2026). El peso industrial tiene al menos cuatro cifras distintas (25,8%, 26,7%, ~30%, 31%). El número de empresas industriales más reciente con fuente oficial es de 2021.
- **Datos de adopción de IA:** los del INE miden "uso de alguna tecnología de IA", no integración en procesos. La edición 2025-1T2026 aún no se ha publicado y cambiará de clasificación (CNAE-2025).
- **Precios de Copilot:** varían entre fuentes secundarias (18,20 €, 26 €, 30,24 €) por promociones, planes y fechas. Hay que confirmarlos en la tienda de Microsoft antes de cualquier material comercial. Los precios de Dust cambiaron a mediados de 2026 y la página oficial muestra los importes en euros y en dólares.
- **Ayudas:** el estado de Kit Digital es contradictorio entre fuentes. Las intensidades concretas de la línea foral de fomento de la empresa digital por modalidad deben comprobarse en las bases publicadas en el BON. Las cifras de RedIA por empresa navarra vienen de prensa y conviene contrastarlas con la resolución de concesión de Red.es.
- **AI Act:** las fechas tras el Digital Omnibus proceden de fuentes jurídicas secundarias coincidentes. Hay que verificar el texto final en el DOUE, sobre todo los plazos del art. 50 para el marcado de contenido.
- **Elementos marcados [H]:** el pricing, las personas, los objetivos de KPI y las hipótesis de ROI son hipótesis de diseño que deben validarse con clientes. No son datos de mercado.