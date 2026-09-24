"""8 instrucciones de trabajo (produccion/instrucciones-trabajo). DATOS SINTÉTICOS (ADR-0004).

Formatos: PDF de texto (reportlab, invariant), DOCX y un PDF "escaneado" (imágenes rotadas y con ruido, sin capa de texto).
"""
from __future__ import annotations

import random
from pathlib import Path

import reportlab
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import ListFlowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from common import COMPANY, DOCS, FIXED_DT, Doc

FOLDER = "produccion/instrucciones-trabajo"
_FONT_DIR = Path(reportlab.__file__).parent / "fonts"
pdfmetrics.registerFont(TTFont("Vera", str(_FONT_DIR / "Vera.ttf")))
pdfmetrics.registerFont(TTFont("VeraBd", str(_FONT_DIR / "VeraBd.ttf")))
pdfmetrics.registerFont(TTFont("VeraIt", str(_FONT_DIR / "VeraIt.ttf")))
pdfmetrics.registerFont(TTFont("VeraBI", str(_FONT_DIR / "VeraBI.ttf")))
pdfmetrics.registerFontFamily("Vera", normal="Vera", bold="VeraBd", italic="VeraIt", boldItalic="VeraBI")

# ----------------------------------------------------------------------------- contenido
# Cada IT: bloques = (tipo, contenido). tipos: h, p, list, table, pb (salto de página)

