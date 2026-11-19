# 2026-11-19 · Vertical CFO PYME: procesos de una PYME en Ecuador y auditoría de la plantilla `cfo`

**Pregunta:** ¿qué procesos y procedimientos financieros y tributarios necesita una PYME ecuatoriana cada mes? ¿Las cuatro reglas de la propuesta de canal y de la plantilla `cfo` (rama `feat/motor-linear-cfo` de illariumcore) cubren lo importante?
**Método:** búsqueda web el 19/11/2026 y lectura de `lib/templates/cfo.json`, `lib/seeds/cfo.ts` y `lib/rules-engine.ts` en esa rama. Cada dato normativo lleva su nivel de comprobación:

- **[oficial]** lo dice una página del SRI, el IESS o la Supercias, según el resumen del buscador. No se ha leído a mano.
- **[secundaria]** prensa, consultoras o proveedores de software. Varias coinciden.
- **[sin confirmar]** las fuentes se contradicen o solo hay una.

Esto es evidencia, no asesoramiento financiero ni tributario. Nadie cualificado lo ha revisado. Antes de enseñárselo a la socia o al contador, hay que leer a mano las fuentes **[oficial]**.

## Resultado

1. **Las cuatro reglas sirven para una demo, pero dos miden mal.** R-MAR-03 cuenta como ingreso cualquier crédito del banco (préstamos, aportes de socios, traspasos entre cuentas propias). R-LIQ-01 deja fuera obligaciones a 30 días que se conocen con certeza: retenciones del 103, IESS y nómina.
2. **R-SRI-02 usa un umbral inventado (100 $) y deja fuera el que fija la ley (500 $).** Desde la Ley Orgánica de Eficiencia Económica (diciembre de 2023), un gasto de más de 500 $ pagado fuera del sistema financiero no es deducible ni da crédito de IVA **[secundaria, varias coinciden]**. Ese pago no aparece en el extracto. Se detecta en el comprobante recibido, en su forma de pago. Esta es la regla con más valor económico directo para la PYME, y la plantilla no la tiene.
3. **Falta el proceso que más duele: el calendario.** IVA (104), retenciones (103), ATS e IESS vencen cada mes en una fecha fija que depende del noveno dígito del RUC. El operador `days_until` ya existe y se usa en Jurídico. Una regla de vencimiento cuesta poco y es la que más se entiende en una demo.
4. **La plantilla tiene que decir a quién sirve.** RIMPE Negocio Popular (hasta 20 000 $ de ingresos) no declara IVA como el régimen general, y RIMPE Emprendedor lo declara cada semestre **[secundaria]**. Las reglas de IVA y R-LIQ-01 suponen régimen general con IVA mensual. Propuesta: «sociedades y personas obligadas a llevar contabilidad, régimen general».
5. **La propuesta original choca en tres puntos con los principios, y la rama ya los resolvió:** `movimientos_sin_conciliar` como atributo resumido, `policy_hash` escrito a mano y `confidence_threshold` por pack. Queda abierto uno: la acción «emitir dictamen» no existe en `cfo.json` (ninguna regla tiene `action`).

## A. Mapa de procesos de una PYME en Ecuador

### A1. Mensuales (calendario fijo)

| Proceso | Qué es | Plazo | Fuente |
|---|---|---|---|
| Declaración de IVA (formulario 104) | Ventas gravadas menos crédito tributario de compras y retenciones de IVA recibidas | Mes siguiente al periodo, día según el noveno dígito del RUC: 1 → día 10, 2 → 12 … 0 → 28 | **[oficial]** sri.gob.ec (IVA); días: **[secundaria]** |
| IVA semestral | RIMPE Emprendedor y quien solo vende con tarifa 0 %. Primer semestre en julio, segundo en enero | Noveno dígito | **[oficial]** sri.gob.ec (IVA) |
| Retenciones en la fuente (formulario 103) | Impuesto a la renta retenido a proveedores y empleados | Mes siguiente, noveno dígito | **[secundaria]**. Desde el 03/11/2025, un 103 sin pagar del todo cuenta como no presentado **[sin confirmar]** |
| Anexo Transaccional Simplificado (ATS) | Detalle de compras, ventas y retenciones | **Mes subsiguiente** (dos meses después), noveno dígito. Semestral si el IVA es semestral | **[oficial]** sri.gob.ec |
| Aportes y fondos de reserva al IESS | Planilla del mes de los trabajadores en relación de dependencia | Hasta el día 15 del mes siguiente. Con 30 días de mora, el IESS puede cobrar por coactiva | **[oficial]** gob.ec/iess (trámites) |
| Facturación electrónica | Emitir y recibir comprobantes autorizados por el SRI | Continuo | **[oficial]** |
| Conciliación bancaria | Cruzar cada movimiento con su comprobante o justificante | Cierre del mes | Práctica contable, no norma |
| Ventas a crédito (Supercias) | Reporte de ventas a crédito de las compañías bajo control | Alrededor del día 10 | **[sin confirmar]**, solo consultoras |

