"""Suite `qa` del runner (M2-T6 → M2-T7): `/ask` sobre `golden/qa.jsonl` con el LLM real.

Única vía para evaluar `/ask` (M2-T7): `runner.py --suite qa` (o `--suite qa --calibrate`, sin
LLM). La lógica vivía en `solaris/evals_qa.py` (M2-T6); se movió aquí para que el paquete del
producto no contenga código que lee el golden (PAT-004). `solaris.evals_qa` queda como alias.

Recorre el mismo camino que el endpoint: `answer_question(Principal del ítem, pregunta)` con la
recuperación por defecto (ACL en SQL + referencia a documento + expansión D4 + traducción ES↔EN).

Métricas (golden/README.md):
- precisión de citas (micro) en factual/recurrence/multilingual: citas devueltas que coinciden con
  alguna `expected_citations` (doc_id + versión + locator compatible) ÷ citas devueltas;
- cobertura: ítems con ≥1 cita esperada (y variante con todas las `required_doc_ids`);
- "no encontrado" correcto (5/5): `not_found=true` y 0 citas; `must_not_claim` se revisa a mano;
- ACL (0 fugas): 0 fragmentos recuperados o citados fuera de las carpetas del rol o prohibidos;
- `must_include` (coincidencia normalizada), latencia p50/p95 de extremo a extremo, de la
  recuperación y del LLM (también por proveedor, PAT-009) y coste.
"""

from __future__ import annotations

import json
import time
from collections import defaultdict
from typing import Any

import scoring

CITABLE = ("factual", "recurrence", "multilingual")
SID = "eval-qa"
GATE = {"citation_precision": 0.90, "not_found": "5/5", "acl_leaks": 0, "p95_ms": 8000.0}


def _r(v: float | None, nd: int = 3) -> float | None:
    return None if v is None else round(v, nd)


def principal_for(user: str, acl_file: Any) -> Any:
    from solaris.auth.core import Principal
    from solaris.rag.acl import resolve_role

    role = resolve_role(user, acl_file)
    if role is None:
        raise SystemExit(f"usuario sin rol en acl.json: {user}")
    return Principal(user, role, SID)


# --- calibración (sin LLM) ----------------------------------------------------------------------


def calibrate(items: list[dict[str, Any]], thresholds: list[float], settings: Any,
              acl_file: Any) -> dict[str, Any]:
    from solaris.rag.answer import K
    from solaris.rag.crosslingual import retrieve_bilingual
    from solaris.rag.retrieve import RetrievalTrace

    retrieve_bilingual(principal_for("inaki.calidad", acl_file), "calentamiento", K,
                       settings=settings)
    rows = []
    for it in items:
        tr = RetrievalTrace(user=it["user"], role=None)
        hits = retrieve_bilingual(principal_for(it["user"], acl_file), it["question"], K,
                                  settings=settings, trace=tr)
        top = max((h.rerank for h in hits if h.rerank is not None), default=None)
        exp = it.get("expected_citations") or []
        rank = scoring.first_match_rank(exp, [h.citation() for h in hits]) if exp else None
        rows.append({"id": it["id"], "category": it["category"], "top_rerank": _r(top),
                     "expected_rank": rank, "n_hits": len(hits)})
        print(f"{it['id']} {it['category']:<13} top_rerank={_r(top)} expected_rank={rank}")
    table = []
    for th in thresholds:
        gated = [r for r in rows if r["top_rerank"] is None or r["top_rerank"] < th]
        by: dict[str, int] = defaultdict(int)
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
    out["acl_leaks"] = scoring.acl_violations(
        hits + cits, visible_folders=vis, forbidden_doc_ids=it.get("forbidden_doc_ids", []),
        forbidden_folders=it.get("forbidden_folders", []))
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
        out["no_leak"] = not out["acl_leaks"]
        out["declared_not_found"] = res.not_found
    return out


def _pcts(xs: list[float]) -> dict[str, float | None]:
    return {"p50": _r(scoring.percentile(xs, 50), 1), "p95": _r(scoring.percentile(xs, 95), 1),
            "max": _r(max(xs), 1) if xs else None}


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    def agg(sel: list[dict[str, Any]]) -> dict[str, Any]:
        cit = [r for r in sel if r["category"] in CITABLE]
        ok = sum(r["score"]["citations_ok"] for r in cit)
        tot = sum(r["score"]["citations_total"] for r in cit)
        nf = [r for r in sel if r["category"] == "not_found"]
        an = [r for r in sel if r["category"] == "acl_negative"]
        lat = [r["latency_ms"] for r in sel]
        llm = [r["llm_latency_ms"] for r in sel if r["llm_latency_ms"] is not None]
        ret = [r["retrieval_ms"].get("total", 0.0) for r in sel if r.get("retrieval_ms")]
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
            "retrieval_ms": _pcts(ret),
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
    return {"overall": agg(rows), "by_category": {k: agg(v) for k, v in sorted(by_cat.items())},
            "by_provider": by_provider(rows), "gate": gate(agg(rows))}


