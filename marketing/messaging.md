# Mensaje, oferta y claims — M7-G1 ([ADR-0008](../wiki/decisions/ADR-0008-evidencia-comercial.md))

> Fuente única para la landing, los posts y el outbound. **Si una cifra no está en la tabla de claims (§4), no se publica.**

## 1. Una frase

**Illarium redacta el 8D por ti en minutos, con cada dato citado y trazado al ERP, y no envía nada sin tu firma.**

Descriptor fijo: *copiloto de calidad 8D para proveedores de automoción*. El nombre está abierto en [O07](../wiki/opportunities/O07-mensaje-y-marca.md).

## 2. Propuesta de valor por persona

| Persona | Dolor (con sus palabras) | Lo que obtiene | Prueba en el demo |
|---|---|---|---|
| **Responsable de calidad** (champion) | "Me llega la reclamación del cliente y tengo 24 h para la contención y 10 días para el 8D, encima del día a día" | El borrador D1–D4 listo en minutos, con 8D anteriores similares, AMFE y lotes afectados ya cruzados. Él revisa y firma | Pasos 2–6 y 8 del guion |
| **IT/OT** (veto) | "No voy a dar a una IA acceso a mi ERP" | Acceso de **solo lectura** con su propio usuario, permisos por carpeta, aprobación humana obligatoria, registro inalterable de cada paso y datos procesados en la UE | Pasos 5, 7 y 9 |
| **Gerencia** (firma) | "¿Cuánto me cuesta y cuándo lo recupero?" | Menos horas de calidad por reclamación y menos riesgo de penalización del cliente. Piloto acotado y posiblemente subvencionable | Paso 10 |

**Regla de tono:** se abre con el dolor y el plazo. La tecnología (RAG, LLM, MCP) solo aparece como prueba, y nunca en el titular.

## 3. Oferta

**Piloto de implantación en tu planta** (6–8 semanas, orientativo):
1. Diagnóstico de 1 día: tus 8D, tu AMFE, tu ERP.
2. Carga de tu documentación con tus permisos.
3. Conexión de solo lectura al ERP.
4. 5 reclamaciones reales en paralelo a tu proceso actual, midiendo tiempo y % editado.

**Ayuda foral (Navarra, plazo hasta el 06/11/2026):** la convocatoria de fomento de la empresa digital cubre la implantación de soluciones avanzadas (hasta 30.000 €, por orden de llegada).
- **Estado de verificación (17/10):** solo se ha visto en fuentes de terceros (agregadores y el catálogo de AIN). **Falta confirmar en las bases oficiales** la elegibilidad del tipo A, la inversión mínima (las fuentes dicen 600 € o 5.000 €), la intensidad (35–90 %) y si el proveedor tiene que estar en algún catálogo.
- **Hasta entonces**, en público se dice: *"Puede ser subvencionable con la ayuda foral de empresa digital: te ayudamos a comprobarlo"*. Nunca un porcentaje ni un importe garantizado.

**Precio:** no se publica. En la conversación se usan las referencias del PRD (implantación de 6.000–18.000 €; suscripción "Planta" ≈790 €/mes), marcadas como orientativas.

## 4. Tabla de claims permitidos

Etiqueta obligatoria junto a cualquier cifra: **"Demo con planta ficticia (datos sintéticos)"**.

| # | Claim público | Valor | Fuente | Condición de uso |
|---|---|---|---|---|
| C1 | Borrador D1–D4 en menos de 1 minuto | p50 26,6 s; rango 22,7–34,7 s en 5 casos | `wiki/skill-impact.md` #26; `raw/eval-runs/2026-09-27_8d_*` | "En nuestra demo"; el objetivo de producto es < 3 min (F04) |
| C2 | Cada frase del borrador lleva su cita al documento de origen | Precisión de citas del 93 % en el golden set de 50 preguntas | `wiki/features/F02-rag-citado.md` (M2-T7) | Decir "en nuestro banco de pruebas"; no prometer 93 % en el corpus del cliente (P06) |
| C3 | Encuentra los 8D anteriores similares ("esto ya nos pasó") | Recurrencia 100 % en el banco de pruebas | `wiki/logs.md` (M2-T7) | Igual que C2 |
| C4 | Detecta instrucciones ocultas en la reclamación y no las obedece | 0 falsos positivos en 90 re-ejecuciones; caso de inyección detectado 3/3 | `wiki/skill-impact.md` #28; red-team M3-T6 | Para IT; no decir "inmune" |
| C5 | Nada sale sin firma humana; la aprobación queda ligada a la versión exacta | Probado en 5 formas de saltarlo (red-team): las 5 bloqueadas | `wiki/skill-impact.md` #29 | Hecho de diseño |
| C6 | Acceso al ERP en solo lectura | 3 roles probados sin escritura, ni por MCP ni por SQL | `wiki/skill-impact.md` #29 | Hecho de diseño |
| C7 | Registro inalterable de cada paso (cadena de hash) | Verificable con `verify_chain()` | `app/backend/migrations/003_audit.sql` | No decir "certificado". El ancla externa sigue pendiente |
| C8 | Datos procesados en la UE, sin retención por el proveedor del modelo | Gemini 2.5 Flash en Vertex UE con ZDR | ADR-0007, `docs-compliance/ficha-modelos.md` | **Pendiente M-3** (jurisdicción efectiva): usar "configurado para región UE" hasta cerrarlo |
| C9 | Ahorro esperado ~450 h/año en una planta de 100 empleados | 16.000–20.000 €/año | ADR-0006 (PRD §3.4) | **Solo como estimación** ("esperado"), nunca como resultado medido |

**Claims prohibidos:**
- "Clientes que ya lo usan".
- Logos de clientes.
- "Cumple el AI Act / IATF".
- "Sin errores".
- Cualquier marca real de OEM.
- "Reduce un X % el tiempo" (eso es H02 y aún no está medido con clientes).

## 5. Objeciones frecuentes (respuesta corta)

| Objeción | Respuesta |
|---|---|
| "Ya tenemos Copilot" | Copilot no conoce tu AMFE, no consulta tu ERP con tus permisos y no deja traza de qué dato sostiene cada frase del 8D |
| "¿Y si se inventa algo?" | Cada frase lleva su cita, y si no hay fuente dice "no encontrado". Además, tú firmas antes de que salga nada |
| "IT no lo va a permitir" | Solo lectura, con tu usuario, en la UE y con un registro inalterable. Lo revisa tu IT en la demo (paso 9) |
| "Nuestros documentos son un desastre" | Es lo que medimos en el piloto. Empezamos con 5 reclamaciones reales y vemos qué falla |
