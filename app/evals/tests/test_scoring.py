"""Tests de las funciones de puntuación del runner de evals (M2-T7). Sin BD ni LLM.

    uv run --project app/backend pytest app/evals/tests -q
"""

import pytest

import scoring as sc


def cit(doc, ver, **loc):
    return {"doc_id": doc, "version": ver, "locator": loc}


# --- locator -------------------------------------------------------------------------------------


@pytest.mark.parametrize(("raw", "expected"), [
    ("13-13", (13, 13)), ("11–12", (11, 12)), (" 4 - 8 ", (4, 8)), ("7", (7, 7)),
    ([18, 30], (18, 30)), ((1, 1), (1, 1)), (5, (5, 5)),
    ("12-3", None), ("a-b", None), ([1], None), (None, None), (True, None), ([1, "2"], None),
])
def test_parse_rows(raw, expected):
    assert sc.parse_rows(raw) == expected


@pytest.mark.parametrize(("exp", "got", "ok"), [
    # PDF: misma página; `part` del chunker se ignora
    ({"page": 2}, {"page": 2}, True),
    ({"page": 2}, {"page": 2, "part": 1}, True),
    ({"page": 2}, {"page": 3}, False),
    ({"page": 1}, {"page": True}, False),
    # XLSX: misma hoja y filas solapadas (golden "a-b" frente a chunk [a, b])
    ({"sheet": "AMFE", "rows": "15-15"}, {"sheet": "AMFE", "rows": [13, 19]}, True),
    ({"sheet": "AMFE", "rows": "12-13"}, {"sheet": "AMFE", "rows": [13, 13]}, True),
    ({"sheet": "AMFE", "rows": "12-13"}, {"sheet": "AMFE", "rows": [14, 20]}, False),
    ({"sheet": "AMFE", "rows": "15-15"}, {"sheet": "AMFE tuercas", "rows": [13, 19]}, False),
    ({"sheet": "Registro", "rows": "1177-1180"}, {"sheet": "Registro", "rows": [1175, 1187],
                                                 "part": 2}, True),
    # DOCX 8D: sección D1..D8
    ({"section": "D4"}, {"section": "D4", "heading": "D4 · Root cause analysis"}, True),
    ({"section": "D4"}, {"section": "D5", "heading": "D5 · Permanent corrective actions"}, False),
    # DOCX no 8D: título completo; el chunk puede traer section truncada a 120 y heading completo
    ({"section": "3. Frecuencia"}, {"section": "3. Frecuencia"}, True),
    ({"section": "3. Frecuencia"}, {"section": "3. Frecuencias de control"}, False),
    ({"section": "X" * 150}, {"section": "X" * 120, "heading": "X" * 150}, True),
    ({"section": "X" * 150}, {"section": "X" * 120}, True),
    ({"section": "X" * 130}, {"section": "X" * 20}, False),
    # tipos distintos o vacíos
    ({"page": 1}, {"sheet": "AMFE", "rows": [1, 1]}, False),
    ({"section": "D4"}, {"page": 4}, False),
    ({}, {"page": 1}, False),
])
def test_locator_compatible(exp, got, ok):
    assert sc.locator_compatible(exp, got) is ok


def test_citation_match_requires_doc_and_version():
    exp = cit("IT-L2-CR01-03", "v3", page=2)
    assert sc.citation_match(exp, cit("IT-L2-CR01-03", "v3", page=2, part=1))
    assert not sc.citation_match(exp, cit("IT-L2-CR01-03", "v2", page=2))
    assert not sc.citation_match(exp, cit("IT-L2-CR02-02", "v3", page=2))
    # variante solo doc_id: ignora versión y locator
    assert sc.citation_match(exp, cit("IT-L2-CR01-03", "v2", page=9), doc_only=True)
    assert not sc.citation_match(exp, cit("PC-AR1003-01", "v4", page=2), doc_only=True)


# --- recall y MRR --------------------------------------------------------------------------------


HITS = [
    cit("REG-L2-CR01-01", "v1", sheet="Registro", rows=[18, 30]),
    cit("IT-L2-CR01-03", "v3", page=4),
    cit("IT-L2-CR01-03", "v3", page=2, part=1),
    cit("PC-AR1003-01", "v4", sheet="Plan de control", rows=[13, 19]),
]
EXPECTED = [cit("IT-L2-CR01-03", "v3", page=2),
            cit("PC-AR1003-01", "v4", sheet="Plan de control", rows="13-13")]


def test_first_match_rank_locator_and_doc_only():
    assert sc.first_match_rank(EXPECTED, HITS) == 3  # p4 es del doc correcto pero otra página
    assert sc.first_match_rank(EXPECTED, HITS, doc_only=True) == 2
    assert sc.first_match_rank(EXPECTED, HITS[:2]) is None
    assert sc.first_match_rank([], HITS) is None


