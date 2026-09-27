"""Parser de reclamaciones de cliente (M3-T2, F04 · R03). PDF/EML → campos estructurados.

    parsed = parse(file_bytes, filename, principal)          # síncrono (CLI, tests)
    parsed = await parse_async(file_bytes, filename, principal)  # endpoint / orquestador 8D

El documento es de un tercero: **todo su contenido es dato, nunca instrucción** (CLAUDE.md, R03).

1. **Extracción por canales.** PDF con pypdf; EML con `email` (cuerpo; adjuntos solo como
   metadatos: nombre, tipo, tamaño y sha256, sin abrirlos). Cada texto se etiqueta con su canal:
   - `visible`: lo que ve una persona (texto de la página, asunto y cuerpo del correo);
   - `hidden_text`: texto que se extrae pero no se ve (relleno blanco sin fondo, cuerpo < 4 pt,
     modo de render 3, fuera de la página; en HTML, `display:none`, blanco, tamaño 0…);
   - `metadata`: diccionario Info del PDF, anotaciones, cabeceras técnicas del correo y nombres
     de adjuntos.
   El contenido oculto y los metadatos **se conservan marcados** (`segments`), no se borran.
2. **Campos deterministas primero** (regex con los formatos de PLANT.md §6) y **solo sobre el
   texto visible limpio**: el visible sin los fragmentos sospechosos de instrucción. Un código que
   solo aparece en texto oculto, en metadatos o dentro de una instrucción inyectada no llega a los
   campos estructurados.
3. **LLM después** (`route("complaint_parse")`) solo para el texto libre, con la especificación de
   prompts de M2-T8 §4: prompt de sistema estático y versionado, segmentos visibles neutralizados en
   `<untrusted_data nonce>` (JSON), sin herramientas, salida con JSON schema. Al modelo **no** se le
   envían el texto oculto ni los metadatos (no los necesita para extraer y son el canal de ataque).
   Lo que devuelve se valida en el servidor: un lote, albarán o referencia debe cumplir su regex y
   aparecer literalmente en el texto visible limpio (si no, se descarta con un aviso); el texto
   libre pierde URLs, frases con patrones de inyección y frases con códigos que no están en el
   documento; si la salida contiene el nonce o el prompt, se descarta entera.
4. **Inyección:** el detector heurístico de `solaris.prompts.untrusted` sobre cada canal →
   `injection_suspected` + `injection_findings[{channel, location, excerpt, rule}]`. Se registra en
   el audit como `security.instruction_ignored` del evento `llm_call` (convención de M2-T6, sin
   migración); si no hay llamada al LLM, como evento `instruction_ignored` con
   `outcome: not_called` (M3-T4, migración 010; cierra S-T2-1). **Solo el detector determinista
   activa `injection_suspected`** (M3-T8): lo que declara el LLM en `ignored_instructions` sin
   corroboración queda como aviso `model_flagged_text` (severidad `review`) y en el audit.
5. **ERP** vía `mcp_obo` (on-behalf-of del Principal; nunca SQL directo): `search_complaints`,
   `get_lot` y `get_shipments` con argumentos que solo salen de códigos ya validados por regex →
   `erp_match {ok, checked, mismatches[], queries[]}`.
"""

from __future__ import annotations

import asyncio
import contextlib
import email
import hashlib
import io
import json
import logging
import math
import re
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from email import policy
from html.parser import HTMLParser
from pathlib import PurePosixPath, PureWindowsPath
from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel, Field

from solaris.llm import LLMError, route
from solaris.prompts import SystemPrompt, load_prompt
from solaris.prompts.untrusted import (
    build_envelope,
    detect_injection,
    first_match_excerpt,
    make_source,
    neutralize,
    new_nonce,
    strip_invisible,
)
from solaris.rag.answer import _DeferredAudit, leaks_prompt, strip_urls
from solaris.rag.lang import guess_lang
from solaris.settings import Settings, get_settings

if TYPE_CHECKING:
    from solaris.auth.core import Principal

logger = logging.getLogger("solaris.complaint")

TASK = "complaint_parse"
PROMPT_VERSION = "complaint_parse.v1"
MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_PDF_PAGES = 30
MAX_TEXT_CHARS = 100_000  # texto total extraído (todas las páginas y canales)
MAX_ATTACHMENTS = 20
MAX_HEADERS = 40
MAX_SEGMENT_CHARS = 1400  # por segmento enviado al LLM (≤ MAX_SOURCE_CHARS del sobre)
MAX_OUTPUT_TOKENS = 900
MAX_LOTS_TO_CHECK = 5
EXTENSIONS = {".pdf": "pdf", ".eml": "eml"}

Channel = Literal["visible", "hidden_text", "metadata"]


class ComplaintFileError(ValueError):
    """Fichero no admitido (tipo, tamaño, cifrado o ilegible). `kind` = unsupported | too_large |
    invalid. El mensaje es genérico: nunca repite contenido del fichero."""

    def __init__(self, kind: str, message: str) -> None:
        super().__init__(message)
        self.kind = kind


# --- formatos de código (PLANT.md §6) ------------------------------------------------------------

COMPLAINT_ID_RE = re.compile(r"(?<![\w-])(C-[A-Z]{4})-(\d{4})-(\d{4})(?![\w-])")
LOT_RE = re.compile(r"(?<![\w-])L\d{5}-[A-Z]{2}\d{4}-\d{2}(?![\w-])")
DELIVERY_NOTE_RE = re.compile(r"(?<![\w-])AL-\d{2}-\d{5}(?![\w-])")
PART_REF_RE = re.compile(r"(?<![\w-])[A-Z]{2}-\d{4}(?![\w-])")
DRAWING_RE = re.compile(r"(?<![\w-])([A-Z]{2,4}-\d{4,6})(?:\s+rev\.?\s*([A-Z0-9]{1,3}))?(?![\w-])")
EMAIL_RE = re.compile(
    r"(?<![\w.+-])[A-Za-z0-9._%+-]{1,64}@[A-Za-z0-9-]{1,63}(?:\.[A-Za-z0-9-]{1,63})+")
PHONE_RE = re.compile(r"\+\d{2}(?:[ .]?\d){7,12}")
_DATE_RE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b|\b(\d{1,2})[/.](\d{1,2})[/.](\d{4})\b")
_QTY_RE = re.compile(
    r"(?i)\b(?:quantity|qty|cantidad)\s+(?:NOK|non[- ]?conforming|defectuosas?|rechazadas?)\b"
    r"[^\d\n]{0,40}\n?[^\d]{0,40}?(\d{1,3}(?:[.,  ]\d{3})+|\d+)"
)
_ISSUED_LABEL_RE = re.compile(
    r"(?i)\b(?:date\s+issued|issue\s+date|fecha\s+de\s+emisi[oó]n|complaint\s+date|date)\s*:?")
_PART_LABEL_RE = re.compile(
    r"(?i)\b(?:supplier\s+part(?:\s+no\.?)?|referencia\s+del\s+proveedor|part\s+no\.?)")