IT_CR01 = dict(
    code="IT-L2-CR01-03", version="v3", date="03/03/2025", fmt="pdf",
    title="Soldadura MIG robotizada en la célula CR-01 (AR-1003 / AR-1004)", refs=["AR-1003", "AR-1004"],
    roles=("O. Zabaleta (Ingeniería L2)", "X. Urrutia (Producción L2)", "I. Etxeberria (Calidad)"),
    blocks=[
        ("h", "1. Objeto"),
        ("p", "Definir el arranque, la operación, el mantenimiento de primer nivel y los autocontroles de la célula robotizada de "
              "soldadura MIG CR-01 para los soportes de la bandeja de baterías AR-1003 (LH) y AR-1004 (RH). La resistencia de la "
              "soldadura es una característica crítica (CC) del cliente OEM Norte."),
        ("h", "2. Alcance"),
        ("p", "Célula CR-01 (robot de 6 ejes, fuente de soldadura pulsada 400 A, alimentador de hilo, escariador de boquilla y mesa "
              "giratoria con dos útiles). Programas P12 (AR-1003) y P14 (AR-1004). Aplica a todos los turnos que operan la célula."),
        ("h", "3. Responsabilidades"),
        ("list", ["Operario de célula: arranque, carga y descarga, cambio de consumibles, autocontrol y registros.",
                  "Jefe de turno: verificar el checklist de arranque y firmar el registro de cambio de boquillas.",
                  "Técnico L2 (turnos de mañana y tarde): ajustes de trayectoria y averías de la fuente o del alimentador.",
                  "Ingeniería de procesos L2: único nivel autorizado para modificar parámetros (consola bloqueada con contraseña)."]),
        ("h", "4. Seguridad y EPI"),
        ("list", ["Pantalla de soldadura DIN 11 al acceder a la célula con arco; guantes de soldador; ropa ignífuga.",
                  "Acceso a la célula solo con el robot en posición de servicio y la barrera óptica en modo mantenimiento.",
                  "La boquilla y el tubo de contacto están calientes: usar pinzas de cambio y guantes."]),
        ("pb", None),
        ("h", "5. Operativa"),
        ("h2", "5.1 Arranque de turno (checklist de célula)"),
        ("table", ["Punto", "Valor / criterio", "Cómo"],
         [["Programa activo", "P12 (AR-1003) / P14 (AR-1004)", "Pantalla principal"],
          ["Velocidad de hilo (WFS)", "9,4 ± 0,3 m/min", "Consola (solo lectura)"],
          ["Tensión de arco", "23,5 ± 0,5 V", "Consola (solo lectura)"],
          ["Velocidad de soldadura", "0,55 m/min", "Consola (solo lectura)"],
          ["Gas M21 (Ar 82 / CO2 18)", "14–18 l/min en boquilla", "Caudalímetro de boquilla"],
          ["Escariador", "Ciclo cada 20 piezas activo", "Contador en pantalla"],
          ["Antiproyecciones", "Depósito > 1/4", "Visual"]]),
        ("p", "Si algún valor está fuera de criterio: no arrancar y avisar al jefe de turno y a Ingeniería L2."),
        ("h2", "5.2 Cambio de boquilla y tubo de contacto"),
        ("p", "<b>Frecuencia: cada 8 h.</b> El cambio se realiza al inicio del turno de mañana (06:00) y al inicio del turno de "
              "tarde (14:00), antes de soldar la primera pieza del turno. Se registra en REG-L2-CR01-01 (fecha, turno, hora, "
              "operario y firma del jefe de turno)."),
        ("p", "Además, cambiar la boquilla y el tubo de contacto siempre que se observe: salpicadura excesiva, arco inestable o "
              "ruidoso, hilo pegado en el tubo o cordón irregular."),
        ("list", ["1. Llevar el robot a la posición de servicio (programa P99) y activar el modo mantenimiento.",
                  "2. Cortar el hilo a 15 mm de la boquilla.",
                  "3. Retirar la boquilla de gas con la pinza de cambio.",
                  "4. Desenroscar el tubo de contacto (Ø1,0 mm, CuCrZr). Desecharlo en el contenedor de cobre.",
                  "5. Montar un tubo de contacto nuevo del kit de la célula; apriete a mano + 1/4 de vuelta con la llave.",
                  "6. Montar una boquilla nueva; comprobar que el tubo queda 2 mm hacia dentro.",
                  "7. Ejecutar el programa P98 (verificación de TCP). Desviación admisible ≤ 0,5 mm.",
                  "8. Registrar el cambio en REG-L2-CR01-01."]),
        ("pb", None),
        ("h2", "5.3 Cambio de bobina de hilo"),
        ("list", ["Usar solo hilo G3Si1 Ø1,0 mm homologado (proveedor S-GOIE) en bidón de 250 kg.",
                  "Anotar el número de lote del hilo en REG-L2-CR01-01 (motivo 'Cambio de lote').",
                  "Pasar el hilo por el conducto y verificar la presión de los rodillos de arrastre (marca 2,5).",
                  "El programa de soldadura no se modifica en el cambio de bobina."]),
        ("h2", "5.4 Ciclo de producción"),
        ("list", ["Cargar las piezas estampadas en el útil (lado A) y comprobar las bridas neumáticas y los detectores de presencia.",
                  "Pulsar ciclo. Mientras el robot suelda el lado B, descargar y cargar el lado A.",
                  "Cada 20 piezas el robot ejecuta el escariado de la boquilla automáticamente."]),
        ("h2", "5.5 Autocontrol visual del cordón"),
        ("p", "Inspeccionar el 100 % de los cordones W1 y W2: sin grietas, poros, mordeduras ni cráteres en el final. Longitud de W2: "
              "45 ± 3 mm. Piezas dudosas: a la caja roja y avisar al jefe de turno."),
        ("pb", None),
        ("h", "6. Controles de calidad"),
        ("table", ["Control", "Frecuencia", "Responsable", "Registro"],
         [["Ensayo de cincel", "1 pieza por turno", "Operario", "Hoja de control L2"],
          ["Arrancamiento (≥ 18 kN; aviso 20 kN)", "3 piezas por lote", "Laboratorio", "Registro de laboratorio"],
          ["Macrografía W2 (penetración ≥ 1,0 mm)", "1 pieza por semana y programa", "Laboratorio", "Registro de laboratorio"]]),
        ("h", "7. Plan de reacción"),
        ("list", ["Grieta visible o fallo del ensayo de cincel: parar la célula, bloquear las piezas desde el último control OK y avisar al jefe de turno y a Calidad.",
                  "Arrancamiento < 20 kN: 5 piezas adicionales + macrografía. Arrancamiento < 18 kN: bloquear el lote y abrir 8D.",
                  "Parámetros fuera de ventana: no producir; avisar a Ingeniería L2."]),
        ("h", "8. Registros"),
        ("list", ["REG-L2-CR01-01 Registro de cambios de boquilla, tubo de contacto y bobina (en la célula).",
                  "Checklist de arranque de CR-01 (en la célula, archivo mensual en Producción L2).",
                  "Hoja de control L2."]),
        ("h", "9. Historial de cambios"),
        ("table", ["Versión", "Fecha", "Cambio"],
         [["v1", "20/06/2023", "Emisión"],
          ["v2", "28/05/2024", "Bloqueo de parámetros y checklist de arranque de turno (reclamación de cliente)"],
          ["v3", "03/03/2025", "Apartado 5.2: cambio de boquilla y tubo de contacto cada 8 h y registro REG-L2-CR01-01 (reclamación de cliente)"]]),
    ],
)

