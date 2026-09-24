"""Redacción del payload antes de escribirlo en el audit log (M4-T2, F08).

Reglas:
- **Nunca** se guardan secretos: claves con nombre de secreto (`password`, `api_key`, `token`,
  `authorization`...) se sustituyen por `[REDACTED]`, y en cualquier texto se borran los valores
  con forma de secreto (claves `sk-...`, `Bearer ...`, contraseñas en URLs de conexión, JWT,
  verificadores SCRAM, claves privadas PEM) y los valores exactos de los secretos de `Settings`.
- Los **prompts y respuestas** (`messages`, `prompt`, `completion`, `response`, `content`...) se
  guardan como `{sha256, chars}` y, en modo `truncate`, un extracto ya redactado de N caracteres.
- Las **fuentes recuperadas y las herramientas** (`sources`, `retrieved`, `chunks`, `documents`,
  `tools`, `tool_calls`) se guardan siempre completas (solo se les quitan secretos).
- El resto de textos largos se recorta a 2000 caracteres. El payload final cabe en 64 KiB.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any

from pydantic import SecretStr

from solaris.settings import Settings

REDACTED = "[REDACTED]"
PROMPT_KEYS = frozenset(
    {"messages", "prompt", "system_prompt", "completion", "response", "content", "output"}
)
PROTECTED_KEYS = frozenset(
    {"sources", "retrieved", "chunks", "documents", "tools", "tool_calls", "citations"}
)
MAX_STRING = 2000
MAX_PAYLOAD_BYTES = 60_000  # por debajo del CHECK de 64 KiB de la tabla

_SECRET_KEY_RE = re.compile(
    r"^(?:.*[_-])?(?:pass(?:word|wd)?|secret|api[_-]?key|apikey|token|access[_-]?token|"
    r"refresh[_-]?token|authorization|auth|cookie|set[_-]cookie|private[_-]?key|credentials?|"
    r"database[_-]?url|dsn)$",
    re.IGNORECASE,
)
_SECRET_VALUE_RES: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"),
        REDACTED,
    ),
    (re.compile(r"\bsk-[A-Za-z0-9][A-Za-z0-9_\-]{7,}"), REDACTED),  # OpenRouter / OpenAI
    (re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._\-~+/=]{8,}"), f"Bearer {REDACTED}"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}"), REDACTED),  # JWT
    (re.compile(r"SCRAM-SHA-256\$\S+"), REDACTED),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), REDACTED),
    # usuario:contraseña@ en URLs de conexión: se conserva el usuario
    (re.compile(r"(?i)\b([a-z][a-z0-9+.\-]*://[^:/\s@]+):[^@\s]+@"), rf"\1:{REDACTED}@"),
)
_SECRET_FIELDS = (
    "openrouter_api_key",
    "postgres_password",
    "database_url",
    "erp_reader_password",
    "audit_writer_password",
    "audit_reader_password",
)


def _known_secrets(settings: Settings | None) -> list[str]:
    if settings is None:
        return []
    out: list[str] = []
    for field in _SECRET_FIELDS:
        v = getattr(settings, field, None)
        if isinstance(v, SecretStr):
            raw = v.get_secret_value().strip()
            if len(raw) >= 6:
                out.append(raw)
    return sorted(out, key=len, reverse=True)


def scrub_text(text: str, settings: Settings | None = None) -> str:
    """Quita de un texto cualquier valor con forma de secreto o igual a un secreto conocido."""
    for secret in _known_secrets(settings):
        text = text.replace(secret, REDACTED)
    for pattern, repl in _SECRET_VALUE_RES:
        text = pattern.sub(repl, text)
    return text.replace("\x00", "")  # jsonb no admite \u0000


def summarize_text(text: Any, settings: Settings) -> dict[str, Any]:
    """Resumen auditable de un prompt o respuesta: hash, longitud y (opcional) extracto limpio."""
    if not isinstance(text, str):
        text = json.dumps(text, ensure_ascii=False, sort_keys=True, default=str)
    out: dict[str, Any] = {
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "chars": len(text),
    }
    if settings.audit_prompt_mode == "truncate":
        clean = scrub_text(text, settings)
        n = max(0, settings.audit_prompt_max_chars)
        out["excerpt"] = clean[:n]
        out["truncated"] = len(clean) > n
    return out


def _summarize_prompt_field(key: str, value: Any, settings: Settings) -> Any:
    if key == "messages" and isinstance(value, list):
        return [
            {"role": m.get("role"), **summarize_text(m.get("content", ""), settings)}
            if isinstance(m, dict)
            else summarize_text(m, settings)
            for m in value
        ]
    return summarize_text(value, settings)


def _walk(value: Any, settings: Settings, *, protected: bool, max_string: int) -> Any:
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for k, v in value.items():
            key = scrub_text(str(k), settings)[:200]
            if _SECRET_KEY_RE.match(key) and v not in (None, ""):
                out[key] = REDACTED
            elif not protected and key in PROMPT_KEYS:
                out[key] = _summarize_prompt_field(key, v, settings)
            else:
                out[key] = _walk(
                    v, settings, protected=protected or key in PROTECTED_KEYS,
                    max_string=max_string,
                )
        return out
    if isinstance(value, list | tuple | set | frozenset):
        return [_walk(v, settings, protected=protected, max_string=max_string) for v in value]
    if isinstance(value, SecretStr):
        return REDACTED
    if isinstance(value, bool) or value is None or isinstance(value, int):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, bytes):
        return {"bytes": len(value), "sha256": hashlib.sha256(value).hexdigest()}
    text = scrub_text(str(value), settings)
    if not protected and len(text) > max_string:
        return text[:max_string] + "…[truncado]"
    return text


def redact_payload(payload: dict[str, Any] | None, settings: Settings) -> dict[str, Any]:
    """Devuelve una copia del payload apta para el audit log (sin secretos, acotada en tamaño)."""
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        payload = {"value": payload}
    clean = _walk(payload, settings, protected=False, max_string=MAX_STRING)
    size = len(json.dumps(clean, ensure_ascii=False).encode("utf-8"))
    if size <= MAX_PAYLOAD_BYTES:
        return clean
    clean = _walk(payload, settings, protected=False, max_string=200)
    size2 = len(json.dumps(clean, ensure_ascii=False).encode("utf-8"))
    if size2 <= MAX_PAYLOAD_BYTES:
        return {**clean, "_shrunk": True}
    return {
        "_oversize": True,
        "bytes": size,
        "sha256": hashlib.sha256(
            json.dumps(clean, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest(),
        "keys": sorted(clean)[:50],
    }