_ID_LABEL_RE = re.compile(r"(?i)\b(?:complaint\s+no\.?|n[ºo°]\.?\s+de\s+reclamaci[oó]n)")
_DRAWING_LABEL_RE = re.compile(r"(?i)\b(?:drawing(?:\s+no\.?)?|plano|dibujo)\b")
_CONTAIN_RE = re.compile(r"(?i)\b(?:containment|contenci[oó]n)\b")
_REPORT8D_RE = re.compile(r"(?i)\b8D\s+(?:report|informe)\b|\b(?:informe|report)\s+8D\b")
_WITHIN_H_RE = re.compile(r"(?i)\b(\d{1,3})\s*(?:h|hours?|horas?)\b")
_WITHIN_D_RE = re.compile(
    r"(?i)\b(\d{1,3})\s*(working\s+days|business\s+days|d[ií]as\s+laborables|d[ií]as\s+h[aá]biles"
    r"|days|d[ií]as)\b")
_FORM_8D_RE = re.compile(r"(?i)\bform\s+([A-Z]{2,6}-[A-Z]{2,4}-8D(?:\s+rev\.\s*\d{1,2})?)")
# Token con forma de código (letras, guiones y al menos un dígito): en el texto libre del LLM
# solo se admite si aparece en el documento.
_CODE_TOKEN_RE = re.compile(r"(?<![\w-])[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+(?![\w-])")
_NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)*")


# --- modelos de salida ----------------------------------------------------------------------------


class InjectionFinding(BaseModel):
    channel: Channel
    location: dict[str, Any]
    excerpt: str
    rule: str


class Deadline(BaseModel):
    text: str | None = None  # p. ej. "24 h", "10 working days"
    value: int | None = None
    unit: Literal["hours", "working_days", "days"] | None = None
    due_date: date | None = None


class RequestedDeadlines(BaseModel):
    containment: Deadline | None = None
    report_8d: Deadline | None = None


class Contact(BaseModel):
    name: str | None = None
    role: str | None = None
    email: str | None = None
    phone: str | None = None


class Attachment(BaseModel):
    filename: str
    content_type: str
    size: int
    sha256: str


class SourceInfo(BaseModel):
    filename: str
    format: Literal["pdf", "eml"]
    size: int
    sha256: str
    pages: int | None = None


class Segment(BaseModel):
    """Texto extraído y marcado. `text` ya neutralizado (se muestra o se cita, nunca se ejecuta)."""

    id: str
    channel: Channel
    location: dict[str, Any]
    suspicious: bool
    reasons: list[str] = Field(default_factory=list)
    text: str


class ErpMismatch(BaseModel):
    field: str
    parsed: Any = None
    erp: Any = None


class ErpQuery(BaseModel):
    tool: str
    arguments: dict[str, Any]
    ok: bool


class ErpMatch(BaseModel):
    ok: bool = False
    checked: bool = False
    mismatches: list[ErpMismatch] = Field(default_factory=list)
    queries: list[ErpQuery] = Field(default_factory=list)
    error: str | None = None


class ComplaintParsed(BaseModel):
    complaint_id: str | None = None
    customer_code: str | None = None
    part_ref: str | None = None
    drawing_no: str | None = None
    lot_codes: list[str] = Field(default_factory=list)
    delivery_notes: list[str] = Field(default_factory=list)
    qty_affected: int | None = None
    defect_description: str | None = None
    evidence: list[str] = Field(default_factory=list)
    requested_deadlines: RequestedDeadlines = Field(default_factory=RequestedDeadlines)
    issued_date: date | None = None
    language: Literal["ES", "EN"] | None = None
    contact: Contact = Field(default_factory=Contact)
    template_ref: str | None = None
    attachments: list[Attachment] = Field(default_factory=list)
    source: SourceInfo
    injection_suspected: bool = False
    injection_findings: list[InjectionFinding] = Field(default_factory=list)
    erp_match: ErpMatch = Field(default_factory=ErpMatch)
    field_sources: dict[str, str] = Field(default_factory=dict)  # regex | llm | llm_verified
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    segments: list[Segment] = Field(default_factory=list)
    model: str | None = None
    ai_generated: bool = True


# Campos estructurados (lo que el 8D usa como hechos). La eval comprueba que ahí no aparece nada
# inyectado; `segments`, `injection_findings` y `warnings` son las zonas donde SÍ puede aparecer
# (marcado) el contenido sospechoso.
STRUCTURED_FIELDS = (
    "complaint_id", "customer_code", "part_ref", "drawing_no", "lot_codes", "delivery_notes",
    "qty_affected", "defect_description", "evidence", "requested_deadlines", "issued_date",
    "language", "contact", "template_ref", "erp_match",
)


# --- extracción -----------------------------------------------------------------------------------


@dataclass
class RawSegment:
    channel: Channel
    location: dict[str, Any]
    text: str
    reasons: list[str] = field(default_factory=list)


@dataclass
class Extracted:
    format: Literal["pdf", "eml"]
    segments: list[RawSegment]
    pages: int | None = None
    attachments: list[Attachment] = field(default_factory=list)
    email_from: str | None = None
    email_date: date | None = None


def _mul(a: list[float], b: list[float]) -> list[float]:
    return [a[0] * b[0] + a[1] * b[2], a[0] * b[1] + a[1] * b[3],
            a[2] * b[0] + a[3] * b[2], a[2] * b[1] + a[3] * b[3],
            a[4] * b[0] + a[5] * b[2] + b[4], a[4] * b[1] + a[5] * b[3] + b[5]]


def _is_white(rgb: tuple[float, ...]) -> bool:
    return all(c >= 0.95 for c in rgb)


def _floats(args: list[Any]) -> list[float]:
    out = []
    for a in args:
        try:
            out.append(float(a))
        except (TypeError, ValueError):
            out.append(0.0)
    return out


