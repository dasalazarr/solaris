"""Arnés sin LLM de la suite `8d` (M3-T7): la respuesta grabada se re-puntúa con cada regla."""

import eightd_replay as rp

CASE = {
    "case_id": "8D-CASE-03", "user": "inaki.calidad",
    "expected_similar_8d": ["8D-ARGA-2024-009"], "forbidden_similar_8d": ["8D-ARGA-2024-009"],
    "must_not": ["declarar la reclamación como recurrencia confirmada del 8D-ARGA-2024-009",
                 "otra regla ya evaluada"],
}
CTX = {
    "complaint_id": "C-OEMN-2026-0327", "customer_code": "C-OEMN", "category": "coating",
    "part": {"ref": "AR-1009", "weld_cell": "CR-02", "uses_weld_nut": False},
    "lot": {"steel_lot_code": "S-ULTZ-260150"}, "family": ["AR-1009"],
    "full_text": "EDX at crater centre: Si, Mn and O detected; P and Zn not detected",
    "complaints": [{"complaint_id": "C-OEMN-2024-0163", "customer_code": "C-OEMN",
                    "part_ref": "AR-1009", "lot_code": "L1", "defect": "Poros y cráteres en el "
                    "e-coat", "status": "closed", "report_8d_id": "8D-ARGA-2024-009",
                    "steel_lot_code": "S-ULTZ-240131"}],
    "d2": {"8D-ARGA-2024-009": "5W2H\nHow | Craters (EDX: phosphorus and zinc).\n"},
}
RECORDED_D4 = {
    "similar": [{"doc_id": "8D-ARGA-2024-009", "relation": "misma_causa_probable",
                 "presented_as_same_cause": True, "reason": "erp_same_part",
                 "part_ref": "AR-1009", "complaint_id": "C-OEMN-2024-0163",
                 "date": "2024-07-09", "flags": []}],
    "similar_discarded": [],
    "recurrence": {"confirmed": True, "count": 1, "summary": "x", "citations": [],
                   "timeline": [{"doc_id": "8D-ARGA-2024-009"}]},
}
ITEM = {"case_id": "8D-CASE-03", "draft": {"d4": RECORDED_D4}, "elapsed_s": 20.0,
        "status": "pending_approval", "erp_queries": [],
        "gate": {"time": True, "similar": True, "forbidden": False, "hypotheses": True,
                 "must_not": False, "status": True},
        "must_not": {"violations": [CASE["must_not"][0]]}}


def test_base_reproduces_recorded_and_rule2_fixes_distractor():
    run = {"items": [ITEM]}
    base = rp.replay_run(run, {"8D-CASE-03": CASE}, {"8D-CASE-03": CTX}, frozenset())
    assert base["cases_pass"] == 0 and base["forbidden_as_same_cause"] == 1
    assert base["must_not_violations"] == 1
    r2 = rp.replay_run(run, {"8D-CASE-03": CASE}, {"8D-CASE-03": CTX},
                       frozenset({"cause_coherence"}))
    it = r2["items"][0]
    assert it["pass"] and it["similar"][0][1] == "sintoma_similar_causa_distinta"
    assert it["similar"][0][3] == "descartada" and not it["recurrence_confirmed"]


def test_recorded_violations_of_other_rules_are_kept():
    item = {**ITEM, "must_not": {"violations": ["otra regla ya evaluada"]}}
    r = rp.replay_run({"items": [item]}, {"8D-CASE-03": CASE}, {"8D-CASE-03": CTX},
                      frozenset({"cause_coherence"}))
    assert r["items"][0]["must_not_violations"] == ["otra regla ya evaluada"]


def test_same_symptom_floor_on_recorded_no_relacionado():
    d4 = {**RECORDED_D4, "similar": [], "similar_discarded": [
        {**RECORDED_D4["similar"][0], "relation": "no_relacionado",
         "presented_as_same_cause": False}]}
    out = rp.replay_d4(CTX, d4, frozenset({"same_symptom"}))
    assert [x["relation"] for x in out["similar"]] == ["mismo_sintoma"]
    assert out["similar_discarded"] == []
    assert rp.replay_d4(CTX, d4, frozenset())["similar"] == []


def test_material_family_candidate_added_only_for_material_defects():
    ctx = {**CTX, "category": "material", "customer_code": "C-RIBE", "family": ["AR-1012"],
           "part": {"ref": "AR-1012", "weld_cell": None, "uses_weld_nut": False},
           "lot": {"steel_lot_code": "S-ULTZ-260209"}, "d2": {},
           "complaints": [{"complaint_id": "C-RIBE-2025-0135", "customer_code": "C-RIBE",
                           "part_ref": "AR-1005", "lot_code": "L5", "defect": "Refuerzo "
                           "deformado; material en el límite", "status": "closed",
                           "report_8d_id": "8D-ARGA-2025-005",
                           "steel_lot_code": "S-ULTZ-250150"}]}
    d4 = {"similar": [], "similar_discarded": [], "recurrence": {}}
    out = rp.replay_d4(ctx, d4, frozenset({"material_family"}))
    assert [(x["doc_id"], x["relation"]) for x in out["similar"]] == [
        ("8D-ARGA-2025-005", "analogia")]
    assert rp.replay_d4({**ctx, "category": "coating"}, d4,
                        frozenset({"material_family"}))["similar"] == []
