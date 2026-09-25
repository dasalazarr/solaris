# Ficha de transparencia (AI Act, art. 50) — Solaris / Illarium Industrial OS

> **BORRADOR — requiere revisión legal.** Pack de cumplimiento M4-T5, 2026-09-25.
> Etiquetas: **[V]** verificado (en el repo o en fuentes del research marcadas como verificadas) · **[I]** inferencia
> de security, a validar por un jurista · **[DOUE]** depende de fechas o textos del AI Act tras el Digital Omnibus
> que hay que confirmar en el Diario Oficial · **[PENDIENTE]** aún no implementado.

## 1. Qué es el sistema

- **Nombre comercial:** Illarium Industrial OS (nombre interno: Solaris). Proveedor: Illarium (datos societarios
  por completar).
- **Qué hace [V]:** es un copiloto de calidad y conocimiento para plantas industriales. Recibe una reclamación de
  cliente (p. ej. de automoción), busca en la documentación de la planta (8D anteriores, AMFE, planes de control,
  instrucciones) **con los permisos del usuario**, consulta el ERP **en solo lectura** y redacta un **borrador**
  de las disciplinas D1–D4 de un informe 8D, con citas a las fuentes y las consultas al ERP que ha ejecutado.
- **Cómo lo hace [V]:** modelos de lenguaje de terceros a través de OpenRouter, más modelos locales de búsqueda
  (embeddings, reordenación) y OCR. Detalle por tarea en `ficha-modelos.md`.
- **Qué NO hace [V]:** no toma decisiones, no envía nada al cliente, no escribe en el ERP ni en sistemas de
  planta (OT), no actúa sobre maquinaria y no evalúa a personas. Toda salida es un borrador que un humano con el
  rol designado revisa y aprueba.

## 2. Clasificación preliminar [I]

- **No es un sistema de alto riesgo** del Anexo III: asiste en documentación de calidad; no decide sobre empleo,
  acceso a servicios ni evaluación de personas. Research §1.5 llega a la misma conclusión.
- **No es componente de seguridad de un producto regulado** (Anexo I, p. ej. maquinaria): decisión de producto,
  los agentes **nunca** actúan en lazo cerrado sobre OT. Si esto cambiara, entraría en el régimen del Anexo I
  (aplicable, según el research, desde el 2/8/2028 **[DOUE]**).
- **Obligaciones que sí aplican:** transparencia del art. 50 (este documento) y alfabetización del art. 4 (ver
  `nota-alfabetizacion-art4.md`, con una salvedad sobre su estado tras el Omnibus).
- **Rol de cada parte [I]:** Illarium actúa como **proveedor** del sistema; la empresa cliente, como **responsable
  del despliegue**. A confirmar por el jurista, en especial si el cliente personaliza el sistema de forma sustancial.

## 3. El usuario sabe que interactúa con una IA (art. 50.1)

- **Diseño [V]:** en toda pantalla con salida de IA figura el aviso "Sistema de IA. Los borradores, resúmenes e
  hipótesis de esta aplicación los genera un modelo de IA. Revísalos antes de usarlos; nada se envía sin
  aprobación humana." (`app/demo/wireframes/index.html`, requisito R-X-1 de `plan/demo-script.md`).
- **Implementación [PENDIENTE]:** el flag `ai_generated` en la API y el aviso en la interfaz llegan en M4-T3 (F11)
  y M5-T2. Hasta entonces este apartado describe el diseño, no el producto.
- **Nota [I]:** los usuarios son profesionales internos del cliente y el carácter de IA es evidente por el
  contexto; aun así, se muestra siempre (criterio de diseñar para el nivel más exigente plausible, research §3.6
  riesgo 11).

## 4. Qué genera y cómo se marca (art. 50.2)