def test_recall_at_k_and_mrr():
    ranks = [1, 3, None, 9]
    assert sc.recall_at_k(ranks, 1) == 0.25
    assert sc.recall_at_k(ranks, 3) == 0.5
    assert sc.recall_at_k(ranks, 8) == 0.5
    assert sc.recall_at_k(ranks, 10) == 0.75
    assert sc.recall_at_k([], 8) is None
    assert sc.mrr(ranks) == pytest.approx((1 + 1 / 3 + 0 + 1 / 9) / 4)
    assert sc.mrr(ranks, k=8) == pytest.approx((1 + 1 / 3) / 4)  # MRR@8: el rango 9 no cuenta
    assert sc.mrr([]) is None
    assert sc.reciprocal_rank(None) == 0.0


def test_required_docs_covered():
    got = [cit("8D-A", "v2", section="D4"), cit("IT", "v3", page=1),
           cit("8D-B", "v2", section="D2")]
    assert sc.required_docs_covered(["8D-A", "8D-B"], got, 3) == (True, [])
    assert sc.required_docs_covered(["8D-A", "8D-B"], got, 2) == (False, ["8D-B"])


def test_percentile_linear():
    assert sc.percentile([], 50) is None
    assert sc.percentile([7.0], 95) == 7.0
    assert sc.percentile([1, 2, 3, 4], 50) == 2.5
    assert sc.percentile(list(range(1, 101)), 95) == pytest.approx(95.05)


# --- ACL -----------------------------------------------------------------------------------------


def test_acl_violations_folders_and_forbidden():
    acl = {"folders": {"calidad/8d": ["calidad"], "produccion/instrucciones-trabajo":
                       ["calidad", "planta"], "calidad/planes-control": ["calidad", "planta"]}}
    vis = sc.visible_folders_for("planta", acl)
    assert vis == ["calidad/planes-control", "produccion/instrucciones-trabajo"]
    ok_hits = [{"doc_id": "IT-1", "folder": "produccion/instrucciones-trabajo"}]
    assert sc.acl_violations(ok_hits, visible_folders=vis) == []
    bad = [{"doc_id": "8D-ARGA-2025-014", "folder": "calidad/8d"},
           {"doc_id": "PC-1", "folder": "calidad/planes-control"}]
    v = sc.acl_violations(bad, visible_folders=vis, forbidden_doc_ids=["8D-ARGA-2025-014"],
                          forbidden_folders=["calidad/8d"])
    assert v == [{"doc_id": "8D-ARGA-2025-014", "folder": "calidad/8d",
                  "reasons": ["carpeta_no_visible", "doc_prohibido", "carpeta_prohibida"]}]
    # subcarpeta de una carpeta prohibida también cuenta; un prefijo sin '/' no
    assert sc.acl_violations([{"doc_id": "X", "folder": "calidad/8d/viejos"}],
                             visible_folders=["calidad/8d"], forbidden_folders=["calidad/8d"])
    assert not sc.acl_violations([{"doc_id": "X", "folder": "calidad/8dx"}],
                                 visible_folders=["calidad/8dx"], forbidden_folders=["calidad/8d"])
    assert sc.visible_folders_for(None, acl) == []


# --- suite qa (preparada para M2-T6) ------------------------------------------------------------


@pytest.mark.parametrize(("answer", "needle"), [
    ("velocidad de hilo 9.4 m/min", "9,4"),
    ("intervalo de 60,000 golpes", "60.000"),
    ("intervalo de 60000 golpes", "60.000"),
    ("caudal 14-18 l/min", "14–18"),
    ("Cada  8 H", "8 h"),
])
def test_must_include_normalization(answer, needle):
    assert sc.must_include_hits(answer, [needle]) == (True, [])


def test_must_include_reports_missing_and_citation_precision():
    assert sc.must_include_hits("P12 a 23,5 V", ["P12", "9,4"]) == (False, ["9,4"])
    system = [cit("IT-L2-CR01-03", "v3", page=2), cit("IT-L2-CR01-03", "v3", page=5)]
    assert sc.citation_precision(system, EXPECTED) == (1, 2)
    assert sc.citation_precision([], EXPECTED) == (0, 0)


def test_compare_sets():
    r = sc.compare_sets(["L1", "L2"], ["L2", "L3"])
    assert r == {"expected": 2, "got": 2, "recall": 0.5, "missing": ["L1"], "extra": ["L3"],
                 "exact": False}
    assert sc.compare_sets([], [])["recall"] == 1.0