Si la fecha cae en un día no hábil: unas fuentes dicen que pasa al día hábil siguiente y otras que al anterior **[sin confirmar]**. Hay que leerlo en el calendario oficial antes de convertirlo en regla. Una nota de prensa dice que, desde junio de 2026, el IVA se declara y se paga a la vez **[sin confirmar]**.

### A2. Anuales o periódicos

| Proceso | Plazo | Fuente |
|---|---|---|
| Impuesto a la renta de sociedades (101) y de personas naturales (102) | Abril (sociedades) y marzo (personas naturales), por noveno dígito | **[secundaria]** |
| Renta RIMPE | Marzo o mayo según la fuente | **[sin confirmar]** |
| Décimo tercero (1/12 de lo ganado en el año) | Diciembre, o mensualizado | **[secundaria]** |
| Décimo cuarto (un SBU; 482 $ en 2026 según prensa) | Costa en marzo, Sierra en agosto | **[secundaria]** |
| Participación de trabajadores en utilidades (15 %) | Abril | **[sin confirmar]** en esta búsqueda |
| Estados financieros a la Supercias | Primer cuatrimestre, por noveno dígito | **[sin confirmar]** en esta búsqueda |

### A3. Reglas con efecto económico directo

- **Bancarización de más de 500 $.** Artículo 25 de la Ley Orgánica de Eficiencia Económica y Generación de Empleo (Registro Oficial, 20/12/2023), según la prensa. Antes el umbral era 1 000 $. Para que el gasto sea deducible y dé crédito de IVA, se paga por giro, transferencia, tarjeta, cheque u otro medio electrónico. El justificante es el comprobante de venta más el del pago **[secundaria, varias coinciden; el número de artículo varía según la fuente]**. La ley no prohíbe pagar en efectivo: lo que se pierde es el beneficio tributario.
- **Multas y recargos por declarar tarde.** Existen, pero no se cuantifican aquí.

### A4. Gestión (no son norma; los umbrales los fija el especialista)

- Liquidez a 30 días (o flujo de caja a 13 semanas).
- Antigüedad de la cartera por cobrar: 0-30, 31-60, 61-90 y más de 90 días.
- Concentración de clientes y de proveedores.
- Peso de los gastos fijos sobre los ingresos de explotación.
- Presupuesto frente a lo real.

## B. Clasificación para Solaris

Operadores que existen en la rama (`lib/rules-engine.ts`): comparador, `days_until`, `exists`, `compare_related`, `count_related` y `linear`.

| Proceso | Encaje | Qué falta |
|---|---|---|
| Vencimiento del 104, 103 y ATS | **(a)** `days_until` sobre la fecha de vencimiento | Objeto `Obligacion` (tipo, periodo, `vence`, `presentada`). La fecha la calcula la plantilla desde el noveno dígito, no el modelo |
| Planilla del IESS el día 15 | **(a)** `days_until` | El mismo objeto `Obligacion` |
| Sustento de pagos a proveedores | **(a)** `count_related`; ya existe (R-SRI-02) | Ajustar el umbral |
| Bancarización de más de 500 $ | **(a)** comparador en `ComprobanteSRI` | Atributos `tipo` (emitido o recibido) y `forma_pago` en el comprobante |
| Liquidez a 30 días | **(a)** `linear`; ya existe (R-LIQ-01) | Términos para retenciones, IESS y nómina a 30 días (cabe en el límite de 8 términos) |
| Gastos fijos sobre ingresos | **(a)** `linear`; ya existe (R-MAR-03) | `ingresos_operativos` (créditos de categoría `cobro`), en lugar de `total_creditos` |
| Concentración de cartera | **(a)** comparador; ya existe (R-CON-04) | Nada |
| Cartera vencida a más de 90 días | **(a)** `linear` o comparador | Atributo `cxc_mas_90d` en `Cartera` |
| Cálculo del IVA a pagar | **(c)** fuera: es cálculo tributario | Se cita la cifra del 104 o del contador, no se calcula |
| Décimos, utilidades, renta anual | **(b)** fuera del cierre mensual | Otro proceso, si algún día se pide |
| Leer PDF y XML reales | **(b)** Fase 4 | Bloqueado por [[ADR-0026]] y la Fase 5 |

## C. Auditoría de la propuesta y de la plantilla actual

Cada hallazgo dice cómo comprobarlo.

