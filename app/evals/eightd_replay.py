"""Arnés sin LLM de la suite `8d` (M3-T7): re-puntúa respuestas GRABADAS con reglas del servidor.

Toma los eval-runs `8d` ya grabados (raw/eval-runs/*_8d_*.json: el borrador D1–D4 con la relación
que devolvió el LLM para cada antecedente), sustituye la llamada al LLM por esa respuesta y vuelve a
aplicar las reglas deterministas de `solaris.agents.eight_d.domain.apply_relation_rules` con un
subconjunto de reglas. Así se mide el efecto de cada regla gratis (PAT-010: una regla por
iteración) antes de gastar una pasada real.

Datos que usa (solo el evaluador, como admin, nunca el producto; PAT-004):
- la reclamación (texto visible no sospechoso, extracción determinista del parser, sin LLM);
- el ERP (piezas, lotes, reclamaciones) y los AMFE visibles, para "mismo síntoma" y la familia
  de material;
- la sección D2 de cada 8D candidato (rag.chunks), para la coherencia de la causa.

Qué se re-puntúa: similares (recall, prohibidos como misma causa) y el `must_not` de recurrencia
confirmada. Lo demás (tiempo, hipótesis, D3, resto de `must_not`, estado) es lo grabado: las
reglas no lo tocan.

    uv run --project app/backend python app/evals/eightd_replay.py [--runs 'glob'] [--out f.json]
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

import eightd_suite as es  # noqa: E402

CASES_FILE = EVALS_DIR / "golden" / "8d_cases.jsonl"
DEFAULT_RUNS = [
    "raw/eval-runs/2026-09-26_8d_deepseek-deepseek-chat_pasada1.json",
    "raw/eval-runs/2026-09-26_8d_deepseek-deepseek-chat_pasada2.json",
    "raw/eval-runs/2026-09-27_8d_*_m3t5*.json",
]
# Iteraciones (PAT-010): cada una añade UNA regla a la anterior; "r2_sola" aísla la regla 2.
RULESETS: list[tuple[str, frozenset[str]]] = [
    ("base", frozenset()),
    ("r1_mismo_sintoma", frozenset({"same_symptom"})),
    ("r1b_familia_material", frozenset({"same_symptom", "material_family"})),
    ("r2_coherencia_causa", frozenset({"same_symptom", "material_family", "cause_coherence"})),
    ("r2_sola", frozenset({"cause_coherence"})),
]
RECURRENCE_RULE = "recurrencia confirmada"


# --- datos del caso (evaluador) ------------------------------------------------------------------


def case_context(case: dict[str, Any], settings: Any) -> dict[str, Any]:
    """Todo lo que las reglas necesitan de un caso, leído sin LLM ni MCP."""
    from solaris.agents.complaint import prepare
    from solaris.agents.eight_d import domain as dom
    from solaris.agents.eight_d import nodes
    from solaris.agents.eight_d import sources as src
    from solaris.auth.core import Principal
    from solaris.db import connect

    path = REPO_ROOT / case["complaint_file"]
    c = prepare(path.read_bytes(), path.name).parsed.model_dump(mode="json")
    full = nodes._full_text(c)
    lot_code = (c.get("lot_codes") or [None])[0]
    with connect(settings) as conn:
        cols = ("ref", "description", "customer_code", "routing", "material",
                "special_char", "char_class", "die", "weld_cell", "uses_weld_nut")
        row = conn.execute(f"SELECT {', '.join(cols)} FROM erp.parts WHERE ref = %s",  # noqa: S608
                           (c["part_ref"],)).fetchone()
        part = dict(zip(cols, row, strict=True))
        lot_cols = ("lot_code", "steel_lot_code", "weld_cell")
        lrow = conn.execute("SELECT lot_code, steel_lot_code, weld_cell FROM erp.lots"
                            " WHERE lot_code = %s", (lot_code,)).fetchone()
        lot = dict(zip(lot_cols, lrow, strict=True)) if lrow else {}
        comp = conn.execute(
            "SELECT c.complaint_id, c.customer_code, c.part_ref, c.lot_code, c.defect, c.status,"
            " c.report_8d_id, l.steel_lot_code FROM erp.complaints c"
            " LEFT JOIN erp.lots l ON l.lot_code = c.lot_code").fetchall()
        d2 = {d: t for d, t in conn.execute(
            "SELECT doc_id, string_agg(content, E'\\n' ORDER BY chunk_no) FROM rag.chunks"
            " WHERE section = 'D2' AND doc_id LIKE '8D-%' GROUP BY doc_id").fetchall()}
    part.setdefault("weld_cell", lot.get("weld_cell"))
    category = dom.classify_defect(full, part)
    fam = src.fmea_documents(Principal(case["user"], "", "replay"), c["part_ref"], category,
                             settings=settings)
    family = list(fam.get("family") or [c["part_ref"]])[:4]
    complaints = [dict(zip(("complaint_id", "customer_code", "part_ref", "lot_code", "defect",
                            "status", "report_8d_id", "steel_lot_code"), r, strict=True))
                  for r in comp]
    return {"complaint_id": c.get("complaint_id"), "customer_code": c.get("customer_code"),
            "full_text": full, "part": part, "lot": lot, "category": category,
            "family": family, "complaints": complaints, "d2": d2}


# --- reglas sobre una respuesta grabada (puro) ---------------------------------------------------


def candidates_for(ctx: dict[str, Any], recorded: list[dict[str, Any]],
                   rules: frozenset[str]) -> list[dict[str, Any]]:
    """Candidatos del caso: los grabados (con el síntoma calculado como en D1) y, con la regla 1b,
    los de la familia de material (misma decisión que `nodes._material_family`)."""
    from solaris.agents.eight_d import domain as dom

    by_complaint = {x["complaint_id"]: x for x in ctx["complaints"]}
    by_8d = {x["report_8d_id"]: x for x in ctx["complaints"] if x.get("report_8d_id")}
    out = []
    for r in recorded:
        cand = {k: r.get(k) for k in ("doc_id", "date", "part_ref", "complaint_id", "reason")}
        row = by_complaint.get(r.get("complaint_id") or "")
        if row and r.get("reason") in ("erp_same_part", "erp_amfe_family"):
            cand["symptom"] = dom.symptom_match(ctx["category"], ctx["part"], row["defect"],
                                                row["part_ref"], ctx["family"])
        elif r.get("reason") == "erp_material_family" and r["doc_id"] in by_8d:
            row = by_8d[r["doc_id"]]
            cand["symptom"] = dom.material_family_match(
                "material", ctx["part"], row["defect"], ctx["lot"].get("steel_lot_code"),
                row.get("steel_lot_code"))
        out.append(cand)
    if "material_family" in rules and ctx["category"] == "material":
        # En el producto la búsqueda del ERP va ANTES que la de RAG: un 8D que la respuesta
        # grabada tenía como `rag_similarity` pasa a ser candidato de la familia de material.
        known = {x["doc_id"]: x for x in out}
        n = 0
        for row in ctx["complaints"]:
            doc = row.get("report_8d_id")
            prev = known.get(doc or "")
            if (row["customer_code"] != ctx["customer_code"] or row["status"] != "closed"
                    or not doc or (prev and prev["reason"] != "rag_similarity")
                    or row["part_ref"] in ctx["family"]
                    or row["complaint_id"] == ctx["complaint_id"] or not row.get("lot_code")
                    or dom.classify_defect(row["defect"],
                                           dom.process_flags(ctx["part"])) != "material"):
                continue
            sym = dom.material_family_match("material", ctx["part"], row["defect"],
                                            ctx["lot"].get("steel_lot_code"),
                                            row.get("steel_lot_code"))
            if sym and n < 2:
                n += 1
                if prev:
                    prev.update(reason="erp_material_family", symptom=sym,
                                part_ref=row["part_ref"], complaint_id=row["complaint_id"])
                    continue
                out.append({"doc_id": doc, "date": None, "part_ref": row["part_ref"],
                            "complaint_id": row["complaint_id"],
                            "reason": "erp_material_family", "symptom": sym})
    return out


def replay_d4(ctx: dict[str, Any], d4: dict[str, Any],
              rules: frozenset[str]) -> dict[str, Any]:
    """D4 con la respuesta grabada del LLM y las reglas `rules` (mismo código que el nodo)."""
    from solaris.agents.eight_d import domain as dom
    from solaris.agents.eight_d.nodes import build_recurrence

    recorded = list(d4.get("similar") or []) + list(d4.get("similar_discarded") or [])
    cands = candidates_for(ctx, recorded, rules)
    by_doc = {x["doc_id"]: x for x in cands}
    items = {x["doc_id"]: {**x, "flags": [f for f in x.get("flags") or []
                                          if not f.startswith(("relation_floor_",
                                                               "same_cause_"))]}
             for x in recorded}
    for d, cand in by_doc.items():
        if d not in items:
            items[d] = {**{k: cand.get(k) for k in ("doc_id", "date", "part_ref",
                                                    "complaint_id", "reason")},
                        "relation": "sin_valorar", "presented_as_same_cause": False,
                        "cause_summary": "", "citations": [], "flags": ["not_assessed"]}
    contradictions = {d: dom.cause_contradictions(ctx["full_text"], ctx["d2"][d])
                      for d in by_doc if d in ctx["d2"]}
    similar = [dom.apply_relation_rules(x, by_doc[x["doc_id"]], contradictions.get(x["doc_id"]),
                                        rules) for x in items.values()]
    rec0 = d4.get("recurrence") or {}
    rec = build_recurrence(similar, bool(rec0.get("confirmed")), rec0.get("summary") or "",
                           rec0.get("citations") or [])
    return {**d4, "similar": [x for x in similar if x["relation"] != "no_relacionado"],
            "similar_discarded": [x for x in similar if x["relation"] == "no_relacionado"],
            "recurrence": rec}


def rescore_item(case: dict[str, Any], item: dict[str, Any], d4: dict[str, Any]) -> dict[str, Any]:
    """Gate del caso con el D4 re-calculado; el resto, lo grabado."""
    sim = es.score_similar(case, d4)
    draft = {**item["draft"], "d4": d4}
    recomputed = [r for r in case.get("must_not") or [] if RECURRENCE_RULE in r.lower()]
    v = {"draft": draft, "erp_queries": item.get("erp_queries") or [],
         "status": item.get("status"), "warnings": []}
    fresh = es.check_must_not({**case, "must_not": recomputed}, {**v, "_linked_ok": []})
    kept = [r for r in item["must_not"]["violations"] if r not in recomputed]
    violations = kept + fresh["violations"]
    gate = {**item["gate"], "similar": sim["ok"], "forbidden": not sim["forbidden_as_same_cause"],
            "must_not": not violations}
    return {"case_id": case["case_id"], "pass": all(gate.values()), "gate": gate,
            "elapsed_s": item.get("elapsed_s"),
            "similar": [(x["doc_id"], x["relation"], (x.get("symptom") or {}).get("basis"),
                         (x.get("cause_check") or {}).get("status")) for x in d4["similar"]],
            "discarded": [x["doc_id"] for x in d4["similar_discarded"]],
            "forbidden_as_same_cause": sim["forbidden_as_same_cause"],
            "must_not_violations": violations,
            "recurrence_confirmed": d4["recurrence"]["confirmed"]}


def replay_run(run: dict[str, Any], cases: dict[str, dict[str, Any]],
               ctxs: dict[str, dict[str, Any]], rules: frozenset[str]) -> dict[str, Any]:
    items = []
    for it in run["items"]:
        if "draft" not in it or it["case_id"] not in cases:
            continue
        d4 = replay_d4(ctxs[it["case_id"]], it["draft"].get("d4") or {}, rules)
        items.append(rescore_item(cases[it["case_id"]], it, d4))
    return {"cases_pass": sum(1 for i in items if i["pass"]),
            "forbidden_as_same_cause": sum(len(i["forbidden_as_same_cause"]) for i in items),
            "must_not_violations": sum(len(i["must_not_violations"]) for i in items),
            "pass_by_case": {i["case_id"]: i["pass"] for i in items}, "items": items}


# --- CLI -----------------------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--runs", nargs="*", default=DEFAULT_RUNS)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args(argv)
    from solaris.settings import get_settings

    settings = get_settings()
    cases = {c["case_id"]: c for c in (json.loads(x) for x in CASES_FILE.read_text(
        encoding="utf-8").splitlines() if x.strip())}
    ctxs = {cid: case_context(c, settings) for cid, c in cases.items()}
    files = sorted({f for pat in args.runs for f in glob.glob(str(REPO_ROOT / pat))})
    res: dict[str, Any] = {"suite": "8d_replay", "runs": [], "rulesets": {
        n: sorted(r) for n, r in RULESETS}, "categories": {
        k: {"category": v["category"], "family": v["family"]} for k, v in ctxs.items()}}
    header = f"{'run':58} " + " ".join(f"{n[:14]:>14}" for n, _ in RULESETS)
    print(header)
    for f in files:
        run = json.loads(Path(f).read_text(encoding="utf-8"))
        rec = {"file": str(Path(f).relative_to(REPO_ROOT)),
               "recorded_cases_pass": run["metrics"]["cases_pass"], "rulesets": {}}
        for name, rules in RULESETS:
            rec["rulesets"][name] = replay_run(run, cases, ctxs, rules)
        res["runs"].append(rec)
        print(f"{Path(f).name[:58]:58} " + " ".join(
            f"{r['cases_pass']}/5 f{r['forbidden_as_same_cause']} m{r['must_not_violations']}"
            .rjust(14) for r in rec["rulesets"].values()))
    agg = {n: {"cases_pass": sum(r["rulesets"][n]["cases_pass"] for r in res["runs"]),
               "cases": 5 * len(res["runs"]),
               "forbidden": sum(r["rulesets"][n]["forbidden_as_same_cause"] for r in res["runs"]),
               "must_not": sum(r["rulesets"][n]["must_not_violations"] for r in res["runs"]),
               "by_case": {c: sum(1 for r in res["runs"] if r["rulesets"][n]["pass_by_case"]
                                  .get(c)) for c in cases}}
           for n, _ in RULESETS}
    res["aggregate"] = agg
    print(json.dumps(agg, ensure_ascii=False))
    if args.out:
        args.out.write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str) + "\n",
                            encoding="utf-8")
        print(f"→ {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
