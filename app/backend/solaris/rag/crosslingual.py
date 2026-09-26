"""Recuperación cruzada ES↔EN (M2-T7, F02).

El corpus mezcla documentos en español (IT, AMFE, 8D internos) y en inglés (8D del OEM). El
cross-encoder bge-reranker-base y la rama léxica apenas cruzan idiomas, así que una pregunta en
español no encuentra un 8D en inglés (y al revés). `retrieve_bilingual` traduce la pregunta con
`route("translate")` (ficha de modelo, OpenRouter, ADR-0003) y pasa la traducción a `retrieve` como
**consulta alternativa**: solo aporta candidatos (sus ramas léxica y vectorial se fusionan por RRF).
La ACL, los filtros y las citas no cambian: todo sigue saliendo de `rag.visible_*` para el
Principal.

Seguridad (spec §4 de M2-T8): la pregunta es dato no confiable. Va en el sobre
`<untrusted_data nonce>` como JSON, con un prompt de sistema estático y versionado
(`query_translate.v1`), sin herramientas. La salida solo se usa como texto de búsqueda (se limpia,
se trunca y nunca se muestra ni se pasa al LLM de respuesta). Si falla o tarda más de
`rag_translate_timeout_s`, se sigue sin ella (la respuesta nunca depende de la traducción).
"""

from __future__ import annotations

import hashlib
import logging
import re
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from typing import TYPE_CHECKING, Any

from solaris.llm import route
from solaris.prompts import load_prompt
from solaris.prompts.untrusted import build_envelope, new_nonce, strip_invisible
from solaris.rag.lang import guess_lang
from solaris.rag.retrieve import MAX_QUERY_CHARS, Hit, RetrievalTrace, retrieve_as
from solaris.settings import Settings, get_settings

if TYPE_CHECKING:
    from solaris.auth.core import Principal

logger = logging.getLogger("solaris.rag")

TASK = "translate"
PROMPT_VERSION = "query_translate.v1"
MAX_TRANSLATION_CHARS = 600
_EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="solaris-translate")


def clean_translation(text: str, question: str, nonce: str) -> str | None:
    """Primera línea útil, sin invisibles, comillas ni prefijos. Sospechosa o vacía → None."""
    if not isinstance(text, str) or nonce in text or "untrusted_data" in text.lower():
        return None
    line = next((ln for ln in strip_invisible(text).splitlines() if ln.strip()), "")
    line = re.sub(r"^\s*(?:translation|traducci[oó]n)\s*:\s*", "", line, flags=re.I)
    line = " ".join(line.strip().strip("\"'«»“”").split())[:MAX_TRANSLATION_CHARS]
    if not line or line.lower() == question.strip().lower():
        return None
    return line


def translate_query(
    principal: Principal,
    question: str,
    *,
    settings: Settings | None = None,
    route_fn: Callable[..., Any] = route,
    audit: Callable[..., None] | None = None,
) -> str | None:
    """Traducción ES↔EN de la pregunta para usarla como consulta alternativa (o None)."""
    s = settings or get_settings()
    prompt = load_prompt(PROMPT_VERSION)
    nonce = new_nonce()
    user_msg, _ = build_envelope(question[:MAX_QUERY_CHARS], [], nonce)
    res = route_fn(
        TASK,
        [{"role": "system", "content": prompt.text}, {"role": "user", "content": user_msg}],
        settings=s, actor=principal.actor, audit=audit,
        audit_meta={"purpose": "cross_lingual_query", "question_lang": guess_lang(question),
                    "security": {"prompt_version": prompt.version,
                                 "prompt_sha256": prompt.sha256,
                                 "nonce_sha256": hashlib.sha256(nonce.encode()).hexdigest()[:16]}},
        max_tokens=200, temperature=0.0,
    )
    return clean_translation(res.content, question, nonce)


def start_translation(
    principal: Principal, question: str, *, settings: Settings,
    translate_fn: Callable[..., str | None] = translate_query,
) -> Callable[[], tuple[str | None, str]]:
    """Lanza la traducción en segundo plano. Devuelve una función que espera el resultado hasta
    `rag_translate_timeout_s` desde el lanzamiento → (texto o None, estado).

    Estados: ok | empty | timeout | error."""
    t0 = time.perf_counter()
    fut = _EXECUTOR.submit(translate_fn, principal, question, settings=settings)

    def wait() -> tuple[str | None, str]:
        left = max(0.0, settings.rag_translate_timeout_s - (time.perf_counter() - t0))
        try:
            out = fut.result(timeout=left)
        except FutureTimeout:
            return None, "timeout"
        except Exception as exc:  # el proveedor falla: la recuperación sigue sin traducción
            logger.warning("traducción de la consulta no disponible: %s", type(exc).__name__)
            return None, "error"
        return out, "ok" if out else "empty"

    return wait


def translate_with_timeout(
    principal: Principal, question: str, *, settings: Settings,
    translate_fn: Callable[..., str | None] = translate_query,
) -> tuple[str | None, str]:
    """Traducción síncrona con tope de tiempo (runner de evals)."""
    return start_translation(principal, question, settings=settings, translate_fn=translate_fn)()


def retrieve_bilingual(
    principal: Principal,
    question: str,
    k: int = 8,
    filters: dict[str, Any] | None = None,
    *,
    settings: Settings | None = None,
    trace: RetrievalTrace | None = None,
    translate_fn: Callable[..., str | None] = translate_query,
    **kwargs: Any,
) -> list[Hit]:
    """`retrieve_as` + la traducción de la pregunta como consulta alternativa (si está activa).

    La traducción se lanza antes y `retrieve` la espera después de puntuar los candidatos de la
    consulta original (embedding + SQL + rerank ≈ 1,5 s en CPU), así que su coste en latencia es
    max(0, traducción − recuperación original) + el rerank de los candidatos nuevos.
    Misma firma que `retrieve_as` (es el `retrieve_fn` por defecto de `answer_question`)."""
    s = settings or get_settings()
    tr = trace if trace is not None else RetrievalTrace(user=principal.user, role=None)
    alt: Callable[[], list[str]] | None = None
    if s.rag_cross_lingual == "translate" and isinstance(question, str) and question.strip():
        wait = start_translation(principal, question, settings=s, translate_fn=translate_fn)

        def alt() -> list[str]:
            text, tr.translate_status = wait()
            return [text] if text else []

    return retrieve_as(principal, question, k, filters, settings=s, trace=tr, alt_queries=alt,
                       **kwargs)
