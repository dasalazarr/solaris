# Planta ficticia — Componentes Arga S.L.

> **Datos 100% sintéticos** ([ADR-0004](../../../wiki/decisions/ADR-0004-demo-datos-sinteticos.md)). Las empresas, personas, marcas y códigos son inventados. Cualquier parecido con una organización real es accidental.
> Esta ficha es la **fuente de verdad** que deben respetar el corpus (M1-T2), el ERP mock (M1-T3), las reclamaciones (M1-T4) y el golden set (M1-T5). Si otro artefacto la contradice, se corrige el artefacto, no la ficha. Los cambios en la ficha van con una entrada en `wiki/skill-impact.md`.

## 1. Empresa

| Campo | Valor |
|---|---|
| Razón social | Componentes Arga S.L. (código ERP `ARGA`) |
| Ubicación | Polígono industrial ficticio "Arga Norte", Orkoien (Navarra) |
| Empleados | 180 (3 turnos: mañana, tarde y noche) |
| Posición en la cadena | Tier 2. Vende soportes y refuerzos metálicos a **Tier 1** y directamente a **OEM Norte** en piezas de repuesto y montaje directo |
| Certificación | IATF 16949 (ficticia; auditoría de seguimiento en 03/2027) |
| ERP / MES | ERP genérico ("ERP mock", modelo SAP B1-like). MES = hojas Excel por línea ([H03](../../../wiki/hypotheses/H03-erp-pymes.md)) |
| Idiomas documentales | Castellano (interno), inglés (cliente), algún documento en alemán del OEM |

### Clientes (ficticios)

| Código | Cliente | Tipo | Formato 8D exigido |
|---|---|---|---|
| `C-OEMN` | **OEM Norte** (planta de ensamblaje de vehículos eléctricos, Navarra) | OEM | Plantilla propia "OEM Norte 8D Report v3" (DOCX, EN). Contención ≤24 h, 8D ≤10 días laborables |
| `C-RIBE` | **Ribera Chassis Systems** | Tier 1 (subchasis) | Plantilla 8D interna de Arga (ES) aceptada |
| `C-LEIZ` | **Leitzaran Seating** | Tier 1 (estructuras de asiento) | Plantilla 8D interna de Arga (EN) |

## 2. Líneas de producción

| Línea | Proceso | Equipos principales | Referencias que pasan |
|---|---|---|---|
| **L1 — Estampación** | Corte + estampación progresiva y transfer | Prensa transfer 400 t `PR-400`, prensa progresiva 250 t `PR-250`, matrices `MT-xx` | Todas (primera operación) |
| **L2 — Soldadura** | Soldadura MIG robotizada + soldadura por puntos + tuercas soldables | Células robot `CR-01`, `CR-02`; pinza de puntos `SP-01`; alimentador de tuercas `AT-01` | AR-1003, AR-1004, AR-1005, AR-1006, AR-1009, AR-1010, AR-1011 |
| **L3 — Acabado e inspección** | Cataforesis (e-coat) interna, horno de curado, inspección final y embalaje | Línea de e-coat `EC-01`, horno `HC-01`, puesto de control por visión `VI-01`, calibres pasa/no pasa | Todas |

## 3. Referencias de pieza (12)

| Ref. | Descripción | Cliente | Líneas | Material | Característica especial (SC/CC) |
|---|---|---|---|---|---|
| AR-1001 | Soporte de cableado del vano motor | C-OEMN | L1 → L3 | DC04 1,5 mm | Posición de taladros (SC) |
| AR-1002 | Escuadra de fijación del parachoques trasero | C-RIBE | L1 → L3 | DC04 2,0 mm | Planitud (SC) |
| **AR-1003** | **Soporte de la bandeja de baterías (lado izquierdo)** | C-OEMN | L1 → L2 → L3 | HSLA 420 3,0 mm | **Resistencia de la soldadura MIG (CC)** |
| AR-1004 | Soporte de la bandeja de baterías (lado derecho) | C-OEMN | L1 → L2 → L3 | HSLA 420 3,0 mm | Resistencia de la soldadura MIG (CC) |
| AR-1005 | Refuerzo del travesaño del subchasis | C-RIBE | L1 → L2 → L3 | HSLA 340 2,5 mm | Penetración de la soldadura (CC) |
| AR-1006 | Soporte del compresor de climatización | C-OEMN | L1 → L2 → L3 | DC04 2,0 mm | Par de la tuerca soldada (SC) |
| **AR-1007** | **Brida de anclaje del cinturón de seguridad** | C-LEIZ | L1 → L3 | HSLA 500 3,5 mm | **Diámetro del agujero y rebaba (CC)** |
| AR-1008 | Placa de refuerzo de la bisagra del portón | C-OEMN | L1 → L3 | DC04 2,5 mm | Posición del taladro (SC) |
| AR-1009 | Soporte del radiador de baja temperatura | C-OEMN | L1 → L2 → L3 | DC04 1,5 mm | Espesor del e-coat (SC) |
| AR-1010 | Soporte del inversor de potencia | C-OEMN | L1 → L2 → L3 | HSLA 420 2,5 mm | Par de la tuerca soldada (SC) |
| AR-1011 | Escuadra del bastidor del asiento | C-LEIZ | L1 → L2 → L3 | HSLA 340 2,0 mm | Resistencia del punto de soldadura (CC) |
| AR-1012 | Clip de sujeción del tubo de freno | C-RIBE | L1 → L3 | Acero para muelles 1,0 mm | Fuerza de retención (SC) |

