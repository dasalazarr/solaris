"""`route()`: interfaz única hacia LLMs vía OpenRouter (ADR-0003, F10).

- El modelo se resuelve por tarea desde config/models.yaml (ficha de modelo).
- Siempre se envía la política de proveedor de la ficha (`data_collection: deny` por defecto).
- Reintentos acotados en errores transitorios; si el primario falla, se prueba el `fallback`.
- Nunca se registra la clave ni el contenido de los mensajes.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx
from pydantic import BaseModel

from solaris.llm.config import ModelCard, load_model_cards
from solaris.llm.errors import (
    LLMAuthError,
    LLMConfigError,
    LLMProviderError,
    UnknownTaskError,
)
from solaris.settings import Settings, get_settings

logger = logging.getLogger("solaris.llm")

# Opciones que el llamante puede ajustar por llamada. `model` y `provider` NO están:
# el modelo y la política de proveedor solo se cambian en la ficha (models.yaml).
ALLOWED_OPTS = frozenset(
    {"temperature", "max_tokens", "top_p", "stop", "seed", "response_format"}
)
ALLOWED_ROLES = frozenset({"system", "user", "assistant", "tool"})
RETRYABLE_STATUS = frozenset({408, 429, 500, 502, 503, 504})


class LLMResult(BaseModel):
    task: str
    content: str
    model: str
    requested_model: str
    provider: str | None = None
    used_fallback: bool = False
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    cost_usd: float | None = None
    latency_ms: float
    attempts: int


def _validate_messages(messages: list[dict[str, Any]]) -> None:
    if not isinstance(messages, list) or not messages:
        raise LLMConfigError("messages debe ser una lista no vacía")
    for i, m in enumerate(messages):
        if not isinstance(m, dict) or m.get("role") not in ALLOWED_ROLES or "content" not in m:
            raise LLMConfigError(f"messages[{i}] inválido: requiere 'role' válido y 'content'")


def build_payload(
    card: ModelCard, model: str, messages: list[dict[str, Any]], opts: dict[str, Any]
) -> dict[str, Any]:
    unknown = set(opts) - ALLOWED_OPTS
    if unknown:
        raise LLMConfigError(f"Opciones no permitidas en route(): {sorted(unknown)}")
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": card.max_tokens,
        "temperature": card.temperature,
        "provider": card.provider_policy.to_payload(),
        "usage": {"include": True},
        "stream": False,
    }
    payload.update(opts)
    return payload


def _headers(settings: Settings) -> dict[str, str]:
    key = settings.openrouter_api_key
    if key is None or not key.get_secret_value().strip():
        raise LLMConfigError(
            "Falta OPENROUTER_API_KEY. Cópiala en el .env de la raíz del repo "
            "(ver .env.example)."
        )
    return {
        "Authorization": f"Bearer {key.get_secret_value().strip()}",
        "Content-Type": "application/json",
        "HTTP-Referer": settings.app_referer,
        "X-Title": settings.app_title,
    }


def _call_once(
    client: httpx.Client,
    settings: Settings,
    headers: dict[str, str],
    payload: dict[str, Any],
) -> tuple[dict[str, Any], int]:
    """Llama al endpoint con reintentos acotados. Devuelve (json, intentos)."""
    url = f"{settings.openrouter_base_url.rstrip('/')}/chat/completions"
    last_error = "sin intentos"
    attempts = 0
    for attempt in range(settings.llm_max_retries + 1):
        attempts = attempt + 1
        if attempt:
            time.sleep(settings.llm_backoff_s * (2 ** (attempt - 1)))
        try:
            resp = client.post(url, json=payload, headers=headers, timeout=settings.llm_timeout_s)
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            last_error = f"{type(exc).__name__}"
            continue
        if resp.status_code in (401, 403):
            raise LLMAuthError(f"OpenRouter rechaza la clave (HTTP {resp.status_code})")
        if resp.status_code in RETRYABLE_STATUS:
            last_error = f"HTTP {resp.status_code}"
            continue
        if resp.status_code >= 400:
            raise LLMProviderError(
                f"HTTP {resp.status_code} para {payload['model']}", attempts=attempts
            )
        try:
            data = resp.json()
        except ValueError as exc:
            raise LLMProviderError("Respuesta no JSON de OpenRouter", attempts=attempts) from exc
        if isinstance(data, dict) and data.get("error"):
            code = data["error"].get("code") if isinstance(data["error"], dict) else None
            last_error = f"error en cuerpo (code={code})"
            continue
        return data, attempts
    raise LLMProviderError(
        f"{payload['model']}: agotados {attempts} intentos ({last_error})", attempts=attempts
    )


def _parse(
    data: dict[str, Any], task: str, requested: str, used_fallback: bool, t0: float, attempts: int
) -> LLMResult:
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMProviderError("Respuesta sin choices[0].message.content") from exc
    usage = data.get("usage") or {}
    return LLMResult(
        task=task,
        content=content or "",
        model=data.get("model") or requested,
        requested_model=requested,
        provider=data.get("provider"),
        used_fallback=used_fallback,
        prompt_tokens=usage.get("prompt_tokens"),
        completion_tokens=usage.get("completion_tokens"),
        total_tokens=usage.get("total_tokens"),
        cost_usd=usage.get("cost"),
        latency_ms=round((time.perf_counter() - t0) * 1000, 1),
        attempts=attempts,
    )


def route(
    task: str,
    messages: list[dict[str, Any]],
    *,
    settings: Settings | None = None,
    client: httpx.Client | None = None,
    **opts: Any,
) -> LLMResult:
    """Ejecuta `messages` con el modelo de la ficha de `task`.

    El contenido externo (reclamaciones, documentos) debe llegar ya delimitado como
    datos en un mensaje `user`; route() no concatena nada al prompt de sistema.
    """
    settings = settings or get_settings()
    cards = load_model_cards(settings.models_file)
    card = cards.get(task)
    if card is None:
        raise UnknownTaskError(f"Tarea desconocida '{task}'. Tareas: {sorted(cards)}")
    _validate_messages(messages)
    headers = _headers(settings)

    candidates = [(card.model, False)]
    if card.fallback and card.fallback != card.model:
        candidates.append((card.fallback, True))

    own_client = client is None
    http = client or httpx.Client()
    t0 = time.perf_counter()
    total_attempts = 0
    try:
        errors: list[str] = []
        for model, is_fallback in candidates:
            payload = build_payload(card, model, messages, opts)
            try:
                data, attempts = _call_once(http, settings, headers, payload)
            except LLMProviderError as exc:
                errors.append(str(exc))
                logger.warning("llm task=%s model=%s fallo: %s", task, model, exc)
                total_attempts += exc.attempts
                continue
            total_attempts += attempts
            result = _parse(data, task, model, is_fallback, t0, total_attempts)
            logger.info(
                "llm task=%s model=%s provider=%s fallback=%s tokens=%s cost=%s latency_ms=%s",
                task, result.model, result.provider, result.used_fallback,
                result.total_tokens, result.cost_usd, result.latency_ms,
            )
            return result
        raise LLMProviderError(f"Tarea '{task}': fallaron todos los modelos: {errors}")
    finally:
        if own_client:
            http.close()