| # | Hallazgo | Gravedad | Cómo se comprueba |
|---|---|---|---|
| C1 | **R-MAR-03 suma como ingreso cualquier crédito bancario.** `total_creditos` incluye préstamos, aportes y traspasos. Un préstamo de 20 000 $ haría cumplir la regla a una empresa en apuros | Alta (falso conforme) | Añadir al seed un crédito de categoría `prestamo` de 20 000 $ en octubre: R-MAR-03 pasa a conforme sin que cambie nada de la operación |
| C2 | **R-LIQ-01 deja fuera obligaciones ciertas a 30 días.** Retenciones del 103, aportes al IESS y nómina del mes que viene. El seed tiene nómina mensual, y la regla no la ve salvo que esté dentro de `cuentas_por_pagar_30d`, que no lo dice | Media | Leer la etiqueta de `cuentas_por_pagar_30d` en `cfo.json`: «proveedores» o nada. Preguntar al contador qué incluye |
| C3 | **R-LIQ-01 aplica el margen del 15 % también al IVA.** El IVA es una cifra conocida, no un riesgo | Baja | Decisión del especialista: margen solo sobre proveedores |
| C4 | **R-SRI-02 usa 100 $, un umbral que no está en ninguna norma.** Puede servir como criterio del especialista, pero el `thresholds` de la plantilla debe decir que es suyo | Baja | Ya lo dice el `scope`. Repetirlo en `thresholdSummary` |
| C5 | **Falta la regla de bancarización de más de 500 $.** Es la única de todo el expediente que se traduce directamente en dólares de impuesto | Alta (valor) | El extracto no puede mostrar un pago en efectivo. Hace falta el comprobante recibido con su forma de pago |
| C6 | **Falta el calendario de obligaciones.** Es lo que más se entiende en una demo y `days_until` ya existe | Media (valor) | — |
| C7 | **R-CON-04: la propuesta dice «facturación o cuentas por cobrar».** La plantilla eligió cartera, y está bien. La propuesta escribía `0.35` y la plantilla `35`: unidades distintas para el mismo umbral | Baja | `cfo.json`: `value: 35` con la etiqueta «(%)». Coherente |
| C8 | **Ninguna regla tiene `action`.** La acción de la propuesta (dictamen firmado por el especialista sénior) no se genera. Hoy solo están las revisiones del seed (REV-CFO-01 a 03) | Media | `grep '"action"' lib/templates/cfo.json` no devuelve nada |
| C9 | **Régimen sin declarar.** Las reglas de IVA no aplican a RIMPE Negocio Popular | Media | El `sector` dice «PYME comercial», no el régimen |
| C10 | **La propuesta original frente a los principios.** `movimientos_sin_conciliar == 0` hacía que el modelo decidiera la regla (principio 2); la rama la modela movimiento a movimiento. `policy_hash: "sha256:8f4b…"` estaba escrito a mano; el motor lo calcula. `confidence_threshold` por pack; el motor usa `MIN_CONFIDENCE = 0.8` común | Resuelto | ADR-0026 y la rama |
| C11 | **«5 minutos en lugar de 4 horas»** sigue sin medir | Abierto | Se mide en el concierge (ADR-0026) |

## D. Propuesta para la plantilla `cfo`

Solo es una propuesta. Diego elige y dev la implementa. Se ordena por valor y coste, y nada exige leer documentos reales.

| Prioridad | Cambio | Operador | Datos nuevos | Coste |
|---|---|---|---|---|
| 1 | **R-MAR-03 sobre ingresos operativos** (C1) | `linear` | `ExtractoBancario.ingresos_operativos`, que el seed calcula desde los movimientos de categoría `cobro` | Bajo: seed + golden |
| 2 | **R-BAN-05 · Bancarización de más de 500 $** (C5). SI comprobante recibido Y importe > 500 Y forma de pago = sin sistema financiero → incumplida | comparador | `ComprobanteSRI.tipo`, `ComprobanteSRI.forma_pago`; un comprobante ficticio pagado en efectivo | Bajo-medio |
| 3 | **R-CAL-06 · Obligaciones del mes** (C6). `presentada == false` Y `days_until(vence) <= 5` → requiere aprobación | `days_until` + comparador | Objeto `Obligacion` (104, 103, ATS, IESS) con `vence` derivado del noveno dígito ficticio | Medio: tipo nuevo |
| 4 | **R-LIQ-01 con retenciones, IESS y nómina** (C2, C3) | `linear` | Tres atributos en `Cartera` u `Obligacion` | Bajo, pero cambia el golden |
| 5 | **`action` en R-LIQ-01**: borrador del plan de caja que firma el especialista (C8) | — | `action.title` y `action.draft` | Bajo |
| — | Cartera a más de 90 días | comparador | `cxc_mas_90d` | Esperar a que el contador lo pida |

