# /// script
# requires-python = ">=3.10"
# dependencies = ["python-docx>=1.1", "openpyxl>=3.1", "reportlab>=4.0", "pillow>=10.0"]
# ///
"""Genera el corpus documental sintético de Componentes Arga S.L. (M1-T2) y su manifest.json.

Uso:  uv run app/data/synthetic/docs/build_corpus.py
Determinista: lee el ERP mock desde erp/seed.sql (no necesita docker) y fija fechas de los binarios.
DATOS SINTÉTICOS (ADR-0004). La verdad del escenario (PLANT.md §5) NO se escribe en ningún documento (PAT-004).
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "_build"))

import build_8d  # noqa: E402
import build_amfe_pc  # noqa: E402
import build_it  # noqa: E402
import build_misc  # noqa: E402

ACL = json.loads((HERE.parent / "acl.json").read_text(encoding="utf-8"))
TOP_FOLDERS = ["calidad", "produccion", "compras", "direccion"]


def main() -> None:
    for top in TOP_FOLDERS:            # regeneración limpia
        shutil.rmtree(HERE / top, ignore_errors=True)
    entries = build_8d.build_all() + build_amfe_pc.build_all() + build_it.build_all() + build_misc.build_all()
    for e in entries:
        e["acl_roles"] = ACL["folders"][e["folder"]]
    (HERE / "calidad" / "reclamaciones").mkdir(parents=True, exist_ok=True)   # vacía: reclamaciones abiertas en M1-T4
    manifest = {
        "_comment": "Corpus sintético de Componentes Arga S.L. (ADR-0004). Generado por build_corpus.py; no editar a mano. "
                    "acl_roles copiados de ../acl.json según la carpeta.",
        "generated_by": "app/data/synthetic/docs/build_corpus.py",
        "documents": sorted(entries, key=lambda e: e["path"]),
    }
    (HERE / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    by_type: dict[str, int] = {}
    for e in entries:
        by_type[e["doc_type"]] = by_type.get(e["doc_type"], 0) + 1
    print(f"{len(entries)} documentos:", ", ".join(f"{k}={v}" for k, v in sorted(by_type.items())))


if __name__ == "__main__":
    main()
