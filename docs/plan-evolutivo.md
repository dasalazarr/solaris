# Plan evolutivo de Solaris

De demo de muestra a un To Be funcional y parametrizable. Decisión en [[ADR-0015]]; criterios de interfaz en [`spec-experiencia.md`](spec-experiencia.md). Versión del 2026-11-07. Las duraciones son estimaciones, para una persona con agentes.

## Dónde estamos

Comprobado en código (110 tests) y recorriendo producción el 07/11, en escritorio y a 390 px.

| Hace falta | Estado real | Hueco |
|---|---|---|
| Leer los documentos del expediente | Formulario simulado y rotulado | **Crítico** |
| Citar la página exacta | Cita verificada contra fragmentos de texto; no hay PDF | **Crítico** |
| Responder a una pregunta libre | En producción responde «No puedo responder ahora» | **Crítico para mostrar** |
| Detectar huecos con reglas | Motor real, sin condiciones entre objetos | Medio |
| Aprobación con rastro | Rol elegido en el cliente; se pierde al recargar | **Crítico para un piloto** |
| Crear un proceso sin programar | Cada proceso es código | **Crítico** |
| Prueba con expedientes propios | Imposible hoy | **Crítico** |
| Instalación local | No existe; se presenta como compromiso | Alto, se decide con evidencia |
| Medir uso y ahorro | Sin telemetría; KPI de muestra | Medio |

## Fases

Cada fase es un PR único a `main` por repositorio ([[PAT-005]]), que fusiona Diego.

| Fase | Resultado | Duración |
|---|---|---|
| 0 · Verdad y orden | ADR, spec, plan y trabajo pendiente en orden | Hecha el 07/11, salvo fusión |
| 1 · Mostrar | La experiencia del vídeo sobre el producto actual | ≈2 semanas |
| 2 · Núcleo persistente | Lo aprobado se guarda y el servidor impone el rol | ≈1,5 semanas |
| 3 · Parametrización | Un proceso nuevo sin programar | ≈2 semanas |
| 4 · Documentos reales | Del PDF a la decisión, con cita a la página | ≈2 semanas |
| 5 · Listo para probar | Evaluación, seguridad y material | ≈1 semana |

### Fase 1 · Mostrar
- Dividir `SolarisWorkspace.tsx` en marco y una pieza por superficie: el rediseño toca las cuatro.
- Aplicar [`spec-experiencia.md`](spec-experiencia.md): navegación, recorrido, matriz, revisión y registro.
- Pregunta libre con clave y tope de gasto, o sin campo en la demo. No puede quedar como callejón sin salida.
- «Reiniciar demo», sin pedir datos del onboarding que no se usan.
- Accesibilidad: `htmlFor`, nombre en el `select`, foco visible, teclado en la matriz.
- Veracidad:
  - El CSV respeta el filtro y hay hoja de impresión para el PDF.
  - Se resuelven `handleSwitchPack` y los errores silenciados de `app/page.tsx`.
  - Se corrigen la mezcla tú/usted, `.env.example` y los relojes del registro.
  - Se revisan las citas de IFS (§4.6 parece errónea; el límite de 6,0 min está sin contrastar).
- Eventos anónimos del recorrido, con la política de privacidad actualizada.
- `landing/src/components/ProductWindow.tsx` y `video/src/ventana.tsx` reflejan el menú real, y el vídeo se vuelve a renderizar.

### Fase 2 · Núcleo persistente
- `Store` según `nivel2-preguntas-y-contrato.md`. Propuesta: un fichero SQLite por espacio, con aislamiento físico, sin filtro por cliente y el mismo artefacto en nube y en local.
- Revisiones y registro en la API; registro de solo anexar; idempotencia por `step_id` + `args_hash`.
- Código por persona con rol en la sesión firmada; el servidor rechaza a quien no lo tenga.
- Contenedor en Europa y dominio propio, porque Vercel no sirve para SQLite en disco.

### Fase 3 · Parametrización ([[F07]], [[H03]])
- Definición de proceso como JSON versionado y validado: contrato, tipos de objeto y atributos, tipos de documento, roles, reglas y acciones.
- Compras, Jurídico, IFS y EUDR migran a plantillas. Compras debe dar los mismos resultados.
- Motor con operadores fijos para comparar con un objeto relacionado y contar relacionados.
- Superficie «Contrato»: contrato, KPI y formularios, con el efecto en la matriz antes de publicar.
- `policy_hash` real, hash del JSON canónico; cada decisión conserva su versión.

**Puerta al acabar:** con las entrevistas, Diego decide primer piloto, prioridad de OCR y Nivel 2 local, y si la Fase 4 sigue como está.

### Fase 4 · Documentos reales
- `Ingestor`: PDF con texto nativo por expediente, texto por página y SHA-256 real. Un escaneo se marca «no legible».
- El modelo propone atributos con página y cita literal; el servidor descarta lo no literal; todo queda como candidato hasta que una persona lo valide.
- Visor de PDF real con el fragmento resaltado.
- Pregunta libre con búsqueda simple por página, sin base vectorial.
- Reloj real en espacios reales; `SAMPLE_NOW` en la muestra.
- El entorno dice qué instancia es y si el texto va a un modelo en la nube.

### Fase 5 · Listo para probar
- 20 expedientes ficticios con resultado esperado, en `raw/eval-runs/`.
- Revisión de `security`, con veto. Ningún documento real hasta pasarla y tener acuerdo de confidencialidad y encargo de tratamiento revisados.
- Guion de demo y de prueba; vídeo y landing al día.

### En paralelo · Entrevistas
De 5 a 10, desde el final de la Fase 1, con las preguntas de la [síntesis](../raw/research/2026-11-07_estudio-mercado-sintesis.md) y [`playbook-evaluacion-piloto.md`](playbook-evaluacion-piloto.md).

## Criterios de «listo»

| Modo | Se cumple cuando |
|---|---|
| **Mostrar** | Alguien que no es Diego hace la demo con el guion, en móvil y escritorio, y cada plano del vídeo tiene su pantalla real |
| **Usar** | Lo aprobado sigue ahí al recargar y el rol lo impone el servidor |
| **Parametrizar** | Alguien sin programar crea un proceso nuevo en menos de 2 horas |
| **Probar** | Un expediente de PDF ficticios va de la carga a la decisión registrada, con cita a la página real |

## Qué no se construye
Conectores ERP/CRM, OCR, instalador y modelo local (hasta la puerta), portal de proveedores, sistema multicliente, SSO, base vectorial, editor visual de grafos, profundizar IFS o EUDR como verticales.

## Verificación
- **Cada PR:** tests, lint y build; navegador a 375 px y escritorio; `python3 scripts/wiki_lint.py`.
- **Experiencia:** cada plano del vídeo frente a su pantalla, en 16:9 y 4:5.
- **Vídeo:** `npm run gate` en `video/`.
- **Regresión de oro:** Compras migrado deja PC-0412 con R-03 `requiere_aprobacion` y R-02 `conforme`, los mismos 3 huecos y PC-0419 sin evidencia de R-02.
- **Servidor:** un rol incorrecto se rechaza por API; dos envíos con la misma clave dejan una sola entrada.
- **Coherencia:** landing, vídeo y producto dicen lo mismo al cerrar cada fase.
