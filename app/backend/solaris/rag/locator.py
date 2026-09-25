"""Etiqueta legible de un locator de chunk (sin dependencias: la usan ingesta, recuperación y /ask).

M2-T6: vivía en `solaris.rag.ingest`; se separa para que la API (`/ask` → `retrieve`) no importe el
módulo de ingesta, que usa la conexión de administración (test_import_graph, spec §3.1 de M2-T8).
"""

from __future__ import annotations

from typing import Any


def loc_label(loc: dict[str, Any]) -> str:
    if "page" in loc:
        s = f"página {loc['page']}"
    elif "sheet" in loc:
        rows = loc.get("rows")
        if isinstance(rows, list | tuple) and len(rows) == 2:
            s = f"hoja {loc['sheet']}, filas {rows[0]}–{rows[1]}"
        else:
            s = f"hoja {loc['sheet']}, filas {rows}"
    else:
        s = loc.get("heading") or loc.get("section", "")
    return f"{s} (parte {loc['part']})" if "part" in loc else s
