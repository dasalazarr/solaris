"""`route()`: interfaz única hacia LLMs vía OpenRouter (ADR-0003, F10).

- El modelo se resuelve por tarea desde config/models.yaml (ficha de modelo).
- Siempre se envía la política de proveedor de la ficha (`data_collection: deny` por defecto).
- Reintentos acotados en errores transitorios; si el primario falla, se prueba el `fallback`.
- Nunca se registra la clave ni el contenido de los mensajes en el log de aplicación.
- Cada llamada (éxito o fallo) anexa un evento `llm_call` al audit log (M4-T2, F08): tarea, modelo
  realmente usado, si hubo fallback, tokens, coste, latencia y prompts redactados (solaris.audit).
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

import httpx
from pydantic import BaseModel

from solaris.audit import Actor, AuditError, record_safe, writer_configured
from solaris.llm.config import ModelCard, load_model_cards
from solaris.llm.errors import (
    LLMAuthError,
    LLMConfigError,
    LLMProviderError,
    UnknownTaskError,
)
from solaris.settings import Settings, check_openrouter_base_url, get_settings

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
    # S4: se revalida aquí porque `model_copy(update=...)` no pasa por los validadores de Settings.
    try:
        base = check_openrouter_base_url(settings.openrouter_base_url)
    except ValueError as exc:
        raise LLMConfigError("OPENROUTER_BASE_URL no permitida (allowlist)") from exc
    url = f"{base}/chat/completions"
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


AuditFn = Callable[..., None]


def _audit_llm(
    settings: Settings,
    audit: AuditFn | None,
    *,
    actor: Actor | None,
    case_id: str | None,
    card: ModelCard,
    task: str,
    messages: list[dict[str, Any]],
    result: LLMResult | None,
    errors: list[str],
    outcome: str,
    latency_ms: float,
    attempts: int,
    audit_meta: dict[str, Any] | None,
) -> None:
    """Anexa `llm_call`. Sin credenciales de audit y con AUDIT_REQUIRED=false, no hace nada."""
    if audit is None:
        if not writer_configured(settings):
            if settings.audit_required:
                raise AuditError("AUDIT_REQUIRED=true pero falta AUDIT_WRITER_PASSWORD")
            logger.debug("audit desactivado: llm_call de %s sin registrar", task)
            return
        audit = record_safe
    payload: dict[str, Any] = {
        **(audit_meta or {}),  # p. ej. sources / tools: se guardan completos (sin secretos)
        "task": task,
        "outcome": outcome,
        "requested_model": card.model,
        "fallback_model": card.fallback,
        "model_used": result.model if result else None,
        "fallback_used": result.used_fallback if result else None,
        "provider": result.provider if result else None,
        "provider_policy": card.provider_policy.to_payload(),
        "attempts": attempts,
        "prompt_tokens": result.prompt_tokens if result else None,
        "completion_tokens": result.completion_tokens if result else None,
        "total_tokens": result.total_tokens if result else None,
        "cost_usd": result.cost_usd if result else None,
        "latency_ms": latency_ms,
        "errors": errors,
        "messages": messages,  # la redacción los convierte en sha256 + extracto/nada
        "response": result.content if result else None,
    }
    audit(
        "llm_call",
        actor,
        payload,
        case_id=case_id,
        model=result.model if result else card.model,
        provider=result.provider if result else None,
        settings=settings,
    )


def route(
    task: str,
    messages: list[dict[str, Any]],
    *,
    settings: Settings | None = None,
    client: httpx.Client | None = None,
    actor: Actor | None = None,
    case_id: str | None = None,
    audit_meta: dict[str, Any] | None = None,
    audit: AuditFn | None = None,
    **opts: Any,
) -> LLMResult:
    """Ejecuta `messages` con el modelo de la ficha de `task`.

    El contenido externo (reclamaciones, documentos) debe llegar ya delimitado como
    datos en un mensaje `user`; route() no concatena nada al prompt de sistema.

    `actor` (usuario autenticado, on-behalf-of) y `case_id` van al audit. `audit_meta` añade al
    evento las fuentes recuperadas y las herramientas invocadas. `audit` sustituye el escritor
    (tests); por defecto `solaris.audit.record_safe` según `AUDIT_REQUIRED`.
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
    errors: list[str] = []

    def _audit(result: LLMResult | None, outcome: str) -> None:
        _audit_llm(
            settings, audit, actor=actor, case_id=case_id, card=card, task=task,
            messages=messages, result=result, errors=errors, outcome=outcome,
            latency_ms=round((time.perf_counter() - t0) * 1000, 1), attempts=total_attempts,
            audit_meta=audit_meta,
        )

    try:
        for model, is_fallback in candidates:
            payload = build_payload(card, model, messages, opts)
            try:
                data, attempts = _call_once(http, settings, headers, payload)
            except LLMProviderError as exc:
                errors.append(str(exc))
                logger.warning("llm task=%s model=%s fallo: %s", task, model, exc)
                total_attempts += exc.attempts
                continue
            except LLMAuthError as exc:
                errors.append(str(exc))
                _audit(None, "auth_error")
                raise
            total_attempts += attempts
            result = _parse(data, task, model, is_fallback, t0, total_attempts)
            logger.info(
                "llm task=%s model=%s provider=%s fallback=%s tokens=%s cost=%s latency_ms=%s",
                task, result.model, result.provider, result.used_fallback,
                result.total_tokens, result.cost_usd, result.latency_ms,
            )
            _audit(result, "ok")
            return result
        _audit(None, "error")
        raise LLMProviderError(f"Tarea '{task}': fallaron todos los modelos: {errors}")
    finally:
        if own_client:
            http.close()