class _PdfPageScanner:
    """Estado gráfico mínimo para clasificar el texto de una página en visible u oculto.

    pypdf llama a `before()` antes de cada operador y a `text()` al volcar cada trozo de texto.
    Se sigue el color de relleno (rg/g/k, pila q/Q), el modo de render (Tr) y los rectángulos
    rellenos (re + f) para saber si un texto blanco va sobre un fondo de color (visible, p. ej. la
    cabecera de un formulario) o sobre el papel (oculto).
    Limitaciones (anotadas para security): no se evalúan imágenes de fondo, recortes (W), capas
    opcionales (OCG), espacios de color con patrones ni el solapamiento con otro texto.
    """

    TINY_PT = 4.0

    def __init__(self, mediabox: tuple[float, float, float, float]) -> None:
        self.fill: tuple[float, ...] = (0.0, 0.0, 0.0)
        self.tr = 0
        self.stack: list[tuple[tuple[float, ...], int]] = []
        self.path: list[tuple[float, float, float, float, list[float]]] = []
        self.rects: list[tuple[float, float, float, float, tuple[float, ...]]] = []
        self.chunks: list[tuple[str, list[str]]] = []
        self.box = mediabox

    def before(self, op: bytes, args: list[Any], cm: list[float], tm: list[float]) -> None:
        if op == b"q":
            self.stack.append((self.fill, self.tr))
        elif op == b"Q":
            if self.stack:
                self.fill, self.tr = self.stack.pop()
        elif op in (b"rg", b"sc", b"scn") and len(args) == 3:
            self.fill = tuple(_floats(args))
        elif op in (b"g", b"sc", b"scn") and len(args) == 1:
            self.fill = (_floats(args)[0],) * 3
        elif op in (b"k", b"sc", b"scn") and len(args) == 4:
            c, m, y, k = _floats(args)
            self.fill = ((1 - c) * (1 - k), (1 - m) * (1 - k), (1 - y) * (1 - k))
        elif op == b"Tr" and args:
            self.tr = int(_floats(args)[0])
        elif op == b"re" and len(args) == 4:
            x, y, w, h = _floats(args)
            self.path.append((x, y, w, h, list(cm)))
        elif op in (b"f", b"F", b"f*", b"B", b"B*", b"b", b"b*"):
            for x, y, w, h, m in self.path:
                pts = [(px * m[0] + py * m[2] + m[4], px * m[1] + py * m[3] + m[5])
                       for px in (x, x + w) for py in (y, y + h)]
                xs, ys = [p[0] for p in pts], [p[1] for p in pts]
                self.rects.append((min(xs), min(ys), max(xs), max(ys), self.fill))
            self.path.clear()
        elif op in (b"n", b"S", b"s"):
            self.path.clear()

    def text(self, text: str, cm: list[float], tm: list[float], _font: Any, size: float) -> None:
        if not text:
            return
        if not text.strip():
            self.chunks.append((text, []))
            return
        m = _mul(list(tm), list(cm))
        x, y = m[4], m[5]
        scale = math.hypot(m[2], m[3]) or 1.0
        eff = (size or 0.0) * scale
        reasons: list[str] = []
        if self.tr in (3, 7):
            reasons.append("render_invisible")
        if 0 < eff < self.TINY_PT:
            reasons.append("tiny_font")
        if _is_white(self.fill):
            on_color = any(r[0] - 1 <= x <= r[2] + 1 and r[1] - 1 <= y <= r[3] + 1
                           and not _is_white(r[4]) for r in self.rects)
            if not on_color:
                reasons.append("white_fill")
        x0, y0, x1, y1 = self.box
        if not (x0 - 5 <= x <= x1 + 5 and y0 - 5 <= y <= y1 + 5):
            reasons.append("off_page")
        self.chunks.append((text, reasons))


_PDF_INFO_FIELDS = {"/Title": "title", "/Subject": "subject", "/Author": "author",
                    "/Keywords": "keywords", "/Creator": "creator", "/Producer": "producer"}


def extract_pdf(data: bytes) -> Extracted:
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError

    try:
        reader = PdfReader(io.BytesIO(data), strict=False)
        if reader.is_encrypted:
            raise ComplaintFileError("invalid", "PDF cifrado: no se admite")
        n_pages = len(reader.pages)
    except ComplaintFileError:
        raise
    except (PdfReadError, ValueError, KeyError, TypeError, OSError) as exc:
        raise ComplaintFileError("invalid", "PDF ilegible") from exc
    if n_pages == 0 or n_pages > MAX_PDF_PAGES:
        raise ComplaintFileError("invalid", f"El PDF debe tener entre 1 y {MAX_PDF_PAGES} páginas")

    segs: list[RawSegment] = []
    total = 0
    for pn, page in enumerate(reader.pages, 1):
        try:
            mb = page.mediabox
            scan = _PdfPageScanner((float(mb.left), float(mb.bottom), float(mb.right),
                                    float(mb.top)))
            page.extract_text(visitor_operand_before=scan.before, visitor_text=scan.text)
        except Exception as exc:  # pypdf lanza tipos variados ante contenido corrupto
            raise ComplaintFileError("invalid", "PDF ilegible") from exc
        visible = "".join(t for t, r in scan.chunks if not r)
        hidden = [(t, r) for t, r in scan.chunks if r]
        hidden_text = "".join(t if t.endswith("\n") else t + "\n" for t, _ in hidden)
        reasons = sorted({x for _, r in hidden for x in r})
        # Capa de texto de un escaneo (OCR): toda la página en modo de render 3 → es el texto
        # "visible" de esa página, no un canal oculto.
        if not visible.strip() and hidden and reasons == ["render_invisible"]:
            visible, hidden_text, reasons = hidden_text, "", []
            segs.append(RawSegment("visible", {"page": pn, "ocr_layer": True}, visible))
        else:
            segs.append(RawSegment("visible", {"page": pn}, visible))
            if hidden_text.strip():
                segs.append(RawSegment("hidden_text", {"page": pn}, hidden_text, reasons))
        total += len(visible) + len(hidden_text)
        if total > MAX_TEXT_CHARS:
            raise ComplaintFileError("too_large", "Demasiado texto en el PDF")
        # Anotaciones (comentarios, notas): canal de metadatos.
        try:
            annots = page.get("/Annots") or []
            for i, a in enumerate(list(annots)[:50]):
                obj = a.get_object()
                contents = obj.get("/Contents") if hasattr(obj, "get") else None
                if contents:
                    segs.append(RawSegment("metadata", {"field": f"pdf_annotation.p{pn}.{i}"},
                                           str(contents)[:4000]))
        except Exception:  # anotación corrupta: no bloquea el parseo
            logger.debug("anotación ilegible en la página %s", pn)
    try:
        info = reader.metadata or {}
    except Exception:
        info = {}
    for key, value in dict(info).items():
        if not isinstance(value, str) or key in ("/CreationDate", "/ModDate", "/Trapped"):
            continue
        name = _PDF_INFO_FIELDS.get(key, re.sub(r"[^a-z0-9_]", "", str(key).lower())[:30])
        segs.append(RawSegment("metadata", {"field": f"pdf_metadata.{name}"}, value[:4000]))
    return Extracted("pdf", segs, pages=n_pages)


class _HtmlText(HTMLParser):
    """Texto de una parte HTML separando lo oculto por estilo (canal `hidden_text`)."""

    _VOID = frozenset({"br", "hr", "img", "meta", "link", "input", "col", "area", "base", "wbr",
                       "source", "track", "embed", "param"})
    _HIDE_RE = re.compile(
        r"display\s*:\s*none|visibility\s*:\s*hidden|opacity\s*:\s*0(?:\.0*)?\s*(?:;|$)|"
        r"font-size\s*:\s*[0-2](?:\.\d+)?\s*(?:px|pt)?\s*(?:;|$)|"
        r"(?<![-\w])color\s*:\s*(?:#fff(?:fff)?\b|white\b|rgb\(\s*255\s*,\s*255\s*,\s*255\s*\))",
        re.I)

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, bool]] = []
        self.visible: list[str] = []
        self.hidden: list[str] = []

    def _hidden(self) -> bool:
        return any(h for _, h in self.stack)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k.lower(): (v or "") for k, v in attrs}
        hide = tag in ("script", "style", "head", "title") or "hidden" in a or \
            bool(self._HIDE_RE.search(a.get("style", "")))
        if tag in ("br", "p", "div", "tr", "li"):
            (self.hidden if self._hidden() else self.visible).append("\n")
        if tag not in self._VOID:
            self.stack.append((tag, hide))

    def handle_endtag(self, tag: str) -> None:
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data: str) -> None:
        if self.stack and self.stack[-1][0] in ("script", "style"):
            return
        (self.hidden if self._hidden() else self.visible).append(data)


def _decode_part(part: Any) -> str:
    try:
        content = part.get_content()
    except (LookupError, UnicodeError, ValueError, KeyError, AssertionError):
        raw = part.get_payload(decode=True) or b""
        content = raw.decode("utf-8", errors="replace")
    return content if isinstance(content, str) else ""