IT_CR02 = dict(
    code="IT-L2-CR02-02", version="v2", date="24/03/2025", fmt="pdf",
    title="Soldadura MIG robotizada y estación de tuercas en la célula CR-02 (AR-1005 / AR-1009 / AR-1010)",
    refs=["AR-1005", "AR-1009", "AR-1010"],
    roles=("O. Zabaleta (Ingeniería L2)", "X. Urrutia (Producción L2)", "I. Etxeberria (Calidad)"),
    blocks=[
        ("h", "1. Objeto y alcance"),
        ("p", "Operación de la célula CR-02: soldadura MIG de AR-1005, AR-1009 y AR-1010 y soldadura por proyección de la tuerca M8 "
              "de AR-1010 (alimentador AT-01). Aplica a los tres turnos."),
        ("h", "2. Arranque de turno"),
        ("table", ["Programa", "Referencia", "WFS (m/min)", "Tensión (V)", "Gas (l/min)"],
         [["P21", "AR-1005", "8,8 ± 0,3", "22,5 ± 0,5", "14–18"], ["P23", "AR-1009", "6,5 ± 0,3", "19,0 ± 0,5", "12–16"],
          ["P25", "AR-1010", "8,2 ± 0,3", "22,0 ± 0,5", "14–18"]]),
        ("p", "Verificar los parámetros en consola (bloqueada) y firmar el checklist de arranque."),
        ("h", "3. Cambio de boquilla y tubo de contacto"),
        ("p", "<b>Frecuencia: al inicio de cada turno (06:00, 14:00 y 22:00)</b> y siempre que haya salpicadura excesiva o arco "
              "inestable. Registrar en la hoja de consumibles de CR-02."),
        ("list", ["Robot en posición de servicio (P99).", "Cortar hilo, retirar boquilla y tubo, montar kit nuevo.", "Verificar TCP con el programa P98."]),
        ("pb", None),
        ("h", "4. Estación de tuercas (AR-1010)"),
        ("list", ["Tuerca M8 Zn-Ni de S-BIDA; solo lotes liberados por Calidad (etiqueta verde con espesor XRF).",
                  "Comprobar la alineación del electrodo con la galga tras cualquier intervención de mantenimiento.",
                  "Par de arrancamiento: 3 piezas cada 2 h (≥ 40 Nm) y primera pieza tras mantenimiento."]),
        ("h", "5. Autocontrol y plan de reacción"),
        ("list", ["Visual 100 % de cordones y tuerca.", "Tuerca que gira o par < 40 Nm: parar, bloquear desde el último control OK, avisar a Calidad.",
                  "Macrografía semanal por programa (laboratorio)."]),
        ("h", "6. Historial"),
        ("table", ["Versión", "Fecha", "Cambio"],
         [["v1", "12/09/2023", "Emisión"], ["v2", "24/03/2025", "Cambio de boquilla y tubo de contacto al inicio de cada turno (extensión de la mejora de CR-01)"]]),
    ],
)

IT_SP01 = dict(
    code="IT-L2-SP01-02", version="v5", date="02/03/2026", fmt="docx",
    title="Soldadura por puntos y proyección con la pinza SP-01 (AR-1006 / AR-1011)", refs=["AR-1006", "AR-1011"],
    roles=("O. Zabaleta (Ingeniería L2)", "X. Urrutia (Producción L2)", "I. Etxeberria (Calidad)"),
    blocks=[
        ("h", "1. Objeto y alcance"),
        ("p", "Operación de la pinza de soldadura por resistencia SP-01: puntos de soldadura de AR-1011 y proyección de la tuerca M8 de AR-1006."),
        ("h", "2. Arranque de turno"),
        ("list", ["Comprobar el agua de refrigeración (caudal ≥ 6 l/min, temperatura ≤ 30 °C).",
                  "Comprobar el diámetro de la cara del electrodo con la plantilla: 6,0 mm (máx. 7,0 mm).",
                  "Verificar que el rectificador de electrodos (tip dresser) no tiene alarma. La anulación de la alarma requiere llave de mantenimiento.",
                  "Primera pieza: ensayo de cincel (AR-1011) o par de arrancamiento (AR-1006)."]),
        ("h", "3. Parámetros"),
        ("table", ["Programa", "Referencia", "Corriente (kA)", "Tiempo (ciclos)", "Fuerza (kN)"],
         [["S11", "AR-1011 puntos S1–S4", "9,5 ± 0,3", "12", "3,2"], ["T06", "AR-1006 tuerca M8", "11,0 ± 0,4", "8", "4,5"]]),
        ("h", "4. Mantenimiento de primer nivel"),
        ("list", ["Rectificado de electrodos automático cada 150 puntos.", "Cambio de caps cada 3.000 puntos o si la cara supera 7,0 mm.",
                  "Tras cualquier intervención en electrodos: galga de alineación + prueba de primera pieza antes de liberar."]),
        ("h", "5. Controles"),
        ("table", ["Control", "Frecuencia"],
         [["Diámetro de cara del electrodo", "Cada 2 h"], ["Ensayo de cincel AR-1011", "1 pieza cada 2 h"],
          ["Par de arrancamiento AR-1006 (≥ 40 Nm)", "3 piezas cada 2 h"]]),
        ("h", "6. Historial"),
        ("table", ["Versión", "Fecha", "Cambio"],
         [["v3", "20/12/2024", "Alineación de electrodos y prueba de primera pieza tras mantenimiento"],
          ["v4", "25/07/2025", "Par de arrancamiento cada 2 h; tuercas con XRF"],
          ["v5", "02/03/2026", "Plantilla de diámetro de cara cada 2 h; bloqueo de la anulación de alarma del rectificador"]]),
    ],
)