| Salida | Naturaleza | Marca visible | Marca legible por máquina |
|---|---|---|---|
| Borrador D1–D4 del 8D | Texto sintético, **borrador revisable** | Etiqueta "Generado por IA · revisar antes de usar", modelo usado y estado (borrador / pendiente de aprobación / aprobado) [V diseño, PENDIENTE implementación] | Flag `ai_generated` en la API [PENDIENTE M4-T3]; en el audit, evento `llm_call` con modelo, proveedor y fallback [V] |
| Respuestas citadas (preguntas a la documentación) | Texto sintético con citas | Aviso de IA y chips de cita a documento y página [V diseño] | Flag `ai_generated` [PENDIENTE] |
| Hipótesis de causa (D4) | Texto sintético | Cada hipótesis con estado `probable` / `a verificar` / `descartada` y su evidencia [V requisito M3-T3] | Idem |
| Exportación a plantilla del cliente | Documento aprobado por un humano | Pie "Borrador asistido por IA, revisado y aprobado por <usuario> el <fecha>" [I propuesta] | Metadato en el fichero exportado [I propuesta, PENDIENTE F07] |

- **Trazabilidad [V]:** cada llamada al modelo queda en el registro de auditoría de solo anexar (usuario, rol,
  modelo solicitado y usado, proveedor, uso de fallback, prompt y respuesta redactados o en hash). Ver
  `medidas-tecnicas.md` A3–A4.
- **[DOUE]** El research indica que el art. 50 aplica desde el **2/8/2026**, "aunque algunas fuentes indican
  plazos específicos posteriores para el marcado legible por máquina". Hay que confirmar en el texto publicado
  del Omnibus: (a) la fecha del art. 50.2 para el marcado legible por máquina y si hay periodo transitorio para
  sistemas ya comercializados; (b) si la excepción de "función de asistencia a la edición" o la revisión humana
  editorial afecta a un borrador que siempre revisa y aprueba una persona.

## 5. Limitaciones conocidas [V salvo indicación]

1. **Puede equivocarse o inventar.** Por eso el servidor valida que cada cita corresponde a una fuente
   realmente recuperada y descarta las inventadas (especificación de M2-T8 §4; implementación con `/ask`, M2-T6
   **[PENDIENTE]**). Sin citas válidas, la respuesta es "no encontrado".
2. **Solo sabe lo que el usuario puede ver.** Si un documento está en una carpeta sin permiso para su rol, no
   existe para el sistema: puede dar "no encontrado" aunque el dato exista en la empresa.
3. **Documentos difíciles:** planos, tablas escaneadas y AMFE mal estructurados reducen la calidad (research §3.6
   riesgo 8). El OCR puede leer mal cifras.
4. **Inyección de instrucciones:** una reclamación o documento externo puede contener texto que intenta dar
   órdenes al sistema. Se trata como dato, se marca como sospechoso y se registra; la suite de pruebas completa
   (M4-T4) está **[PENDIENTE]**.
5. **Modelos de terceros:** la calidad y la región de inferencia dependen del modelo y del proveedor (ver
   `ficha-modelos.md`). En el demo **no hay garantía de región UE**; por eso el demo usa solo datos sintéticos.
6. **Calidad aún no medida:** las métricas contra el conjunto de evaluación (precisión de citas, exactitud) se
   publican tras M3-T5 **[PENDIENTE]**.
7. **Idiomas:** diseñado para castellano; otros idiomas (inglés del OEM, euskera) sin evaluar **[I]**.

## 6. Supervisión humana [V diseño, PENDIENTE implementación HITL]

- Nada sale del sistema sin aprobación de un rol designado (en el demo, Calidad). La aprobación es por **API**,
  no solo en la interfaz: avanzar a D5 o exportar sin aprobación devuelve 403 y se registra (M3-T4, F06).
- El usuario puede editar el borrador; se guardan las versiones y quién aprobó cuál.

## 7. Contacto y reclamaciones

- Responsable de cumplimiento: _(por designar; hoy, el fundador)_.
- Canal para reportar un resultado erróneo o un problema de seguridad: _(por definir: correo dedicado)_.

## 8. Preguntas abiertas para revisión legal

1. ¿Confirma el jurista la clasificación "no alto riesgo" y el reparto proveedor / responsable del despliegue?
2. Fechas finales del art. 50 (en especial 50.2) tras el Omnibus publicado en el DOUE.
3. ¿Es suficiente la marca visible más el flag en la API, o hace falta un estándar de marcado (metadatos
   C2PA o similar) para texto?
4. ¿Qué texto exacto debe llevar el documento exportado que llega al OEM?
