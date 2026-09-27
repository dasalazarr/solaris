"""M3-T7 (F04): reglas deterministas del servidor sobre la relación con 8D anteriores.

Regla 1 (mismo síntoma calculado con el ERP: el LLM no puede marcarlo `no_relacionado`), regla 1b
(familia de material: otra pieza, acero del mismo proveedor → `analogia`) y regla 2 (coherencia de
la causa: `misma_causa_probable` se degrada si la reclamación contradice la firma 5W2H del
antecedente). Sin BD, sin MCP, sin LLM salvo el test en vivo de `eightd_sections` (se salta).
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from solaris.agents.eight_d import domain as dom
from solaris.agents.eight_d import nodes
from solaris.agents.eight_d import sources as src
from solaris.auth.core import Principal
from tests.test_eightd import DEFAULT_REPLIES, Harness

# Firmas (5W2H) y reclamaciones con la forma del corpus sintético.
D2_BATH = ("D2 · Problem description (5W2H)\n5W2H\n"
           "What | Pinholes and craters Ø0.2–0.8 mm, mainly on the flat face; e-coat thickness "
           "14–17 µm locally (spec 18–25 µm).\n"
           "Which | AR-1009 lots coated with bath make-up chemistry lot S-ARAK-240132.\n"
           "How | Craters with contamination at the centre (EDX: phosphorus and zinc).\n")
C_ECOAT = ("E-coat thickness, flat areas (5 points, 10 parts)\n19–23 µm (requirement 18–25 µm)\n"
           "E-coat thickness at crater rim\n4–8 µm\nEDX at crater centre (3 craters)\n"
           "Si, Mn and O detected (glassy residue); P and Zn not detected")
D2_INSERT = ("D2 · Descripción del problema (5W2H)\n"
             "Qué | Fuerza de retención 28–41 N (requisito ≥ 45 N, SC).\n"
             "Cómo | Ángulo de la lengüeta de retención 86–87° (nominal 90 ± 1°): menor precarga "
             "sobre el tubo.\n")
C_CLIP = ("no alcanzaron la fuerza de retención mínima (requisito ≥ 45 N). Tras la reclamación "
          "añadimos la medida del ángulo de la lengüeta. En este\nlote el ángulo es conforme, por "
          "lo que el problema no parece el mismo de entonces.")
D2_WELD = ("5W2H\nWhat | Crack / lack of fusion at the root of seam W2.\n"
           "How | Fracture along the weld root; macro-section shows root penetration of 0.4–0.6 "
           "mm (requirement ≥ 1.0 mm).\n")
C_WELD = ("root penetration 0.4 mm (drawing: ≥ 1.0 mm), porosity and spatter inclusions near the "
          "end crater. Base material hardness and chemistry within specification.")


# --- extracción explícita (regla 2) --------------------------------------------------------------


def test_analytes_found_and_absent():
    assert dom.analytes_found(D2_BATH) == {"P", "Zn"}
    assert dom.analytes_absent(C_ECOAT) == {"P", "Zn"}
    assert dom.analytes_absent("EDX con Si, Mn y O sin P ni Zn") == {"P", "Zn"}
    assert dom.analytes_absent("Si, Mn and O detected") == set()
    # un analito negado en el propio análisis no cuenta como encontrado
    assert dom.analytes_found("How | EDX: silicon; no zinc") == {"Si"}


def test_characteristics_out_of_spec_and_conforming():
    assert dom.characteristics_out_of_spec(dom.fivew2h_signature_text(D2_BATH)) == {"thickness"}
    assert dom.characteristics_out_of_spec(dom.fivew2h_signature_text(D2_INSERT)) == {
        "retention", "angle"}
    assert "thickness" in dom.characteristics_conforming(C_ECOAT)
    assert dom.characteristics_conforming(C_CLIP) == {"angle"}
    assert "angle" not in dom.characteristics_conforming("el ángulo no conforme")
    assert dom.characteristics_conforming(C_WELD) == {"hardness"}


def test_cause_contradictions_by_case():
    bath = dom.cause_contradictions(C_ECOAT, D2_BATH)
    assert {c["kind"] for c in bath} == {"analysis_negative", "characteristic_conforming"}
    assert dom.cause_check_status(bath) == "descartada"
    clip = dom.cause_contradictions(C_CLIP, D2_INSERT)
    assert clip == [{"kind": "characteristic_conforming", "items": ["angle"]}]
    assert dom.cause_check_status(clip) == "a_verificar"
    # misma firma (penetración fuera en ambos; dureza conforme no figura en el antecedente)
    assert dom.cause_contradictions(C_WELD, D2_WELD) == []
    assert dom.cause_contradictions(C_ECOAT, "sin 5W2H") == []


# --- mismo síntoma y familia de material (regla 1/1b) --------------------------------------------

PART_ECOAT = {"ref": "AR-1009", "special_char": "Espesor del e-coat", "weld_cell": "CR-02",
              "uses_weld_nut": False}
PART_CLIP = {"ref": "AR-1012", "special_char": "Fuerza de retención", "weld_cell": None,
             "uses_weld_nut": False}


def test_symptom_match_same_part_family_and_category():
    s = dom.symptom_match("coating", PART_ECOAT, "Poros y cráteres en el e-coat", "AR-1009",
                          ["AR-1009"])
    assert s == {"same": True, "basis": "same_part", "category": "coating"}
    assert dom.symptom_match("coating", PART_ECOAT, "Grieta en el cordón MIG", "AR-1009",
                             ["AR-1009"]) is None
    assert dom.symptom_match("coating", PART_ECOAT, "Poros en el e-coat", "AR-1003",
                             ["AR-1009"]) is None
    fam = dom.symptom_match("coating", PART_ECOAT, "Poros en el e-coat", "AR-1010",
                            ["AR-1009", "AR-1010"])
    assert fam and fam["basis"] == "amfe_family"
    assert dom.symptom_match("other", PART_ECOAT, "x", "AR-1009", ["AR-1009"]) is None


def test_prior_defect_not_biased_by_current_special_char():
    # "Fuerza de retención" (característica de AR-1012) no convierte en defecto de material un
    # defecto de embalaje de otra pieza.
    assert dom.material_family_match("material", PART_CLIP, "Escuadras deformadas; cajas "
                                     "retornables dañadas", "S-ULTZ-260209",
                                     "S-ULTZ-240120") is None
    m = dom.material_family_match("material", PART_CLIP, "Refuerzo deformado bajo carga; "
                                  "material en el límite", "S-ULTZ-260209", "S-ULTZ-250150")
    assert m == {"same": True, "basis": "material_family", "category": "material",
                 "supplier": "S-ULTZ"}
    assert dom.material_family_match("material", PART_CLIP, "material en el límite",
                                     "S-ULTZ-260209", "S-OTRO-250150") is None
    assert dom.supplier_of("S-ULTZ-250150") == "S-ULTZ" and dom.supplier_of("x") is None


# --- apply_relation_rules ------------------------------------------------------------------------

ALL = nodes.RELATION_RULES


def _item(rel: str) -> dict[str, Any]:
    return {"doc_id": "8D-X", "relation": rel, "presented_as_same_cause":
            rel == "misma_causa_probable", "flags": []}


def test_floor_same_symptom_never_no_relacionado():
    cand = {"doc_id": "8D-X", "symptom": {"same": True, "basis": "same_part"}}
    for rel in ("no_relacionado", "sin_valorar", "analogia"):
        out = dom.apply_relation_rules(_item(rel), cand, None, ALL)
        assert out["relation"] == dom.SAME_SYMPTOM and not out["presented_as_same_cause"]
        assert "relation_floor_same_part" in out["flags"]
    for rel in ("misma_causa_probable", "sintoma_similar_causa_distinta"):
        assert dom.apply_relation_rules(_item(rel), cand, None, ALL)["relation"] == rel
    # sin síntoma calculado (candidato por RAG) o con la regla apagada: la decisión del LLM
    assert dom.apply_relation_rules(_item("no_relacionado"), {"doc_id": "8D-X"}, None,
                                    ALL)["relation"] == "no_relacionado"
    assert dom.apply_relation_rules(_item("no_relacionado"), cand, None,
                                    frozenset())["relation"] == "no_relacionado"


def test_material_family_floor_is_analogy():
    cand = {"doc_id": "8D-X", "symptom": {"same": True, "basis": "material_family"}}
    out = dom.apply_relation_rules(_item("no_relacionado"), cand, None, ALL)
    assert out["relation"] == "analogia"
    out = dom.apply_relation_rules(_item("no_relacionado"), cand, None,
                                   frozenset({"same_symptom"}))
    assert out["relation"] == "no_relacionado"


def test_cause_coherence_degrades_same_cause_and_never_upgrades():
    cand = {"doc_id": "8D-X", "symptom": {"same": True, "basis": "same_part"}}
    neg = [{"kind": "analysis_negative", "items": ["P"]}]
    out = dom.apply_relation_rules(_item("misma_causa_probable"), cand, neg, ALL)
    assert out["relation"] == "sintoma_similar_causa_distinta"
    assert out["cause_check"]["status"] == "descartada" and not out["presented_as_same_cause"]
    conf = [{"kind": "characteristic_conforming", "items": ["angle"]}]
    out = dom.apply_relation_rules(_item("misma_causa_probable"), cand, conf, ALL)
    assert out["relation"] == dom.SAME_SYMPTOM and out["cause_check"]["status"] == "a_verificar"
    # sin contradicción, o si la regla está apagada, se mantiene
    assert dom.apply_relation_rules(_item("misma_causa_probable"), cand, [],
                                    ALL)["presented_as_same_cause"]
    assert dom.apply_relation_rules(_item("misma_causa_probable"), cand, neg,
                                    frozenset({"same_symptom"}))["presented_as_same_cause"]
    # ninguna regla sube a misma causa
    for rel in ("no_relacionado", "analogia", "sin_valorar", "sintoma_similar_causa_distinta"):
        assert not dom.apply_relation_rules(_item(rel), cand, neg, ALL)["presented_as_same_cause"]


# --- en el grafo ---------------------------------------------------------------------------------


def _harness(settings, sections: dict[str, str] | None = None, fail: bool = False) -> Harness:
    h = Harness(settings)
    orig = h.deps

    def fake_sections(principal, ids, secs=("D2",), **kw):
        assert isinstance(principal, Principal) and secs == ("D2",)
        if fail:
            raise RuntimeError("BD caída")
        return {k: v for k, v in (sections or {}).items() if k in ids}

    def deps():
        d = orig()
        d.sections_fn = fake_sections
        return d

    h.deps = deps  # type: ignore[method-assign]
    return h


def test_graph_llm_cannot_mark_same_symptom_as_unrelated(settings):
    h = _harness(settings)
    h.llm.replies["eightd_similar"] = {**DEFAULT_REPLIES["eightd_similar"], "similar": [
        {**DEFAULT_REPLIES["eightd_similar"]["similar"][0], "relation": "no_relacionado"}],
        "recurrence": {"confirmed": False, "summary": "", "citations": []}}
    _, v = h.run()
    sim = {x["doc_id"]: x for x in v["draft"]["d4"]["similar"]}
    x = sim["8D-ARGA-2025-014"]
    assert x["relation"] == dom.SAME_SYMPTOM and x["symptom"]["basis"] == "same_part"
    assert "relation_floor_same_part" in x["flags"]
    step = next(p for et, p, _ in h.audit if et == "agent_step" and p["node"] == "D4_root_cause")
    assert step["relation_rules"] == sorted(nodes.RELATION_RULES)
    assert step["similar"][0]["symptom_basis"] == "same_part"


def test_graph_contradicted_same_cause_is_not_recurrence(settings):
    d2 = ("5W2H\nWhat | Crack at W2 root; hardness 180–190 HV1 (requirement 200–240 HV1).\n"
          "How | EDX: zinc at the crack origin.\n")
    h = _harness(settings, {"8D-ARGA-2025-014": d2})
    extra = ("Base material hardness within specification. EDX at the crack origin: "
             "Zn not detected.")
    from tests.test_eightd import _eml

    _, v = h.run(_eml(extra))
    d4 = v["draft"]["d4"]
    x = {s["doc_id"]: s for s in d4["similar"]}["8D-ARGA-2025-014"]
    assert x["relation"] == "sintoma_similar_causa_distinta"
    assert x["cause_check"]["status"] == "descartada"
    assert {c["kind"] for c in x["cause_check"]["contradictions"]} == {
        "analysis_negative", "characteristic_conforming"}
    assert d4["recurrence"]["confirmed"] is False and d4["recurrence"]["count"] == 0


def test_graph_sections_down_still_drafts(settings):
    h = _harness(settings, fail=True)
    _, v = h.run()
    assert v["status"] == "pending_approval"
    assert v["draft"]["d4"]["similar"][0]["relation"] == "misma_causa_probable"


def test_material_family_candidates_use_filtered_queries():
    calls: list[tuple[str, dict[str, Any]]] = []

    class FakeErp:
        async def call(self, tool, args):
            calls.append((tool, args))
            if tool == "search_complaints":
                return 1, {"complaints": [
                    {"complaint_id": "C-R-2025-1", "part_ref": "AR-1005", "lot_code": "L-5",
                     "received_date": "2025-04-08", "status": "closed",
                     "defect": "Refuerzo deformado; material en el límite",
                     "report_8d_id": "8D-ARGA-2025-005"},
                    {"complaint_id": "C-R-2024-1", "part_ref": "AR-1002", "lot_code": "L-2",
                     "received_date": "2024-06-20", "status": "closed",
                     "defect": "Escuadras deformadas; cajas retornables dañadas",
                     "report_8d_id": "8D-ARGA-2024-007"},
                    {"complaint_id": "C-R-2025-2", "part_ref": "AR-1012", "lot_code": "L-12",
                     "received_date": "2025-12-09", "status": "closed",
                     "defect": "Fuerza de retención baja", "report_8d_id": "8D-ARGA-2025-015"}]}
            return 2, {"found": True, "lot": {"steel_lot_code": "S-ULTZ-250150"}}

    c = {"customer_code": "C-RIBE", "complaint_id": "C-R-2026-0140"}
    out = asyncio.run(nodes._material_family(FakeErp(), c, PART_CLIP,
                                             {"steel_lot_code": "S-ULTZ-260209"}, ["AR-1012"],
                                             {"8D-ARGA-2025-015"}))
    assert [x["doc_id"] for x in out] == ["8D-ARGA-2025-005"]
    assert out[0]["reason"] == "erp_material_family"
    assert calls[0] == ("search_complaints", {"customer_code": "C-RIBE", "status": "closed"})
    assert calls[1:] == [("get_lot", {"lot_code": "L-5"})]
    assert all(any(v is not None for v in a.values()) for _, a in calls)


# --- lectura de la D2 como el usuario (en vivo; se salta sin BD) ---------------------------------


@pytest.fixture(scope="module")
def real_settings():
    from solaris.settings import get_settings

    s = get_settings()
    try:
        from solaris.db import connect_app

        with connect_app(s) as c:
            c.execute("SELECT 1 FROM rag.visible_chunks('calidad') LIMIT 1")
    except Exception as exc:
        pytest.skip(f"Postgres/solaris_app no disponible: {type(exc).__name__}")
    return s


def test_eightd_sections_respects_acl_and_audits_ids_only(real_settings, monkeypatch):
    events: list[tuple[str, dict[str, Any]]] = []
    monkeypatch.setattr(src, "record_safe", lambda et, actor, payload, **kw: events.append(
        (et, payload)))
    got = src.eightd_sections(Principal("inaki.calidad", "calidad", "t"),
                              ["8D-ARGA-2024-009", "x'; DROP TABLE y; --"], ("D2",),
                              settings=real_settings)
    assert list(got) == ["8D-ARGA-2024-009"] and "EDX" in got["8D-ARGA-2024-009"]
    assert events == [("retrieval", {"kind": "eightd_sections", "role": "calidad",
                                     "sections": ["D2"], "documents": ["8D-ARGA-2024-009"]})]
    # planta no ve calidad/8d
    assert src.eightd_sections(Principal("ander.turno", "planta", "t"), ["8D-ARGA-2024-009"],
                               settings=real_settings) == {}
    assert src.eightd_sections(Principal("nadie", "", "t"), ["8D-ARGA-2024-009"],
                               settings=real_settings) == {}
