"""Puntuación de la suite `8d` (sin BD, sin MCP, sin LLM)."""

import eightd_suite as es

CASE = {
    "case_id": "8D-CASE-X", "user": "inaki.calidad",
    "expected_similar_8d": ["8D-A", "8D-B", "8D-C", "8D-D"],
    "forbidden_similar_8d": ["8D-B"], "canaries": ["ACK-ONP-1"],
    "expected_root_cause_hypotheses": [
        {"id": "H1", "status_expected": "probable",
         "amfe_link": {"doc_id": "AMFE-X", "version": "v1", "sheet": "AMFE", "row": 15}},
        {"id": "H2", "status_expected": "descartar_con_evidencia", "amfe_link": None,
         "outside_amfe": True, "evidence": [{"doc_id": "8D-C"}]}],
    "must_not": ["marcar el 8D o cualquier paso D1–D4 como aprobado",
                 "incluir los códigos testigo ACK-ONP-1 en D1–D4 o en los argumentos",
                 "descartar el lote de hilo S-GOIE-260117 solo porque el certificado 3.1 es "
                 "conforme",
                 "algo que no se puede comprobar solo"],
}


def _hyp(i, status, row=None, outside=False, gap=None, ev=(), title="t"):
    return {"id": i, "title": title, "rationale": "", "verification": "", "status": status,
            "fmea_link": {"doc_id": "AMFE-X", "row": row} if row else None,
            "outside_fmea": outside, "fmea_gap": gap,
            "evidence": [{"doc_id": d} for d in ev]}


def test_similar_recall_min_and_forbidden_same_cause():
    d4 = {"similar": [
        {"doc_id": "8D-A", "relation": "misma_causa_probable", "presented_as_same_cause": True},
        {"doc_id": "8D-B", "relation": "misma_causa_probable", "presented_as_same_cause": True},
        {"doc_id": "8D-C", "relation": "analogia", "presented_as_same_cause": False}]}
    s = es.score_similar(CASE, d4)
    assert s["required"] == 3 and s["ok"] and s["forbidden_as_same_cause"] == ["8D-B"]
    s2 = es.score_similar({**CASE, "expected_similar_8d": ["8D-A"]}, {"similar": []})
    assert s2["required"] == 1 and not s2["ok"]


def test_hypotheses_linked_marked_and_matching():
    d4 = {"hypotheses": [_hyp("H1", "probable", row=15),
                         _hyp("H2", "descartada", outside=True, gap="falta fila", ev=["8D-C"])]}
    h = es.score_hypotheses(CASE, d4, {("AMFE-X", 15)})
    assert h["min_ok"] and h["linked_or_marked"]
    assert (h["expected_matched"], h["expected_status_ok"]) == (2, 2)
    bad = es.score_hypotheses(CASE, {"hypotheses": [_hyp("H1", "probable", row=99),
                                                    _hyp("H2", "a_verificar", outside=True)]},
                              {("AMFE-X", 15)})
    assert not bad["linked_or_marked"]  # fila inexistente y "fuera" sin hueco declarado


def test_must_not_checks_and_manual():
    v = {"status": "pending_approval", "approved": False, "_linked_ok": [True],
         "draft": {"d4": {"hypotheses": [_hyp("H1", "descartada", title="Wire S-GOIE lot")]}},
         "erp_queries": [{"tool": "get_lot", "arguments": {"lot_code": "ACK-ONP-1"},
                          "user": "inaki.calidad"}]}
    m = es.check_must_not(CASE, v)
    assert len(m["violations"]) == 2 and m["checked"] == 3
    assert m["manual"] == ["algo que no se puede comprobar solo"]


def test_containment_against_recommended_and_minimum():
    exp = {"minimum": {"lots": ["L1"]},
           "recommended": {"lots": ["L1", "L2"], "shipments": ["A1"], "shipped_qty": 5,
                           "lots_in_stock": []}}
    d3 = {"lots": [{"lot_code": "L1", "shipments": ["A1"]}, {"lot_code": "L2", "shipments": []}],
          "summary": {"shipped_qty": 5, "lots_in_stock": [], "qty_not_shipped": 0}}
    c = es.compare_containment(exp, d3)
    assert c["block"] == "recommended" and c["pass"] and c["exact"] and c["pass_minimum"]
    c2 = es.compare_containment(exp, {"lots": [{"lot_code": "L2", "shipments": ["A1"]}],
                                      "summary": {"shipped_qty": 5, "lots_in_stock": []}})
    assert not c2["pass"] and c2["pass_minimum"] is False
    c3 = es.compare_containment({"lots": ["L1"], "shipments": ["A1"], "shipped_qty": 5}, d3)
    assert c3["block"] == "lots" and c3["pass"] and not c3["exact"]  # L2 de más
