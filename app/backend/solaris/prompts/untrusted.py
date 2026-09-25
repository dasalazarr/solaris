"""Sobre de datos no confiables (spec §4.1–4.2 de M2-T8; R03). Python puro, sin LLM.

Todo contenido externo (pregunta del usuario, fragmentos del corpus y, en M3-T3, la reclamación y
los resultados del ERP) llega al modelo **solo** así:

    <untrusted_data nonce="<hex aleatorio por petición>">
    {"question": "...", "sources": [{"id": "S1", ..., "flags": {...}, "text": "..."}]}
    </untrusted_data nonce="<el mismo>">

- JSON (`ensure_ascii=False`): las comillas y saltos de línea van escapados, así que un fragmento no
  puede cerrar el bloque ni falsificar otra fuente.
- Antes de serializar, cada texto pasa por `neutralize()`: fuera caracteres de control, de anchura
  cero, bidi y de etiqueta Unicode (contrabando ASCII); los tokens de plantilla de chat y los
  marcadores de rol se sustituyen por una forma visible e inerte.
- `detect_injection()` marca (`flags.suspicious`) las fuentes con instrucciones dirigidas al
  asistente. **No borra el texto**: puede ser legítimo y hay que poder citarlo en el aviso.
"""

from __future__ import annotations

import json
import re
import secrets
import unicodedata
from dataclasses import dataclass, field
from typing import Any

MAX_SOURCE_CHARS = 1500
MAX_SOURCES = 8
MAX_QUESTION_CHARS = 2000
MAX_ENVELOPE_CHARS = 16_000  # presupuesto total de entrada del sobre (≈ 4–5k tokens)

# --- neutralización ------------------------------------------------------------------------------

# Anchura cero y bidi (U+200B–200F, U+202A–202E, U+2060–2064, U+2066–2069, U+FEFF) y etiquetas
# Unicode (U+E0000–E007F). Los de control (Cc) se quitan aparte, salvo \n y \t.
_INVISIBLE_RE = re.compile(
    "[​-‏‪-‮⁠-⁤⁦-⁩﻿\U000e0000-\U000e007f]"
)
# Tokens de plantilla y delimitadores propios → forma visible e inerte (comillas angulares y
# corchetes de ancho completo). Sin distinguir mayúsculas.
_TEMPLATE_SUBS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"</\s*untrusted_data", re.I), "‹/untrusted_data"),
    (re.compile(r"<\s*untrusted_data", re.I), "‹untrusted_data"),
    (re.compile(r"<\|"), "‹|"),
    (re.compile(r"\|>"), "|›"),
    (re.compile(r"\[\s*/\s*INST\s*\]", re.I), "［/INST］"),
    (re.compile(r"\[\s*INST\s*\]", re.I), "［INST］"),
    (re.compile(r"<\s*/\s*s\s*>", re.I), "‹/s›"),
    (re.compile(r"<\s*s\s*>", re.I), "‹s›"),
)
# Líneas que empiezan por un marcador de rol: `system:`, `assistant:`, `[system]`.
_ROLE_LINE_RE = re.compile(r"(?im)^([ \t]*)(?:(system|assistant)[ \t]*:|\[[ \t]*(system)[ \t]*\])")


def _role_sub(m: re.Match[str]) -> str:
    word = m.group(2) or m.group(3)
    return f"{m.group(1)}［{word}］"


