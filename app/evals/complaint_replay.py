"""Arnés sin LLM del parser de reclamaciones (M3-T8, PAT-011): re-puntúa respuestas GRABADAS.

Toma salidas brutas del LLM `complaint_parse` ya grabadas (campo `llm_raw` de la suite
`complaints` desde M3-T8, o de las filas de diagnóstico de M3-T8) y vuelve a ejecutar el parser
con esa respuesta en lugar de la llamada real (sin ERP, sin audit). Mide, con el código actual:

- falsos positivos del aviso rojo (`injection_suspected`) en los 4 casos limpios;
- los que habría dado la regla anterior (`legacy_fp`: el LLM solo activaba el aviso, M3-T2);
- canales detectados en la #5 (C-OEMN-2026-0331) y fugas de testigos o de patrones de
  inyección a los campos estructurados.

Además del modo `recorded` (cada respuesta sobre su propio fichero) hay un modo `adversarial`:
una respuesta sintética que declara TODOS los segmentos enviados, por caso. Es el peor caso de
la señal del modelo y no gasta llamadas.

    uv run --project app/backend python app/evals/complaint_replay.py --runs 'glob' [--repeat 5]
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path
from typing import Any

EVALS_DIR = Path(__file__).resolve().parent
REPO_ROOT = EVALS_DIR.parents[1]
if str(EVALS_DIR) not in sys.path:
    sys.path.insert(0, str(EVALS_DIR))

import complaint_suite as cs  # noqa: E402

EMPTY_OUT = {"defect_description": "", "evidence": [], "contact_name": "", "contact_role": "",
             "template_ref": "", "part_ref": "", "drawing_no": "", "lot_codes": [],
             "delivery_notes": [], "ignored_instructions": []}


def load_recorded(patterns: list[str]) -> list[dict[str, Any]]:
    """[(file, llm_raw, origen)] de los JSON que tengan `llm_raw` por ítem."""
    out = []
    for pat in patterns:
        for f in sorted(glob.glob(str(REPO_ROOT / pat))):
            d = json.loads(Path(f).read_text(encoding="utf-8"))
            rows = d.get("items", []) if isinstance(d, dict) else d
            for r in rows:
                if r.get("llm_raw") and r.get("file"):
                    out.append({"file": r["file"], "llm_raw": r["llm_raw"],
                                "origin": Path(f).name})
    return out


def _fake_route(content: str) -> Any:
    from solaris.llm import LLMResult

    def fn(task: str, messages: list[dict[str, Any]], **_: Any) -> Any:
        return LLMResult(task=task, content=content, model="replay/recorded",
                         requested_model="replay/recorded", latency_ms=0.0, attempts=1)
    return fn


def replay_one(file: str, content: str, settings: Any) -> dict[str, Any]:
    from solaris.agents.complaint import STRUCTURED_FIELDS, parse
    from solaris.auth.core import Principal
    from solaris.prompts.untrusted import detect_injection

    raw = (cs.COMPLAINTS_DIR / file).read_bytes()
    p = parse(raw, file, Principal("inaki.calidad", "calidad", "replay"), settings=settings,
              route_fn=_fake_route(content), check_erp=False, audit=lambda *a, **k: None)
    pd = p.model_dump(mode="json")
    notes = [w for w in pd["warnings"] if w.get("type") == "model_flagged_text"]
    struct = json.dumps({k: pd.get(k) for k in STRUCTURED_FIELDS}, ensure_ascii=False)
    leaks = [c for c in cs.canaries().values() if c in struct] + detect_injection(struct)
    return {"injection_suspected": pd["injection_suspected"],
            "channels": sorted({f["channel"] for f in pd["injection_findings"]}),
            "rules": sorted({f["rule"] for f in pd["injection_findings"]}),
            "model_only": notes[0]["sources"] if notes else [],
            # regla anterior (M3-T2): sin hallazgo determinista, una declaración del LLM
            # bastaba para activar el aviso rojo.
            "legacy_suspected": pd["injection_suspected"] or bool(notes),
            "leaks": leaks}


def adversarial(file: str) -> str:
    from solaris.agents.complaint import prepare

    n = len(prepare((cs.COMPLAINTS_DIR / file).read_bytes(), file).pieces)
    return json.dumps({**EMPTY_OUT, "ignored_instructions": [
        {"source": f"S{i}", "summary": "replay"} for i in range(1, n + 1)]})


def run(patterns: list[str], settings: Any, repeat: int = 1) -> dict[str, Any]:
    truth = cs.load_truth()
    files = {t["file"]: cid for cid, t in truth.items()}
    jobs = [("recorded", r["file"], r["llm_raw"], r["origin"]) for r in load_recorded(patterns)
            if r["file"] in files]
    jobs += [("adversarial", f, adversarial(f), "synthetic") for f in files]
    items, by_mode = [], {}
    for mode, file, content, origin in jobs:
        for rep in range(repeat):
            r = replay_one(file, content, settings)
            cid = files[file]
            items.append({"mode": mode, "complaint_id": cid, "file": file, "origin": origin,
                          "rep": rep + 1, **r})
            m = by_mode.setdefault(mode, {"runs": 0, "clean_runs": {}, "fp": 0, "legacy_fp": 0,
                                          "model_only_notes": 0, "case5_runs": 0,
                                          "case5_3of3": 0, "leaks": 0})
            m["runs"] += 1
            m["leaks"] += len(r["leaks"])
            if cid == cs.INJECTION_CASE_ID:
                m["case5_runs"] += 1
                m["case5_3of3"] += len(r["channels"]) == 3
            else:
                m["clean_runs"][cid] = m["clean_runs"].get(cid, 0) + 1
                m["fp"] += r["injection_suspected"]
                m["legacy_fp"] += r["legacy_suspected"]
                m["model_only_notes"] += bool(r["model_only"])
    return {"metrics": by_mode, "items": items}


def main() -> int:
    from solaris.settings import get_settings

    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--runs", nargs="+", default=["raw/eval-runs/*complaint_parse*.json"])
    ap.add_argument("--repeat", type=int, default=1)
    ap.add_argument("--out")
    a = ap.parse_args()
    res = run(a.runs, get_settings(), a.repeat)
    print(json.dumps(res["metrics"], ensure_ascii=False, indent=1))
    if a.out:
        Path(a.out).write_text(json.dumps({"suite": "complaint_replay", "runs": a.runs,
                                           "repeat": a.repeat, **res}, ensure_ascii=False,
                                          indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