IT_PR250 = dict(
    code="IT-L1-PR250-04", version="v3", date="12/05/2026", fmt="scan",
    title="Montaje de matrices y aprobación de primera pieza en la prensa PR-250", refs=["AR-1001", "AR-1006", "AR-1007", "AR-1008", "AR-1009", "AR-1011", "AR-1012"],
    roles=("U. Ezkurra (Matricería)", "J. Elizalde (Producción L1)", "I. Etxeberria (Calidad)"),
    blocks=[
        ("h", "1. OBJETO"),
        ("p", "Definir el cambio de matriz en la prensa progresiva PR-250 (250 t) y la aprobación de la primera pieza antes de producir."),
        ("h", "2. ALCANCE"),
        ("p", "Matrices MT-01, MT-06, MT-07, MT-08, MT-09, MT-11 y MT-12. Todos los turnos."),
        ("h", "3. PREPARACIÓN"),
        ("list", ["Comprobar en el tablero que la matriz está 'APTA' (etiqueta verde de matricería).",
                  "Comprobar el contador de golpes de la matriz frente al plan de afilado PROC-L1-AFILADO-01.",
                  "Preparar calzas, bridas y el útil de control de la referencia."]),
        ("h", "4. MONTAJE"),
        ("list", ["Colocar la matriz contra los pasadores de posicionado del portamatrices (no usar los topes antiguos).",
                  "Embridar con par de 250 Nm en cruz.", "Ajustar la altura de cierre según la ficha de la matriz.",
                  "CONECTAR los sensores de protección de matriz (alimentación de banda y expulsión) y probarlos: la prensa no debe dar golpe sin señal.",
                  "Ajustar el alimentador: paso y liberación de pilotos."]),
        ("pb", None),
        ("h", "5. APROBACIÓN DE PRIMERA PIEZA"),
        ("list", ["Estampar 5 piezas en golpe a golpe.", "Medir la 5ª pieza en el útil de control y las cotas SC/CC de la ficha.",
                  "Turno de mañana y tarde: aprueba el técnico de Calidad.",
                  "Turno de noche: aprueba el jefe de turno con el útil de control y adjunta foto en el registro de montaje.",
                  "No embalar ninguna pieza hasta la aprobación."]),
        ("h", "6. DURANTE LA PRODUCCIÓN"),
        ("list", ["Útil de control cada 2 h y después de cada cambio de bobina.",
                  "AR-1007: rebaba y diámetro según IT-L1-MT07-01.", "Anotar los golpes al final del turno."]),
        ("h", "7. HISTORIAL"),
        ("table", ["Versión", "Fecha", "Cambio"],
         [["v1", "05/2023", "Emisión"], ["v2", "09/2025", "Conexión y prueba de sensores de protección de matriz"],
          ["v3", "05/2026", "Pasadores de posicionado; aprobación de primera pieza en el turno de noche"]]),
    ],
)