**CC** = característica crítica (seguridad o legal) · **SC** = característica significativa.

## 4. Proveedores (6)

| Código | Proveedor (ficticio) | Suministra | Nota para los escenarios |
|---|---|---|---|
| `S-ULTZ` | Aceros Ultzama S.A. | Bobina de acero DC04 y HSLA | En 2025 hubo un lote de HSLA 340 con límite elástico en el mínimo de especificación, origen del 8D-ARGA-2025-005 (AR-1005) |
| `S-BIDA` | Fijaciones Bidasoa S.L. | Tuercas soldables M6/M8 | Variación del recubrimiento de las tuercas → fallos de par (AR-1006, AR-1010) |
| `S-GOIE` | Hilos y Gases Goierri S.L. | Hilo MIG y gas de protección | Cambio de lote de hilo relacionado con la **familia de recurrencia A** |
| `S-ARAK` | Química Araxes S.A. | Pintura y química de cataforesis | Contaminación del baño → poros en el e-coat (AR-1009) |
| `S-ZIDA` | Tratamientos Zidacos S.L. | Afilado y rectificado de matrices (subcontrata) | Mantenimiento de las matrices `MT-07`, relacionado con la **familia de recurrencia B** |
| `S-ERRO` | Embalajes Erro S.L. | Cajas retornables y separadores | Daños de transporte (deformación) en un 8D histórico |

## 5. Familias de recurrencia (siembra de [O01](../../../wiki/opportunities/O01-memoria-calidad.md))

Los 8D históricos (M1-T2) y las reclamaciones nuevas (M1-T4) **deben** reflejar estas familias. Es lo que el agente tiene que "recordar".

