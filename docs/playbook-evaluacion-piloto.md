# Playbook · Evaluación del piloto Jurídico y mercantil

Guía para obtener y registrar, con el despacho, la información que falta en el PRD de producto (§8). Se usa en la sesión de diagnóstico y otra vez antes de instalar el Nivel 2.

**El listón ya está fijado (PRD §5):** 1 piloto de Nivel 2 convertido a contrato de pago, con ≥ 95 % de respuestas con cita verificada por el cliente y 0 afirmaciones sin fuente presentadas como hecho. Este playbook define todo lo demás.

## Reglas antes de empezar

- **Nada real en el repositorio.** Ni nombres del despacho, ni de sus clientes, ni fragmentos de expedientes. En las actas se usa «Despacho A», «socio responsable», «expediente 1». Los originales se quedan en el despacho o en el gestor privado de Illarium.
- **Preguntas abiertas primero, opciones después.** Lo que importa es su forma de describir el problema, no que confirmen nuestras hipótesis.
- **Cifras, no adjetivos.** «Tardamos mucho» no sirve; «unas 3 h por contrato» sí.
- **Al terminar:** se vuelcan las respuestas al PRD §8. Si algo implica elegir entre alternativas, se escribe una nota en `docs/decisiones/`.

---

## Bloque 1 · Aceptación por superficie

Objetivo: para cada superficie, una tarea real que el socio debe poder hacer y el criterio con el que la dará por buena.

### Preguntar (respuesta con cita)

- ¿Qué preguntas se hacen hoy sobre un contrato o un expediente que obligan a releerlo entero?
- Cuando alguien del despacho responde una de esas preguntas, ¿cómo comprueba usted que es correcta?
- ¿Qué tendría que ver en pantalla para fiarse de una respuesta sin abrir el documento?

**Tarea de prueba propuesta:** 20 preguntas reales sobre 5 contratos del despacho, formuladas por el socio.
**Aceptado si:** ≥ 95 % con cita correcta (documento, página, fragmento literal), y lo que no consta aparece como «sin fuente».

### Explorar (objetos, evidencias, ingesta)

- ¿Qué datos de un contrato necesita localizar siempre? (partes, fechas, importes, garantías, vencimientos, cláusulas concretas)
- ¿Cuántos documentos tiene un expediente típico? ¿Qué parte son escaneados?
- ¿Quién validaría un dato que la máquina no tiene claro (confianza < 0,80)? ¿Cuánto tiempo puede dedicarle a la semana?

**Tarea de prueba propuesta:** ingerir un expediente completo y revisar la cola de candidatos.
**Aceptado si:** los datos clave salen con su evidencia y la cola de validación cabe en el tiempo que el despacho está dispuesto a dedicar.

### Huecos (reglas deterministas)

- ¿Qué comprueba siempre antes de dar por bueno un contrato o un anexo? (firmas, poderes, garantías vigentes, plazos)
- ¿Qué error u omisión le ha costado más en los últimos dos años?
- ¿Esas comprobaciones están escritas en algún sitio (checklist, manual interno) o viven en la cabeza de alguien?

**Tarea de prueba propuesta:** convertir 5–10 de esas comprobaciones en reglas y ejecutarlas sobre expedientes ya cerrados, donde el resultado se conoce.
**Aceptado si:** las reglas detectan los huecos conocidos y no generan falsas alarmas que el socio considere ruido.

### Revisar (aprobación humana y registro)

- ¿Quién puede aprobar qué en el despacho? (socio, asociado, administración)
- ¿Qué tiene que quedar registrado de una decisión para que sirva ante el cliente o ante una auditoría?
- ¿En qué formato necesita el registro? (CSV, PDF, integración con su gestor)

**Tarea de prueba propuesta:** recorrer una aprobación completa: borrador, edición, aprobación y exportación del registro.
**Aceptado si:** el registro exportado sirve tal cual para su archivo y nada se ejecuta sin la aprobación del rol que corresponde.

### Tabla para rellenar

| Superficie | Tarea real acordada | Criterio de aceptación | Quién valida | Fecha |
|---|---|---|---|---|
| Preguntar | | | | |
| Explorar | | | | |
| Huecos | | | | |
| Revisar | | | | |

---

## Bloque 2 · La métrica que hace pagar