IT_MT07 = dict(
    code="IT-L1-MT07-01", version="v2", date="10/09/2025", fmt="docx",
    title="Control de rebaba y diámetro del agujero de anclaje (AR-1007, matriz MT-07)", refs=["AR-1007"],
    roles=("U. Ezkurra (Matricería)", "J. Elizalde (Producción L1)", "I. Etxeberria (Calidad)"),
    blocks=[
        ("h", "1. Objeto"),
        ("p", "Controlar la rebaba (≤ 0,2 mm) y el diámetro del agujero de anclaje (Ø11,20 +0,15/0) de la brida AR-1007. Característica crítica (CC)."),
        ("h", "2. Medios"),
        ("list", ["Calibre tampón pasa/no pasa Ø11,20 / Ø11,35 (verificar la etiqueta de calibración: validez 3 meses).",
                  "Reloj comparador con palpador plano sobre soporte (rebaba).", "Lupa 5x."]),
        ("h", "3. Frecuencia"),
        ("p", "Primera pieza tras el montaje de la matriz, cada 2 h y última pieza del lote."),
        ("h", "4. Método"),
        ("list", ["Introducir el lado 'pasa' sin forzar; el lado 'no pasa' no debe entrar.",
                  "Medir la rebaba en 4 posiciones a 90° en la cara de salida del punzón.",
                  "Anotar el valor máximo y los golpes del contador en la hoja de control L1."]),
        ("h", "5. Reacción"),
        ("list", ["Rebaba > 0,15 mm: avisar a matricería (desgaste próximo).",
                  "Rebaba > 0,2 mm o 'pasa' que no entra: parar la prensa, segregar desde el último control OK y montar el punzón de repuesto.",
                  "Nunca desbarbar a mano piezas NOK (característica CC)."]),
        ("h", "6. Afilado"),
        ("p", "El afilado preventivo del punzón P3 lo realiza S-ZIDA según PROC-L1-AFILADO-01. El contador de PR-250 avisa al llegar al intervalo."),
        ("h", "7. Historial"),
        ("table", ["Versión", "Fecha", "Cambio"],
         [["v1", "21/11/2024", "Emisión: control cada 2 h"], ["v2", "10/09/2025", "Rebaba en 4 posiciones; control de la calibración del tampón"]]),
    ],
)

IT_PR400 = dict(
    code="IT-L1-PR400-03", version="v2", date="02/06/2025", fmt="docx",
    title="Estampación transfer en la prensa PR-400 (AR-1002 / AR-1003 / AR-1004 / AR-1005 / AR-1010)",
    refs=["AR-1002", "AR-1003", "AR-1004", "AR-1005", "AR-1010"],
    roles=("U. Ezkurra (Matricería)", "J. Elizalde (Producción L1)", "I. Etxeberria (Calidad)"),
    blocks=[
        ("h", "1. Objeto y alcance"),
        ("p", "Operación de la prensa transfer PR-400 (400 t) con las matrices MT-02, MT-03, MT-04, MT-05 y MT-10."),
        ("h", "2. Arranque"),
        ("list", ["Lubricación de la banda: nivel y boquillas.", "Transfer: verificar dedos y sensores de pieza.",
                  "Bobina: comprobar material y espesor contra la orden de fabricación (etiqueta de lote de S-ULTZ)."]),
        ("h", "3. Liberación de matriz tras reparación"),
        ("p", "Toda matriz que vuelva de reparación o de cambio de insertos se libera con medición completa de primera pieza (cotas SC/CC y "
              "planitud) por Calidad. La matricería entrega la hoja de reparación con la revisión del plano utilizada."),
        ("h", "4. Controles"),
        ("table", ["Referencia", "Control", "Frecuencia"],
         [["AR-1002", "Planitud ≤ 0,5 mm (mármol + galga)", "Cada 2 h"], ["AR-1003/1004", "Holgura de encaje ≤ 1,0 mm (útil)", "Inicio de turno y cada 4 h"],
          ["AR-1005", "Espesor en radio ≥ 2,12 mm", "Por lote"], ["AR-1010", "Útil de control", "Por turno"]]),
        ("h", "5. Historial"),
        ("table", ["Versión", "Fecha", "Cambio"],
         [["v1", "03/2023", "Emisión"], ["v2", "02/06/2025", "Liberación tras reparación con medición completa; planitud cada 2 h"]]),
    ],
)

