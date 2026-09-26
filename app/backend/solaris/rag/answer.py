"""Respuesta citada (M2-T6, F02): recuperación con ACL → umbral de evidencia → sobre de datos → LLM
→ validación de citas en el servidor → limpieza de URLs.

Especificación obligatoria: `raw/sessions/2026-09-25_security_M2-T8.md` §4. Resumen de garantías:
- Prompt de sistema **estático** (`solaris/prompts/rag_answer.v2.md`), su versión y sha256 al audit.
- Pregunta y fragmentos solo en el mensaje `user`, en JSON dentro de `<untrusted_data nonce=…>`,
  neutralizados (invisibles, tokens de plantilla, marcadores de rol) y marcados (`ocr`, `hidden`,
  `suspicious`). Las fuentes sospechosas se marcan, no se borran.
- `route()` sin herramientas (no las admite) y con salida estructurada (JSON schema).
- El servidor solo acepta citas a fuentes enviadas (S1…Sn: chunks recuperados y visibles para el
  Principal). Las inventadas se descartan y se registran; sin citas válidas → "no encontrado".
- Se quitan URLs, enlaces e imágenes markdown de la respuesta. Si la salida contiene el nonce o una
  línea literal del prompt de sistema, se descarta.
- `instruction_ignored` (detector heurístico, del modelo o ambos) va al audit del `llm_call` y como
  aviso en la respuesta.
- Sin evidencia suficiente (umbral calibrado, ver `EvidenceGate`) → "no encontrado" **sin llamar al
  LLM**.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from solaris.audit import AuditError, record_safe, writer_configured
from solaris.llm import route
from solaris.prompts import SystemPrompt, load_prompt
from solaris.prompts.untrusted import (
    EnvelopeSource,
    build_envelope,
    first_match_excerpt,
    make_source,
    new_nonce,
    strip_invisible,
)
from solaris.rag.crosslingual import retrieve_bilingual
from solaris.rag.lang import guess_lang
from solaris.rag.retrieve import Hit, RetrievalTrace
from solaris.settings import Settings, get_settings

if TYPE_CHECKING:
    from solaris.auth.core import Principal

# M2-T7: v3 (autocomprobación "asked"/"asked_in_sources") dio la mejor precisión medida (93 %,
# 1.ª pasada). v4 (source_term/same_meaning + guarda term_mismatch) arregló QA-041 pero bajó la
# precisión al 78,8 % (2.ª pasada): queda versionado y seleccionable, no por defecto.
PROMPT_VERSION = "rag_answer.v3"  # v1/v2: M2-T6 (se conservan, versionados)
TASK = "rag_answer"
K = 8  # fuentes como máximo (spec §4.2: k ≤ 8)
MAX_CITATIONS = 3  # M2-T7: citas por respuesta como máximo (las de mejor rango de recuperación)
MAX_ANSWER_TOKENS = 700  # la salida esperada es de ~100–300 tokens (≤120 palabras + JSON)

_IGNORED_SCHEMA: dict[str, Any] = {
    "type": "array",
    "items": {
        "type": "object",
        "additionalProperties": False,
        "required": ["source", "summary"],
        "properties": {"source": {"type": "string"}, "summary": {"type": "string"}},
    },
}
_BASE_FIELDS: dict[str, Any] = {
    "answer": {"type": "string"},
    "citations": {"type": "array", "items": {"type": "string"}},
    "not_found": {"type": "boolean"},
    "ignored_instructions": _IGNORED_SCHEMA,
}
# Campos de autocomprobación que el modelo rellena ANTES de la respuesta (orden del esquema).
_CHECK_FIELDS: dict[str, dict[str, Any]] = {
    "rag_answer.v1": {},
    "rag_answer.v2": {},
    "rag_answer.v3": {"asked": {"type": "string"}, "asked_in_sources": {"type": "boolean"}},
    "rag_answer.v4": {"asked": {"type": "string"}, "source_term": {"type": "string"},
                      "same_meaning": {"type": "boolean"}},
}


def response_format(prompt_version: str) -> dict[str, Any]:
    """Salida estructurada (JSON schema estricto) del prompt `prompt_version`."""
    props = {**_CHECK_FIELDS[prompt_version], **_BASE_FIELDS}
    return {"type": "json_schema",
            "json_schema": {"name": "rag_answer", "strict": True,
                            "schema": {"type": "object", "additionalProperties": False,
                                       "required": list(props), "properties": props}}}


RESPONSE_FORMAT: dict[str, Any] = response_format(PROMPT_VERSION)

NOT_FOUND_TEXT = {
    "es": "No encontrado: no hay evidencia en los documentos a los que tienes acceso para "
          "responder a esta pregunta.",
    "en": "Not found: there is no evidence in the documents you have access to that answers "
          "this question.",
}

# --- umbral de evidencia --------------------------------------------------------------------------


@dataclass(frozen=True)
class EvidenceGate:
    """Umbral de "no encontrado" antes del LLM (calibrado en M2-T6 con qa.jsonl, solo recuperación).

    Con rerank: si la mejor puntuación del cross-encoder es < `min_rerank`, no hay evidencia.
    Sin rerank (backend `none`): solo "sin resultados". La decisión fina (información relacionada
    que no responde) la toma el modelo con la regla "not_found" del prompt y, en el servidor, la
    validación de citas.
    """

    min_rerank: float = -7.0

    def has_evidence(self, hits: list[Hit]) -> tuple[bool, float | None]:
        if not hits:
            return False, None
        scores = [h.rerank for h in hits if h.rerank is not None]
        if not scores:
            return True, None
        top = max(scores)
        return top >= self.min_rerank, top


DEFAULT_GATE = EvidenceGate()

# --- salida del modelo ----------------------------------------------------------------------------

_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.I)
_MARKER_RE = re.compile(r"\[\s*(S\d{1,3}(?:\s*[,;]\s*S\d{1,3})*)\s*\]", re.I)
_MD_IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
_MD_LINK_RE = re.compile(r"\[([^\]]*)\]\(\s*[^)]*\)")
_HTML_TAG_RE = re.compile(r"<\s*(?:img|a|iframe|script|link)\b[^>]*>|<\s*/\s*a\s*>", re.I)
_URL_RE = re.compile(
    r"(?i)\b(?:https?|ftp|file|data|javascript):[^\s<>\"'\])]+|\bwww\.[^\s<>\"'\])]+|"
    r"//[a-z0-9.-]+\.[a-z]{2,}[^\s<>\"'\])]*"
)


def parse_model_output(content: str) -> dict[str, Any] | None:
    """JSON del modelo (tolera vallas ``` y texto alrededor). Estructura inválida → None."""
    text = _FENCE_RE.sub("", content or "").strip()
    try:
        data = json.loads(text)
    except ValueError:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            return None
        try:
            data = json.loads(text[start:end + 1])
        except ValueError:
            return None
    if not isinstance(data, dict) or not isinstance(data.get("answer"), str):
        return None
    return data


def strip_urls(text: str) -> tuple[str, int]:
    """Quita imágenes markdown, enlaces (se conserva el texto), etiquetas HTML de enlace y URLs."""
    n = 0

    def count(repl: str | Callable[[re.Match[str]], str]):
        def _f(m: re.Match[str]) -> str:
            nonlocal n
            n += 1
            return repl(m) if callable(repl) else repl
        return _f

    text = _MD_IMAGE_RE.sub(count(""), text)
    text = _MD_LINK_RE.sub(count(lambda m: m.group(1)), text)
    text = _HTML_TAG_RE.sub(count(""), text)
    text = _URL_RE.sub(count("[enlace eliminado]"), text)
    return text, n


@dataclass
class ValidatedOutput:
    answer: str
    cited_ids: list[str]  # ids válidos en orden de aparición
    dropped: list[str]  # ids citados que no se enviaron
    model_not_found: bool
    model_ignored: list[dict[str, str]]
    urls_removed: int
    capped: list[str] = field(default_factory=list)  # citas válidas retiradas por el tope
    asked_in_sources: bool | None = None  # autocomprobación del modelo (same_meaning en v4)


def validate_output(data: dict[str, Any], valid_ids: set[str], *,
                    max_citations: int | None = None,
                    priority: dict[str, int] | None = None) -> ValidatedOutput:
    """Citas solo a fuentes enviadas; los marcadores [Sx] válidos se renumeran a [1], [2]…

    `max_citations` (M2-T7): se conservan como mucho N citas, las de mejor `priority` (rango de
    recuperación; a igualdad, orden de aparición). Los marcadores de las demás se quitan del texto.
    La autocomprobación del modelo `same_meaning: false` (prompt v4; `asked_in_sources` en v3)
    cuenta como "no encontrado": el dato de la fuente no es el tipo de dato preguntado."""
    answer = strip_invisible(str(data.get("answer", "")))
    order: list[str] = []
    dropped: list[str] = []

    def note(sid: str) -> None:
        sid = sid.upper()
        if sid in valid_ids:
            if sid not in order:
                order.append(sid)
        elif sid not in dropped:
            dropped.append(sid)

    for m in _MARKER_RE.finditer(answer):
        for sid in re.split(r"\s*[,;]\s*", m.group(1)):
            note(sid)
    raw_cits = data.get("citations")
    for c in raw_cits if isinstance(raw_cits, list) else []:
        if isinstance(c, str):
            note(c.strip().strip("[]"))

    capped: list[str] = []
    if max_citations is not None and len(order) > max_citations:
        prio = priority or {}
        keep = set(sorted(order, key=lambda x: (prio.get(x, 10**6), order.index(x)))[
            :max_citations])
        capped = [x for x in order if x not in keep]
        order = [x for x in order if x in keep]

    def renumber(m: re.Match[str]) -> str:
        ids = [s.upper() for s in re.split(r"\s*[,;]\s*", m.group(1))]
        nums = [str(order.index(s) + 1) for s in ids if s in order]
        return f"[{', '.join(nums)}]" if nums else ""

    answer = _MARKER_RE.sub(renumber, answer)
    answer, n_urls = strip_urls(answer)
    answer = re.sub(r"[ \t]+([.,;:])", r"\1", re.sub(r"[ \t]{2,}", " ", answer)).strip()
    ignored = []
    for it in data.get("ignored_instructions") or []:
        if isinstance(it, dict) and isinstance(it.get("source"), str):
            ignored.append({"source": it["source"].strip().strip("[]").upper()[:8],
                            "summary": strip_urls(str(it.get("summary", "")))[0][:200]})
    asked_in_sources = data.get("same_meaning", data.get("asked_in_sources"))
    return ValidatedOutput(answer=answer, cited_ids=order, dropped=dropped,
                           model_not_found=data.get("not_found") is True
                           or asked_in_sources is False,
                           model_ignored=ignored, urls_removed=n_urls, capped=capped,
                           asked_in_sources=asked_in_sources
                           if isinstance(asked_in_sources, bool) else None)


_ART = frozenset({"el", "la", "los", "las", "lo", "un", "una", "unos", "unas"})
_LINK = frozenset(("de", "del", "of"))
_TERM_STOP = frozenset({
    "el", "la", "los", "las", "lo", "un", "una", "a", "al", "en", "con", "para", "por", "que",
    "qué", "cuál", "cual", "y", "o", "the", "an", "to", "for", "on", "in", "which", "what",
})


def _fold(text: str) -> list[str]:
    t = unicodedata.normalize("NFKD", text.lower())
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    return re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", t)


def _head_and_complement(text: str) -> tuple[str | None, str | None]:
    """Núcleo y primer complemento con "de"/"of": "par de apriete de los tornillos" → (par,
    apriete)."""
    toks = [w for w in _fold(text) if w not in _TERM_STOP or w in _LINK]
    toks = [w for w in toks if w not in _ART]
    if not toks or toks[0] in _LINK:
        return None, None
    head = toks[0]
    for i, w in enumerate(toks[1:4], 1):
        if w in _LINK and i + 1 < len(toks):
            return head, toks[i + 1]
    return head, None


def term_mismatch(asked: str, source_term: str) -> bool:
    """Guarda determinista sobre la autocomprobación del modelo (M2-T7): mismo núcleo con distinto
    complemento ("par de apriete" frente a "par de arrancamiento", "presión de aire" frente a
    "presión de gas") = otro tipo de dato. Solo decide cuando ambos términos tienen núcleo y
    complemento; en cualquier otro caso (otro idioma, paráfrasis) no interviene."""
    if not isinstance(asked, str) or not isinstance(source_term, str):
        return False
    h1, c1 = _head_and_complement(asked)
    h2, c2 = _head_and_complement(source_term)
    return bool(h1 and h1 == h2 and c1 and c2 and c1 != c2)


def leaks_prompt(answer: str, nonce: str, prompt: SystemPrompt) -> bool:
    if nonce in answer:
        return True
    low = " ".join(answer.lower().split())
    return any(" ".join(line.lower().split()) in low for line in prompt.leak_lines())


# --- resultado ------------------------------------------------------------------------------------


@dataclass
class AskResult:
    answer: str
    citations: list[dict[str, Any]]
    not_found: bool
    warnings: list[dict[str, Any]]
    model: str | None
    latency_ms: float
    ai_generated: bool = True
    # Diagnóstico para evals (no se expone por HTTP).
    debug: dict[str, Any] = field(default_factory=dict)

    def public(self) -> dict[str, Any]:
        return {"answer": self.answer, "citations": self.citations, "not_found": self.not_found,
                "warnings": self.warnings, "ai_generated": self.ai_generated,
                "model": self.model, "latency_ms": self.latency_ms}


def _src_ref(s: EnvelopeSource, folder: str | None = None) -> dict[str, Any]:
    out = {"doc_id": s.doc_id, "version": s.version, "locator": s.locator, "title": s.title}
    if folder is not None:
        out["folder"] = folder
    return out


class _DeferredAudit:
    """Recoge el `llm_call` que emite `route()` para completarlo con la validación posterior
    (citas descartadas, instrucciones declaradas por el modelo, fuga del nonce) y escribirlo una
    sola vez. Si `route()` falla, se escribe igualmente (outcome error)."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, Any, dict[str, Any], dict[str, Any]]] = []

    def __call__(self, event_type: str, actor: Any, payload: dict[str, Any], **kw: Any) -> None:
        self.calls.append((event_type, actor, payload, kw))

    def flush(self, writer: Callable[..., None] | None, settings: Settings,
              security: dict[str, Any] | None = None) -> None:
        for event_type, actor, payload, kw in self.calls:
            if security:
                payload.setdefault("security", {}).update(security)
            if writer is not None:
                writer(event_type, actor, payload, **kw)
            elif writer_configured(settings):
                record_safe(event_type, actor, payload, **kw)
            elif settings.audit_required:
                raise AuditError("AUDIT_REQUIRED=true pero falta AUDIT_WRITER_PASSWORD")
        self.calls.clear()


def _not_found(question: str, t0: float, warnings: list[dict[str, Any]] | None = None,
               model: str | None = None, **debug: Any) -> AskResult:
    return AskResult(answer=NOT_FOUND_TEXT[guess_lang(question)], citations=[], not_found=True,
                     warnings=warnings or [], model=model,
                     latency_ms=round((time.perf_counter() - t0) * 1000, 1), debug=debug)


RetrieveFn = Callable[..., list[Hit]]


def answer_question(
    principal: Principal,
    question: str,
    filters: dict[str, Any] | None = None,
    *,
    settings: Settings | None = None,
    retrieve_fn: RetrieveFn | None = None,
    route_fn: Callable[..., Any] = route,
    audit: Callable[..., None] | None = None,
    gate: EvidenceGate = DEFAULT_GATE,
    prompt_version: str = PROMPT_VERSION,
    nonce: str | None = None,
) -> AskResult:
    """Pipeline de `/ask` para el usuario autenticado `principal` (on-behalf-of).

    `retrieve_fn`, `route_fn` y `audit` se sustituyen en tests. Los errores del proveedor LLM
    (`LLMError`) y de la BD (`DbUnavailable`) se propagan: el endpoint los traduce a 502/503
    genéricos.
    """
    s = settings or get_settings()
    t0 = time.perf_counter()
    trace = RetrievalTrace(user=principal.user, role=None)
    if retrieve_fn is None:  # por defecto: ACL del Principal + recuperación cruzada ES↔EN
        retrieve_fn = retrieve_bilingual
    hits = retrieve_fn(principal, question, K, filters, settings=s, trace=trace)
    ok, top = gate.has_evidence(hits)
    dbg: dict[str, Any] = {"retrieval_ms": trace.timings_ms, "top_rerank": top,
                           "hits": [h.citation() | {"folder": h.folder, "rerank": h.rerank,
                                                    "rank": h.rank, "via": h.via}
                                    for h in hits]}
    if not ok:
        return _not_found(question, t0, gate="below_threshold", **dbg)

    prompt = load_prompt(prompt_version)
    nonce = nonce or new_nonce()
    sources = [
        make_source(f"S{i}", doc_id=h.doc_id, version=h.version, locator=h.locator,
                    title=h.title, text=h.content)
        for i, h in enumerate(hits, 1)
    ]
    user_msg, sent = build_envelope(question, sources, nonce)
    by_id = {src.id: (src, hits[int(src.id[1:]) - 1]) for src in sent}
    heuristic = {src.id: src for src in sent if src.flags["suspicious"]}

    audit_sources = [
        {"id": src.id, "doc_id": h.doc_id, "version": h.version, "locator": h.locator,
         "folder": h.folder, "flags": src.flags, "rerank": h.rerank}
        for src, h in by_id.values()
    ]
    deferred = _DeferredAudit()
    base_security = {
        "prompt_version": prompt.version,
        "prompt_sha256": prompt.sha256,
        "nonce_sha256": hashlib.sha256(nonce.encode()).hexdigest()[:16],
    }
    messages = [{"role": "system", "content": prompt.text},
                {"role": "user", "content": user_msg}]
    try:
        result = route_fn(
            TASK, messages, settings=s, actor=principal.actor, audit=deferred,
            audit_meta={"sources": audit_sources, "question_lang": guess_lang(question),
                        "security": dict(base_security)},
            response_format=response_format(prompt.version), max_tokens=MAX_ANSWER_TOKENS,
        )
    except Exception:
        deferred.flush(audit, s)
        raise

    warnings: list[dict[str, Any]] = []
    data = parse_model_output(result.content)
    discarded = None
    if data is None:
        discarded = "invalid_output"
        v = ValidatedOutput("", [], [], True, [], 0)
    else:
        v = validate_output(data, set(by_id), max_citations=MAX_CITATIONS,
                            priority={sid: h.rank or int(sid[1:]) for sid, (_, h) in
                                      by_id.items()})
        if leaks_prompt(v.answer, nonce, prompt) or any(
            nonce in i["summary"] for i in v.model_ignored
        ):
            discarded = "prompt_leak"

    # instruction_ignored: heurístico (sobre lo enviado) ∪ declarado por el modelo.
    model_ids = {i["source"] for i in v.model_ignored if i["source"] in by_id}
    ignored_log = []
    for sid in sorted(set(heuristic) | model_ids, key=lambda x: int(x[1:])):
        src, h = by_id[sid]
        det = ("both" if sid in heuristic and sid in model_ids
               else "heuristic" if sid in heuristic else "model")
        excerpt = first_match_excerpt(h.content) if sid in heuristic else ""
        ignored_log.append({
            "source_id": sid, "doc_id": h.doc_id, "version": h.version, "locator": h.locator,
            "detector": det, "pattern": ",".join(src.patterns) or None,
            "excerpt_sha256": hashlib.sha256(excerpt.encode()).hexdigest() if excerpt else None,
            "excerpt": excerpt or None,
        })
        warnings.append({"type": "instruction_ignored", "source": _src_ref(src, h.folder),
                         "message": "El documento contiene instrucciones dirigidas al asistente "
                                    "que se han ignorado."})

    citations: list[dict[str, Any]] = []
    not_found = True
    answer = NOT_FOUND_TEXT[guess_lang(question)]
    if discarded:
        warnings.append({"type": "output_discarded", "reason": discarded})
    elif data is not None and v.cited_ids and not v.model_not_found and term_mismatch(
            str(data.get("asked", "")), str(data.get("source_term", ""))):
        warnings.append({"type": "term_mismatch",
                         "message": "La fuente contiene un dato parecido, no el preguntado."})
    elif v.model_not_found:
        # Un "not_found" sin explicación útil (p. ej. la palabra suelta) → texto fijo en el idioma.
        answer = v.answer if len(v.answer) >= 20 else answer
    elif v.cited_ids:
        not_found = False
        answer = v.answer
        for sid in v.cited_ids:
            src, h = by_id[sid]
            citations.append({"doc_id": h.doc_id, "version": h.version, "title": h.title,
                              "locator": h.locator, "folder": h.folder})
            if src.flags["ocr"] or src.flags["hidden"]:
                warnings.append({"type": "low_confidence_source", "source": _src_ref(src, h.folder),
                                 "reason": "ocr" if src.flags["ocr"] else "hidden"})
    else:
        warnings.append({"type": "no_valid_citations"})
    if v.dropped:
        warnings.append({"type": "citations_dropped", "count": len(v.dropped)})
    if v.capped and not not_found:
        warnings.append({"type": "citations_capped", "count": len(v.capped)})
    if v.urls_removed:
        warnings.append({"type": "urls_removed", "count": v.urls_removed})
    if not_found:
        answer, _ = strip_urls(answer)
        answer = _MARKER_RE.sub("", answer)
        answer = re.sub(r"\s*\[\d+(?:\s*,\s*\d+)*\]", "", answer).strip() or NOT_FOUND_TEXT[
            guess_lang(question)]

    deferred.flush(audit, s, {
        "instruction_ignored": ignored_log,
        "nonce_leak": discarded == "prompt_leak",
        "output_discarded": discarded,
        "citations_dropped": len(v.dropped),
        "citations_dropped_ids": v.dropped,
        "urls_removed": v.urls_removed,
        "citations_capped_ids": v.capped,
        "asked_in_sources": v.asked_in_sources,
        "term_mismatch": any(w["type"] == "term_mismatch" for w in warnings),
        "cited": [{"id": sid, "doc_id": by_id[sid][1].doc_id} for sid in v.cited_ids]
        if not not_found else [],
        "not_found": not_found,
    })
    dbg.update({"llm": {"prompt_tokens": result.prompt_tokens,
                        "completion_tokens": result.completion_tokens,
                        "cost_usd": result.cost_usd, "latency_ms": result.latency_ms,
                        "provider": result.provider, "used_fallback": result.used_fallback},
                "model_not_found": v.model_not_found, "dropped": v.dropped,
                "capped": v.capped, "asked": str((data or {}).get("asked", ""))[:300],
                "source_term": str((data or {}).get("source_term", ""))[:300],
                "asked_in_sources": v.asked_in_sources,
        "term_mismatch": any(w["type"] == "term_mismatch" for w in warnings),
                "retrieval_trace": {"alt_queries": trace.alt_queries,
                                    "translate_status": trace.translate_status},
                "sent_sources": len(sent)})
    return AskResult(answer=answer, citations=citations, not_found=not_found, warnings=warnings,
                     model=result.model, latency_ms=round((time.perf_counter() - t0) * 1000, 1),
                     debug=dbg)