_VISIBLE_HEADERS = ("subject", "from", "date")


def extract_eml(data: bytes) -> Extracted:
    if b"\x00" in data[:65536]:
        raise ComplaintFileError("unsupported", "El fichero no es un correo (.eml) de texto")
    try:
        msg = email.message_from_bytes(data, policy=policy.default)
        headers = list(msg.items())
    except Exception as exc:
        raise ComplaintFileError("invalid", "Correo ilegible") from exc
    names = {k.lower() for k, _ in headers}
    if not ({"from", "subject"} <= names or ({"from", "date"} <= names)):
        raise ComplaintFileError("unsupported", "El fichero no es un correo (.eml)")

    segs: list[RawSegment] = []
    email_from, email_date = None, None
    for k, v in headers[:MAX_HEADERS]:
        key = k.lower()
        value = str(v)[:1000]
        if key in _VISIBLE_HEADERS:
            segs.append(RawSegment("visible", {"field": f"email.{key}"}, value))
            if key == "from":
                email_from = value
            if key == "date":
                with contextlib.suppress(TypeError, ValueError, AttributeError):
                    email_date = v.datetime.date()  # type: ignore[union-attr]
        elif key not in ("to", "cc", "mime-version", "content-type",
                         "content-transfer-encoding"):
            segs.append(RawSegment("metadata", {"field": f"email.header.{key[:40]}"}, value))

    plain: list[str] = []
    html_visible: list[str] = []
    attachments: list[Attachment] = []
    total = 0
    for part in msg.walk():
        if part.is_multipart():
            continue
        ctype = part.get_content_type()
        disp = part.get_content_disposition()
        fname = part.get_filename()
        if disp != "attachment" and fname is None and ctype in ("text/plain", "text/html"):
            text = _decode_part(part)
            total += len(text)
            if total > MAX_TEXT_CHARS:
                raise ComplaintFileError("too_large", "Demasiado texto en el correo")
            if ctype == "text/plain":
                plain.append(text)
            else:
                h = _HtmlText()
                with contextlib.suppress(Exception):
                    h.feed(text)
                    h.close()
                html_visible.append("".join(h.visible))
                hidden = "".join(h.hidden)
                if hidden.strip():
                    segs.append(RawSegment("hidden_text", {"field": "email.html"}, hidden[:8000],
                                           ["html_hidden_style"]))
            continue
        if len(attachments) >= MAX_ATTACHMENTS:
            continue
        payload = part.get_payload(decode=True) or b""
        name = _safe_filename(fname or "(sin nombre)")
        attachments.append(Attachment(filename=name, content_type=ctype[:100], size=len(payload),
                                      sha256=hashlib.sha256(payload).hexdigest()))
        segs.append(RawSegment("metadata", {"field": f"email.attachment.{len(attachments)}"},
                               f"{fname or ''} ({ctype})"))
    body = "\n".join(plain) if plain else "\n".join(html_visible)
    segs.append(RawSegment("visible", {"field": "email.body"}, body))
    return Extracted("eml", segs, attachments=attachments, email_from=email_from,
                     email_date=email_date)


def _safe_filename(name: str) -> str:
    base = PureWindowsPath(PurePosixPath(str(name)).name).name
    return neutralize(base, 120).replace("\n", " ") or "(sin nombre)"


# --- fragmentos sospechosos en el texto visible ---------------------------------------------------


def _paragraphs(text: str) -> list[tuple[int, int]]:
    """Párrafos por líneas: una línea larga (≥ 60) continúa en la siguiente (texto justificado);
    las cortas (celdas de tabla, títulos) y las vacías cierran el párrafo."""
    out: list[tuple[int, int]] = []
    start = None
    prev_long = False
    for m in re.finditer(r"[^\n]*\n?", text):
        if m.start() == m.end():
            break
        line = m.group().rstrip("\n")
        if not line.strip():
            if start is not None:
                out.append((start, m.start()))
            start, prev_long = None, False
            continue
        if start is None or not prev_long:
            if start is not None:
                out.append((start, m.start()))
            start = m.start()
        prev_long = len(line.strip()) >= 60
    if start is not None:
        out.append((start, len(text)))
    return out


_SENT_RE = re.compile(r".+?(?:[.!?](?=\s|$)|$)", re.S)


def suspicious_spans(text: str) -> list[tuple[int, int, list[str]]]:
    """Tramos del texto con instrucciones dirigidas al asistente: las frases donde el detector
    coincide y la frase siguiente del mismo párrafo (suele ser el "código de confirmación")."""
    spans: list[tuple[int, int, list[str]]] = []
    for p0, p1 in _paragraphs(text):
        para = text[p0:p1]
        sents = [(m.start() + p0, m.end() + p0) for m in _SENT_RE.finditer(para)
                 if m.group().strip()]
        flagged: dict[int, list[str]] = {}
        for i, (s0, s1) in enumerate(sents):
            pats = detect_injection(text[s0:s1])
            if pats:
                flagged.setdefault(i, [])
                flagged[i] += [p for p in pats if p not in flagged[i]]
                if i + 1 < len(sents):
                    flagged.setdefault(i + 1, [])
        for i in sorted(flagged):
            s0, s1 = sents[i]
            if spans and spans[-1][1] >= s0 - 2 and spans[-1][0] >= p0:
                a, _, pats = spans[-1]
                spans[-1] = (a, s1, pats + [p for p in flagged[i] if p not in pats])
            else:
                spans.append((s0, s1, list(flagged[i])))
    return spans


def _cut(text: str, spans: list[tuple[int, int, list[str]]]) -> list[tuple[str, bool]]:
    """Trozos (texto, sospechoso) en orden; los limpios se parten en ≤ MAX_SEGMENT_CHARS."""
    out: list[tuple[str, bool]] = []
    pos = 0
    for s0, s1, _ in spans:
        if s0 > pos:
            out.append((text[pos:s0], False))
        out.append((text[s0:s1], True))
        pos = s1
    if pos < len(text):
        out.append((text[pos:], False))
    pieces: list[tuple[str, bool]] = []
    for chunk, sus in out:
        if not chunk.strip():
            continue
        while len(chunk) > MAX_SEGMENT_CHARS:
            cut = chunk.rfind("\n", 0, MAX_SEGMENT_CHARS)
            cut = cut if cut > MAX_SEGMENT_CHARS // 2 else MAX_SEGMENT_CHARS
            pieces.append((chunk[:cut], sus))
            chunk = chunk[cut:]
        if chunk.strip():
            pieces.append((chunk, sus))
    return pieces


# --- extracción determinista ----------------------------------------------------------------------


def _parse_date(m: re.Match[str]) -> date | None:
    try:
        if m.group(1):
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        return date(int(m.group(6)), int(m.group(5)), int(m.group(4)))  # dd/mm/aaaa (ES/EU)
    except ValueError:
        return None


def _uniq(seq: list[str]) -> list[str]:
    return list(dict.fromkeys(seq))


def _labelled(text: str, label: re.Pattern[str], value: re.Pattern[str],
              window: int = 80) -> re.Match[str] | None:
    for lm in label.finditer(text):
        m = value.search(text, lm.end(), min(len(text), lm.end() + window))
        if m:
            return m
    return None