| Familia | Referencias | Defecto | Causa raíz real (verdad del escenario) | 8D históricos | Reclamación nueva que la repite |
|---|---|---|---|---|---|
| **A — Grieta en la soldadura MIG** | AR-1003 (y AR-1004) | Grieta o falta de fusión en el cordón del soporte de baterías; rotura en la prueba de arrancamiento del cliente | Desgaste de la boquilla/tubo de contacto en `CR-01` + cambio de lote de hilo `S-GOIE` sin reajustar los parámetros. La acción correctiva de 2025 (cambio de boquilla cada 8 h) **no se estandarizó** en la instrucción de trabajo del turno de noche | 3 (2024-Q2, 2025-Q1, 2025-Q4) | Sí: la reclamación nueva del OEM Norte sobre AR-1003 (M1-T4 #1) |
| **B — Rebaba y diámetro del agujero fuera de tolerancia** | AR-1007 | Rebaba > 0,2 mm y Ø fuera de tolerancia en el agujero de anclaje; el cinturón no monta en la línea del cliente | Desgaste del punzón de la matriz `MT-07` en `PR-250`; el intervalo de afilado (`S-ZIDA`) se amplió de 40.000 a 60.000 golpes para ahorrar costes | 2 (2024-Q4, 2025-Q3) | Sí: la reclamación nueva de Leitzaran sobre AR-1007 (M1-T4 #2) |

El resto de los 8D históricos (hasta 15) son casos **no recurrentes** que sirven de distractores realistas: poros en el e-coat (AR-1009), par de tuerca bajo (AR-1006/AR-1010), deformación por embalaje (AR-1002), planitud (AR-1002), límite elástico del material (AR-1005), etc.

## 6. Convenciones de códigos

| Objeto | Formato | Ejemplo |
|---|---|---|
| Lote de producción | `L<AA><SSS>-<ref sin guion>-<nn>` (AA = año, SSS = día juliano) | `L26241-AR1003-02` |
| Lote de material de proveedor | `<proveedor>-<AA><nnnn>` | `S-GOIE-260117` |
| 8D interno | `8D-ARGA-<AAAA>-<nnn>` | `8D-ARGA-2025-014` |
| Reclamación de cliente | `<cliente>-<AAAA>-<nnnn>` | `C-OEMN-2026-0312` |
| Documento | `<tipo>-<ref o área>-<nn>`, versión `vN` | `AMFE-AR1003-01 v4`, `IT-L2-CR01-03 v2` |

Tipos de documento: `8D`, `AMFE`, `PC` (plan de control), `IT` (instrucción de trabajo), `PROC` (procedimiento), `EVAL` (evaluación de proveedor), `COST` (costes), `TPL` (plantilla).

## 7. Estructura de carpetas del repositorio documental (simula SharePoint/SMB, [L06](../../../wiki/places/L06-repositorio-documental.md))

```
docs/
├── calidad/
│   ├── 8d/                    # 15 8D históricos (8D-ARGA-*)
│   ├── amfe/                  # 5 AMFE de proceso (xlsx), 1 "sucio"
│   ├── planes-control/        # 5 planes de control
│   ├── reclamaciones/         # reclamaciones de cliente recibidas (históricas)
│   └── plantillas/            # TPL-8D-ARGA (interna) + TPL-8D-OEMN (OEM Norte, ficticia)
├── produccion/
│   ├── instrucciones-trabajo/ # 8 IT por línea/equipo, 1 como PDF escaneado
│   └── mantenimiento/         # plan de afilado de matrices, registros de cambio de boquillas
├── compras/
│   └── proveedores/           # EVAL-* evaluaciones de proveedores (sensibles)
└── direccion/
    └── confidencial/          # COST-* costes de no calidad y márgenes por cliente (muy sensible)
```

## 8. Usuarios y roles (F09)

| Usuario (demo) | Nombre ficticio | Rol | Persona de referencia | Uso en el demo |
|---|---|---|---|---|
| `inaki.calidad` | Iñaki Etxeberria | **Calidad** | Iñaki (Responsable de Calidad) | Protagonista: recibe la reclamación y aprueba el 8D |
| `ander.turno` | Ander Goñi | **Planta** | Jefe de turno / técnico | Consulta IT y mantenimiento. **No** ve 8D ni costes → test negativo de ACL |
| `auditora.ext` | Nerea Lasa (auditora externa) | **Auditor** | Auditor de tercera parte o de cliente | Lectura de calidad y audit log. **No** ve compras ni dirección |
| `jon.it` | Jon Arrieta | **Admin** | Jon (Director de IT/OT) | Consola de auditoría, configuración y fichas de modelo |

## 9. Matriz de ACL (rol → carpetas, **solo lectura** salvo lo indicado)

| Carpeta | Calidad | Planta | Auditor | Admin |
|---|:-:|:-:|:-:|:-:|
| `calidad/8d` | ✅ | ❌ | ✅ | ✅ |
| `calidad/amfe` | ✅ | ❌ | ✅ | ✅ |
| `calidad/planes-control` | ✅ | ✅ | ✅ | ✅ |
| `calidad/reclamaciones` | ✅ | ❌ | ❌ | ✅ |
| `calidad/plantillas` | ✅ | ❌ | ❌ | ✅ |
| `produccion/instrucciones-trabajo` | ✅ | ✅ | ✅ | ✅ |
| `produccion/mantenimiento` | ✅ | ✅ | ❌ | ✅ |
| `compras/proveedores` | ✅ | ❌ | ❌ | ✅ |
| `direccion/confidencial` | ❌ | ❌ | ❌ | ✅ |

Tablas del ERP mock (vía MCP, solo lectura): **Calidad** y **Admin** acceden a todas. **Planta**, solo a `lots` y `production_orders`. **Auditor**, solo a `complaints`. Además, solo **Calidad** puede aprobar pasos del 8D (HITL, [F06](../../../wiki/features/F06-bandeja-aprobaciones.md)).

La versión legible por máquina está en [`acl.json`](acl.json) y es la que consumen la ingesta (M2-T3) y el RBAC (M4-T1).

### Casos de test de ACL que esta matriz habilita (para el golden set, M1-T5)
1. `ander.turno` pregunta por el 8D de la grieta en AR-1003 → **0 fragmentos** de `calidad/8d` y respuesta "no encontrado o sin acceso".
2. `inaki.calidad` pregunta por el coste de no calidad de 2025 → **0 fragmentos** de `direccion/confidencial`.
3. `auditora.ext` pregunta por la evaluación del proveedor `S-GOIE` → **0 fragmentos** de `compras/proveedores`.
4. `ander.turno` pregunta cada cuánto se cambia la boquilla de `CR-01` → **sí** responde, citando `IT-L2-CR01-*` o `produccion/mantenimiento`.
5. `jon.it` accede a todo (control positivo).

## 10. Contraste con las personas (gate de M1-T1)

| Persona (IllariumOS §3.2) | ¿Está cubierta? | Dónde |
|---|---|---|
| Iñaki, Calidad Tier 2 automoción (180 empleados, IATF, reclamaciones de OEM, 8D en EN/DE) | ✅ | Empresa §1, cliente OEM Norte con plantilla EN y plazos 24 h/10 días, usuario `inaki.calidad` |
| Jon, IT/OT (ERP SAP B1-like, veto, auditoría) | ✅ | ERP mock SAP B1-like, `jon.it` Admin, audit y fichas de modelo |
| Jefe de turno / técnico (respuesta con la página del manual) | ✅ | `ander.turno` con IT y mantenimiento, test ACL #4 |
| Auditor (evidencias IATF) | ✅ | `auditora.ext` |
| Maite (agro) y Javier (CEO) | ➖ fuera de la cuña | Javier es la audiencia del cierre del demo (ROI), no un usuario del sistema |

## 11. Registro canónico de 8D históricos y reclamaciones abiertas

Esta lista la fija el ERP mock (`erp/generate_seed.py`, M1-T3). El corpus (M1-T2) debe tener **un documento 8D por fila** con el mismo ID, pieza, cliente y lote (consultable en `erp.complaints`). Las reclamaciones abiertas son las que redacta M1-T4. La columna "Familia" es **verdad del escenario**: no está en el ERP (PAT-004).

| 8D | Cliente | Ref. | Recepción | Defecto (resumen) | Familia |
|---|---|---|---|---|---|
| 8D-ARGA-2024-004 | C-OEMN | AR-1003 | 14/05/2024 | Grieta en el cordón MIG | **A** |
| 8D-ARGA-2024-007 | C-RIBE | AR-1002 | 20/06/2024 | Deformación por embalaje (S-ERRO) | — |
| 8D-ARGA-2024-009 | C-OEMN | AR-1009 | 09/07/2024 | Poros en el e-coat (baño S-ARAK) | — |
| 8D-ARGA-2024-012 | C-LEIZ | AR-1007 | 05/11/2024 | Rebaba en el agujero de anclaje | **B** |
| 8D-ARGA-2024-013 | C-OEMN | AR-1006 | 03/12/2024 | Par bajo de la tuerca soldada | — |
| 8D-ARGA-2025-002 | C-OEMN | AR-1003 | 11/02/2025 | Falta de fusión en el cordón MIG | **A** |
| 8D-ARGA-2025-005 | C-RIBE | AR-1005 | 08/04/2025 | Deformación bajo carga; material en el límite (S-ULTZ) | — |
| 8D-ARGA-2025-006 | C-RIBE | AR-1002 | 13/05/2025 | Planitud fuera de tolerancia | — |
| 8D-ARGA-2025-008 | C-OEMN | AR-1010 | 17/06/2025 | Tuerca soldada gira (recubrimiento S-BIDA) | — |
| 8D-ARGA-2025-010 | C-LEIZ | AR-1007 | 26/08/2025 | Ø de agujero bajo + rebaba | **B** |
| 8D-ARGA-2025-011 | C-OEMN | AR-1001 | 16/09/2025 | Posición de taladros desplazada | — |
| 8D-ARGA-2025-014 | C-OEMN | AR-1003 | 18/11/2025 | Grieta en la raíz del cordón MIG | **A** |
| 8D-ARGA-2025-015 | C-RIBE | AR-1012 | 09/12/2025 | Fuerza de retención baja | — |
| 8D-ARGA-2026-001 | C-LEIZ | AR-1011 | 10/02/2026 | Punto de soldadura pegado | — |
| 8D-ARGA-2026-003 | C-OEMN | AR-1008 | 21/04/2026 | Posición del taladro | — |

| Reclamación abierta (M1-T4) | Ref. | Lote | Recepción | Nota del escenario |
|---|---|---|---|---|
| C-OEMN-2026-0312 | AR-1003 | L26241-AR1003-02 | 22/09/2026 | **Caso principal del demo** (familia A). Lote con hilo `S-GOIE-260117`, `CR-01`, turno de noche |
| C-LEIZ-2026-0088 | AR-1007 | L26245-AR1007-01 | 18/09/2026 | Familia B |
| C-OEMN-2026-0327 | AR-1009 | L26250-AR1009-01 | 23/09/2026 | Parecida a 8D-2024-009, pero la causa la decide M1-T4 (¿distractor?) |
| C-RIBE-2026-0140 | AR-1012 | L26236-AR1012-03 | 16/09/2026 | En ES, plantilla interna |
| C-OEMN-2026-0331 | AR-1010 | L26252-AR1010-01 | 23/09/2026 | **Lleva la inyección de prompts** (R03), que se redacta en M1-T4 |