def by_provider(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Latencias por proveedor de OpenRouter (PAT-009): LLM y extremo a extremo."""
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        if r["llm_latency_ms"] is not None:
            groups[f"{r['provider']} · {r['model']}"].append(r)
    return {p: {"n": len(v), "llm_ms": _pcts([r["llm_latency_ms"] for r in v]),
                "e2e_ms": _pcts([r["latency_ms"] for r in v]),
                "completion_tokens_p50": _r(scoring.percentile(
                    [r["completion_tokens"] or 0 for r in v], 50), 0)}
            for p, v in sorted(groups.items())}


def gate(m: dict[str, Any]) -> dict[str, Any]:
    out = {
        "citation_precision": m["citation_precision"],
        "citation_precision_ok": (m["citation_precision"] or 0) >= GATE["citation_precision"],
        "not_found": m["not_found_correct"],
        "not_found_ok": m["not_found_correct"] == GATE["not_found"],
        "acl_leaks": m["acl_leaks_total"], "acl_ok": m["acl_leaks_total"] == 0,
        "p95_ms": m["latency_p95_ms"],
        "p95_ok": (m["latency_p95_ms"] or 1e9) < GATE["p95_ms"],
    }
    out["pass"] = all(v for k, v in out.items() if k.endswith("_ok"))
    return out


def _count_warnings(sel: list[dict[str, Any]]) -> dict[str, int]:
    c: dict[str, int] = defaultdict(int)
    for r in sel:
        for w in r["warnings"]:
            c[w["type"]] += 1
    return c


def run(items: list[dict[str, Any]], settings: Any, acl_file: Any, *,
        min_rerank: float | None = None, prompt_version: str | None = None) -> dict[str, Any]:
    from solaris.rag.answer import DEFAULT_GATE, EvidenceGate, K, answer_question
    from solaris.rag.crosslingual import retrieve_bilingual

    acl = json.loads(acl_file.read_text(encoding="utf-8"))
    ev_gate = DEFAULT_GATE if min_rerank is None else EvidenceGate(min_rerank=min_rerank)
    # Calentamiento (carga de e5 y del reranker, como el arranque de la API): no cuenta.
    retrieve_bilingual(principal_for("inaki.calidad", acl_file), "calentamiento", K,
                       settings=settings)
    rows = []
    for it in items:
        p = principal_for(it["user"], acl_file)
        t0 = time.perf_counter()
        try:
            res = answer_question(p, it["question"], settings=settings, gate=ev_gate,
                                  **({"prompt_version": prompt_version} if prompt_version else {}))
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
            "retrieval_ms": res.debug.get("retrieval_ms"),
            "retrieval_trace": res.debug.get("retrieval_trace"),
            "llm_latency_ms": llm.get("latency_ms"), "provider": llm.get("provider"),
            "used_fallback": llm.get("used_fallback"),
            "cost_usd": llm.get("cost_usd"), "prompt_tokens": llm.get("prompt_tokens"),
            "completion_tokens": llm.get("completion_tokens"),
            "gated": res.debug.get("gate") == "below_threshold",
            "top_rerank": _r(res.debug.get("top_rerank")),
            "retrieved": res.debug.get("hits"), "model_not_found": res.debug.get(
                "model_not_found"), "asked": res.debug.get("asked"),
            "asked_in_sources": res.debug.get("asked_in_sources"),
            "source_term": res.debug.get("source_term"),
            "dropped": res.debug.get("dropped"), "capped": res.debug.get("capped"),
            "expected_citations": it.get("expected_citations"),
            "must_include": it.get("must_include"), "must_not_claim": it.get("must_not_claim"),
        }
        row["score"] = score_item(it, res, acl, p.role)
        rows.append(row)
        sc = row["score"]
        extra = (f"cit {sc.get('citations_ok')}/{sc.get('citations_total')}"
                 if it["category"] in CITABLE else f"nf={res.not_found}")
        print(f"{it['id']} {it['category']:<13} {extra:<10} {row['latency_ms']:>7.0f} ms "
              f"ret={(row['retrieval_ms'] or {}).get('total')} llm={row['llm_latency_ms']} "
              f"{row['provider']}")
    ok_rows = [r for r in rows if "error" not in r]
    return {"items": rows, "errors": [r for r in rows if "error" in r],
            "metrics": aggregate(ok_rows)}