Las prioridades 1, 2 y 5 caben en el sprint hasta el 09/12 sin desplazar nada más que días de dev. La 3 es la que más luce en la demo, pero añade un tipo de objeto. Antes de escribir R-BAN-05 hay que confirmar los códigos de forma de pago en la ficha técnica de comprobantes electrónicos del SRI (de memoria, «01 = sin utilización del sistema financiero») **[sin confirmar]**.

## E. Preguntas para la socia y el contador

1. ¿En qué régimen están las empresas del concierge (general, RIMPE Emprendedor, RIMPE Negocio Popular)? ¿Son sociedades o personas naturales?
2. ¿Qué entra en «cuentas por pagar a 30 días»: solo proveedores, o también impuestos, IESS y nómina?
3. ¿El margen del 15 % se aplica a todo o solo a proveedores?
4. ¿Gastos fijos sobre ingresos de explotación o sobre todo lo cobrado? ¿El 40 % es para comercio, para servicios o para los dos?
5. El umbral de 100 $ para exigir factura, ¿es suyo? ¿Preferís el de 500 $ de la ley, o los dos?
6. ¿Os sirve el calendario de obligaciones (104, 103, ATS, IESS) como parte del diagnóstico?
7. En los expedientes reales, ¿el reporte del SRI trae la forma de pago de cada comprobante recibido?

## Fuentes

Oficiales (resumen del buscador; falta leerlas a mano):
- [SRI · Impuesto al Valor Agregado](https://www.sri.gob.ec/en/impuesto-al-valor-agregado-iva): plazos del IVA mensual y semestral por noveno dígito; ATS en el mes subsiguiente.
- [SRI · Guía tributaria del IVA (PDF)](https://www.sri.gob.ec/o/sri-portlet-biblioteca-alfresco-internet/descargar/34839464-da45-49a5-b7f8-7f3481c4812b/Gu%C3%ADa%20Tributaria%202%20-%20(IVA)%20Impuesto%20al%20Valor%20Agregado.pdf)
- [SRI · Régimen para microempresas / RIMPE](https://www.sri.gob.ec/en/regimen-impositivo-para-microempresas)
- [IESS · Acuerdo de pagos parciales](https://www.gob.ec/iess/tramites/solicitud-acuerdo-pagos-parciales-plazo-maximo-12-meses): pago patronal hasta el día 15 y coactiva tras 30 días de mora.

Secundarias:
- [El Universo · pagos de más de 500 $](https://www.eluniverso.com/noticias/economia/los-pagos-mayores-a-500-dolares-ya-no-podran-realizarse-en-efectivo-segun-dispone-la-ley-de-eficiencia-economica-si-se-quiere-aplicar-una-deduccion-o-un-credito-tributario-nota/), [Expreso](https://www.expreso.ec/actualidad/economia/compras-500-dolares-pagar-efectivo-183274.html), [Primicias](https://primicias.ec/noticias/economia/pagos-efectivo-reforma-tributaria-impuestos), [PwC Tax Summaries](https://taxsummaries.pwc.com/ecuador/corporate/deductions), [CCB Abogados](https://ccbabogados.com/en/2024/01/02/informativo-tributario-ley-organica-de-eficiencia-economica-y-generacion-de-empleo/): bancarización.
- [Factuplan · calendario 2026](https://factuplan.com.ec/blog/calendario-tributario-sri-2026-noveno-digito), [Siigo · calendario 2026](https://www.siigo.com/ec/blog/obligaciones-fiscales/calendario-tributario-sri/), [El Comercio](https://www.elcomercio.com/actualidad/negocios/impuestos-declaraciones-vencen-hasta-diciembre-ecuador/): días por noveno dígito.
- [Expreso · IVA declarar y pagar el mismo día](https://www.expreso.ec/tramites-y-servicios/iva-ecuador-declarar-y-pagar-mismo-dia-desde-junio-2026-279106.html)
- [Factuplan · RIMPE 2026](https://factuplan.com.ec/blog/rimpe-emprendedores-negocio-popular-ecuador-2026), [Verifactura · RIMPE](https://www.verifacturaec.com/guias/sri/regimen-rimpe): umbrales de 20 000 $ y 300 000 $.
- [Primicias · décimos](https://www.primicias.ec/economia/decimos-tercero-cuarto-sueldos-mensual-acumulacion-trabajadores-pensionistas-iess-113337/)
- [Andersen · obligaciones empresariales enero 2026 (PDF)](https://ec.andersen.com/wp-content/uploads/2025/12/TIPS-41-Obligaciones-empresariales-enero-2026.pdf): Supercias e IESS en el calendario mensual.

## Sin comprobar

- Ninguna fuente oficial leída a mano.
- Regla del día no hábil, fechas de renta RIMPE, utilidades y Supercias.
- Códigos de forma de pago del comprobante electrónico.
- Qué incluye `cuentas_por_pagar_30d` en los expedientes reales (pregunta E2).