IT_EC01 = dict(
    code="IT-L3-EC01-02", version="v2", date="20/08/2024", fmt="pdf",
    title="Control del baño de cataforesis EC-01 y del aclarado", refs=["AR-1009"],
    roles=("G. Lizarraga (Ingeniería L3)", "J. Elizalde (Producción L3)", "I. Etxeberria (Calidad)"),
    blocks=[
        ("h", "1. Objeto"),
        ("p", "Mantener el baño de cataforesis EC-01 y el aclarado con agua desionizada dentro de parámetros para evitar poros, cráteres y espesor insuficiente."),
        ("h", "2. Parámetros del baño"),
        ("table", ["Parámetro", "Objetivo", "Frecuencia"],
         [["Sólidos", "19–21 %", "Diaria"], ["pH", "5,8–6,2", "Por turno"], ["Conductividad baño", "1.200–1.600 µS/cm", "Por turno"],
          ["Fosfatos", "< 20 ppm", "Diaria"], ["Temperatura", "30–32 °C", "Continua"], ["Aclarado DI", "< 20 µS/cm (alarma y parada)", "Continua"]]),
        ("h", "3. Adición de química (S-ARAK)"),
        ("list", ["Antes de añadir un lote nuevo: análisis de fosfatos y conductividad en el laboratorio L3 (muestra de 1 l).",
                  "Solo se añade con la etiqueta 'APTO' firmada por Ingeniería L3.", "Registrar el lote de química en el libro del baño."]),
        ("pb", None),
        ("h", "4. Filtración y ultrafiltrado"),
        ("list", ["Cambio de bolsas de filtro: semanal (lunes, turno de mañana).", "Purga de ultrafiltrado según análisis."]),
        ("h", "5. Controles de producto"),
        ("list", ["Espesor 5 puntos, 1 pieza de cada 20.", "Visual con 1.000 lux, 5 piezas por bastidor (poros y cráteres).",
                  "Niebla salina 480 h: 3 piezas al mes (laboratorio externo)."]),
        ("h", "6. Historial"),
        ("table", ["Versión", "Fecha", "Cambio"],
         [["v1", "02/2023", "Emisión"], ["v2", "20/08/2024", "Análisis de cada lote de química, alarma de aclarado DI, filtros semanales (reclamación de cliente por poros)"]]),
    ],
)

IT_VI01 = dict(
    code="IT-L3-VI01-01", version="v2", date="04/07/2024", fmt="docx",
    title="Inspección final por visión (VI-01) y embalaje en cajas retornables", refs=["AR-1001", "AR-1002", "AR-1003", "AR-1004", "AR-1005", "AR-1006", "AR-1007", "AR-1008", "AR-1009", "AR-1010", "AR-1011", "AR-1012"],
    roles=("M. Irigoyen (Calidad)", "A. Olaberri (Logística)", "I. Etxeberria (Calidad)"),
    blocks=[
        ("h", "1. Objeto"),
        ("p", "Inspección final por visión artificial en VI-01 y embalaje de producto terminado en cajas retornables con separadores."),
        ("h", "2. Inspección VI-01"),
        ("list", ["Cargar la receta de la referencia (lector de código de la orden).", "Piezas rechazadas por visión: a la caja roja; revisión por Calidad.",
                  "Verificación de la cámara con la pieza patrón al inicio de turno."]),
        ("h", "3. Embalaje"),
        ("list", ["Solo separadores de cartón de 5 mm (proveedor S-ERRO) íntegros y secos; desechar los aplastados o húmedos.",
                  "Cantidad por caja según la ficha de embalaje del cliente.", "Máximo 4 alturas de caja en el camión.",
                  "Etiqueta con lote de producción y albarán."]),
        ("h", "4. Historial"),
        ("table", ["Versión", "Fecha", "Cambio"],
         [["v1", "03/2023", "Emisión"], ["v2", "04/07/2024", "Control del estado de separadores y límite de apilado (reclamación de cliente)"]]),
    ],
)

ITS = [IT_CR01, IT_CR02, IT_SP01, IT_PR250, IT_MT07, IT_PR400, IT_EC01, IT_VI01]