def _most_common(values: list[str]) -> str | None:
    if not values:
        return None
    counts: dict[str, int] = {}
    for v in values:
        counts[v] = counts.get(v, 0) + 1
    return max(counts, key=lambda v: (counts[v], -values.index(v)))


def _deadline(text: str, anchor: re.Pattern[str], within_re: re.Pattern[str],
              unit_of: Callable[[str], str]) -> Deadline | None:
    for am in anchor.finditer(text):
        win = text[am.start(): am.start() + 160]
        wm = within_re.search(win)
        dm = _DATE_RE.search(win)
        if wm or dm:
            return Deadline(
                text=" ".join(wm.group(0).split()) if wm else None,
                value=int(wm.group(1)) if wm else None,
                unit=unit_of(wm.group(2) if wm and wm.lastindex and wm.lastindex >= 2 else "h")
                if wm else None,
                due_date=_parse_date(dm) if dm else None)
    return None


def _day_unit(u: str) -> str:
    u = u.lower()
    return "working_days" if any(w in u for w in ("working", "business", "laborab", "hábil",
                                                  "habil")) else "days"


def deterministic_fields(clean: str) -> dict[str, Any]:
    """Campos por regex sobre el texto visible limpio (sin tramos sospechosos)."""
    out: dict[str, Any] = {}
    ids = [m.group(0) for m in COMPLAINT_ID_RE.finditer(clean)]
    lab = _labelled(clean, _ID_LABEL_RE, COMPLAINT_ID_RE, 60)
    out["complaint_id"] = lab.group(0) if lab else _most_common(ids)
    if out["complaint_id"]:
        out["customer_code"] = COMPLAINT_ID_RE.fullmatch(out["complaint_id"]).group(1)  # type: ignore[union-attr]
    lots = _uniq([m.group(0) for m in LOT_RE.finditer(clean)])
    out["lot_codes"] = lots
    out["delivery_notes"] = _uniq([m.group(0) for m in DELIVERY_NOTE_RE.finditer(clean)])
    lab = _labelled(clean, _PART_LABEL_RE, PART_REF_RE, 60)
    parts = [m.group(0) for m in PART_REF_RE.finditer(clean)]
    out["part_ref"] = lab.group(0) if lab else _most_common(parts)
    dm = _labelled(clean, _DRAWING_LABEL_RE, DRAWING_RE, 40)
    out["drawing_no"] = dm.group(1) if dm else None
    out["drawing_rev"] = dm.group(2) if dm and dm.group(2) else None
    qm = _QTY_RE.search(clean)
    out["qty_affected"] = int(re.sub(r"[.,  ]", "", qm.group(1))) if qm else None
    im = _labelled(clean, _ISSUED_LABEL_RE, _DATE_RE, 40)
    out["issued_date"] = _parse_date(im) if im else None
    out["requested_deadlines"] = RequestedDeadlines(
        containment=_deadline(clean, _CONTAIN_RE, _WITHIN_H_RE, lambda _u: "hours"),
        report_8d=_deadline(clean, _REPORT8D_RE, _WITHIN_D_RE, _day_unit),
    )
    fm = _FORM_8D_RE.search(clean)
    out["template_ref"] = " ".join(fm.group(1).split()) if fm else None
    emails = [m.group(0) for m in EMAIL_RE.finditer(clean)]
    out["email"] = emails[-1] if emails else None  # el contacto va al final del formulario
    phones = [m.group(0) for m in PHONE_RE.finditer(clean)]
    out["phone"] = " ".join(phones[-1].split()) if phones else None
    return out


# --- validación de la salida del LLM --------------------------------------------------------------

_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.I)
LLM_FIELDS = ("defect_description", "evidence", "contact_name", "contact_role", "template_ref",
              "part_ref", "drawing_no", "lot_codes", "delivery_notes", "ignored_instructions")


def response_format() -> dict[str, Any]:
    s = {"type": "string"}
    arr = {"type": "array", "items": {"type": "string"}}
    props: dict[str, Any] = {
        "defect_description": s, "evidence": arr, "contact_name": s, "contact_role": s,
        "template_ref": s, "part_ref": s, "drawing_no": s, "lot_codes": arr,
        "delivery_notes": arr,
        "ignored_instructions": {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": ["source", "summary"],
            "properties": {"source": s, "summary": s}}},
    }
    return {"type": "json_schema",
            "json_schema": {"name": TASK, "strict": True,
                            "schema": {"type": "object", "additionalProperties": False,
                                       "required": list(props), "properties": props}}}


def parse_llm_json(content: str) -> dict[str, Any] | None:
    text = _FENCE_RE.sub("", content or "").strip()
    try:
        data = json.loads(text)
    except ValueError:
        a, b = text.find("{"), text.rfind("}")
        if a < 0 or b <= a:
            return None
        try:
            data = json.loads(text[a:b + 1])
        except ValueError:
            return None
    return data if isinstance(data, dict) else None


def _norm(s: str) -> str:
    return " ".join(strip_invisible(s).split()).casefold()


def _literal_in(value: str, norm_source: str) -> bool:
    v = _norm(value)
    return bool(v) and v in norm_source


def _num_forms(tok: str) -> set[str]:
    return {tok, tok.replace(",", "."), tok.replace(".", ","), re.sub(r"[.,]", "", tok)}


def _numbers_ok(value: str, source_numbers: set[str]) -> bool:
    return all(_num_forms(t) & source_numbers for t in _NUMBER_RE.findall(value))


@dataclass
class _Guard:
    """Contexto de validación: texto visible limpio normalizado, códigos y números presentes."""

    clean: str
    norm: str = ""
    codes: set[str] = field(default_factory=set)
    numbers: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        self.norm = _norm(self.clean)
        self.codes = set(_CODE_TOKEN_RE.findall(self.clean))
        self.numbers = set()
        for t in _NUMBER_RE.findall(self.clean):
            self.numbers |= _num_forms(t)


_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?;])\s+")


def clean_free_text(value: Any, guard: _Guard, max_chars: int, where: str,
                    warnings: list[dict[str, Any]], *, check_numbers: bool = False) -> str | None:
    """Texto libre del modelo: sin URLs, sin frases con patrones de inyección ni con códigos que no
    aparecen en el documento; con `check_numbers`, se descarta si trae cifras ausentes."""
    if not isinstance(value, str) or not value.strip():
        return None
    text, n_urls = strip_urls(strip_invisible(value))
    if n_urls:
        warnings.append({"type": "urls_removed", "field": where, "count": n_urls})
    kept = []
    for sent in _SENTENCE_SPLIT_RE.split(text):
        if not sent.strip():
            continue
        if detect_injection(sent):
            warnings.append({"type": "llm_text_dropped", "field": where, "reason": "injection"})
            continue
        bad = [c for c in _CODE_TOKEN_RE.findall(sent) if any(ch.isdigit() for ch in c)
               and c not in guard.codes]
        if bad:
            warnings.append({"type": "llm_text_dropped", "field": where,
                             "reason": "unknown_code", "codes": [neutralize(b, 40) for b in bad]})
            continue
        kept.append(sent.strip())
    out = " ".join(kept).strip()
    if not out:
        return None
    if check_numbers and not _numbers_ok(out, guard.numbers):
        warnings.append({"type": "llm_text_dropped", "field": where, "reason": "unknown_number"})
        return None
    return neutralize(out, max_chars)


