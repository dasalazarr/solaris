#!/usr/bin/env python3
"""Genera docs-compliance/ficha-modelos.md a partir de la configuración del repo (M4-T5).

Fuentes (nada se escribe a mano en la ficha):
  - app/backend/config/models.yaml        -> modelos LLM por tarea (vía OpenRouter, ADR-0003/F10)
  - app/backend/solaris/settings.py       -> modelos locales de embeddings y rerank (repo + revisión)
  - app/backend/uv.lock                   -> versión de rapidocr-onnxruntime (OCR local)

La salida es determinista (sin fecha de generación) para que regenerar no produzca diferencias.

Uso (desde la raíz del repo, python3 >= 3.9 con PyYAML):
    python3 docs-compliance/gen_ficha_modelos.py           # reescribe ficha-modelos.md
    python3 docs-compliance/gen_ficha_modelos.py --check   # sale con 1 si la ficha no está al día
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
MODELS_YAML = ROOT / "app/backend/config/models.yaml"
SETTINGS_PY = ROOT / "app/backend/solaris/settings.py"
UV_LOCK = ROOT / "app/backend/uv.lock"
OUT = Path(__file__).resolve().parent / "ficha-modelos.md"

# Licencias de los modelos locales: verificadas por security en M2-T8
# (raw/sessions/2026-09-25_security_M2-T8.md §3.7). Si cambia el modelo en settings.py y no está
# aquí, la ficha lo marca como "SIN VERIFICAR" en lugar de inventar una licencia.
LOCAL_LICENSES = {
    "intfloat/multilingual-e5-large": ("MIT", "Microsoft (intfloat)", "US"),
    "BAAI/bge-reranker-base": ("MIT", "BAAI (Beijing Academy of AI)", "CN"),
    "jinaai/jina-reranker-v2-base-multilingual": ("CC-BY-NC-4.0 (NO comercial)", "Jina AI", "DE"),
    "rapidocr-onnxruntime": ("Apache-2.0 (modelos PP-OCRv4, Apache-2.0)", "RapidAI (modelos de PaddleOCR, Baidu)", "CN"),
}


def _settings_value(name: str, text: str) -> str:
    m = re.search(rf"^\s*{name}\s*:[^=]*=\s*\"([^\"]+)\"", text, re.M)
    if not m:
        raise SystemExit(f"No encuentro {name} en {SETTINGS_PY}")
    return m.group(1)


def _lock_version(pkg: str, text: str) -> str:
    m = re.search(rf'^name = "{re.escape(pkg)}"\nversion = "([^"]+)"', text, re.M)
    return m.group(1) if m else "SIN VERSIÓN EN uv.lock"


def _prov(p: dict | None) -> str:
    if not p:
        return "—"
    return f"{p['organization']} ({p['country']})"


def _policy(p: dict) -> str:
    parts = [f"`{k}: {str(v).lower() if isinstance(v, bool) else v}`" for k, v in p.items()]
    if "zdr" not in p:
        parts.append("`zdr`: sin activar")
    if "only" not in p:
        parts.append("`only`: sin restringir")
    return " · ".join(parts)


def _lic(model: str) -> tuple[str, str, str]:
    return LOCAL_LICENSES.get(model, ("SIN VERIFICAR", "SIN VERIFICAR", "?"))


def render() -> str:
    cfg = yaml.safe_load(MODELS_YAML.read_text(encoding="utf-8"))
    tasks: dict = cfg["tasks"]
    settings = SETTINGS_PY.read_text(encoding="utf-8")
    lock = UV_LOCK.read_text(encoding="utf-8")

    out: list[str] = []
    w = out.append
    w("<!-- GENERADO por docs-compliance/gen_ficha_modelos.py a partir de models.yaml, settings.py y uv.lock."
      " NO EDITAR A MANO: edita la fuente y regenera. -->")
    w("")
    w("# Ficha de modelos — Solaris (Illarium Industrial OS)")
    w("")
    w("> **BORRADOR — requiere revisión legal.** Documento del pack de cumplimiento (M4-T5).")
    w("> Estado: demo con **datos 100 % sintéticos** (ADR-0004). No apto como ficha de un piloto con datos")
    w("> reales hasta que exista la ruta solo UE (R01) y M3-T5 fije los modelos definitivos.")
    w("")
    w("## 1. Modelos de lenguaje (LLM) por tarea")
    w("")
    w("Todas las llamadas pasan por `solaris.llm.route()` → OpenRouter (ADR-0003, F10). El modelo y el proveedor")
    w("no se pueden cambiar por llamada; cambiar de modelo = editar `app/backend/config/models.yaml`.")
    w("Una ficha con `data_collection` distinto de `deny` no carga (`app/backend/solaris/llm/config.py`).")
    w("")
    w("| Tarea | Modelo primario | Procedencia | Fallback | Procedencia fallback | max_tokens / temp. | eval_score |")
    w("|---|---|---|---|---|---|---|")
    for name, t in tasks.items():
        score = t.get("eval_score")
        score_s = "pendiente M3-T5" if score is None else f"{score}"
        w(f"| `{name}` | `{t['model']}` | {_prov(t.get('provenance'))} | `{t.get('fallback') or '—'}` | "
          f"{_prov(t.get('fallback_provenance'))} | {t.get('max_tokens')} / {t.get('temperature')} | {score_s} |")
    w("")
    w("### Política de proveedor (objeto `provider` de OpenRouter) y nota de región")
    w("")
    groups: dict[tuple[str, str], list[str]] = {}
    for name, t in tasks.items():
        key = (_policy(t.get("provider_policy") or {}), " ".join(str(t.get("region_note", "")).split()))
        groups.setdefault(key, []).append(name)
    for (pol, note), names in groups.items():
        w(f"- **Tareas:** {', '.join(f'`{n}`' for n in names)}")
        w(f"  - **Política:** {pol}")
        w(f"  - **Nota de región (literal de models.yaml):** {note}")
    w("")
    w("### Lectura de security (no generada: criterio fijo)")
    w("")
    w("- La **procedencia** es la organización que publica el modelo, **no** el lugar donde se ejecuta. Con")
    w("  OpenRouter, la región real de inferencia depende del proveedor que elija el enrutado; hoy no hay")
    w("  restricción `only` a proveedores UE, así que **no hay garantía de región UE** para ninguna tarea.")
    w("- La misma política se aplica al primario y al fallback (R07 n.º 6 / M2-T8 S5). La ruta solo UE necesita")
    w("  política por modelo, `zdr: true` y `only` con proveedores UE antes de un piloto.")
    w("- `eval_score` vacío = los modelos aún no se han medido contra el golden set (M3-T5).")
    w("")

    embed_model = _settings_value("embed_model", settings)
    embed_repo = _settings_value("embed_model_repo", settings)
    embed_rev = _settings_value("embed_model_revision", settings)
    rr_model = _settings_value("rerank_model", settings)
    rr_repo = _settings_value("rerank_model_repo", settings)
    rr_rev = _settings_value("rerank_model_revision", settings)
    ocr_ver = _lock_version("rapidocr-onnxruntime", lock)
    ort_ver = _lock_version("onnxruntime", lock)

    w("## 2. Modelos locales (se ejecutan en el equipo; no envían datos a terceros)")
    w("")
    w("Se descargan una vez (revisión fijada) y corren con ONNX Runtime "
      f"{ort_ver} en local. ADR-0003 no aplica: no son llamadas LLM.")
    w("")
    w("| Uso | Modelo | Artefacto / revisión | Procedencia | Licencia | Estado |")
    w("|---|---|---|---|---|---|")
    lic, org, cc = _lic(embed_model)
    w(f"| Embeddings (F01/F02) | `{embed_model}` | `{embed_repo}` @ `{embed_rev[:12]}` | {org} ({cc}) | {lic} | Por defecto |")
    lic, org, cc = _lic(rr_model)
    w(f"| Rerank (F02) | `{rr_model}` | `{rr_repo}` @ `{rr_rev[:12]}` | {org} ({cc}) | {lic} | Por defecto |")
    lic, org, cc = _lic("jinaai/jina-reranker-v2-base-multilingual")
    w(f"| Rerank alternativo | `jinaai/jina-reranker-v2-base-multilingual` | configurable con `RERANK_MODEL` | {org} ({cc}) | "
      f"**{lic}** | **No usar en entornos comerciales.** Sin guarda en código todavía (M2-T8 L1, R07 n.º 8) |")
    lic, org, cc = _lic("rapidocr-onnxruntime")
    w(f"| OCR de PDF escaneados (F01) | `rapidocr-onnxruntime` {ocr_ver} | paquete pip (uv.lock) | {org} ({cc}) | {lic} | Por defecto |")
    w("")
    w("## 3. Qué falta para que esta ficha sea válida en un piloto")
    w("")
    w("1. M3-T5: modelos ganadores por tarea, `eval_score`, coste por 8D y latencia p95.")
    w("2. Verificar qué proveedores de inferencia usa OpenRouter para cada modelo y su región, y si `zdr: true`")
    w("   es viable (si no, documentarlo aquí).")
    w("3. Ruta solo UE conmutable por config y probada, con política por modelo (R01, R07 n.º 6).")
    w("4. Guarda contra el reranker CC-BY-NC (R07 n.º 8).")
    w("5. Añadir versión exacta del modelo servido y proveedor efectivo por llamada (ya queda en el audit")
    w("   `llm_call`: `model_used`, `provider`, `fallback_used`).")
    w("")
    return "\n".join(out)


def main() -> int:
    text = render()
    if "--check" in sys.argv[1:]:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != text:
            print(f"DESACTUALIZADA: {OUT.relative_to(ROOT)} (ejecuta sin --check para regenerar)")
            return 1
        print(f"OK: {OUT.relative_to(ROOT)} al día")
        return 0
    OUT.write_text(text, encoding="utf-8")
    print(f"Escrita {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
