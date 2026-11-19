---
id: ADR-0026
type: decision
title: "Vertical CFO PYME: concierge fuera del producto y plantilla ficticia, con un operador lineal en el motor"
status: proposed
owner_role: product
links: ["[[ADR-0011]]", "[[ADR-0015]]", "[[ADR-0017]]", "[[ADR-0020]]"]
evidence: ["raw/research/2026-11-19_cfo-pyme-procesos-ecuador.md"]
updated: 2026-11-19
---

# ADR-0026 · Vertical CFO PYME

- Estado: propuesta. Diego la acepta o la corrige al revisar el PR del producto.
- Contexto: llega una propuesta de canal para una vertical de diagnóstico financiero y tributario mensual de PYMES en Ecuador. La PYME entrega su expediente del mes (extracto bancario, comprobantes electrónicos del SRI y cartera a 30 días), cuatro reglas lo evalúan y un especialista revisa el resultado antes de entregarlo. La variante en la que una firma contable usa la herramienta para su propia cartera de clientes es la tesis de canal de [[ADR-0011]]. El alcance está congelado ([[ADR-0015]]).

## Problema

1. Dos de las cuatro reglas (cobertura de liquidez y techo de gastos fijos) combinan atributos de varios objetos con coeficientes. Los operadores de `lib/rules-engine.ts` (comparador, `days_until`, `exists`, `compare_related`, `count_related`) no lo expresan.
2. La conciliación de débitos bancarios con comprobantes del SRI no puede llegar como un atributo resumido por el modelo («movimientos sin conciliar»): sería el modelo quien decide la regla, y eso rompe el principio 2.
3. `plan-evolutivo.md` (Fase 5) no admite documentos reales hasta pasar la revisión de `security` y tener acuerdo de confidencialidad y encargo de tratamiento. La Fase 4 (lectura de PDF y XML) no existe.

## Opciones

1. **No hacerla.** No desplaza nada. Deja sin respuesta a un posible canal.
2. **Piloto real en el producto.** Ingesta de extractos y XML reales de cinco empresas. Incumple la Fase 5, necesita la Fase 4 y expone a la ley de protección de datos de Ecuador sin Nivel 2.
3. **Concierge fuera del producto y plantilla ficticia.** La demanda se valida con diagnósticos hechos a mano por un especialista, fuera de Solaris. En el producto entran un operador determinista y una plantilla con datos inventados.

## Decisión

Opción 3, en un sprint de 21 días (19/11 → 09/12):

- **Motor.** Operador `{op: 'linear', terms: [{relation?, attr, coef}], cmp, value}`: calcula Σ coef·valor y lo compara con `value`. No divide, así que no hay división por cero. Cada término usa el atributo del propio objeto o del único objeto en esa relación. Si una relación no es 1:1 o un término no tiene evidencia, el resultado es `sin_evidencia`. Si algún término tiene confianza < 0,80 o está sin validar, y ninguno está en `sin_evidencia`, es `candidato`. El resultado no depende del orden de los términos. Las evidencias son la unión de las de todos los términos.
- **Plantilla `cfo`.** Empresa y banco inventados. Tipos: `CierreMensual`, `ExtractoBancario`, `ReporteSRI`, `Cartera`, `MovimientoBancario` y `ComprobanteSRI`. La conciliación se modela por movimiento: un débito de más de 100 $ exige al menos un `sustentado_por` hacia un comprobante. El `scope` lleva: «no es asesoramiento financiero ni tributario».
- **Prompt, para todos los procesos.** El modelo no calcula importes que no estén literalmente en una evidencia ni que no salgan del motor.
- **Prueba de concepto (P2, se puede cortar).** Un lector determinista de XML del SRI con ficheros ficticios, en una rama que no se fusiona. Mide si la conciliación puede salir del código. Si necesita una dependencia, se anota aquí.
- **Concierge.** Fuera de todo repositorio. A Solaris solo llegan agregados anonimizados, en `raw/research/`.

## Qué desplaza

El arranque de la Fase 4 se retrasa de 6 a 8 días, igual que los pendientes de dev de la auditoría del 14/11.

## Puerta del 09/12

- **3 de 5 empresas pagan** (factura pagada u orden firmada, no intención), **o una firma pide licencia:** nueva ADR para adelantar la Fase 4 hacia extracto + XML del SRI, con Nivel 2 por firma y veto de `security`.
- **Si no:** la plantilla queda como muestra, igual que Compliance ([[ADR-0020]]), y no se profundiza.

## Consecuencias

- El ROADMAP pasa de cinco plantillas a seis. La de este proceso es de muestra.
- La landing no la nombra mientras no se decida en la puerta.
- El dato «5 minutos en lugar de 4 horas» no se usa en ningún material hasta medirlo en el concierge.
- Quedan fuera: documentos reales, exportar el dictamen a PDF, multicliente y las condiciones comerciales de la alianza.

## Abierto para Diego

1. ¿Identificador `cfo` y nombre «Finanzas · Cierre mensual»?
2. ¿Quién revisa los umbrales de las reglas antes de enseñarlas a la socia?
3. Auditoría del 19/11 (`raw/research/2026-11-19_cfo-pyme-procesos-ecuador.md`, sección D): ¿qué correcciones entran antes del 09/12? Recomendado: R-MAR-03 sobre ingresos operativos, regla de bancarización de más de 500 $ y una `action` en R-LIQ-01. El calendario de obligaciones (`days_until`) añade un tipo de objeto: entra solo si el contador lo pide.