def validate_codes(values: Any, pattern: re.Pattern[str], guard: _Guard, where: str,
                   warnings: list[dict[str, Any]]) -> list[str]:
    """Códigos propuestos por el LLM: formato (regex completa) + presencia literal en el texto
    visible limpio. Lo demás se descarta con un aviso (el LLM no puede inventar códigos)."""
    if isinstance(values, str):
        values = [values]
    if not isinstance(values, list):
        return []
    ok: list[str] = []
    for v in values:
        if not isinstance(v, str) or not v.strip():
            continue
        code = v.strip()
        if pattern.fullmatch(code) and re.search(
                rf"(?<![\w-]){re.escape(code)}(?![\w-])", guard.clean):
            ok.append(code)
        else:
            warnings.append({"type": "llm_code_discarded", "field": where,
                             "value": neutralize(code, 40),
                             "reason": "format" if not pattern.fullmatch(code) else "not_in_text"})
    return _uniq(ok)


# --- ERP (vía MCP, on-behalf-of) ------------------------------------------------------------------


SessionFactory = Callable[[], Any]  # () -> async context manager que da un ToolSession


def _default_session_factory() -> Any:
    from solaris.mcp_stdio import StdioToolSession

    return StdioToolSession.erp_mock(timeout_s=30.0)


def _tool_payload(res: Any) -> tuple[bool, dict[str, Any]]:
    """(ok, data) de un resultado de `tools/call` (ToolResult del cliente stdio o dict en tests)."""
    if getattr(res, "is_error", False) or (isinstance(res, dict) and res.get("isError")):
        return False, {}
    data = getattr(res, "data", res)
    if isinstance(data, dict) and isinstance(data.get("data"), dict):
        data = data["data"]
    return isinstance(data, dict), data if isinstance(data, dict) else {}


async def erp_check(parsed: ComplaintParsed, principal: Principal,
                    session_factory: SessionFactory | None = None,
                    settings: Settings | None = None) -> ErpMatch:
    """Coteja id, cliente, pieza, lotes, cantidad y albaranes con el ERP (solo lectura, como el
    usuario autenticado). Los argumentos salen solo de códigos ya validados por regex."""
    from solaris.mcp_obo import call_erp_tool

    match = ErpMatch()
    if not parsed.complaint_id and not parsed.lot_codes:
        match.error = "sin_codigos"
        return match
    factory = session_factory or _default_session_factory
    mism: list[ErpMismatch] = []

    async def call(session: Any, tool: str, args: dict[str, Any]) -> dict[str, Any] | None:
        res = await call_erp_tool(session, principal, tool, args, settings=settings)
        ok, data = _tool_payload(res)
        match.queries.append(ErpQuery(tool=tool, arguments=args, ok=ok))
        return data if ok else None

    try:
        async with factory() as session:
            if parsed.customer_code or parsed.part_ref:
                args = {k: v for k, v in (("customer_code", parsed.customer_code),
                                          ("part_ref", parsed.part_ref)) if v}
                data = await call(session, "search_complaints", args)
                rows = (data or {}).get("complaints") or []
                row = next((r for r in rows if r.get("complaint_id") == parsed.complaint_id), None)
                if data is None:
                    mism.append(ErpMismatch(field="complaint_id", parsed=parsed.complaint_id,
                                            erp="consulta_fallida"))
                elif row is None:
                    mism.append(ErpMismatch(field="complaint_id", parsed=parsed.complaint_id,
                                            erp=None))
                else:
                    for f_parsed, f_erp in (("customer_code", "customer_code"),
                                            ("part_ref", "part_ref"),
                                            ("qty_affected", "qty_affected")):
                        pv = getattr(parsed, f_parsed)
                        if pv is not None and pv != row.get(f_erp):
                            mism.append(ErpMismatch(field=f_parsed, parsed=pv, erp=row.get(f_erp)))
                    if row.get("lot_code") and row["lot_code"] not in parsed.lot_codes:
                        mism.append(ErpMismatch(field="lot_codes", parsed=parsed.lot_codes,
                                                erp=row["lot_code"]))
            shipped: set[str] = set()
            for lot in parsed.lot_codes[:MAX_LOTS_TO_CHECK]:
                data = await call(session, "get_lot", {"lot_code": lot})
                if not data or not data.get("found"):
                    mism.append(ErpMismatch(field="lot_code", parsed=lot, erp=None))
                    continue
                part = data.get("part") or {}
                if parsed.part_ref and part.get("ref") != parsed.part_ref:
                    mism.append(ErpMismatch(field="lot_code.part_ref", parsed=parsed.part_ref,
                                            erp=part.get("ref")))
                if parsed.customer_code and part.get("customer_code") != parsed.customer_code:
                    mism.append(ErpMismatch(field="lot_code.customer_code",
                                            parsed=parsed.customer_code,
                                            erp=part.get("customer_code")))
                if parsed.delivery_notes:
                    sdata = await call(session, "get_shipments", {"lot_code": lot})
                    for s in (sdata or {}).get("shipments") or []:
                        if parsed.customer_code in (None, s.get("customer_code")):
                            shipped.add(str(s.get("shipment_id")))
            missing = [d for d in parsed.delivery_notes if d not in shipped]
            if parsed.delivery_notes and parsed.lot_codes and missing:
                mism.append(ErpMismatch(field="delivery_notes", parsed=missing,
                                        erp=sorted(shipped)))
    except Exception as exc:  # MCP caído, ERP/audit no disponibles, rechazo de identidad...
        logger.warning("complaint: validación ERP no disponible (%s)", type(exc).__name__)
        match.error = "erp_unavailable"
        match.mismatches = mism
        return match
    match.checked = True
    match.mismatches = mism
    match.ok = not mism
    return match


# --- pipeline -------------------------------------------------------------------------------------


def detect_format(data: bytes, filename: str) -> Literal["pdf", "eml"]:
    """Tipo por extensión + firma (magic). Si no coinciden, se rechaza."""
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    fmt = EXTENSIONS.get(ext)
    if fmt is None:
        raise ComplaintFileError("unsupported", "Tipo de fichero no admitido (solo .pdf y .eml)")
    head = data[:1024].lstrip()
    if fmt == "pdf" and not head.startswith(b"%PDF-"):
        raise ComplaintFileError("unsupported", "El fichero .pdf no es un PDF")
    if fmt == "eml" and (head.startswith(b"%PDF-") or not re.match(rb"[\x21-\x39\x3b-\x7e]+:",
                                                                     head)):
        raise ComplaintFileError("unsupported", "El fichero .eml no es un correo")
    return fmt  # type: ignore[return-value]


def _findings(segs: list[RawSegment]) -> tuple[list[InjectionFinding],
                                               dict[int, list[tuple[int, int, list[str]]]]]:
    findings: list[InjectionFinding] = []
    spans_by_seg: dict[int, list[tuple[int, int, list[str]]]] = {}
    for i, s in enumerate(segs):
        if s.channel == "visible":
            spans = suspicious_spans(s.text)
            spans_by_seg[i] = spans
            for s0, s1, pats in spans:
                if pats:
                    findings.append(InjectionFinding(
                        channel="visible", location=s.location,
                        excerpt=first_match_excerpt(s.text[s0:s1]), rule=",".join(pats)))
        else:
            pats = detect_injection(s.text)
            if pats:
                loc = {**s.location, **({"reasons": s.reasons} if s.reasons else {})}
                findings.append(InjectionFinding(channel=s.channel, location=loc,
                                                 excerpt=first_match_excerpt(s.text),
                                                 rule=",".join(pats)))
    return findings, spans_by_seg


