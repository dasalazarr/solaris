"""Evaluación de `/ask` sobre `app/evals/golden/qa.jsonl` (M2-T6) y calibración del umbral.

**Solo para evals (PAT-004):** lee el golden set; ningún módulo del runtime lo importa
(tests/test_ask.py::test_api_import_graph_has_no_admin_paths). Reutiliza, sin modificarlas, las
funciones de puntuación de `app/evals/scoring.py` (runner de M2-T7, a medias).

Uso (desde app/backend):
    uv run python -m solaris.evals_qa --calibrate          # solo recuperación, sin LLM
    uv run python -m solaris.evals_qa                      # 50 ítems con el LLM real
    uv run python -m solaris.evals_qa --only QA-001,QA-041 --no-write

Métricas (golden/README.md):
- precisión de citas (micro) en factual/recurrence/multilingual: citas devueltas que coinciden con
  alguna `expected_citations` (doc_id + versión + locator compatible) ÷ citas devueltas;
- cobertura: ítems con ≥1 cita esperada (y variante con todas las `required_doc_ids`);
- "no encontrado" correcto (5/5): `not_found=true` y 0 citas; `must_not_claim` se revisa a mano;
- ACL (0 fugas): en `acl_negative`, 0 fragmentos recuperados y 0 citas de `forbidden_*` o de
  carpetas no visibles; en todos los ítems, 0 fragmentos fuera de las carpetas del rol;
- `must_include` (coincidencia normalizada), latencia p50/p95 de extremo a extremo y del LLM, coste.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from solaris.auth.core import Principal
from solaris.rag.acl import resolve_role
from solaris.rag.answer import DEFAULT_GATE, EvidenceGate, K, answer_question
from solaris.rag.retrieve import RetrievalTrace, retrieve_as
from solaris.settings import REPO_ROOT, get_settings

EVALS_DIR = REPO_ROOT / "app" / "evals"
QA_FILE = EVALS_DIR / "golden" / "qa.jsonl"
ACL_FILE = REPO_ROOT / "app" / "data" / "synthetic" / "acl.json"
OUT_DIR = REPO_ROOT / "raw" / "eval-runs"
CITABLE = ("factual", "recurrence", "multilingual")
SID = "eval-qa"

if str(EVALS_DIR) not in sys.path:
    sys.path.insert(0, str(EVALS_DIR))
import scoring  # noqa: E402  (app/evals/scoring.py, reutilizado tal cual)


def load_items(only: list[str] | None) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in QA_FILE.read_text(encoding="utf-8").splitlines()
            if line.strip()]
    return [r for r in rows if not only or r["id"] in only]


def principal_for(user: str) -> Principal:
    role = resolve_role(user, ACL_FILE)
    if role is None:
        raise SystemExit(f"usuario sin rol en acl.json: {user}")
    return Principal(user, role, SID)


def out_path(name: str) -> Path:
    base = OUT_DIR / f"{date.today().isoformat()}_{name}.json"
    p, n = base, 2
    while p.exists():  # raw/ es de solo anexar
        p = base.with_name(f"{base.stem}_{n}.json")
        n += 1
    return p


def _r(v: float | None, nd: int = 3) -> float | None:
    return None if v is None else round(v, nd)


# --- calibración (sin LLM) ----------------------------------------------------------------------


def calibrate(items: list[dict[str, Any]], thresholds: list[float]) -> dict[str, Any]:
    s = get_settings()
    retrieve_as(principal_for("inaki.calidad"), "calentamiento", K, settings=s)  # carga modelos
    rows = []
    for it in items:
        tr = RetrievalTrace(user=it["user"], role=None)
        hits = retrieve_as(principal_for(it["user"]), it["question"], K, settings=s, trace=tr)
        top = max((h.rerank for h in hits if h.rerank is not None), default=None)
        exp = it.get("expected_citations") or []
        rank = scoring.first_match_rank(exp, [h.citation() for h in hits]) if exp else None
        rows.append({"id": it["id"], "category": it["category"], "top_rerank": _r(top),
                     "expected_rank": rank, "n_hits": len(hits)})
        print(f"{it['id']} {it['category']:<13} top_rerank={_r(top)} expected_rank={rank}")
    table = []
    for th in thresholds:
        gated = [r for r in rows if r["top_rerank"] is None or r["top_rerank"] < th]
        by = defaultdict(int)
        for r in gated:
            by[r["category"]] += 1
        answerable = [r for r in gated if r["category"] in CITABLE]
        table.append({
            "threshold": th,
            "not_found_gated": by["not_found"], "acl_negative_gated": by["acl_negative"],
            "answerable_gated": len(answerable),
            "answerable_gated_with_expected_in_topk": sum(
                1 for r in answerable if r["expected_rank"] is not None),
            "answerable_gated_ids": [r["id"] for r in answerable],
        })
    dist: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        if r["top_rerank"] is not None:
            dist[r["category"]].append(r["top_rerank"])
    summary = {c: {"n": len(v), "min": min(v), "p10": _r(scoring.percentile(v, 10)),
                   "median": _r(scoring.percentile(v, 50)), "max": max(v)}
               for c, v in sorted(dist.items())}
    return {"items": rows, "distribution": summary, "thresholds": table}


# --- evaluación con LLM -------------------------------------------------------------------------


def score_item(it: dict[str, Any], res: Any, acl: dict[str, Any], role: str) -> dict[str, Any]:
    cat = it["category"]
    cits = res.citations
    hits = res.debug.get("hits", [])
    exp = it.get("expected_citations") or []
    vis = scoring.visible_folders_for(role, acl)
    out: dict[str, Any] = {"not_found": res.not_found, "n_citations": len(cits)}
    # ACL en todos los ítems: nada recuperado ni citado fuera de lo visible (o prohibido).
    leaks = scoring.acl_violations(
        hits + cits, visible_folders=vis, forbidden_doc_ids=it.get("forbidden_doc_ids", []),
        forbidden_folders=it.get("forbidden_folders", []))
    out["acl_leaks"] = leaks
    if cat in CITABLE:
        ok, total = scoring.citation_precision(cits, exp)
        out["citations_ok"], out["citations_total"] = ok, total
        out["covered"] = ok > 0
        req_ok, missing = scoring.required_docs_covered(
            it.get("required_doc_ids") or [], cits, len(cits) or 1)
        out["covered_required"] = ok > 0 and req_ok
        out["required_missing"] = missing
        mi_ok, mi_missing = scoring.must_include_hits(res.answer, it.get("must_include") or [])
        out["must_include_ok"], out["must_include_missing"] = mi_ok, mi_missing
        out["expected_in_retrieval"] = scoring.first_match_rank(exp, hits)
        out["wrong_citations"] = [c for c in cits
                                  if not any(scoring.citation_match(e, c) for e in exp)]
    elif cat == "not_found":
        out["correct"] = res.not_found and not cits
    elif cat == "acl_negative":
        out["no_leak"] = not leaks
        out["declared_not_found"] = res.not_found
    return out


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    def agg(sel: list[dict[str, Any]]) -> dict[str, Any]:
        cit = [r for r in sel if r["category"] in CITABLE]
        ok = sum(r["score"]["citations_ok"] for r in cit)
        tot = sum(r["score"]["citations_total"] for r in cit)
        nf = [r for r in sel if r["category"] == "not_found"]
        an = [r for r in sel if r["category"] == "acl_negative"]
        lat = [r["latency_ms"] for r in sel]
        llm = [r["llm_latency_ms"] for r in sel if r["llm_latency_ms"] is not None]
        return {
            "n": len(sel),
            "citation_precision": _r(ok / tot) if tot else None,
            "citations_ok": ok, "citations_total": tot,
            "coverage": _r(sum(r["score"]["covered"] for r in cit) / len(cit)) if cit else None,
            "coverage_required": _r(sum(r["score"]["covered_required"] for r in cit) / len(cit))
            if cit else None,
            "answered_not_found_on_citable": sum(r["score"]["not_found"] for r in cit),
            "must_include": _r(sum(r["score"]["must_include_ok"] for r in cit) / len(cit))
            if cit else None,
            "not_found_correct": f"{sum(r['score']['correct'] for r in nf)}/{len(nf)}"
            if nf else None,
            "acl_negative_no_leak": f"{sum(r['score']['no_leak'] for r in an)}/{len(an)}"
            if an else None,
            "acl_negative_declared_not_found":
                f"{sum(r['score']['declared_not_found'] for r in an)}/{len(an)}" if an else None,
            "acl_leaks_total": sum(len(r["score"]["acl_leaks"]) for r in sel),
            "gated_without_llm": sum(r["gated"] for r in sel),
            "latency_p50_ms": _r(scoring.percentile(lat, 50), 1),
            "latency_p95_ms": _r(scoring.percentile(lat, 95), 1),
            "latency_max_ms": _r(max(lat), 1) if lat else None,
            "llm_latency_p50_ms": _r(scoring.percentile(llm, 50), 1),
            "llm_latency_p95_ms": _r(scoring.percentile(llm, 95), 1),
            "cost_usd": _r(sum(r["cost_usd"] or 0 for r in sel), 5),
            "prompt_tokens": sum(r["prompt_tokens"] or 0 for r in sel),
            "completion_tokens": sum(r["completion_tokens"] or 0 for r in sel),
            "warnings": dict(sorted(_count_warnings(sel).items())),
        }

    by_cat: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by_cat[r["category"]].append(r)
        for flag in ("requires_ocr", "dirty_amfe"):
            if r.get(flag):
                by_cat[f"flag:{flag}"].append(r)
        if r.get("subcategory") and r["category"] == "factual":
            by_cat[f"factual/{r['subcategory']}"].append(r)
    return {"overall": agg(rows), "by_category": {k: agg(v) for k, v in sorted(by_cat.items())}}


def _count_warnings(sel: list[dict[str, Any]]) -> dict[str, int]:
    c: dict[str, int] = defaultdict(int)
    for r in sel:
        for w in r["warnings"]:
            c[w["type"]] += 1
    return c


def run(items: list[dict[str, Any]], gate: EvidenceGate) -> dict[str, Any]:
    s = get_settings()
    acl = json.loads(ACL_FILE.read_text(encoding="utf-8"))
    retrieve_as(principal_for("inaki.calidad"), "calentamiento", K, settings=s)  # carga modelos
    rows = []
    for it in items:
        p = principal_for(it["user"])
        t0 = time.perf_counter()
        try:
            res = answer_question(p, it["question"], settings=s, gate=gate)
        except Exception as exc:  # un fallo del proveedor no debe perder la pasada completa
            print(f"{it['id']} ERROR {type(exc).__name__}")
            rows.append({"id": it["id"], "category": it["category"], "error": type(exc).__name__})
            continue
        wall = (time.perf_counter() - t0) * 1000
        llm = res.debug.get("llm") or {}
        row = {
            "id": it["id"], "user": it["user"], "role": p.role, "category": it["category"],
            "subcategory": it.get("subcategory"), "requires_ocr": it.get("requires_ocr", False),
            "dirty_amfe": it.get("dirty_amfe", False), "question": it["question"],
            "answer": res.answer, "citations": res.citations, "warnings": res.warnings,
            "model": res.model, "latency_ms": round(wall, 1),
            "llm_latency_ms": llm.get("latency_ms"), "provider": llm.get("provider"),
            "cost_usd": llm.get("cost_usd"), "prompt_tokens": llm.get("prompt_tokens"),
            "completion_tokens": llm.get("completion_tokens"),
            "gated": res.debug.get("gate") == "below_threshold",
            "top_rerank": _r(res.debug.get("top_rerank")),
            "retrieved": res.debug.get("hits"), "model_not_found": res.debug.get(
                "model_not_found"), "dropped": res.debug.get("dropped"),
            "expected_citations": it.get("expected_citations"),
            "must_include": it.get("must_include"), "must_not_claim": it.get("must_not_claim"),
        }
        row["score"] = score_item(it, res, acl, p.role)
        rows.append(row)
        sc = row["score"]
        extra = (f"cit {sc.get('citations_ok')}/{sc.get('citations_total')}"
                 if it["category"] in CITABLE else f"nf={res.not_found}")
        print(f"{it['id']} {it['category']:<13} {extra:<10} {row['latency_ms']:>7.0f} ms "
              f"llm={row['llm_latency_ms']} {row['provider']}")
    ok_rows = [r for r in rows if "error" not in r]
    return {"items": rows, "errors": [r for r in rows if "error" in r],
            "metrics": aggregate(ok_rows)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m solaris.evals_qa", description=__doc__.split(
        "\n")[0])
    ap.add_argument("--calibrate", action="store_true", help="solo recuperación (sin LLM)")
    ap.add_argument("--thresholds", default="-9,-8,-7,-6,-5,-4,-3,-2,-1,0")
    ap.add_argument("--min-rerank", type=float, default=DEFAULT_GATE.min_rerank)
    ap.add_argument("--only", default=None)
    ap.add_argument("--label", default=None, help="sufijo del fichero de salida")
    ap.add_argument("--no-write", action="store_true")
    a = ap.parse_args(argv)
    only = [x.strip() for x in a.only.split(",")] if a.only else None
    items = load_items(only)
    s = get_settings()
    meta = {"started_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "golden": str(QA_FILE.relative_to(REPO_ROOT)), "n_items": len(items),
            "rerank_backend": s.rerank_backend, "rerank_model": s.rerank_model,
            "embed_model": s.embed_model}
    if a.calibrate:
        ths = [float(x) for x in a.thresholds.split(",")]
        res = {"suite": "qa_calibration", **meta, **calibrate(items, ths)}
        name = "qa_calibration"
        for row in res["thresholds"]:
            print(row)
    else:
        from solaris.llm import load_model_cards
        from solaris.rag.answer import PROMPT_VERSION

        card = load_model_cards(s.models_file)["rag_answer"]
        res = {"suite": "qa", **meta, "task": "rag_answer", "model": card.model,
               "fallback": card.fallback, "provider_policy": card.provider_policy.to_payload(),
               "prompt_version": PROMPT_VERSION, "min_rerank": a.min_rerank,
               **run(items, EvidenceGate(min_rerank=a.min_rerank))}
        name = f"qa_{card.model.replace('/', '-')}" + (f"_{a.label}" if a.label else "")
        print(json.dumps(res["metrics"]["overall"], ensure_ascii=False, indent=1))
    res["finished_at"] = datetime.now(UTC).isoformat(timespec="seconds")
    if not a.no_write:
        path = out_path(name)
        path.write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str) + "\n",
                        encoding="utf-8")
        print(f"→ {path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