Objetivo: una métrica con línea base de hoy, medible durante el piloto y con un umbral acordado. Sin línea base no hay forma de demostrar el ahorro.

### Línea base (cómo trabajan hoy)

- ¿Cuántos contratos o expedientes revisan al mes?
- ¿Cuánto tarda una revisión típica? ¿Y una complicada?
- ¿Cuántas veces al año aparece un error u omisión después de cerrar? ¿Qué cuesta cada uno (tiempo, dinero, relación con el cliente)?
- Si mañana revisaran el doble de contratos con el mismo equipo, ¿qué cambiaría para el despacho?

### Métricas candidatas

| Métrica | Cómo se mide en el piloto | Línea base | Umbral acordado |
|---|---|---|---|
| Horas por revisión | Cronometrar N revisiones con y sin Solaris | | |
| Huecos detectados confirmados | Huecos señalados por las reglas que el socio confirma como reales | | |
| Tiempo hasta la respuesta citada | Desde la pregunta hasta la respuesta con cita verificada | | |
| Errores que llegan al cliente | Omisiones detectadas después de cerrar, antes y durante el piloto | | |

**Pregunta de cierre:** «Si al final del piloto vemos [métrica] en [umbral], ¿firmamos?». Se apunta la respuesta literal.

---

## Bloque 3 · Qué queda fuera de v1

Objetivo: decidir por adelantado qué se dice que no y por qué, para que el piloto no se convierta en un desarrollo a medida.

### Peticiones probables y respuesta por defecto

| Petición | Respuesta por defecto | Motivo |
|---|---|---|
| Que Solaris envíe, firme o presente documentos por su cuenta | No | Principio 3: ninguna acción externa sin Revisión aprobada |
| Usarlo con expedientes reales desde la nube | No | Principio 4 y secreto profesional: los documentos reales solo en Nivel 2 |
| Un modelo distinto por tipo de asunto | Fuera de v1 | Visión v2 («modelos por proceso»), necesita una decisión registrada |
| Cruzar información entre áreas del despacho | Fuera de v1 | Visión v2 («federación entre procesos») |
| Integración con su gestor documental o de expedientes | Por decidir | Depende de cuál usen; valorar como importación, no como sincronización |
| Firma electrónica integrada | Por decidir | Solo si bloquea el piloto; si no, fuera de v1 |

### Tabla para rellenar

| Petición del despacho | Decisión (dentro / fuera / por decidir) | Motivo | Nota de decisión |
|---|---|---|---|
| | | | |

---

## Protocolo de verificación de citas (para el ≥ 95 %)

1. El socio redacta las preguntas. Nosotros no las elegimos, para no sesgar la muestra.
2. Muestra mínima: 20 preguntas en la evaluación inicial y 50 en la de cierre del piloto.
3. Para cada respuesta, el socio marca:
   - **Correcta:** la cita existe, está en esa página y respalda la afirmación.
   - **Incorrecta:** la cita no existe, está en otro sitio o no respalda la afirmación.
   - **Sin fuente correcta:** el sistema dijo «sin fuente» y efectivamente no consta.
   - **Sin fuente incorrecta:** el sistema dijo «sin fuente» pero sí constaba.
4. **% de citas verificadas** = (correctas + sin fuente correctas) / total.
5. **Afirmaciones sin fuente presentadas como hecho:** toda afirmación factual sin cita cuenta como fallo grave. El objetivo es 0.

---

## Plantilla de acta

```markdown
# Acta · Evaluación piloto · Despacho A · AAAA-MM-DD

Asistentes (roles, sin nombres): socio responsable, …
Duración:

## Bloque 1 · Aceptación por superficie
(tabla rellena)

## Bloque 2 · Métrica de pago
Línea base: …
Métrica elegida: …  Umbral: …
Respuesta literal a «¿firmamos si…?»: …

## Bloque 3 · Fuera de v1
(tabla rellena)

## Verificación de citas (si se hizo prueba)
Preguntas: N · Correctas: … · Sin fuente correctas: … · % verificado: …
Afirmaciones sin fuente presentadas como hecho: …

## Decisiones y siguientes pasos
- …
```

Las actas con datos del despacho no se guardan en este repositorio. Aquí solo se vuelcan las conclusiones anonimizadas al PRD §8.
