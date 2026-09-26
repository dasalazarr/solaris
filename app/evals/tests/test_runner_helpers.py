"""Helpers puros del runner (sin BD, sin MCP, sin LLM)."""

import runner


def test_item_tags_by_category():
    assert runner.item_tags({"category": "factual", "subcategory": "IT", "requires_ocr": True}) == [
        "factual", "citable", "factual/IT", "factual/escaneado_ocr"]
    assert "multilingual/en→es" in runner.item_tags(
        {"category": "multilingual", "question_lang": "en", "doc_lang": "es"})
    assert runner.item_tags({"category": "acl_negative"}) == ["acl_negative"]


def test_compare_containment_recall_and_exact_fields():
    exp = {"lots": ["L1", "L2"], "shipments": ["A1"], "shipped_qty": 10, "lots_in_stock": ["L2"]}
    ok = runner.compare_containment(exp, {"lots": ["L1", "L2"], "shipments": ["A1"],
                                          "shipped_qty": 10, "lots_in_stock": ["L2"]})
    assert ok["pass"] and "qty_not_shipped" in ok["not_checked"]
    # un lote de más se reporta pero no falla por sí solo; los albaranes y la cantidad sí
    extra = runner.compare_containment(exp, {"lots": ["L1", "L2", "L3"], "shipments": ["A1"],
                                             "shipped_qty": 10, "lots_in_stock": ["L2"]})
    assert extra["pass"] and extra["lots"]["extra"] == ["L3"]
    missing = runner.compare_containment(exp, {"lots": ["L1"], "shipments": ["A1"],
                                               "shipped_qty": 10, "lots_in_stock": ["L2"]})
    assert not missing["pass"]
    qty = runner.compare_containment(exp, {"lots": ["L1", "L2"], "shipments": ["A1"],
                                           "shipped_qty": 11, "lots_in_stock": ["L2"]})
    assert not qty["pass"]


def test_out_path_never_overwrites(tmp_path):
    p1 = runner.out_path("retrieval", "default", tmp_path, "2026-09-25")
    p1.write_text("{}")
    p2 = runner.out_path("retrieval", "default", tmp_path, "2026-09-25")
    assert p1.name == "2026-09-25_retrieval_default.json"
    assert p2.name == "2026-09-25_retrieval_default_2.json"


def test_parse_args_always_includes_primary_k():
    a = runner.parse_args(["--suite", "retrieval", "--k", "3,5", "--config", "default,norerank"])
    assert a.k == [3, 5, 8] and a.config == ["default", "norerank"]


def test_llm_suites_are_stubs_without_key(monkeypatch, capsys):
    from pydantic import SecretStr
    from solaris.settings import Settings

    monkeypatch.setattr("solaris.settings.get_settings",
                        lambda: Settings(_env_file=None, openrouter_api_key=SecretStr("")))
    for suite in ("qa", "8d"):
        assert runner.main(["--suite", suite]) == 2
        assert "requiere OPENROUTER_API_KEY" in capsys.readouterr().out


def _row(cat, lat, llm, provider="P1", ok=1, tot=1, correct=True):
    score = {"acl_leaks": [], "not_found": False}
    if cat in ("factual", "recurrence", "multilingual"):
        score |= {"citations_ok": ok, "citations_total": tot, "covered": ok > 0,
                  "covered_required": ok > 0, "must_include_ok": True}
    elif cat == "not_found":
        score |= {"correct": correct}
    return {"category": cat, "latency_ms": lat, "llm_latency_ms": llm, "provider": provider,
            "model": "m", "completion_tokens": 50, "cost_usd": 0.001, "prompt_tokens": 1,
            "gated": False, "warnings": [], "retrieval_ms": {"total": 100.0}, "score": score}


def test_qa_aggregate_gate_and_providers():
    import qa_suite

    rows = [_row("factual", 3000, 2000, ok=9, tot=10), _row("recurrence", 4000, 3000, "P2"),
            *[_row("not_found", 1000, 500) for _ in range(5)]]
    m = qa_suite.aggregate(rows)
    assert m["overall"]["citation_precision"] == round(10 / 11, 3)
    g = m["gate"]
    assert g["citation_precision_ok"] and g["not_found_ok"] and g["acl_ok"] and g["p95_ok"]
    assert g["pass"]
    assert set(m["by_provider"]) == {"P1 · m", "P2 · m"} and m["by_provider"]["P2 · m"]["n"] == 1
    rows[2]["score"]["correct"] = False
    rows += [_row("factual", 9000, 8000), _row("factual", 9500, 8000)]
    g2 = qa_suite.aggregate(rows)["gate"]
    assert not g2["not_found_ok"] and not g2["p95_ok"] and not g2["pass"]
