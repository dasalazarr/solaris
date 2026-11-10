---
id: ADR-0018
type: decision
title: "La demo y el MVP son el mismo producto; los distingue la configuración del espacio"
status: validating
owner_role: dev
links: ["[[ADR-0003]]", "[[ADR-0015]]", "[[ADR-0016]]", "[[ADR-0017]]", "[[H03]]"]
evidence: ["docs/plan-evolutivo.md", "product/lib/environment-label.ts", "product/lib/space-auth.ts", "product/lib/store/index.ts"]
updated: 2026-11-10
---

# ADR-0018 · Demo y MVP

- Estado: propuesta del cofundador (2026-11-10). La acepta Diego.
- Contexto: al explicar cómo se configura el proceso de compras salió la pregunta de cómo distinguimos la demo del MVP. No estaba escrito, y la respuesta condiciona la landing, el piloto y lo que se promete en cada reunión.

## Opciones

1. **Dos productos.** La demo es una maqueta con datos fijos y el MVP es otra base de código. Se enseña rápido, pero lo enseñado deja de ser lo que se entrega, y eso choca con el principio 4.
2. **Un producto con banderas de función.** La demo esconde o simula partes. Cada bandera crea un camino que nadie prueba en producción.
3. **Un producto y la configuración del espacio.** El mismo código; cambian el entorno, la naturaleza de los datos, el almacén y quién entra con qué rol.

## Decisión

Opción 3. Lo que separa la demo del MVP vive en `SOLARIS_SPACES` y en el entorno del servidor, nunca en el código de la interfaz:

| Eje | Demo (Nivel 1) | MVP del piloto (Nivel 2) | Dónde se fija |
|---|---|---|---|
| Etiqueta de entorno | «Demo en la nube · datos de muestra» | «Instancia local · documentos reales» | `environmentLevel` y `dataNature` del espacio; la lee `environmentLabel` |
| Datos | Ficticios, de las plantillas | Los del cliente, en su instancia | `dataNature`. Ningún documento real entra en los repositorios |
| Persistencia | Ninguna: al recargar vuelve al estado de muestra | SQLite por espacio | `SOLARIS_DATA_DIR`. Sin ella, el producto sigue en modo demostración. No se pone en Vercel |
| Rol | Lo elige quien mira, para enseñar el circuito | Lo impone el servidor por persona | Códigos por persona en `people` |
| Proceso | Plantillas: compras, jurídico, IFS y EUDR | Plantilla adaptada o proceso propio, publicado con versión y `policy_hash` | `lib/templates/*.json` y el editor de Contrato ([[ADR-0017]]) |

### Qué está listo, por modo

| Modo | Criterio | Estado a 2026-11-10 |
|---|---|---|
| Mostrar | Alguien que no es Diego hace la demo con el guion | Prácticamente cumplido |
| Usar | Lo aprobado sigue al recargar y el rol lo impone el servidor | Construido y fusionado; no hay ninguna instancia con almacén |
| Parametrizar | Alguien sin programar crea un proceso en menos de 2 horas | Construido; [[H03]] sin medir |
| Probar | De PDF ficticios a decisión registrada, con cita a la página | Fase 4, sin construir |

## Consecuencias

- La landing y las reuniones solo pueden prometer como MVP lo que esté en «Usar» o más allá con su criterio cumplido. Hoy eso excluye leer documentos reales del cliente.
- Una demo nunca puede mostrar «Instancia local» ni «documentos reales»: la etiqueta sale de la configuración y el principio 4 lo exige.
- Abrir un piloto es una tarea de configuración y despliegue, no de desarrollo: espacio con Nivel 2, `DOCUMENTOS_REALES`, almacén y códigos por persona. Va al manual del piloto.
- Si algún día hace falta una función solo para la demo, se reabre esta decisión antes de añadir una bandera.