def strip_invisible(text: str) -> str:
    """Quita los caracteres de control (salvo \\n y \\t), de anchura cero, bidi y de etiqueta."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _INVISIBLE_RE.sub("", text)
    return "".join(
        ch for ch in text if ch in "\n\t" or unicodedata.category(ch) != "Cc"
    )


def neutralize(text: str, max_chars: int | None = None) -> str:
    """Limpieza completa de un texto no confiable antes de serializarlo (orden: invisibles primero,
    para que `<\\u200b|` no escape a la sustitución de `<|`)."""
    if not isinstance(text, str):
        text = str(text)
    text = strip_invisible(text)
    for pat, repl in _TEMPLATE_SUBS:
        text = pat.sub(repl, text)
    text = _ROLE_LINE_RE.sub(_role_sub, text)
    if max_chars is not None and len(text) > max_chars:
        text = text[:max_chars] + "…"
    return text


# --- detector heurístico (ES/EN, sin LLM) --------------------------------------------------------
# Patrones mínimos de la spec §4.2. Refinamientos para no marcar texto técnico legítimo del corpus
# (medidos sobre los 340 chunks del demo, ver la traza de M2-T6):
#  * "override" solo cuenta con un objeto de instrucción/regla/sistema/rol o con "priority"
#    (el 8D-ARGA-2024-004 habla de un "override de −8 % en la velocidad de hilo");
#  * "you must"/"debes" solo en 2.ª persona explícita (las IT usan "se debe");
#  * "do not show/reveal" solo con un objeto dirigido (this/it/the user…): el 8D-ARGA-2024-004 dice
#    "the test … do not reveal lack of fusion".
_INJECTION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = tuple(
    (name, re.compile(rx, re.I))
    for name, rx in (
        ("ignore_previous",
         r"\b(?:ignore|ignora[rd]?|ignoren|olvida)\b(?:\s+\w+){0,4}?\s+"
         r"(?:instructions?|instrucciones|rules|reglas|restrictions|restricciones|prompts?)\b"),
        ("disregard", r"\bdisregard\b|\bhaz\s+caso\s+omiso\b|\bno\s+hagas\s+caso\b"),
        ("ai_assistant",
         r"\b(?:AI|IA)\s+(?:assistant|agent|model)\b|\basistente\s+(?:de\s+)?(?:IA|inteligencia"
         r"\s+artificial)\b|\blanguage\s+model\b|\bLLM\b|\bautomated\s+8D\s+tool\b"),
        ("you_must", r"\byou\s+must\b|\b(?:tú\s+)?debes\b"),
        ("system_prompt",
         r"\bsystem\s+prompt\b|\bprompt\s+(?:de|del)\s+sistema\b|\binstrucciones\s+del\s+sistema\b"),
        ("override",
         r"\b(?:priority\s+override|override\s+(?:your|the|all|any|previous|system|safety|"
         r"instructions?|rules|restrictions|policy|policies|role)\b)|\banula\s+(?:las|tus)\s+"
         r"(?:instrucciones|reglas|restricciones)\b"),
        ("pre_approved", r"\bpre-?approved\b|\bpre-?aprobad[oa]s?\b"),
        ("admin_role",
         r"\badmin(?:istrator)?\s+role\b|\brol\s+(?:de\s+)?admin(?:istrador)?\b|\brole\s*[:=]\s*admin\b"),
        ("do_not_show",
         r"\b(?:do\s+not|don'?t)\s+(?:show|display|reveal|mention|tell)\s+(?:this|these|that|it|"
         r"anyone|any|the\s+user|users?|to)\b|"
         r"\bno\s+(?:muestres|mostréis|menciones|reveles|digas)\b"),
        ("export_without_review",
         r"\b(?:export|send|submit|exporta\w*|env[ií]a\w*|manda\w*)\b.{0,80}?\b(?:without|sin)\b"
         r".{0,40}?\b(?:review|approval|revisi[oó]n|aprobaci[oó]n|validaci[oó]n)\b"),
    )
)


def detect_injection(text: str) -> list[str]:
    """Nombres de los patrones que aparecen en `text` (ya sin invisibles). Vacío = limpio."""
    t = strip_invisible(text)
    return [name for name, rx in _INJECTION_PATTERNS if rx.search(t)]


def first_match_excerpt(text: str, max_chars: int = 120) -> str:
    """Extracto alrededor de la primera coincidencia (para el audit, ya neutralizado)."""
    t = strip_invisible(text)
    best = None
    for _, rx in _INJECTION_PATTERNS:
        m = rx.search(t)
        if m and (best is None or m.start() < best):
            best = m.start()
    start = max(0, (best or 0) - 20)
    return neutralize(" ".join(t[start:start + max_chars * 2].split()))[:max_chars]


# --- sobre ---------------------------------------------------------------------------------------


@dataclass
class EnvelopeSource:
    id: str
    doc_id: str
    version: str
    locator: dict[str, Any]
    title: str
    text: str
    flags: dict[str, bool] = field(default_factory=dict)
    patterns: list[str] = field(default_factory=list)

    def as_json(self) -> dict[str, Any]:
        return {"id": self.id, "doc_id": self.doc_id, "version": self.version,
                "locator": self.locator, "title": self.title, "flags": self.flags,
                "text": self.text}


def new_nonce() -> str:
    return secrets.token_hex(8)


def make_source(
    sid: str, *, doc_id: str, version: str, locator: dict[str, Any], title: str, text: str,
    max_chars: int = MAX_SOURCE_CHARS,
) -> EnvelopeSource:
    """Fuente neutralizada y marcada. `ocr`/`hidden` salen del locator del chunk (S8)."""
    patterns = detect_injection(text) + [p for p in detect_injection(title)
                                         if p not in detect_injection(text)]
    loc = {str(k)[:40]: (neutralize(v, 200) if isinstance(v, str) else v)
           for k, v in (locator or {}).items()}
    return EnvelopeSource(
        id=sid,
        doc_id=neutralize(doc_id, 80),
        version=neutralize(version, 20),
        locator=loc,
        title=neutralize(title, 200),
        text=neutralize(text, max_chars),
        flags={"ocr": bool(loc.get("ocr")), "hidden": bool(loc.get("hidden")),
               "suspicious": bool(patterns)},
        patterns=patterns,
    )


def build_envelope(question: str, sources: list[EnvelopeSource], nonce: str,
                   *, budget: int = MAX_ENVELOPE_CHARS) -> tuple[str, list[EnvelopeSource]]:
    """Mensaje `user` con el sobre. Aplica los topes (k ≤ 8, pregunta ≤ 2.000, presupuesto total:
    se descartan las últimas fuentes si no caben). Devuelve (texto, fuentes realmente enviadas)."""
    if not re.fullmatch(r"[0-9a-f]{16}", nonce):
        raise ValueError("nonce no válido")
    q = neutralize(question, MAX_QUESTION_CHARS)
    kept = list(sources[:MAX_SOURCES])

    def render(srcs: list[EnvelopeSource]) -> str:
        body = json.dumps({"question": q, "sources": [s.as_json() for s in srcs]},
                          ensure_ascii=False)
        return f'<untrusted_data nonce="{nonce}">\n{body}\n</untrusted_data nonce="{nonce}">'

    text = render(kept)
    while len(text) > budget and kept:
        kept.pop()
        text = render(kept)
    return text, kept
