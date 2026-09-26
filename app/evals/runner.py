"""Runner de evals de Solaris (M2-T7). Lee el golden set; nunca lo expone al producto (PAT-004).

Uso (desde la raíz del repo):
    uv run --project app/backend python app/evals/runner.py --suite retrieval [--config default]
    uv run --project app/backend python app/evals/runner.py --suite retrieval --config all
    uv run --project app/backend python app/evals/runner.py --suite containment
    uv run --project app/backend python app/evals/runner.py --suite qa [--label x]  # LLM (~0,07 $)
    uv run --project app/backend python app/evals/runner.py --suite qa --calibrate  # sin LLM
    uv run --project app/backend python app/evals/runner.py --suite 8d   # M3-T3 (LLM)
    uv run --project app/backend python app/evals/runner.py --suite complaints  # M3-T2 (5 llamadas)

Suites:
  * `retrieval` (sin LLM): `retrieve_as(Principal del usuario del ítem)` sobre `golden/qa.jsonl`.
    Recall@k de citas (doc_id + versión + locator compatible, y variante solo doc_id), MRR,
    cobertura de `required_doc_ids`, ACL (0 fragmentos prohibidos o de carpetas no visibles),
    puntuaciones máximas en "no encontrado" (para calibrar el umbral de M2-T6), latencia p50/p95 y
    desglose por categoría. Con varias configuraciones escribe además una comparativa.
  * `containment` (sin LLM): herramienta MCP `containment_scope` vía `solaris.mcp_obo` como
    `inaki.calidad` para los 5 casos de `golden/8d_cases.jsonl`, frente a `expected_d3_containment`.
  * `qa` (LLM real): `/ask` (solaris.rag.answer.answer_question) por ítem como su usuario, con la
    recuperación del producto. Precisión de citas, "no encontrado", ACL, latencia p50/p95 (total,
    recuperación, LLM y por proveedor) y coste; gate de M2 en `metrics.gate` (qa_suite.py).
    `--calibrate`: solo recuperación, para el umbral de "no encontrado".
  * `8d` (LLM real, M3-T3): grafo 8D D1–D4 por caso de `golden/8d_cases.jsonl` como su usuario
    (eightd_suite.py): tiempo, similares, hipótesis con fila del AMFE, contención y must_not.

Salida: un JSON por ejecución en raw/eval-runs/<fecha>_<suite>_<config>.json (raw/ es de solo
anexar: si el nombre existe se añade un sufijo) y un resumen por consola.

Top-k: cada configuración se ejecuta una vez con k = max(--k) y las métricas @k se calculan sobre
el prefijo. Es equivalente a ejecutar con cada k porque el ranking no depende de k mientras
k ≤ rerank_pool (el pool del rerank es max(rerank_pool, k)); el runner lo comprueba.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import platform
import subprocess
import sys
import time
from collections import defaultdict
from dataclasses import asdict, dataclass, replace
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

EVALS_DIR = Path(__file__).resolve().parent
REPO_ROOT = EVALS_DIR.parents[1]
if str(EVALS_DIR) not in sys.path:
    sys.path.insert(0, str(EVALS_DIR))

import scoring  # noqa: E402

GOLDEN_DIR = EVALS_DIR / "golden"
QA_FILE = GOLDEN_DIR / "qa.jsonl"
CASES_FILE = GOLDEN_DIR / "8d_cases.jsonl"
MANIFEST = REPO_ROOT / "app" / "data" / "synthetic" / "docs" / "manifest.json"
ACL_FILE = REPO_ROOT / "app" / "data" / "synthetic" / "acl.json"
OUT_DIR = REPO_ROOT / "raw" / "eval-runs"
EVAL_SID = "eval-runner"  # sid del Principal sintético del runner (no hay sesión HTTP)
PRIMARY_K = 8
CITABLE = ("factual", "recurrence", "multilingual")

# Configuraciones de recuperación comparables (sobre solaris.rag.retrieve.DEFAULT_CONFIG).
# Recuperación tal como la midió M2-T6 (sin referencia a documento, expansión ni traducción).
_M2T6 = {"doc_ref": False, "expand_sections": (), "_xling": False}
PRESETS: dict[str, dict[str, Any]] = {
    "default": {},
    "m2t6": _M2T6,
    "nodocref": {"doc_ref": False},
    "noexpand": {"expand_sections": ()},
    "expand_p1": {"expand_parts": 1},
    "expand_d4d2": {"expand_sections": ("D4", "D2")},
    "expand_max2": {"expand_max_docs": 2},
    "expand_insert": {"expand_replace": False},
    "expand_p1_max4": {"expand_parts": 1, "expand_max_docs": 4},
    "rerank800": {"rerank_max_chars": 800},
    "norerank_m2t6": {**_M2T6, "rerank": False},
    "noxling": {"_xling": False},
    "xling_norerank": {"rerank": False},
    "xling_rerank800": {"rerank_max_chars": 800},
    "xling_walt05": {"w_alt": 0.5},
    "norerank": {"rerank": False},
    "rerank_mpd3": {"max_per_doc": 3},
    "norerank_mpd3": {"rerank": False, "max_per_doc": 3},
    "rerank_mpd1": {"max_per_doc": 1, "pool_per_doc": 2},
    "norerank_mpd1": {"rerank": False, "max_per_doc": 1},
    "rerank_pool24": {"rerank_pool": 24},
}

# Sondas de regresión de M2-T5 (NO son parte del golden set ni del gate): consultas cuya
# degradación con rerank quedó anotada en raw/sessions/2026-09-25_dev_M2-T5.md.
PROBES: list[dict[str, Any]] = [
    {"id": "PROBE-MT07-S6", "user": "inaki.calidad", "question": "Intervalo de afilado de MT-07",
     "expected_citations": [{"doc_id": "IT-L1-MT07-01", "version": "v2",
                             "locator": {"section": "6. Afilado"}}],
     "why": "M2-T5 consulta 3: IT-L1-MT07-01 §6 n.º 2 sin rerank, fuera del top-5 con rerank"},
    {"id": "PROBE-EN-ES-NOZZLE", "user": "inaki.calidad",
     "question": "What is the nozzle replacement frequency on the CR-01 welding cell?",
     "expected_citations": [{"doc_id": "IT-L2-CR01-03", "version": "v3",
                             "locator": {"page": 2}}],
     "why": "M2-T5 consulta 4: la IT en ES quedaba fuera del top-5 con bge-reranker-base"},
]


# --- utilidades comunes -------------------------------------------------------------------------


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_info() -> dict[str, Any]:
    def run(*args: str) -> str:
        try:
            return subprocess.run(  # noqa: S603
                ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True,  # noqa: S607
                timeout=10,
            ).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return ""

    return {"commit": run("rev-parse", "HEAD") or None,
            "dirty": bool(run("status", "--porcelain", "--untracked-files=no"))}


def run_metadata(suite: str, config_name: str) -> dict[str, Any]:
    return {
        "suite": suite,
        "config_name": config_name,
        "started_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "git": git_info(),
        "corpus": {"manifest": str(MANIFEST.relative_to(REPO_ROOT)),
                   "manifest_sha256": sha256_file(MANIFEST)},
        "golden": {"qa_sha256": sha256_file(QA_FILE), "cases_sha256": sha256_file(CASES_FILE)},
        "python": platform.python_version(),
    }


def out_path(suite: str, config_name: str, out_dir: Path, day: str) -> Path:
    base = out_dir / f"{day}_{suite}_{config_name}.json"
    n = 2
    p = base
    while p.exists():  # raw/ es de solo anexar: nunca se sobrescribe una ejecución anterior
        p = base.with_name(f"{base.stem}_{n}.json")
        n += 1
    return p


def write_json(obj: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1, default=str) + "\n",
                    encoding="utf-8")


def _r(v: float | None, nd: int = 3) -> float | None:
    return None if v is None else round(v, nd)


def _pct(v: float | None) -> str:
    return "  —  " if v is None else f"{v * 100:5.1f}"


# --- suite retrieval ----------------------------------------------------------------------------


def item_tags(it: dict[str, Any]) -> list[str]:
    cat = it["category"]
    tags = [cat]
    if cat in CITABLE:
        tags.append("citable")
    if it.get("subcategory"):
        tags.append(f"{cat}/{it['subcategory']}")
    if it.get("requires_ocr"):
        tags.append(f"{cat}/escaneado_ocr")
    if it.get("dirty_amfe"):
        tags.append(f"{cat}/amfe_sucio")
    if cat == "multilingual":
        tags.append(f"multilingual/{it.get('question_lang')}→{it.get('doc_lang')}")
    return tags


def _hit_row(h: Any) -> dict[str, Any]:
    return {"rank": h.rank, "doc_id": h.doc_id, "version": h.version, "locator": h.locator,
            "folder": h.folder, "doc_type": h.doc_type, "rerank": _r(h.rerank),
            "fusion": _r(h.fusion, 5), "vector": _r(h.vector), "bm25": _r(h.bm25),
            "lexical_rank": h.lexical_rank, "vector_rank": h.vector_rank}


def _max(vals: list[float | None]) -> float | None:
    xs = [v for v in vals if v is not None]
    return max(xs) if xs else None


@dataclass
class RetrievalRun:
    name: str
    overrides: dict[str, Any]
    k_list: list[int]


def score_item(it: dict[str, Any], hits: list[dict[str, Any]], k_list: list[int],
               visible: list[str]) -> dict[str, Any]:
    exp = it.get("expected_citations") or []
    r_loc = scoring.first_match_rank(exp, hits) if exp else None
    r_doc = scoring.first_match_rank(exp, hits, doc_only=True) if exp else None
    out: dict[str, Any] = {"first_match_rank": r_loc, "first_match_rank_doc": r_doc}
    if exp:
        out["hit_at"] = {str(k): scoring.hit_at_k(r_loc, k) for k in k_list}
        out["hit_doc_at"] = {str(k): scoring.hit_at_k(r_doc, k) for k in k_list}
    if it.get("required_doc_ids"):
        out["required_docs_at"] = {
            str(k): scoring.required_docs_covered(it["required_doc_ids"], hits, k)[1]
            for k in k_list
        }
    out["acl_violations"] = scoring.acl_violations(
        hits, visible_folders=visible, forbidden_doc_ids=it.get("forbidden_doc_ids", ()),
        forbidden_folders=it.get("forbidden_folders", ()),
    )
    out["max_scores"] = {
        "rerank_top1": hits[0]["rerank"] if hits else None,
        "rerank_max": _max([h["rerank"] for h in hits]),
        "fusion_max": _max([h["fusion"] for h in hits]),
        "vector_max": _max([h["vector"] for h in hits]),
        "bm25_max": _max([h["bm25"] for h in hits]),
    }
    return out


def aggregate(items: list[dict[str, Any]], k_list: list[int]) -> dict[str, Any]:
    by_tag: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for it in items:
        for t in it["tags"]:
            by_tag[t].append(it)
    groups: dict[str, Any] = {}
    for tag, its in sorted(by_tag.items()):
        g: dict[str, Any] = {"n": len(its)}
        scored = [i for i in its if i["expected_citations"]]
        if scored:
            rl = [i["score"]["first_match_rank"] for i in scored]
            rd = [i["score"]["first_match_rank_doc"] for i in scored]
            g["recall_at"] = {str(k): _r(scoring.recall_at_k(rl, k)) for k in k_list}
            g["recall_doc_at"] = {str(k): _r(scoring.recall_at_k(rd, k)) for k in k_list}
            g["mrr"] = _r(scoring.mrr(rl, PRIMARY_K))
            g["mrr_doc"] = _r(scoring.mrr(rd, PRIMARY_K))
        req = [i for i in its if "required_docs_at" in i["score"]]
        if req:
            g["required_docs_at"] = {
                str(k): _r(sum(not i["score"]["required_docs_at"][str(k)] for i in req) / len(req))
                for k in k_list
            }
        g["acl_violations"] = sum(len(i["score"]["acl_violations"]) for i in its)
        lat = [i["latency_ms"]["total"] for i in its]
        g["latency_ms_p50"] = _r(scoring.percentile(lat, 50), 1)
        g["latency_ms_p95"] = _r(scoring.percentile(lat, 95), 1)
        groups[tag] = g
    return groups


def calibration(items: list[dict[str, Any]]) -> dict[str, Any]:
    """Separabilidad de "no encontrado" por la puntuación máxima (para el umbral de M2-T6)."""
    def stats(sel: list[dict[str, Any]], key: str) -> dict[str, Any]:
        xs = [i["score"]["max_scores"][key] for i in sel
              if i["score"]["max_scores"][key] is not None]
        return {"n": len(xs), "min": _r(min(xs)) if xs else None,
                "p10": _r(scoring.percentile(xs, 10)), "median": _r(scoring.percentile(xs, 50)),
                "max": _r(max(xs)) if xs else None}

    answer = [i for i in items if i["category"] in CITABLE
              and i["score"]["first_match_rank_doc"] is not None]
    nf = [i for i in items if i["category"] == "not_found"]
    acl = [i for i in items if i["category"] == "acl_negative"]
    out: dict[str, Any] = {}
    for key in ("rerank_top1", "vector_max", "fusion_max", "bm25_max"):
        out[key] = {"answerable_found": stats(answer, key), "not_found": stats(nf, key),
                    "acl_negative": stats(acl, key)}
    out["not_found_items"] = {i["id"]: i["score"]["max_scores"] for i in nf}
    out["acl_negative_items"] = {i["id"]: i["score"]["max_scores"] for i in acl}
    return out


def run_retrieval(run: RetrievalRun, items: list[dict[str, Any]], acl: dict[str, Any],
                  settings: Any) -> dict[str, Any]:
    from solaris.auth.core import Principal
    from solaris.rag.acl import resolve_role
    from solaris.rag.crosslingual import retrieve_bilingual
    from solaris.rag.retrieve import DEFAULT_CONFIG, RetrievalTrace, retrieve_as

    overrides = dict(run.overrides)
    xling = overrides.pop("_xling", settings.rag_cross_lingual == "translate")
    cfg = replace(DEFAULT_CONFIG, **overrides)
    k_run = max(run.k_list)
    use_rerank = cfg.rerank and settings.rerank_backend != "none"
    if use_rerank and k_run > cfg.rerank_pool:
        raise SystemExit(f"k={k_run} > rerank_pool={cfg.rerank_pool}: las métricas @k por prefijo "
                         "no serían equivalentes. Baja --k o sube rerank_pool.")

    principals: dict[str, Any] = {}

    def principal(user: str) -> Any:
        if user not in principals:
            role = resolve_role(user, settings.acl_file)
            if role is None:
                raise SystemExit(f"Usuario del golden sin rol en acl.json: {user}")
            principals[user] = Principal(user, role, EVAL_SID)
        return principals[user]

    # Calentamiento (carga de e5 y del reranker): no cuenta en la latencia.
    retrieve_as(principal("inaki.calidad"), "calentamiento del runner", k=k_run, config=cfg)

    rows: list[dict[str, Any]] = []
    for it in [*items, *PROBES]:
        p = principal(it["user"])
        tr = RetrievalTrace(user=p.user, role=None)
        t0 = time.perf_counter()
        if xling:  # mismo camino que /ask: traducción en paralelo con la consulta original
            hits = retrieve_bilingual(p, it["question"], k_run, settings=settings, config=cfg,
                                      trace=tr)
        else:
            hits = retrieve_as(p, it["question"], k=k_run, config=cfg, trace=tr)
        wall = (time.perf_counter() - t0) * 1000
        tr.timings_ms["total"] = round(wall, 1)  # incluye la espera de la traducción
        hrows = [_hit_row(h) for h in hits]
        visible = scoring.visible_folders_for(p.role, acl)
        probe = it["id"].startswith("PROBE-")
        rows.append({
            "id": it["id"], "user": it["user"], "role": p.role,
            "category": "probe" if probe else it["category"],
            "tags": ["probe"] if probe else item_tags(it),
            "question": it["question"],
            "expected_citations": it.get("expected_citations") or [],
            "required_doc_ids": it.get("required_doc_ids"),
            "latency_ms": {**tr.timings_ms, "wall": round(wall, 1)},
            "alt_queries": tr.alt_queries, "translate_status": tr.translate_status,
            "candidates": tr.candidates, "reranked": tr.reranked,
            "score": score_item(it, hrows, run.k_list, visible),
            "hits": hrows,
        })

    golden_rows = [r for r in rows if r["category"] != "probe"]
    lat = [r["latency_ms"]["total"] for r in golden_rows]
    phases = {ph: _r(scoring.percentile([r["latency_ms"].get(ph, 0.0) for r in golden_rows], 50),
                     1) for ph in ("alt_wait", "embed", "sql", "rerank")}
    acl_total = sum(len(r["score"]["acl_violations"]) for r in rows)
    groups = aggregate(golden_rows, run.k_list)
    fact = groups.get("factual", {})
    gate = {
        "acl_violations": acl_total,
        "acl_ok": acl_total == 0,
        "factual_recall_doc_at_8": fact.get("recall_doc_at", {}).get(str(PRIMARY_K)),
        "factual_recall_doc_at_8_ok": (fact.get("recall_doc_at", {}).get(str(PRIMARY_K)) or 0)
        >= 0.90,
    }
    return {
        "config": {"name": run.name, "overrides": run.overrides, **asdict(cfg),
                   "k_run": k_run, "k_list": run.k_list, "primary_k": PRIMARY_K,
                   "cross_lingual": "translate" if xling else "none",
                   "rerank_effective": use_rerank, "rerank_backend": settings.rerank_backend,
                   "rerank_model": settings.rerank_model if use_rerank else None,
                   "embed_backend": getattr(settings, "embed_backend", None)},
        "metrics": {
            "n_items": len(golden_rows),
            "latency_ms": {"p50": _r(scoring.percentile(lat, 50), 1),
                           "p95": _r(scoring.percentile(lat, 95), 1),
                           "max": _r(max(lat), 1) if lat else None, "phase_p50": phases},
            "by_group": groups,
            "not_found_calibration": calibration(golden_rows),
            "probes": {r["id"]: {"first_match_rank": r["score"]["first_match_rank"],
                                 "first_match_rank_doc": r["score"]["first_match_rank_doc"],
                                 "top5": [f"{h['doc_id']} {_loc(h['locator'])}"
                                          for h in r["hits"][:5]]}
                       for r in rows if r["category"] == "probe"},
            "gate": gate,
        },
        "items": rows,
    }


def _loc(loc: dict[str, Any]) -> str:
    if "page" in loc:
        s = f"p{loc['page']}"
    elif "sheet" in loc:
        a, b = scoring.parse_rows(loc.get("rows")) or ("?", "?")
        s = f"{loc['sheet']}!{a}-{b}"
    else:
        s = str(loc.get("heading") or loc.get("section", ""))[:40]
    return f"{s}#{loc['part']}" if "part" in loc else s


REPORT_GROUPS = [
    "factual", "factual/IT", "factual/escaneado_ocr", "factual/AMFE", "factual/amfe_sucio",
    "factual/PC", "factual/mantenimiento", "factual/8D", "factual/COST", "recurrence",
    "multilingual", "multilingual/en→es", "multilingual/es→en", "citable",
]


def print_retrieval(res: dict[str, Any]) -> None:
    m, c = res["metrics"], res["config"]
    print(f"\n=== retrieval · {c['name']} · rerank={c['rerank_effective']} "
          f"cross_lingual={c['cross_lingual']} "
          f"max_per_doc={c['max_per_doc']} pool_per_doc={c['pool_per_doc']} "
          f"rerank_pool={c['rerank_pool']} k={c['k_list']} ===")
    ks = [k for k in c["k_list"] if k in (1, 3, 5, 8, 12)]
    head = " ".join(f"@{k:<4}" for k in ks)
    print(f"{'grupo':<24} {'n':>3} | loc {head} | doc {head} | MRR loc/doc | req@8")
    for g in REPORT_GROUPS:
        s = m["by_group"].get(g)
        if not s or "recall_at" not in s:
            continue
        loc = " ".join(_pct(s["recall_at"][str(k)]) for k in ks)
        doc = " ".join(_pct(s["recall_doc_at"][str(k)]) for k in ks)
        req = s.get("required_docs_at", {}).get(str(PRIMARY_K))
        print(f"{g:<24} {s['n']:>3} | {loc} | {doc} | {s['mrr']:.3f}/{s['mrr_doc']:.3f} | "
              f"{_pct(req) if req is not None else '  —  '}")
    lat = m["latency_ms"]
    print(f"latencia retrieve (ms): p50={lat['p50']} p95={lat['p95']} max={lat['max']} "
          f"fases p50={lat['phase_p50']}")
    g = m["gate"]
    print(f"ACL: {g['acl_violations']} violaciones ({'OK' if g['acl_ok'] else 'FALLO CRÍTICO'}) · "
          f"Recall@8 doc factual = {_pct(g['factual_recall_doc_at_8'])} % "
          f"({'OK' if g['factual_recall_doc_at_8_ok'] else '< 90 %'})")
    key = "rerank_top1" if c["rerank_effective"] else "vector_max"
    cal = m["not_found_calibration"][key]
    ans = cal["answerable_found"]
    print(f"calibración 'no encontrado' ({key}): respondibles min/p10={ans['min']}/{ans['p10']}"
          f" · not_found max={cal['not_found']['max']}"
          f" · acl_negative max={cal['acl_negative']['max']}")
    for pid, p in m["probes"].items():
        print(f"sonda {pid}: rango loc={p['first_match_rank']} doc={p['first_match_rank_doc']}")
    misses = [i for i in res["items"] if i["category"] in CITABLE
              and not scoring.hit_at_k(i["score"]["first_match_rank_doc"], PRIMARY_K)]
    for i in misses:
        print(f"  FALLO doc@8 {i['id']} [{i['category']}] esperado "
              f"{sorted({e['doc_id'] for e in i['expected_citations']})} · top3 "
              f"{[h['doc_id'] + ' ' + _loc(h['locator']) for h in i['hits'][:3]]}")


def comparison(results: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for res in results:
        m, c = res["metrics"], res["config"]
        bg = m["by_group"]

        def g(tag: str, key: str, k: int = PRIMARY_K, _bg: dict = bg) -> float | None:
            v = _bg.get(tag, {}).get(key)
            return v.get(str(k)) if isinstance(v, dict) else v

        rows.append({
            "config": c["name"], "rerank": c["rerank_effective"], "max_per_doc": c["max_per_doc"],
            "rerank_pool": c["rerank_pool"],
            "factual_loc@8": g("factual", "recall_at"),
            "factual_doc@8": g("factual", "recall_doc_at"),
            "factual_doc@5": g("factual", "recall_doc_at", 5),
            "citable_loc@8": g("citable", "recall_at"),
            "citable_doc@8": g("citable", "recall_doc_at"),
            "citable_loc@3": g("citable", "recall_at", 3),
            "mrr_citable": bg.get("citable", {}).get("mrr"),
            "mrr_doc_citable": bg.get("citable", {}).get("mrr_doc"),
            "recurrence_req@8": g("recurrence", "required_docs_at"),
            "multilingual_loc@8": g("multilingual", "recall_at"),
            "ocr_loc@8": g("factual/escaneado_ocr", "recall_at"),
            "amfe_sucio_loc@8": g("factual/amfe_sucio", "recall_at"),
            "acl_violations": m["gate"]["acl_violations"],
            "p50_ms": m["latency_ms"]["p50"], "p95_ms": m["latency_ms"]["p95"],
            "probe_mt07_rank": m["probes"].get("PROBE-MT07-S6", {}).get("first_match_rank"),
            "probe_en_es_rank": m["probes"].get("PROBE-EN-ES-NOZZLE", {}).get("first_match_rank"),
        })
    return {"rows": rows}


def print_comparison(cmp: dict[str, Any]) -> None:
    cols = ["config", "factual_loc@8", "factual_doc@8", "citable_loc@8", "citable_loc@3",
            "mrr_citable", "recurrence_req@8", "multilingual_loc@8", "acl_violations",
            "p50_ms", "p95_ms", "probe_mt07_rank", "probe_en_es_rank"]
    print("\n=== comparativa ===")
    print(" | ".join(cols))
    for r in cmp["rows"]:
        print(" | ".join(str(r[c]) for c in cols))


def suite_retrieval(args: argparse.Namespace) -> int:
    from solaris.settings import get_settings

    settings = get_settings()
    items = load_jsonl(QA_FILE)
    if args.only:
        items = [i for i in items if i["id"] in set(args.only)]
    acl = json.loads(ACL_FILE.read_text(encoding="utf-8"))
    names = list(PRESETS) if args.config == ["all"] else args.config
    unknown = [n for n in names if n not in PRESETS]
    if unknown:
        raise SystemExit(f"Configuraciones desconocidas: {unknown}. Disponibles: {list(PRESETS)}")
    results = []
    for name in names:
        meta = run_metadata("retrieval", name)
        res = {**meta, **run_retrieval(RetrievalRun(name, PRESETS[name], args.k), items, acl,
                                       settings)}
        res["finished_at"] = datetime.now(UTC).isoformat(timespec="seconds")
        results.append(res)
        print_retrieval(res)
        if not args.no_write:
            p = out_path("retrieval", name, args.out_dir, args.date)
            write_json(res, p)
            print(f"→ {p.relative_to(REPO_ROOT) if p.is_relative_to(REPO_ROOT) else p}")
    if len(results) > 1:
        cmp = {**run_metadata("retrieval", "compare"), **comparison(results),
               "runs": [r["config"]["name"] for r in results]}
        print_comparison(cmp)
        if not args.no_write:
            p = out_path("retrieval", "compare", args.out_dir, args.date)
            write_json(cmp, p)
            print(f"→ {p.relative_to(REPO_ROOT) if p.is_relative_to(REPO_ROOT) else p}")
    return 0 if all(r["metrics"]["gate"]["acl_ok"] for r in results) else 1


# --- suite containment --------------------------------------------------------------------------

# Consulta de alcance que debe lanzar el orquestador 8D (M3-T3) en cada caso: piezas + lote de
# material sospechoso, deducidos de la reclamación y de la trazabilidad del lote reclamado.
# `expect` elige el bloque de expected_d3_containment con el que se compara.
SCOPE_QUERIES: dict[str, list[dict[str, Any]]] = {
    "8D-CASE-01": [{"part_refs": ["AR-1003", "AR-1004"], "material_lot_code": "S-GOIE-260117",
                    "expect": None}],
    # Caso 2: el criterio es de utillaje (contador de MT-07), no de lote de material.
    # containment_scope no puede expresarlo: el alcance mínimo (lote reclamado y posteriores) se
    # comprueba con find_lots + get_shipments. La llamada a containment_scope con el lote de acero
    # del lote reclamado queda como informativa (no cuenta en el PASS) para documentar el hueco.
    "8D-CASE-02": [{"tool": "find_lots_from_claimed_lot", "part_ref": "AR-1007",
                    "claimed_lot": "L26245-AR1007-01", "expect": "minimum"},
                   {"tool": "containment_scope_claimed_steel", "part_refs": ["AR-1007"],
                    "claimed_lot": "L26245-AR1007-01", "expect": "minimum", "informative": True}],
    "8D-CASE-03": [{"part_refs": ["AR-1009"], "material_lot_code": "S-GOIE-260117",
                    "expect": "recommended"}],
    "8D-CASE-04": [{"part_refs": ["AR-1012"], "material_lot_code": "S-ULTZ-260209",
                    "expect": None}],
    "8D-CASE-05": [{"part_refs": ["AR-1010"], "material_lot_code": "S-BIDA-260136",
                    "expect": "minimum"},
                   {"part_refs": ["AR-1006", "AR-1010"], "material_lot_code": "S-BIDA-260136",
                    "expect": "recommended"}],
}
FIND_LOTS_TO = "2026-09-25"  # fecha de la ejecución del escenario (último día con datos del ERP)


def _scope_from_containment(data: dict[str, Any]) -> dict[str, Any]:
    parts = data.get("parts") or []
    return {
        "lots": sorted(x["lot_code"] for p in parts for x in p.get("lot_detail", [])),
        "shipments": sorted(s["shipment_id"] for p in parts for s in p.get("shipment_detail", [])),
        "shipped_qty": sum(p.get("qty_shipped", 0) for p in parts),
        "lots_in_stock": sorted(x for p in parts for x in p.get("lots_in_stock", [])),
        "per_part": {p["part_ref"]: p["lots"] for p in parts},
        # M3-T3 (F05): piezas buenas sin expedir por lote (la herramienta lo calcula desde el seed).
        "qty_not_shipped": {x["lot_code"]: x["qty_not_shipped"] for p in parts
                            for x in p.get("lot_detail", []) if x.get("qty_not_shipped")},
        "qty_not_shipped_invariant": all(
            x.get("qty_ok", 0) == x.get("qty_shipped", 0) + x.get("qty_not_shipped", 0)
            for p in parts for x in p.get("lot_detail", []) if "qty_ok" in x),
    }


def compare_containment(expected: dict[str, Any], got: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {
        "lots": scoring.compare_sets(expected.get("lots", []), got.get("lots", [])),
    }
    if "shipments" in got:
        out["shipments"] = scoring.compare_sets(expected.get("shipments", []), got["shipments"])
    if "shipped_qty" in got:
        out["shipped_qty"] = {"expected": expected.get("shipped_qty"), "got": got["shipped_qty"],
                              "exact": expected.get("shipped_qty") == got["shipped_qty"]}
    if "lots_in_stock" in got:
        out["lots_in_stock"] = scoring.compare_sets(expected.get("lots_in_stock", []),
                                                    got["lots_in_stock"])
    if "per_part" in expected and "per_part" in got:
        out["per_part"] = {"expected": expected["per_part"], "got": got["per_part"],
                           "exact": expected["per_part"] == got["per_part"]}
    # Recall de lotes 100 % obligatorio (los extra se reportan); albaranes, cantidad, stock y
    # reparto por pieza, exactos (golden/README.md, "Contención").
    if "qty_not_shipped" in got:
        # Sin verdad en scenario_truth.json todavía (propuesta a product en la traza de M3-T3):
        # se comprueba el invariante buenas = enviadas + sin expedir y, si el golden lo trae,
        # la igualdad por lote.
        out["qty_not_shipped"] = {
            "expected": expected.get("qty_not_shipped"), "got": got["qty_not_shipped"],
            "exact": got.get("qty_not_shipped_invariant", True) and (
                "qty_not_shipped" not in expected
                or expected["qty_not_shipped"] == got["qty_not_shipped"])}
    out["pass"] = out["lots"]["recall"] == 1.0 and all(
        v["exact"] for k, v in out.items() if k != "lots" and isinstance(v, dict))
    out["not_checked"] = sorted(
        ({"qty_not_shipped"} if "qty_not_shipped" not in expected else set())
        | ({"lots_produced_after_notification"} & set(expected)))
    return out


async def _containment(cases: list[dict[str, Any]], settings: Any) -> list[dict[str, Any]]:
    from solaris.auth.core import Principal
    from solaris.mcp_obo import call_erp_tool
    from solaris.rag.acl import resolve_role

    from mcp_stdio import StdioToolSession

    rows = []
    async with StdioToolSession.erp_mock() as session:
        for case in cases:
            user = case["user"]
            role = resolve_role(user, settings.acl_file)
            p = Principal(user, role or "", EVAL_SID)
            exp_all = case["expected_d3_containment"]
            for q in SCOPE_QUERIES.get(case["case_id"], []):
                expected = exp_all[q["expect"]] if q["expect"] else exp_all
                t0 = time.perf_counter()
                if q.get("tool") == "find_lots_from_claimed_lot":
                    lot = await call_erp_tool(session, p, "get_lot", {"lot_code": q["claimed_lot"]},
                                              settings=settings)
                    start = lot.data["data"]["lot"]["production_date"]
                    args = {"part_ref": q["part_ref"], "from_date": start, "to_date": FIND_LOTS_TO}
                    r = await call_erp_tool(session, p, "find_lots", args, settings=settings)
                    tool = "find_lots+get_shipments"
                    lots = r.data["data"]["lots"] if not r.is_error else []
                    ships: list[dict[str, Any]] = []
                    for x in lots:
                        rs = await call_erp_tool(session, p, "get_shipments",
                                                 {"lot_code": x["lot_code"]}, settings=settings)
                        ships += rs.data["data"]["shipments"] if not rs.is_error else []
                    got = {"lots": sorted(x["lot_code"] for x in lots),
                           "shipments": sorted(x["shipment_id"] for x in ships),
                           "shipped_qty": sum(x["qty"] for x in ships),
                           "lots_in_stock": sorted(x["lot_code"] for x in lots
                                                   if x["status"] == "in_stock")}
                else:
                    material = q.get("material_lot_code")
                    if q.get("tool") == "containment_scope_claimed_steel":
                        lot = await call_erp_tool(session, p, "get_lot",
                                                  {"lot_code": q["claimed_lot"]}, settings=settings)
                        material = lot.data["data"]["lot"]["steel_lot_code"]
                    args = {"part_refs": q["part_refs"], "material_lot_code": material}
                    r = await call_erp_tool(session, p, "containment_scope", args,
                                            settings=settings)
                    tool = "containment_scope"
                    got = _scope_from_containment(r.data["data"]) if not r.is_error else {}
                ms = round((time.perf_counter() - t0) * 1000, 1)
                cmpres = compare_containment(expected, got) if not r.is_error else {
                    "pass": False, "error": r.text[:300]}
                rows.append({"case_id": case["case_id"], "complaint_id": case["complaint_id"],
                             "user": user, "tool": tool, "arguments": args,
                             "informative": bool(q.get("informative")),
                             "expected_block": q["expect"] or "lots", "latency_ms": ms,
                             "got": got, "comparison": cmpres,
                             "erp_query": (r.data or {}).get("query") if not r.is_error else None})
    return rows


def suite_containment(args: argparse.Namespace) -> int:
    from solaris.settings import get_settings

    settings = get_settings()
    cases = load_jsonl(CASES_FILE)
    meta = run_metadata("containment", "default")
    rows = asyncio.run(_containment(cases, settings))
    gated = [r for r in rows if not r["informative"]]
    ok = sum(r["comparison"]["pass"] for r in gated)
    by_case: dict[str, bool] = defaultdict(lambda: True)
    for r in gated:
        by_case[r["case_id"]] &= r["comparison"]["pass"]
    res = {**meta, "config": {"user": "inaki.calidad", "transport": "stdio",
                              "server": "app/mcp/erp_mock", "scope_queries": SCOPE_QUERIES},
           "metrics": {"queries": len(gated), "queries_pass": ok,
                       "informative_queries": len(rows) - len(gated),
                       "cases": len(by_case), "cases_pass": sum(by_case.values()),
                       "by_case": dict(by_case)},
           "items": rows, "finished_at": datetime.now(UTC).isoformat(timespec="seconds")}
    print("\n=== containment · MCP erp-mock vía mcp_obo (inaki.calidad) ===")
    for r in rows:
        c = r["comparison"]
        if "error" in c:
            print(f"{r['case_id']} {r['tool']}: ERROR {c['error']}")
            continue
        extra = ""
        if "shipments" in c:
            extra = (f" albaranes {c['shipments']['got']}/{c['shipments']['expected']}"
                     f" exact={c['shipments']['exact']} qty {c['shipped_qty']['got']}/"
                     f"{c['shipped_qty']['expected']}")
        verdict = ("informativa: " if r["informative"] else "") + ("PASS" if c["pass"] else "FAIL")
        lots = c["lots"]
        print(f"{r['case_id']} [{r['expected_block']}] {r['tool']} {r['arguments']}: {verdict}"
              f" · lotes {lots['got']}/{lots['expected']} recall={lots['recall']:.2f}"
              f" faltan={lots['missing']} extra={lots['extra']}{extra}"
              f" · stock={c.get('lots_in_stock', {}).get('exact')} · {r['latency_ms']} ms")
    print(f"casos PASS: {sum(by_case.values())}/{len(by_case)} · consultas PASS: {ok}/{len(gated)}")
    for r in rows:
        q = r["got"].get("qty_not_shipped")
        if q:
            print(f"{r['case_id']} qty_not_shipped (propuesta de verdad): {q}")
    print("no comprobado por la herramienta: lots_produced_after_notification (fecha de la "
          "notificación, lo calcula el grafo 8D); qty_not_shipped solo invariante (sin verdad)")
    if not args.no_write:
        p = out_path("containment", "default", args.out_dir, args.date)
        write_json(res, p)
        print(f"→ {p.relative_to(REPO_ROOT) if p.is_relative_to(REPO_ROOT) else p}")
    return 0 if ok == len(gated) else 1


# --- suites con LLM (M2-T6, M3-T3) --------------------------------------------------------------


def _need_llm(suite: str, pending: str) -> int:
    from solaris.settings import get_settings

    key = get_settings().openrouter_api_key
    if key is None or not key.get_secret_value():
        print(f"Suite `{suite}`: requiere OPENROUTER_API_KEY en .env (ADR-0003). No se ejecuta.")
        return 2
    print(f"Suite `{suite}`: pendiente de {pending}. Métricas previstas en scoring.py "
          "(citation_precision, must_include_hits, contención y recall de similares).")
    return 2


def suite_qa(args: argparse.Namespace) -> int:
    """`/ask` por ítem como su usuario (qa_suite.py). Con --calibrate, solo recuperación."""
    from solaris.settings import get_settings

    import qa_suite

    settings = get_settings()
    items = load_jsonl(QA_FILE)
    if args.only:
        items = [i for i in items if i["id"] in set(args.only)]
    if args.calibrate:
        ths = [float(x) for x in args.thresholds.split(",")]
        res = {**run_metadata("qa_calibration", "default"),
               **qa_suite.calibrate(items, ths, settings, ACL_FILE)}
        for row in res["thresholds"]:
            print(row)
        name, rc = "qa_calibration", 0
    else:
        key = settings.openrouter_api_key
        if key is None or not key.get_secret_value():
            print("Suite `qa`: requiere OPENROUTER_API_KEY en .env (ADR-0003). No se ejecuta.")
            return 2
        from solaris.llm import load_model_cards
        from solaris.rag.answer import (
            DEFAULT_GATE,
            MAX_ANSWER_TOKENS,
            MAX_CITATIONS,
            PROMPT_VERSION,
        )
        from solaris.rag.retrieve import DEFAULT_CONFIG

        cards = load_model_cards(settings.models_file)
        card = cards["rag_answer"]
        res = {**run_metadata("qa", args.label or "default"),
               "config": {
                   "task": "rag_answer", "model": card.model, "fallback": card.fallback,
                   "provider_policy": card.provider_policy.to_payload(),
                   "translate_model": cards["translate"].model,
                   "translate_provider_policy": cards["translate"].provider_policy.to_payload(),
                   "prompt_version": args.prompt_version or PROMPT_VERSION,
                   "max_citations": MAX_CITATIONS,
                   "max_answer_tokens": MAX_ANSWER_TOKENS,
                   "min_rerank": args.min_rerank if args.min_rerank is not None
                   else DEFAULT_GATE.min_rerank,
                   "retrieve": asdict(DEFAULT_CONFIG),
                   "cross_lingual": settings.rag_cross_lingual,
                   "translate_timeout_s": settings.rag_translate_timeout_s,
                   "rerank_backend": settings.rerank_backend, "rerank_model": settings.rerank_model,
                   "embed_model": settings.embed_model},
               **qa_suite.run(items, settings, ACL_FILE, min_rerank=args.min_rerank,
                              prompt_version=args.prompt_version)}
        name = f"qa_{card.model.replace('/', '-')}" + (f"_{args.label}" if args.label else "")
        m = res["metrics"]
        print(json.dumps({"overall": m["overall"], "gate": m["gate"],
                          "by_provider": m["by_provider"]}, ensure_ascii=False, indent=1))
        for cat in ("factual", "recurrence", "multilingual", "not_found", "acl_negative"):
            c = m["by_category"].get(cat, {})
            print(f"{cat:<13} precisión={c.get('citation_precision')} "
                  f"cobertura={c.get('coverage')} nf={c.get('not_found_correct')} "
                  f"p95={c.get('latency_p95_ms')}")
        rc = 0 if m["gate"]["pass"] and not res["errors"] else 1
    res["finished_at"] = datetime.now(UTC).isoformat(timespec="seconds")
    if not args.no_write:
        p = out_path(name.split("_", 1)[0], name.split("_", 1)[1] if "_" in name else "default",
                     args.out_dir, args.date)
        write_json(res, p)
        print(f"→ {p.relative_to(REPO_ROOT) if p.is_relative_to(REPO_ROOT) else p}")
    return rc


def suite_8d(args: argparse.Namespace) -> int:
    """M3-T3: grafo 8D D1–D4 por caso (eightd_suite.py): tiempo, similares, hipótesis con fila del
    AMFE, contención y must_not. LLM real: como mucho 2 pasadas completas por tarea."""
    from solaris.llm import load_model_cards
    from solaris.settings import get_settings

    settings = get_settings()
    key = settings.openrouter_api_key
    if key is None or not key.get_secret_value():
        print("Suite `8d`: requiere OPENROUTER_API_KEY en .env (ADR-0003). No se ejecuta.")
        return 2
    from solaris.agents.eight_d import nodes

    import eightd_suite

    cases = load_jsonl(CASES_FILE)
    if args.only:
        cases = [c for c in cases if c["case_id"] in set(args.only)]
    card = load_model_cards(settings.models_file)["8d_draft"]
    res = {**run_metadata("8d", card.model),
           "config": {"task": "8d_draft", "model": card.model, "fallback": card.fallback,
                      "provider_policy": card.provider_policy.to_payload(),
                      "prompts": [nodes.PROMPT_DESCRIBE, nodes.PROMPT_SIMILAR,
                                  nodes.PROMPT_HYPOTHESES],
                      "complaint_parse_model": load_model_cards(settings.models_file)[
                          "complaint_parse"].model,
                      "store": "postgres (eightd_app)", "erp": "MCP erp-mock (stdio) vía mcp_obo",
                      "cross_lingual": settings.rag_cross_lingual,
                      "rerank_backend": settings.rerank_backend,
                      "demo_target_s": eightd_suite.DEMO_TARGET_S},
           **eightd_suite.run(cases, settings, ACL_FILE, EVAL_SID)}
    res["finished_at"] = datetime.now(UTC).isoformat(timespec="seconds")
    m = res["metrics"]
    print(json.dumps({k: v for k, v in m.items()}, ensure_ascii=False))
    for it in res["items"]:
        if "elapsed_s" not in it:
            print(f"{it['case_id']}: ERROR {it['error']}")
            continue
        s, h, c = it["similar"], it["hypotheses"], it["containment"]
        print(f"{it['case_id']} {it['complaint_id']}: {'PASS' if it['pass'] else 'FAIL'} "
              f"{it['elapsed_s']} s · similares {len(s['found'])}/{len(s['expected'])} "
              f"(mín {s['required']}) prohibidos={s['forbidden_as_same_cause']} · hipótesis "
              f"{h['count']} ligadas/marcadas={h['linked_or_marked']} filas={h['fmea_rows']} "
              f"esperadas {h['expected_matched']}/{h['expected_total']} (estado ok "
              f"{h['expected_status_ok']}) · D3 {c['block']} pass={c['pass']} "
              f"exacto={c['exact']} mín={c['pass_minimum']} · "
              f"must_not={it['must_not']['violations']} · "
              f"gate={ {k: v for k, v in it['gate'].items() if not v} }")
    if not args.no_write:
        p = out_path("8d", card.model.replace("/", "-") + (f"_{args.label}" if args.label
                                                           else ""), args.out_dir, args.date)
        write_json(res, p)
        print(f"→ {p.relative_to(REPO_ROOT) if p.is_relative_to(REPO_ROOT) else p}")
    return 0 if m["gate"]["pass"] else 1


def suite_complaints(args: argparse.Namespace) -> int:
    """M3-T2: parser de reclamaciones (LLM real + ERP vía MCP) sobre las 5 del demo."""
    from solaris.llm import load_model_cards
    from solaris.settings import get_settings

    import complaint_suite

    settings = get_settings()
    key = settings.openrouter_api_key
    if key is None or not key.get_secret_value():
        print("Suite `complaints`: requiere OPENROUTER_API_KEY en .env (ADR-0003). No se ejecuta.")
        return 2
    card = load_model_cards(settings.models_file)["complaint_parse"]
    from solaris.agents.complaint import PROMPT_VERSION

    res = {**run_metadata("complaint_parse", card.model),
           "config": {"task": "complaint_parse", "model": card.model, "fallback": card.fallback,
                      "provider_policy": card.provider_policy.to_payload(),
                      "prompt_version": PROMPT_VERSION, "user": "inaki.calidad",
                      "erp": "MCP erp-mock (stdio) vía mcp_obo"},
           **complaint_suite.run(settings)}
    res["finished_at"] = datetime.now(UTC).isoformat(timespec="seconds")
    m = res["metrics"]
    print(json.dumps(m["gate"], ensure_ascii=False))
    for it in res["items"]:
        bad = [k for k, f in it["fields"].items() if not f["ok"]]
        print(f"{it['complaint_id']}: fallos={bad} inyección={it['injection_channels']} "
              f"fugas={it['leaked_canaries'] + it['injection_patterns_in_fields']} "
              f"erp_ok={(it['secondary']['erp_match'] or {}).get('ok')} {it['latency_ms']} ms"
              + (f" ERROR {it['error']}" if it["error"] else ""))
    if not args.no_write:
        p = out_path("complaint_parse", card.model.replace("/", "-"), args.out_dir, args.date)
        write_json(res, p)
        print(f"→ {p.relative_to(REPO_ROOT) if p.is_relative_to(REPO_ROOT) else p}")
    return 0 if m["gate"]["pass"] else 1


SUITES = {"retrieval": suite_retrieval, "containment": suite_containment, "qa": suite_qa,
          "8d": suite_8d, "complaints": suite_complaints}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Runner de evals de Solaris (M2-T7)")
    p.add_argument("--suite", required=True, choices=sorted(SUITES))
    p.add_argument("--config", default="default",
                   help=f"retrieval: preset(s) separados por comas o 'all'. {list(PRESETS)}")
    p.add_argument("--k", default="1,3,5,8,12", help="valores de k para Recall@k (retrieval)")
    p.add_argument("--only", default=None, help="IDs del golden separados por comas (depuración)")
    p.add_argument("--out-dir", type=Path, default=OUT_DIR)
    p.add_argument("--date", default=date.today().isoformat(),
                   help="prefijo de fecha del fichero de salida")
    p.add_argument("--no-write", action="store_true", help="no escribir el JSON en raw/eval-runs")
    p.add_argument("--calibrate", action="store_true",
                   help="qa: solo recuperación (umbral de 'no encontrado'), sin LLM")
    p.add_argument("--thresholds", default="-9,-8,-7,-6,-5,-4,-3,-2,-1,0",
                   help="qa --calibrate: umbrales de rerank a tabular")
    p.add_argument("--min-rerank", type=float, default=None,
                   help="qa: umbral de evidencia (por defecto el de solaris.rag.answer)")
    p.add_argument("--label", default=None, help="qa: sufijo del fichero de salida")
    p.add_argument("--prompt-version", default=None,
                   help="qa: prompt de rag_answer (p. ej. rag_answer.v4)")
    a = p.parse_args(argv)
    a.config = [c.strip() for c in a.config.split(",") if c.strip()]
    a.k = sorted({int(x) for x in a.k.split(",") if x.strip()} | {PRIMARY_K})
    a.only = [x.strip() for x in a.only.split(",")] if a.only else None
    return a


def main(argv: list[str] | None = None) -> int:
    a = parse_args(argv)
    return SUITES[a.suite](a)


if __name__ == "__main__":
    sys.exit(main())
