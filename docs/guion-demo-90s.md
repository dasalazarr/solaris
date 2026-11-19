# Guion de la demostración · 90 segundos

Para el tramo central de la llamada de 30 minutos, con el pack Compras y datos de muestra. Sigue [[ADR-0010]]: no decir nada que la pantalla no pueda respaldar. Requiere illariumcore#9 a #12 publicados.

**Antes de empezar:** diga que la empresa es ficticia y que la demo corre en la nube. Con tus documentos reales, Solaris se instalaría en tu organización; esa instalación se diseña con el primer piloto.

## 1. Preguntar (0–25 s)

**En pantalla:** la pregunta sobre PC-0412 ya está cargada. Pulse la cita [2].

> «Un pedido de 18.450 € está retenido. En vez de buscar entre PDFs y correos, se lo preguntamos al proceso. Solaris responde y enseña el párrafo exacto de la política: lo puede comprobar en un clic. Y lo importante está debajo del dictamen: la regla R-03 pide la aprobación de Dirección financiera. Esa regla no la decide el modelo, la evalúa el código.»

## 2. Explorar (25–40 s)

**En pantalla:** Documentos → Objetos → PC-0412.

> «Detrás no hay un chat suelto. Hay cinco documentos y los objetos que respaldan: pedido, proveedor, factura. Cada dato enseña su fuente, y el plazo de 48 horas que alguien comentó por teléfono sale “sin fuente”: el motor no lo usa. Fíjese también en R-01: sale “no evaluada”. Solaris no da por cumplido lo que no ha comprobado.»

## 3. Huecos (40–60 s)

**En pantalla:** la matriz de reglas y objetos. Señale las celdas de PC-0419 y «Datos por validar».

> «No hace falta preguntar para encontrar problemas. Al abrir el proceso, el motor cruza cada regla con cada objeto. Aquí falta una aprobación; aquí, un certificado caducó el 12 de octubre; y este mismo pedido no tiene evidencia de las tres ofertas. El recargo de la factura va aparte: es una lectura dudosa, y no cuenta hasta que una persona la valide.»

## 4. Revisar (60–90 s)

**En pantalla:** cambie a «Solicitante» y enseñe el aviso. Vuelva a Dirección financiera, edite una palabra del borrador y apruebe. Vuelva a Huecos: el contador baja.

> «Aquí decide una persona. Si actúo como solicitante, no puedo aprobar: la regla exige otro rol. Como Dirección financiera, reviso el borrador, lo edito y apruebo. Solaris no envía nada por su cuenta. La decisión queda en el registro con quién, qué versión y qué evidencia, y el hueco se cierra.»

**Si preguntan por el registro:** «En esta demo se conserva durante la sesión y se puede exportar. El registro persistente llega con el piloto.»

## Qué no decir

| Tentación | Por qué no | Qué decir |
|---|---|---|
| «Registro inmutable», «huella criptográfica» | Es estado de la sesión e identificadores de muestra | «Queda registrado y se puede exportar» |
| «Radar continuo, en segundo plano» | Se evalúa al abrir el proceso | «Al abrir el proceso, el motor cruza…» |
| «Pydantic», «100 % determinista» | Lo primero no corre; el modelo redacta | «El código decide; el modelo redacta» |
| «Se instala en VPC», «se conecta a su ERP» | Ni comprometido ni construido | «Lo vemos en el diagnóstico» |
| «Clientes», «ahorro», «ROI» | No hay piloto medido; los KPI son de muestra | Nada, o «eso lo medimos en el piloto» |

## Comprobar el día antes

- [ ] Local o preview con los PR del producto: el recorrido entero funciona.
- [ ] El espacio de demo tiene un código vigente.
- [ ] Sin `GEMINI_API_KEY` la pregunta libre responde «No puedo responder ahora»: use las preguntas predefinidas.