@dataclass
class _Prepared:
    parsed: ComplaintParsed
    guard: _Guard
    pieces: list[tuple[dict[str, Any], str, bool]]  # (locator, texto, sospechoso) visibles
    findings_audit: list[dict[str, Any]]


def prepare(file_bytes: bytes, filename: str) -> _Prepared:
    """Extracción + campos deterministas + detección (sin LLM ni ERP)."""
    if not isinstance(file_bytes, bytes | bytearray) or not file_bytes:
        raise ComplaintFileError("invalid", "Fichero vacío")
    if len(file_bytes) > MAX_FILE_BYTES:
        raise ComplaintFileError("too_large", "Fichero demasiado grande")
    data = bytes(file_bytes)
    name = _safe_filename(filename or "reclamacion")
    fmt = detect_format(data, name)
    ext = extract_pdf(data) if fmt == "pdf" else extract_eml(data)
    for s in ext.segments:
        s.text = strip_invisible(s.text)

    findings, spans_by_seg = _findings(ext.segments)
    pieces: list[tuple[dict[str, Any], str, bool]] = []
    public: list[Segment] = []
    clean_parts: list[str] = []
    for i, s in enumerate(ext.segments):
        if s.channel == "visible":
            for text, sus in _cut(s.text, spans_by_seg.get(i, [])):
                pieces.append((s.location, text, sus))
                if not sus:
                    clean_parts.append(text)
        else:
            public.append(Segment(id="", channel=s.channel, location=s.location, suspicious=bool(
                detect_injection(s.text)), reasons=s.reasons, text=neutralize(s.text, 4000)))
    for n, (loc, text, sus) in enumerate(pieces, 1):
        public.append(Segment(id=f"S{n}", channel="visible", location=loc, suspicious=sus,
                              text=neutralize(text, MAX_SEGMENT_CHARS)))
    counters = {"hidden_text": 0, "metadata": 0}
    for seg in public:
        if seg.channel != "visible":
            counters[seg.channel] += 1
            seg.id = f"{'H' if seg.channel == 'hidden_text' else 'M'}{counters[seg.channel]}"
    public.sort(key=lambda x: (x.channel != "visible", x.channel, x.id))

    clean = "\n".join(clean_parts)
    det = deterministic_fields(clean)
    guard = _Guard(clean)
    lang = guess_lang(clean) if clean.strip() else None
    contact = Contact(email=det["email"], phone=det["phone"])
    if ext.email_from:
        m = EMAIL_RE.search(ext.email_from)
        if m and not detect_injection(ext.email_from):
            contact.email = m.group(0)
    parsed = ComplaintParsed(
        complaint_id=det["complaint_id"], customer_code=det.get("customer_code"),
        part_ref=det["part_ref"], drawing_no=det["drawing_no"], lot_codes=det["lot_codes"],
        delivery_notes=det["delivery_notes"], qty_affected=det["qty_affected"],
        requested_deadlines=det["requested_deadlines"],
        issued_date=det["issued_date"] or ext.email_date,
        language=lang.upper() if lang else None,  # type: ignore[arg-type]
        contact=contact, template_ref=det["template_ref"], attachments=ext.attachments,
        source=SourceInfo(filename=name, format=fmt, size=len(data),
                          sha256=hashlib.sha256(data).hexdigest(), pages=ext.pages),
        injection_suspected=bool(findings), injection_findings=findings, segments=public,
    )
    for k in ("complaint_id", "customer_code", "part_ref", "drawing_no", "lot_codes",
              "delivery_notes", "qty_affected", "issued_date", "template_ref"):
        v = getattr(parsed, k)
        if v not in (None, []):
            parsed.field_sources[k] = "regex"
    if det["drawing_rev"]:
        parsed.field_sources["drawing_rev"] = det["drawing_rev"]
    if any(s.channel == "hidden_text" for s in ext.segments):
        parsed.warnings.append({"type": "hidden_text_present",
                                "message": "El documento contiene texto que no se ve al abrirlo; "
                                           "se muestra marcado y no se usa para los campos."})
    if findings:
        parsed.warnings.append({
            "type": "instruction_ignored",
            "channels": sorted({f.channel for f in findings}),
            "message": "El documento contiene instrucciones dirigidas al asistente que se han "
                       "ignorado."})
    findings_audit = [
        {"channel": f.channel, "location": f.location, "detector": "heuristic",
         "pattern": f.rule, "excerpt_sha256": hashlib.sha256(f.excerpt.encode()).hexdigest(),
         "excerpt": f.excerpt}
        for f in findings
    ]
    return _Prepared(parsed, guard, pieces, findings_audit)


def model_review_note(prep: _Prepared, declared: list[str],
                      by_id: dict[str, bool]) -> dict[str, Any] | None:
    """Señal del LLM (`ignored_instructions`) → nota de revisión, **nunca** `injection_suspected`.

    M3-T8 (S-T4-11): el aviso rojo solo lo activa el detector determinista (`_findings`, sobre
    todos los canales). El modelo marcaba de forma intermitente requisitos normales del OEM
    ("D1–D4 must be uploaded to the supplier portal…") como instrucciones. Un segmento que el
    detector también marca ya está en `injection_findings` (corroborado); aquí solo quedan los que
    únicamente declara el modelo, como aviso de menor severidad con ubicación y extracto del
    documento (neutralizado). El `summary` del modelo no se muestra: es salida del LLM sobre texto
    no confiable. El audit conserva `model_declared` y `model_only`.
    """
    only = [sid for sid in declared if not by_id.get(sid)]  # by_id: flags.suspicious del detector
    if not only:
        return None
    items = []
    for sid in only:
        loc, text, _ = prep.pieces[int(sid[1:]) - 1]
        items.append({"source": sid, "channel": "visible", "location": loc,
                      "excerpt": neutralize(" ".join(text.split()), 120)})
    return {"type": "model_flagged_text", "severity": "review", "sources": only,
            "items": items,
            "message": "El modelo señaló un fragmento como posible instrucción, pero el detector "
                       "no lo confirma. Revísalo; no se ha ejecutado nada."}


