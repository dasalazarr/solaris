# Caso de estudio · Compliance: alta y seguimiento de clientes (PBC/FT)

Especificación del caso de muestra de la vertical Compliance. Decisión en [[ADR-0020]]; evidencia en `raw/research/2026-11-10_compliance-vertical.md`. Versión del 2026-11-10, alineada con la plantilla `pbc` del producto (`product/lib/templates/pbc.json` y `product/lib/seeds/pbc.ts`).

**Todo es ficticio:** la asesoría, sus clientes, las personas y los documentos están inventados. Cualquier parecido con una entidad real es casual.

**Lo que este caso no afirma:** no es asesoramiento jurídico, no certifica que nadie cumpla la Ley 10/2010 y no decide si una operación es sospechosa. Comprueba que el expediente de cada cliente contiene lo que el contrato del proceso exige, cita dónde, y deja la decisión a la persona responsable. Las referencias a artículos están pendientes de revisión por alguien cualificado.

## 1. El escenario

**Asesoría Ficticia Albariza (caso de muestra).** Asesoría fiscal y contable de 8 personas. Es sujeto obligado por el art. 2.1 m) de la Ley 10/2010. Constituye sociedades para sus clientes y les lleva la contabilidad.

**El dolor.** Cada alta de cliente exige reunir identificación, titularidad real, propósito de la relación y nivel de riesgo. Hoy vive en carpetas y en una hoja de cálculo. Nadie sabe, sin abrir expediente por expediente, a cuáles les falta algo o les toca revisión. El experto externo lo pregunta una vez al año.

**Por qué ahora.** El reglamento cambió en octubre de 2026 y el europeo se aplica en julio de 2027 (ver la investigación; fechas de fuente secundaria).

## 2. Contrato del proceso

| Campo | Valor |
|---|---|
| Nombre | Proceso de alta y seguimiento de clientes (prevención del blanqueo) |
| Nombre corto | Compliance · Alta de clientes |
| Identificador propuesto | `pbc` |
| Sector | Asesoría fiscal y contable (Caso de muestra) |
| Alcance | Comprueba que cada expediente de cliente tiene identificación, titular real, propósito y revisión al día antes de prestar el servicio, y que las altas de riesgo llevan la autorización que exige el manual |
| Responsable | Representante ante el Servicio Ejecutivo (SEPBLAC), área de Cumplimiento |
| Roles | Representante ante el SEPBLAC · Socio director · Gestor del expediente |

Umbrales:
- Titular real: más del 25 % del capital o de los derechos de voto (R-PBC-02).
- Cliente con responsabilidad pública: autorización del Socio director (R-PBC-03).
- Revisión documental vencida: no se presta servicio nuevo sin requerimiento aprobado (R-PBC-04).

## 3. Ontología

**Cliente** — relaciones: `tiene_titular` → Titular real.

| Atributo | Tipo | Sale de |
|---|---|---|
| `tipo_persona` | texto (`fisica` / `juridica`) | Ficha de alta |
| `identificacion_verificada` | sí/no | Documento de identidad o escritura |
| `proposito_documentado` | sí/no | Ficha de alta |
| `nivel_riesgo` | texto (`bajo` / `medio` / `alto`) | Ficha de alta |
| `es_prp` | sí/no | Declaración de responsabilidad pública |
| `autorizacion_direccion` | sí/no | Acta de autorización |
| `fecha_proxima_revision` | fecha | Ficha de alta |

**Titular real** — sin relaciones.

| Atributo | Tipo | Sale de |
|---|---|---|
| `porcentaje_control` | número | Acta de titularidad real |
| `identificacion_verificada` | sí/no | Documento de identidad |

**Documentos de muestra**

| Id | Documento | Fragmento literal que se cita |
|---|---|---|
| DOC-1 | Manual interno de prevención del blanqueo v2.1 (muestra) | «No se prestará servicio a ningún cliente sin haber comprobado su identidad con un documento fehaciente, sin haber identificado a su titular real cuando sea persona jurídica y sin dejar escrito el propósito de la relación.» |
| DOC-2 | Expediente de alta — CL-0312 | «Persona Ficticia A ostenta el 60 % de las participaciones sociales.» (acta, pág. 3) |
| DOC-3 | Expediente de alta — CL-0327 | «Titularidad real: pendiente de acta notarial.» |
| DOC-4 | Expediente de alta — CL-0341 | «Declaro desempeñar el cargo de concejal desde junio de 2023.» (pág. 2) |
| DOC-5 | Expediente de alta — CL-0298 | «Riesgo asignado: alto. Próxima revisión: 30/09/2026.» |
| DOC-6 | Expediente de alta — CL-0355 | Copia escaneada del documento de identidad, leída con confianza 0,72 |
| DOC-7 | Expediente de alta — CL-0360 | La ficha no recoge el propósito de la relación |

