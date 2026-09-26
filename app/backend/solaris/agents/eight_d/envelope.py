"""Sobre de datos y validación de salida para las llamadas LLM del 8D (spec §4 de M2-T8; R03).

Misma forma que `solaris.prompts.untrusted` (JSON dentro de `<untrusted_data nonce>`), con varios
tipos de elemento citable cuyos ids asigna el servidor:

    C1…  segmentos VISIBLES y no sospechosos de la reclamación (lo oculto, los metadatos y lo que
         el detector marca no se envían nunca: M3-T2);
    S1…  fragmentos de documentos del corpus recuperados COMO el usuario (≤ 8 por llamada, ≤ 1.500
         caracteres cada uno);
    F1…  filas del AMFE visibles para el usuario (datos estructurados, cada campo acotado);
    E1…  hechos del ERP devueltos por el MCP como el usuario (acotados).

Todo texto pasa por `neutralize()` y el detector marca `flags.suspicious`. El modelo cita SOLO
esos ids: el servidor descarta los inventados (`validate_ids`) y limpia el texto libre
(`clean_text`: URLs, frases con patrones de inyección y frases con códigos que no están en lo
enviado). Si la salida contiene el nonce o una línea del prompt, se descarta entera.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from solaris.prompts.untrusted import detect_injection, neutralize, strip_invisible
from solaris.rag.answer import strip_urls

MAX_DOC_SOURCES = 8  # spec §4.2: k ≤ 8 fragmentos de documento por llamada
MAX_SOURCE_CHARS = 1500
MAX_COMPLAINT_SEGMENTS = 6
MAX_SEGMENT_CHARS = 1400
MAX_FMEA_ROWS = 16
MAX_FMEA_FIELD = 220
MAX_ERP_FACTS = 14
MAX_ERP_CHARS = 700
# Presupuesto total del sobre del 8D (≈ 8–9k tokens). Mayor que el de /ask (16k): lleva la
# reclamación, filas del AMFE y hechos del ERP además de los fragmentos. Se recortan primero los
# últimos documentos, después los hechos del ERP y las filas del AMFE.
MAX_ENVELOPE_CHARS = 30_000

_CODE_RE = re.compile(r"(?<![\w-])[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+(?![\w-])")
_SENT_RE = re.compile(r"(?<=[.;!?])\s+")
_ID_RE = re.compile(r"^[CSFE]\d{1,3}$")
# Marcadores de id interno en el texto libre ("(S2, S3)", "[F4]", "según E3"): la UI cita con la
# referencia real, así que se quitan.
_ID_MARK_RE = re.compile(r"\s*[\[(]\s*[CSFE]\d{1,3}(?:\s*[,;/]\s*[CSFE]\d{1,3})*\s*[\])]")
_ID_BARE_RE = re.compile(r"\b[CSFE]\d{1,2}\b")


@dataclass
class Item:
    """Elemento citable del sobre. `ref` es la cita que ve la UI (nunca va al modelo)."""

    id: str
    kind: str  # complaint | document | fmea_row | erp
    payload: dict[str, Any]
    ref: dict[str, Any]
    suspicious: bool = False
    patterns: list[str] = field(default_factory=list)

    def as_json(self) -> dict[str, Any]:
        return {"id": self.id, "kind": self.kind, **self.payload,
                "flags": {**self.payload.get("flags", {}), "suspicious": self.suspicious}}


def _clean(v: Any, n: int) -> Any:
    if isinstance(v, str):
        return neutralize(v, n)
    if isinstance(v, dict):
        return {str(k)[:40]: _clean(x, n) for k, x in list(v.items())[:30]}
    if isinstance(v, list):
        return [_clean(x, n) for x in v[:30]]
    return v


def complaint_item(n: int, segment: dict[str, Any], complaint_ref: dict[str, Any]) -> Item:
    text = segment.get("text", "")
    pats = detect_injection(text)
    return Item(id=f"C{n}", kind="complaint",
                payload={"locator": _clean(segment.get("location") or {}, 80),
                         "text": neutralize(text, MAX_SEGMENT_CHARS)},
                ref={**complaint_ref, "locator": segment.get("location") or {},
                     "segment": segment.get("id")},
                suspicious=bool(pats) or bool(segment.get("suspicious")), patterns=pats)


def document_item(n: int, hit: Any) -> Item:
    loc = hit.locator or {}
    pats = detect_injection(hit.content)
    return Item(id=f"S{n}", kind="document",
                payload={"doc_id": neutralize(hit.doc_id, 80),
                         "version": neutralize(hit.version, 20),
                         "locator": _clean(loc, 200), "title": neutralize(hit.title or "", 200),
                         "flags": {"ocr": bool(loc.get("ocr")), "hidden": bool(loc.get("hidden"))},
                         "text": neutralize(hit.content, MAX_SOURCE_CHARS)},
                ref={"kind": "document", "doc_id": hit.doc_id, "version": hit.version,
                     "locator": loc, "title": hit.title, "folder": hit.folder},
                suspicious=bool(pats), patterns=pats)


FMEA_FIELDS = ("process_step", "failure_mode", "effect", "severity", "cause", "occurrence",
               "prevention_control", "detection_control", "detection", "rpn")


def fmea_item(n: int, row: dict[str, Any]) -> Item:
    fields = {k: _clean(row.get(k), MAX_FMEA_FIELD) for k in FMEA_FIELDS}
    text = " ".join(str(v) for v in fields.values() if v is not None)
    pats = detect_injection(text)
    return Item(id=f"F{n}", kind="fmea_row",
                payload={"doc_id": neutralize(row["doc_id"], 80),
                         "version": neutralize(row["version"], 20),
                         "sheet": neutralize(row.get("sheet") or "", 60),
                         "row": row["row_no"], **fields},
                ref={"kind": "fmea_row", "doc_id": row["doc_id"], "version": row["version"],
                     "locator": {"sheet": row.get("sheet"), "row": row["row_no"]},
                     "folder": row.get("folder")},
                suspicious=bool(pats), patterns=pats)


def erp_item(n: int, tool: str, text: str, query_ref: int | None) -> Item:
    pats = detect_injection(text)
    return Item(id=f"E{n}", kind="erp",
                payload={"tool": tool, "text": neutralize(text, MAX_ERP_CHARS)},
                ref={"kind": "erp", "tool": tool, "query_index": query_ref},
                suspicious=bool(pats), patterns=pats)


def build(context: dict[str, Any], items: list[Item], nonce: str,
          budget: int = MAX_ENVELOPE_CHARS) -> tuple[str, list[Item]]:
    """Mensaje `user` con el sobre. Aplica los topes por tipo y el presupuesto total."""
    if not re.fullmatch(r"[0-9a-f]{16}", nonce):
        raise ValueError("nonce no válido")
    caps = {"complaint": MAX_COMPLAINT_SEGMENTS, "document": MAX_DOC_SOURCES,
            "fmea_row": MAX_FMEA_ROWS, "erp": MAX_ERP_FACTS}
    seen: dict[str, int] = {}
    kept: list[Item] = []
    for it in items:
        seen[it.kind] = seen.get(it.kind, 0) + 1
        if seen[it.kind] <= caps[it.kind]:
            kept.append(it)
    ctx = _clean(context, 600)

    def render(xs: list[Item]) -> str:
        body = json.dumps({"context": ctx, "sources": [x.as_json() for x in xs]},
                          ensure_ascii=False, default=str)
        return f'<untrusted_data nonce="{nonce}">\n{body}\n</untrusted_data nonce="{nonce}">'

    text = render(kept)
    for kind in ("document", "erp", "fmea_row", "complaint"):
        while len(text) > budget and any(x.kind == kind for x in kept):
            last = max(i for i, x in enumerate(kept) if x.kind == kind)
            kept.pop(last)
            text = render(kept)
    return text, kept


# --- validación de la salida ---------------------------------------------------------------------


def validate_ids(ids: Any, valid: set[str]) -> tuple[list[str], list[str]]:
    """(citas válidas sin repetir, en orden; citas descartadas). Solo ids enviados."""
    kept: list[str] = []
    dropped: list[str] = []
    for x in ids if isinstance(ids, list) else []:
        if not isinstance(x, str):
            continue
        sid = x.strip().strip("[]").upper()[:8]
        if sid in valid and _ID_RE.match(sid):
            if sid not in kept:
                kept.append(sid)
        elif sid and sid not in dropped:
            dropped.append(sid)
    return kept, dropped


@dataclass
class TextGuard:
    """Limpieza del texto libre del modelo contra lo realmente enviado."""

    allowed_text: str
    removed: list[dict[str, str]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._norm = " ".join(self.allowed_text.upper().split())
        self._codes = set(_CODE_RE.findall(self.allowed_text.upper()))

    def clean(self, value: Any, max_chars: int, where: str) -> str:
        if not isinstance(value, str):
            return ""
        text, n_urls = strip_urls(strip_invisible(value))
        text = _ID_BARE_RE.sub("", _ID_MARK_RE.sub("", text))
        if n_urls:
            self.removed.append({"field": where, "reason": "url"})
        out = []
        for sent in _SENT_RE.split(" ".join(text.split())):
            if not sent:
                continue
            if detect_injection(sent):
                self.removed.append({"field": where, "reason": "injection_pattern"})
                continue
            bad = [c for c in _CODE_RE.findall(sent.upper()) if c not in self._codes]
            if bad:
                self.removed.append({"field": where, "reason": "code_not_in_sources",
                                     "code": neutralize(bad[0], 40)})
                continue
            out.append(sent)
        res = neutralize(" ".join(out), max_chars)
        return res


def parse_json(content: str) -> dict[str, Any] | None:
    text = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", content or "", flags=re.I).strip()
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
    return data if isinstance(data, dict) else None


def schema(name: str, props: dict[str, Any]) -> dict[str, Any]:
    return {"type": "json_schema",
            "json_schema": {"name": name, "strict": True,
                            "schema": {"type": "object", "additionalProperties": False,
                                       "required": list(props), "properties": props}}}


IGNORED_SCHEMA: dict[str, Any] = {
    "type": "array",
    "items": {"type": "object", "additionalProperties": False, "required": ["source", "summary"],
              "properties": {"source": {"type": "string"}, "summary": {"type": "string"}}},
}
CITED_TEXT: dict[str, Any] = {
    "type": "object", "additionalProperties": False, "required": ["text", "citations"],
    "properties": {"text": {"type": "string"},
                   "citations": {"type": "array", "items": {"type": "string"}}},
}
