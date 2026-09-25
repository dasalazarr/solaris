#!/usr/bin/env python3
"""Autocomprobación del gate de M4-T5: toda medida "implementada" cita evidencia que existe.

Recorre la sección delimitada por `<!-- check_evidencias: inicio -->` y `<!-- check_evidencias: fin -->` de
docs-compliance/medidas-tecnicas.md y, para cada ruta entre comillas invertidas:
  - `ruta`              -> el fichero o directorio existe en el repo;
  - `ruta::test_nombre` -> el fichero existe y define `def test_nombre` (o `async def`).
Solo comprueba existencia, no que los tests pasen (eso es el gate de dev: pytest).

Uso: python3 docs-compliance/check_evidencias.py   (sale con 1 si falta algo)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOC = Path(__file__).resolve().parent / "medidas-tecnicas.md"
PREFIXES = ("app/", "raw/", "docs-compliance/", ".gitignore", ".env.example", "docker-compose.yml")


def main() -> int:
    text = DOC.read_text(encoding="utf-8")
    m = re.search(r"<!-- check_evidencias: inicio -->(.*?)<!-- check_evidencias: fin -->", text, re.S)
    if not m:
        print("No encuentro los marcadores de la sección A")
        return 1
    refs = sorted({r for r in re.findall(r"`([^`\s]+)`", m.group(1)) if r.startswith(PREFIXES)})
    fails = 0
    for ref in refs:
        path, _, test = ref.partition("::")
        p = ROOT / path
        if not p.exists():
            print(f"FALTA   {ref}")
            fails += 1
            continue
        if test:
            src = p.read_text(encoding="utf-8")
            if not re.search(rf"^(async )?def {re.escape(test)}\(", src, re.M):
                print(f"NO TEST {ref}")
                fails += 1
                continue
        print(f"ok      {ref}")
    print(f"\n{len(refs)} referencias, {fails} fallos")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