def _apply_llm(prep: _Prepared, data: dict[str, Any], by_id: dict[str, bool]) -> list[str]:
    """Fusiona la salida validada del LLM. Devuelve los ids declarados como instrucción ignorada."""
    p, g, w = prep.parsed, prep.guard, prep.parsed.warnings
    desc = clean_free_text(data.get("defect_description"), g, 500, "defect_description", w)
    if desc:
        p.defect_description = desc
        p.field_sources["defect_description"] = "llm"
        if not _numbers_ok(desc, g.numbers):
            w.append({"type": "unverified_numbers", "field": "defect_description"})
    ev = data.get("evidence") if isinstance(data.get("evidence"), list) else []
    for i, item in enumerate(ev[:6]):
        e = clean_free_text(item, g, 220, f"evidence[{i}]", w, check_numbers=True)
        if e:
            p.evidence.append(e)
    if p.evidence:
        p.field_sources["evidence"] = "llm"
    for key, attr in (("contact_name", "name"), ("contact_role", "role")):
        v = data.get(key)
        if isinstance(v, str) and v.strip():
            if _literal_in(v, g.norm) and not detect_injection(v):
                setattr(p.contact, attr, neutralize(" ".join(v.split()), 120))
                p.field_sources[f"contact.{attr}"] = "llm_verified"
            else:
                w.append({"type": "llm_text_dropped", "field": key, "reason": "not_in_text"})
    tr = data.get("template_ref")
    if p.template_ref is None and isinstance(tr, str) and tr.strip():
        if _literal_in(tr, g.norm) and not detect_injection(tr):
            p.template_ref = neutralize(" ".join(tr.split()), 200)
            p.field_sources["template_ref"] = "llm_verified"
        else:
            w.append({"type": "llm_text_dropped", "field": "template_ref", "reason": "not_in_text"})
    for key, pat in (("lot_codes", LOT_RE), ("delivery_notes", DELIVERY_NOTE_RE)):
        got = validate_codes(data.get(key), pat, g, key, w)
        new = [c for c in got if c not in getattr(p, key)]
        if new:
            setattr(p, key, getattr(p, key) + new)
            p.field_sources[key] = "regex+llm_verified" if key in p.field_sources \
                else "llm_verified"
    for key, pat in (("part_ref", PART_REF_RE), ("drawing_no", re.compile(r"[A-Z]{2,4}-\d{4,6}"))):
        got = validate_codes(data.get(key), pat, g, key, w)
        if got and getattr(p, key) is None:
            setattr(p, key, got[0])
            p.field_sources[key] = "llm_verified"
        elif got and got[0] != getattr(p, key):
            w.append({"type": "llm_disagrees", "field": key, "value": got[0]})
    declared = []
    for it in data.get("ignored_instructions") or []:
        if isinstance(it, dict) and isinstance(it.get("source"), str):
            sid = it["source"].strip().strip("[]").upper()[:8]
            if sid in by_id:
                declared.append(sid)
    return _uniq(declared)


async def parse_async(
    file_bytes: bytes,
    filename: str,
    principal: Principal,
    *,
    settings: Settings | None = None,
    route_fn: Callable[..., Any] = route,
    audit: Callable[..., None] | None = None,
    session_factory: SessionFactory | None = None,
    check_erp: bool = True,
    use_llm: bool = True,
    nonce: str | None = None,
) -> ComplaintParsed:
    """Pipeline completo para el usuario autenticado `principal` (on-behalf-of).

    `route_fn`, `audit` y `session_factory` se sustituyen en tests. Un fallo del proveedor LLM o
    del ERP no rompe el parseo: los campos deterministas se devuelven con un aviso.
    `ComplaintFileError` (tipo, tamaño o fichero ilegible) sí se propaga (→ 413/415/422).
    """
    s = settings or get_settings()
    t0 = time.perf_counter()
    prep = prepare(file_bytes, filename)
    p = prep.parsed
    prompt: SystemPrompt = load_prompt(PROMPT_VERSION)
    deferred = _DeferredAudit()
    nonce = nonce or new_nonce()
    base_security: dict[str, Any] = {
        "prompt_version": prompt.version, "prompt_sha256": prompt.sha256,
        "nonce_sha256": hashlib.sha256(nonce.encode()).hexdigest()[:16],
        "instruction_ignored": prep.findings_audit,
        "injection_suspected": p.injection_suspected,
    }
    audit_meta = {"complaint": {"sha256": p.source.sha256, "format": p.source.format,
                                "size": p.source.size, "pages": p.source.pages,
                                "segments_sent": 0},
                  "security": dict(base_security)}
    post: dict[str, Any] = {}
    llm_ran = False
    if use_llm and prep.pieces:
        sources = []
        for n, (loc, text, sus) in enumerate(prep.pieces, 1):
            src = make_source(f"S{n}", doc_id=p.source.filename, version="upload",
                              locator=loc, title="", text=text, max_chars=MAX_SEGMENT_CHARS)
            src.flags["suspicious"] = src.flags["suspicious"] or sus
            sources.append(src)
        user_msg, sent = build_envelope("", sources, nonce)
        by_id = {x.id: x.flags["suspicious"] for x in sent}
        audit_meta["complaint"]["segments_sent"] = len(sent)
        messages = [{"role": "system", "content": prompt.text},
                    {"role": "user", "content": user_msg}]
        try:
            result = await asyncio.to_thread(
                route_fn, TASK, messages, settings=s, actor=principal.actor, audit=deferred,
                audit_meta=audit_meta, response_format=response_format(),
                max_tokens=MAX_OUTPUT_TOKENS)
            llm_ran = True
        except LLMError as exc:
            logger.warning("complaint: LLM no disponible (%s)", type(exc).__name__)
            p.warnings.append({"type": "llm_unavailable",
                               "message": "Solo campos deterministas: el servicio de extracción "
                                          "no está disponible."})
            result = None
        if result is not None:
            p.model = result.model
            data = parse_llm_json(result.content)
            if data is None:
                p.warnings.append({"type": "output_discarded", "reason": "invalid_output"})
                post["output_discarded"] = "invalid_output"
            elif leaks_prompt(json.dumps(data, ensure_ascii=False), nonce, prompt):
                p.warnings.append({"type": "output_discarded", "reason": "prompt_leak"})
                post["output_discarded"] = "prompt_leak"
            else:
                declared = _apply_llm(prep, data, by_id)
                post["model_declared"] = declared
                note = model_review_note(prep, declared, by_id)
                post["model_only"] = note["sources"] if note else []
                if note:
                    p.warnings.append(note)
    p.ai_generated = llm_ran
    post.update({
        "llm_warnings": [x["type"] for x in p.warnings if x["type"].startswith("llm_")],
        "codes_discarded": sum(1 for x in p.warnings if x["type"] == "llm_code_discarded"),
    })
    if deferred.calls:
        deferred.flush(audit, s, post)
    elif p.injection_suspected:
        # Sin llamada al LLM (sin clave, sin texto visible o LLM desactivado): el hallazgo se
        # registra con su tipo propio `instruction_ignored` (M3-T4, migración 010; antes era un
        # `llm_call` con `outcome: not_called`, punto S-T2-1). Misma forma del payload.
        deferred("instruction_ignored", principal.actor,
                 {"task": TASK, "stage": "complaint_parse", "outcome": "not_called",
                  **audit_meta, "security": {**base_security, **post}}, settings=s)
        deferred.flush(audit, s)
    if check_erp:
        p.erp_match = await erp_check(p, principal, session_factory, s)
        if not p.erp_match.checked:
            p.warnings.append({"type": "erp_unavailable",
                               "message": "No se ha podido cotejar con el ERP."})
        elif p.erp_match.mismatches:
            p.warnings.append({"type": "erp_mismatch", "count": len(p.erp_match.mismatches)})
    logger.info("complaint parsed fmt=%s pages=%s injection=%s erp_ok=%s ms=%s",
                p.source.format, p.source.pages, p.injection_suspected, p.erp_match.ok,
                round((time.perf_counter() - t0) * 1000))
    return p


def parse(file_bytes: bytes, filename: str, principal: Principal, **kw: Any) -> ComplaintParsed:
    """Versión síncrona de `parse_async` (no usar dentro de un bucle asyncio en marcha)."""
    return asyncio.run(parse_async(file_bytes, filename, principal, **kw))