# ----------------------------------------------------------------------------- PDF (texto)
def _pdf(spec) -> int:
    ss = getSampleStyleSheet()
    body = ParagraphStyle("b", parent=ss["Normal"], fontName="Vera", fontSize=9.5, leading=13)
    h1 = ParagraphStyle("h1", parent=body, fontName="VeraBd", fontSize=11.5, spaceBefore=8, spaceAfter=4, textColor=colors.HexColor("#1F4E79"))
    h2 = ParagraphStyle("h2", parent=body, fontName="VeraBd", fontSize=10, spaceBefore=6, spaceAfter=3)
    cell = ParagraphStyle("c", parent=body, fontSize=8, leading=10)
    rel = f"{FOLDER}/{spec['code']}_{spec['version']}.pdf"
    out = DOCS / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    pages = {"n": 0}

    def on_page(c, d):
        pages["n"] += 1
        c.saveState()
        c.setFont("Vera", 7.5)
        c.drawString(2 * cm, A4[1] - 1.2 * cm, f"{COMPANY} · Instrucción de trabajo")
        c.drawRightString(A4[0] - 2 * cm, A4[1] - 1.2 * cm, f"{spec['code']} · {spec['version']} · {spec['date']}")
        c.drawString(2 * cm, 1.0 * cm, "Documento controlado. Copia impresa sin validez si no lleva sello de copia controlada.")
        c.drawRightString(A4[0] - 2 * cm, 1.0 * cm, f"Página {d.page}")
        c.restoreState()

    doc = SimpleDocTemplate(str(out), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=1.8 * cm,
                            title=f"{spec['code']} {spec['title']}", author="Componentes Arga S.L.", invariant=1)
    story = []
    head = Table([[Paragraph(f"<b>INSTRUCCIÓN DE TRABAJO</b><br/>{spec['title']}", body),
                   Paragraph(f"<b>{spec['code']}</b><br/>Versión {spec['version'][1:]}<br/>Emisión {spec['date']}", body)],
                  [Paragraph(f"Elaborado: {spec['roles'][0]}", cell), Paragraph(f"Revisado: {spec['roles'][1]}<br/>Aprobado: {spec['roles'][2]}", cell)]],
                 colWidths=[11.5 * cm, 5.5 * cm])
    head.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.6, colors.grey), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DDE5EE")),
                              ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story += [head, Spacer(1, 10)]
    for kind, val, *rest in spec["blocks"]:
        if kind == "h":
            story.append(Paragraph(val, h1))
        elif kind == "h2":
            story.append(Paragraph(val, h2))
        elif kind == "p":
            story.append(Paragraph(val, body))
            story.append(Spacer(1, 4))
        elif kind == "list":
            story.append(ListFlowable([Paragraph(x, body) for x in val], bulletType="bullet", start="•", leftIndent=12))
        elif kind == "table":
            rows = [[Paragraph(f"<b>{h}</b>", cell) for h in val]] + [[Paragraph(str(x), cell) for x in r] for r in rest[0]]
            t = Table(rows, repeatRows=1)
            t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.grey), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DDE5EE")),
                                   ("VALIGN", (0, 0), (-1, -1), "TOP")]))
            story += [t, Spacer(1, 6)]
        elif kind == "pb":
            story.append(PageBreak())
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    return pages["n"]


# ----------------------------------------------------------------------------- DOCX
def _docx(spec) -> None:
    d = Doc(spec["code"], spec["version"], spec["title"], header_right="Instrucción de trabajo")
    d.title(f"INSTRUCCIÓN DE TRABAJO {spec['code']}", spec["title"])
    d.form([("Código", spec["code"]), ("Versión", spec["version"]), ("Emisión", spec["date"]), ("Elaborado", spec["roles"][0]),
            ("Revisado", spec["roles"][1]), ("Aprobado", spec["roles"][2])], cols=3)
    for kind, val, *rest in spec["blocks"]:
        if kind == "h":
            d.h(val, 1)
        elif kind == "h2":
            d.h(val, 2)
        elif kind == "p":
            d.p(val.replace("<b>", "").replace("</b>", ""))
        elif kind == "list":
            d.bullets(val)
        elif kind == "table":
            d.table(val, rest[0], font=8)
        elif kind == "pb":
            d.page_break()
    d.save(f"{FOLDER}/{spec['code']}_{spec['version']}.docx")


