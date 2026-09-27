import json
import logging

import httpx
import pytest
import respx
from pydantic import SecretStr

from solaris.llm import (
    LLMAuthError,
    LLMConfigError,
    LLMProviderError,
    UnknownTaskError,
    load_model_cards,
    route,
)
from solaris.settings import DEFAULT_MODELS_FILE

from .conftest import FAKE_KEY

URL = "https://openrouter.ai/api/v1/chat/completions"
MSGS = [
    {"role": "system", "content": "Eres un asistente de calidad."},
    {"role": "user", "content": "<complaint>Par de apriete bajo en AR-1003</complaint>"},
]
TASKS = {"rag_answer", "complaint_parse", "8d_draft", "translate"}


def ok_body(model="deepseek/deepseek-chat", content="hola"):
    return {
        "id": "gen-1",
        "model": model,
        "provider": "DeepInfra",
        "choices": [{"message": {"role": "assistant", "content": content}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15, "cost": 0.0001},
    }


def test_models_yaml_has_complete_cards():
    cards = load_model_cards(DEFAULT_MODELS_FILE)
    assert set(cards) >= TASKS
    for card in cards.values():
        assert card.model and card.fallback and card.fallback != card.model
        assert card.provider_policy.data_collection == "deny"
        assert card.provenance.organization and card.provenance.country
        assert card.region_note
        # M3-T5: eval_score se rellena con la comparativa; si existe, es una fracción.
        assert card.eval_score is None or 0.0 <= card.eval_score <= 1.0


def test_eu_route_keeps_zdr_and_closed_provider_list():
    # Decisión del fundador 2026-09-27 (config mixta): parser, 8D y traducción van por región UE.
    # Si alguien abre el pool o quita ZDR, cambia la jurisdicción (R01): debe fallar aquí.
    cards = load_model_cards(DEFAULT_MODELS_FILE)
    for task in ("complaint_parse", "8d_draft", "translate"):
        policy = cards[task].provider_policy
        assert policy.zdr is True
        assert policy.only and set(policy.only) <= {"google-vertex/eu", "mistral/eu"}
        assert policy.allow_fallbacks is False


@respx.mock
def test_resolves_model_per_task_and_builds_payload(settings):
    route_ = respx.post(URL).mock(return_value=httpx.Response(200, json=ok_body()))
    res = route("complaint_parse", MSGS, settings=settings)

    sent = json.loads(route_.calls.last.request.content)
    card = load_model_cards(DEFAULT_MODELS_FILE)["complaint_parse"]
    assert sent["model"] == card.model
    assert sent["messages"] == MSGS
    assert sent["max_tokens"] == card.max_tokens
    assert sent["temperature"] == card.temperature
    assert sent["provider"]["data_collection"] == "deny"
    assert sent["provider"] == card.provider_policy.to_payload()
    assert sent["usage"] == {"include": True}
    assert sent["stream"] is False
    assert route_.calls.last.request.headers["Authorization"] == f"Bearer {FAKE_KEY}"

    assert res.task == "complaint_parse"
    assert res.content == "hola"
    assert res.model == "deepseek/deepseek-chat"
    assert res.provider == "DeepInfra"
    assert (res.prompt_tokens, res.completion_tokens, res.total_tokens) == (10, 5, 15)
    assert res.cost_usd == 0.0001
    assert res.latency_ms >= 0
    assert res.used_fallback is False
    assert res.attempts == 1


@respx.mock
def test_per_call_opts_allowed_but_model_and_provider_locked(settings):
    route_ = respx.post(URL).mock(return_value=httpx.Response(200, json=ok_body()))
    route("rag_answer", MSGS, settings=settings, temperature=0.7)
    assert json.loads(route_.calls.last.request.content)["temperature"] == 0.7
    with pytest.raises(LLMConfigError):
        route("rag_answer", MSGS, settings=settings, provider={"data_collection": "allow"})
    with pytest.raises(LLMConfigError):
        route("rag_answer", MSGS, settings=settings, model="otro/modelo")


@respx.mock
def test_missing_key_raises_config_error(settings):
    route_ = respx.post(URL)
    for bad in (None, SecretStr(""), SecretStr("   ")):
        s = settings.model_copy(update={"openrouter_api_key": bad})
        with pytest.raises(LLMConfigError, match="OPENROUTER_API_KEY"):
            route("rag_answer", MSGS, settings=s)
    assert not route_.called


def test_unknown_task_raises(settings):
    with pytest.raises(UnknownTaskError, match="no_existe"):
        route("no_existe", MSGS, settings=settings)


@respx.mock
def test_fallback_when_primary_fails(settings):
    card = load_model_cards(DEFAULT_MODELS_FILE)["8d_draft"]

    def responder(request):
        model = json.loads(request.content)["model"]
        if model == card.model:
            return httpx.Response(503, json={"error": {"message": "down"}})
        return httpx.Response(200, json=ok_body(model=model, content="borrador"))

    route_ = respx.post(URL).mock(side_effect=responder)
    res = route("8d_draft", MSGS, settings=settings)

    models_called = [json.loads(c.request.content)["model"] for c in route_.calls]
    # primario: 1 intento + 1 reintento (llm_max_retries=1); luego fallback
    assert models_called == [card.model, card.model, card.fallback]
    assert res.used_fallback is True
    assert res.model == card.fallback
    assert res.content == "borrador"
    assert res.attempts == 3
    # la política de proveedor también viaja en la llamada de fallback
    assert json.loads(route_.calls.last.request.content)["provider"]["data_collection"] == "deny"


@respx.mock
def test_retry_on_timeout_then_success(settings):
    route_ = respx.post(URL).mock(
        side_effect=[httpx.ReadTimeout("t"), httpx.Response(200, json=ok_body())]
    )
    res = route("translate", MSGS, settings=settings)
    assert route_.call_count == 2
    assert res.used_fallback is False and res.attempts == 2


@respx.mock
def test_all_models_fail_raises_provider_error(settings):
    respx.post(URL).mock(return_value=httpx.Response(500))
    with pytest.raises(LLMProviderError, match="fallaron todos"):
        route("rag_answer", MSGS, settings=settings)


@respx.mock
def test_auth_error_does_not_fallback(settings):
    route_ = respx.post(URL).mock(return_value=httpx.Response(401))
    with pytest.raises(LLMAuthError):
        route("rag_answer", MSGS, settings=settings)
    assert route_.call_count == 1


@respx.mock
def test_error_in_200_body_is_treated_as_failure(settings):
    respx.post(URL).mock(
        side_effect=[
            httpx.Response(200, json={"error": {"code": 502, "message": "upstream"}}),
            httpx.Response(200, json=ok_body()),
        ]
    )
    res = route("rag_answer", MSGS, settings=settings)
    assert res.attempts == 2


def test_invalid_messages_rejected(settings):
    with pytest.raises(LLMConfigError):
        route("rag_answer", [], settings=settings)
    with pytest.raises(LLMConfigError):
        route("rag_answer", [{"role": "hacker", "content": "x"}], settings=settings)


@respx.mock
def test_key_and_content_never_logged(settings, caplog):
    respx.post(URL).mock(return_value=httpx.Response(200, json=ok_body(content="SECRETO")))
    with caplog.at_level(logging.DEBUG):
        route("rag_answer", MSGS, settings=settings)
    assert FAKE_KEY not in caplog.text
    assert "AR-1003" not in caplog.text and "SECRETO" not in caplog.text
    assert FAKE_KEY not in repr(settings)
