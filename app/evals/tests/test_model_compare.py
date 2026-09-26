"""M3-T5: ficha alternativa del runner (--models-config) y helpers del microbenchmark (sin LLM)."""

import pytest
import yaml

import model_bench
import runner

CARD = {"model": "vendor/model-x", "provenance": {"organization": "X", "country": "FR"},
        "provider_policy": {"data_collection": "deny", "only": ["mistral"]}}


@pytest.fixture
def clean_settings(monkeypatch):
    from solaris.settings import get_settings

    monkeypatch.delenv("MODELS_FILE", raising=False)
    get_settings.cache_clear()
    yield get_settings
    get_settings.cache_clear()


def test_parse_args_models_config(tmp_path):
    a = runner.parse_args(["--suite", "8d", "--models-config", str(tmp_path / "f.yaml")])
    assert a.models_config == tmp_path / "f.yaml"
    assert runner.parse_args(["--suite", "8d"]).models_config is None


def test_apply_models_config_switches_settings_without_touching_default(tmp_path, monkeypatch,
                                                                        clean_settings):
    from solaris.settings import DEFAULT_MODELS_FILE

    before = DEFAULT_MODELS_FILE.read_bytes()
    alt = tmp_path / "alt.yaml"
    alt.write_text(yaml.safe_dump({"tasks": {"8d_draft": CARD}}))
    monkeypatch.setenv("MODELS_FILE", str(DEFAULT_MODELS_FILE))  # se restaura al terminar
    meta = runner.apply_models_config(alt)
    assert clean_settings().models_file == alt.resolve()
    assert meta["default"] is False and meta["sha256"] == runner.sha256_file(alt)
    assert DEFAULT_MODELS_FILE.read_bytes() == before


def test_apply_models_config_rejects_data_collection_allow(tmp_path, monkeypatch, clean_settings):
    from solaris.llm import LLMConfigError

    bad = tmp_path / "bad.yaml"
    bad.write_text(yaml.safe_dump({"tasks": {"8d_draft": {
        **CARD, "provider_policy": {"data_collection": "allow"}}}}))
    monkeypatch.setenv("MODELS_FILE", "/nonexistent-should-stay.yaml")
    with pytest.raises(LLMConfigError):
        runner.apply_models_config(bad)
    import os

    assert os.environ["MODELS_FILE"] == "/nonexistent-should-stay.yaml"


def test_models_meta_default(clean_settings):
    m = runner.models_meta()
    assert m["default"] is True and m["path"] == "app/backend/config/models.yaml"


def test_parse_tuple():
    assert model_bench.parse_tuple("mistralai/mistral-large-2512@mistral/eu") == (
        "mistralai/mistral-large-2512", "mistral/eu")
    for bad in ("deepseek/deepseek-chat", "@deepinfra", "x@"):
        with pytest.raises(ValueError):
            model_bench.parse_tuple(bad)


def test_bench_cards_pin_one_provider_and_keep_limits():
    base = {"tasks": {"8d_draft": {"max_tokens": 4000, "temperature": 0.2},
                      "complaint_parse": {"max_tokens": 1200, "temperature": 0.0}}}
    cards = model_bench.bench_cards("m/x", "groq", ["8d_draft", "complaint_parse"], base)
    t = cards["tasks"]["complaint_parse"]
    assert t["model"] == "m/x" and "fallback" not in t
    assert t["provider_policy"] == {"data_collection": "deny", "only": ["groq"],
                                    "allow_fallbacks": False}
    assert (t["max_tokens"], t["temperature"]) == (1200, 0.0)
    # la ficha temporal pasa el mismo validador que route()
    from solaris.llm.config import ModelCard

    ModelCard.model_validate({**t, "task": "complaint_parse"})


def test_percentile_and_critical_path():
    assert model_bench.percentile([], 50) is None
    assert model_bench.percentile([3, 1, 2], 50) == 2
    assert model_bench.percentile([1, 2, 3, 4, 100], 95) == 100
    calls = [{"case_id": "A", "node": "intake_parse", "ok": True, "latency_ms": 1000},
             {"case_id": "A", "node": "D2_describe", "ok": True, "latency_ms": 9000},
             {"case_id": "A", "node": "D4_similar", "ok": True, "latency_ms": 3000},
             {"case_id": "A", "node": "D4_hypotheses", "ok": True, "latency_ms": 5000}]
    assert model_bench.critical_path_ms(calls) == 6000  # D2 va en paralelo: no cuenta
    assert model_bench.critical_path_ms(calls[1:]) is None
    failed = {"case_id": "A", "node": "x", "ok": False, "error": "HTTP 404"}
    s = model_bench.summarize([*calls, failed])
    assert s["ok"] == 4 and s["errors"] == ["HTTP 404"] and s["critical_path_llm_ms"] == [6000]