Las reglas citan el manual interno de la asesoría, no la ley: es su contrato. Clientes y personas se llaman «Sociedad Ficticia…» y «Persona Ficticia…», como el resto de la muestra.

## 4. Reglas

Solo con los operadores que ya existen (`product/lib/rules-engine.ts`). Ninguna necesita cambiar el motor.

| Código | Regla | Cuándo aplica | Exige | Si falla | Aprueba | Referencia |
|---|---|---|---|---|---|---|
| R-PBC-01 | Identificación antes de prestar servicio | Siempre | `identificacion_verificada == true` | incumplida | Representante | Ley 10/2010, art. 3 |
| R-PBC-02 | Titular real identificado | `tipo_persona == "juridica"` | `count_related(tiene_titular) >= 1` | incumplida | Representante | Art. 4 |
| R-PBC-03 | Autorización en responsabilidad pública | `es_prp == true` | `autorizacion_direccion == true` | requiere_aprobacion | Socio director | Art. 14 |
| R-PBC-04 | Revisión documental al día | `fecha_proxima_revision` existe | `days_until(fecha_proxima_revision) >= 0` | requiere_aprobacion | Representante | RD 304/2014, art. 11 |
| R-PBC-05 | Propósito de la relación documentado | Siempre | `proposito_documentado == true` | incumplida | Representante | Art. 5 |

**Acciones propuestas** (ninguna sale sin Revisión aprobada, principio 3):
- R-PBC-02 y R-PBC-05: borrador de solicitud de documentación al cliente.
- R-PBC-03: borrador de acta de autorización para la firma del Socio director.
- R-PBC-04: borrador de requerimiento de actualización documental.

**Fuera del proceso, a propósito:** el examen especial y la comunicación por indicio. Son juicio humano y tienen reglas de confidencialidad que no hemos leído.

## 5. Resultado esperado

Con fecha de muestra `SAMPLE_NOW` (03/11/2026). Comprobado contra el motor el 10/11: la matriz del producto da exactamente esta tabla.

| Cliente | Situación | R-01 | R-02 | R-03 | R-04 | R-05 |
|---|---|---|---|---|---|---|
| CL-0312 · sociedad, riesgo medio | Todo en orden | conforme | conforme | no aplica | conforme | conforme |
| CL-0327 · sociedad en constitución | Sin titular real | conforme | **incumplida** | no aplica | conforme | conforme |
| CL-0341 · persona física, concejal | Sin acta de autorización | conforme | no aplica | **requiere_aprobacion** | conforme | conforme |
| CL-0298 · sociedad, riesgo alto | Revisión vencida el 30/09/2026 | conforme | conforme | no aplica | **requiere_aprobacion** | conforme |
| CL-0355 · persona física | Identidad leída del documento, sin validar por una persona | **candidato** | no aplica | no aplica | conforme | conforme |
| CL-0360 · sociedad | La ficha no recoge el propósito | conforme | conforme | no aplica | conforme | **sin_evidencia** |

`candidato` y `sin_evidencia` salen de cómo trata el motor un atributo sin validar o sin evidencia (`rules-engine.ts:84-85`). La tabla se convierte en los tests de oro de la plantilla.

## 6. Preguntas de muestra

| Pregunta | Respuesta esperada | Cita |
|---|---|---|
| ¿Podemos empezar a prestar servicio al cliente CL-0327? | No: persona jurídica sin titular real (R-PBC-02) | DOC-3 y DOC-1 |
| ¿Quién es el titular real de CL-0312 y con qué porcentaje? | Persona Ficticia A, 60 % | DOC-2 |
| ¿Consta la autorización del Socio director para CL-0341? | **No consta** | — |

## 7. Indicadores de muestra

- Expedientes de cliente completos antes de prestar servicio: 83 % (objetivo 100 %).
- Revisiones documentales vencidas: 1 (objetivo 0).

Son cifras de muestra, sin relación con los seis clientes del caso.

## 8. Qué enseña la demo en 90 segundos

1. La matriz: seis clientes, cinco reglas, y de un vistazo cuál está parado y por qué.
2. CL-0327: falta el titular real. La cita lleva a la ficha que dice «pendiente de acta notarial».
3. CL-0341: el Gestor no puede aprobar; el Socio director sí. Queda en el registro.
4. La pregunta sin fuente: «No consta».

## 9. Riesgos del caso

- **Datos personales en un piloto real.** Identidad, titularidad y condición de responsabilidad pública. Exige Nivel 2, encargo de tratamiento y veto de `security`. En la demo no hay ninguno real.
- **Parecer asesoramiento.** Las reglas son el contrato que fija la asesoría, no una lectura oficial de la ley. La interfaz debe decirlo.
- **Competencia.** Ya hay software de PBC para despachos. Lo nuestro es la cita al documento y la aprobación con rastro, no el manual ni la verificación de identidad.