# ----------------------------------------------------------------------------- PDF escaneado (sin capa de texto)
def _wrap(text, font, width, draw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _scan(spec) -> int:
    rng = random.Random(4242)
    W, H, M = 1654, 2339, 150   # A4 a 200 ppp
    f_body = ImageFont.truetype(str(_FONT_DIR / "Vera.ttf"), 30)
    f_bold = ImageFont.truetype(str(_FONT_DIR / "VeraBd.ttf"), 32)
    f_small = ImageFont.truetype(str(_FONT_DIR / "Vera.ttf"), 24)
    f_hand = ImageFont.truetype(str(_FONT_DIR / "VeraIt.ttf"), 34)
    pages_blocks, cur = [], []
    for b in spec["blocks"]:
        if b[0] == "pb":
            pages_blocks.append(cur)
            cur = []
        else:
            cur.append(b)
    pages_blocks.append(cur)
    images = []
    n = len(pages_blocks)
    for pi, blocks in enumerate(pages_blocks, start=1):
        img = Image.new("L", (W, H), 250)
        dr = ImageDraw.Draw(img)
        # cabecera
        dr.rectangle([M, 110, W - M, 290], outline=40, width=3)
        dr.line([W - M - 430, 110, W - M - 430, 290], fill=40, width=3)
        dr.text((M + 20, 122), "COMPONENTES ARGA S.L.", font=f_bold, fill=20)
        dr.text((M + 20, 160), "INSTRUCCIÓN DE TRABAJO", font=f_small, fill=40)
        for i, line in enumerate(_wrap(spec["title"], f_body, W - 2 * M - 470, dr)[:2]):
            dr.text((M + 20, 200 + i * 36), line, font=f_body, fill=30)
        dr.text((W - M - 410, 125), spec["code"], font=f_bold, fill=20)
        dr.text((W - M - 410, 175), f"Versión {spec['version'][1:]}   {spec['date']}", font=f_small, fill=30)
        dr.text((W - M - 410, 215), f"Página {pi} de {n}", font=f_small, fill=30)
        y = 340
        for kind, val, *rest in blocks:
            if kind in ("h", "h2"):
                y += 14
                dr.text((M, y), val, font=f_bold, fill=15)
                y += 50
            elif kind == "p":
                for line in _wrap(val, f_body, W - 2 * M, dr):
                    dr.text((M, y), line, font=f_body, fill=25)
                    y += 40
                y += 10
            elif kind == "list":
                for it in val:
                    for k, line in enumerate(_wrap(it, f_body, W - 2 * M - 50, dr)):
                        dr.text((M + (0 if k == 0 else 30), y), ("- " + line) if k == 0 else line, font=f_body, fill=25)
                        y += 40
                    y += 6
            elif kind == "table":
                cols = len(val)
                cw = (W - 2 * M) // cols
                allrows = [val] + rest[0]
                for ri, r in enumerate(allrows):
                    dr.rectangle([M, y, W - M, y + 48], outline=60, width=2)
                    for ci, v in enumerate(r):
                        dr.text((M + 10 + ci * cw, y + 10), str(v)[: max(8, cw // 16)], font=f_bold if ri == 0 else f_small, fill=25)
                        if ci:
                            dr.line([M + ci * cw, y, M + ci * cw, y + 48], fill=60, width=2)
                    y += 48
                y += 20
        if pi == n:
            dr.text((W - M - 520, H - 330), "Revisado en planta  A.G.", font=f_hand, fill=70)
            dr.text((W - M - 520, H - 285), "14/05/26", font=f_hand, fill=70)
            dr.ellipse([M + 40, H - 360, M + 300, H - 230], outline=110, width=4)
            dr.text((M + 70, H - 315), "COPIA CONTROLADA", font=f_small, fill=110)
        # pie
        dr.text((M, H - 120), "Documento controlado - copia impresa", font=f_small, fill=60)
        # ruido de escaneo: motas, bordes y rotación ligera
        px = img.load()
        for _ in range(9000):
            x, yy = rng.randrange(W), rng.randrange(H)
            px[x, yy] = rng.choice([0, 60, 120, 200])
        for _ in range(40):
            x, yy = rng.randrange(W), rng.randrange(H)
            dr.ellipse([x, yy, x + rng.randint(2, 6), yy + rng.randint(2, 6)], fill=rng.randint(40, 140))
        img = img.filter(ImageFilter.GaussianBlur(0.7))
        angle = rng.choice([-1.4, -1.1, 0.9, 1.3])
        img = img.rotate(angle, resample=Image.BICUBIC, expand=False, fillcolor=235)
        dr2 = ImageDraw.Draw(img)
        dr2.rectangle([0, 0, W, 18], fill=90)          # sombra del borde del escáner
        dr2.rectangle([W - 14, 0, W, H], fill=120)
        images.append(img.convert("RGB"))
    rel = f"{FOLDER}/{spec['code']}_{spec['version']}.pdf"
    out = DOCS / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    images[0].save(out, "PDF", resolution=200.0, save_all=True, append_images=images[1:], quality=70,
                   creationDate=FIXED_DT.timetuple(), modDate=FIXED_DT.timetuple(), producer="Canon DR-C225 scan", title="")
    return n


def build_all() -> list[dict]:
    out = []
    for spec in ITS:
        pages = None
        if spec["fmt"] == "pdf":
            pages, ext = _pdf(spec), "pdf"
        elif spec["fmt"] == "scan":
            pages, ext = _scan(spec), "pdf"
        else:
            _docx(spec)
            ext = "docx"
        entry = {"doc_id": spec["code"], "version": spec["version"], "title": spec["title"],
                 "path": f"{FOLDER}/{spec['code']}_{spec['version']}.{ext}", "folder": FOLDER, "doc_type": "IT",
                 "language": "ES", "part_refs": spec["refs"], "pages": pages}
        if spec["fmt"] == "scan":
            entry["quality_flags"] = ["scanned", "no_text_layer"]
        out.append(entry)
    return out
