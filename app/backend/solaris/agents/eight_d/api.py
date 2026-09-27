"""API del 8D (M3-T3): `POST /8d`, `GET /8d/{case_id}` y `GET /8d/{case_id}/events` (SSE).

- Identidad solo por token; **solo el rol calidad** (crear y leer; `require_roles`, PAT-008). La
  autorización va antes de leer el cuerpo. Ningún parámetro de identidad (MATRIX + guarda OpenAPI).
- `POST /8d` admite:
  * `multipart/form-data` con un único campo `file` (.pdf/.eml ≤ 10 MB; mismas comprobaciones que
    `POST /complaints/parse`), o
  * `application/json` `{"complaint_id": "C-OEMN-2026-0312"}`: una reclamación de la bandeja del
    demo (`COMPLAINT_INBOX_DIR/<id>.pdf|.eml`; solo ids con el formato, sin rutas).
  Crea el caso (fichero guardado en `eightd.cases`), lanza el grafo en segundo plano y responde
  202 con `case_id`. Límite por usuario (`EIGHTD_RATE_LIMIT_PER_MIN`).
- `GET /8d/{case_id}`: estado + borrador D1–D4 con citas, consultas ERP, hipótesis y avisos.
- `GET /8d/{case_id}/events`: progreso por nodo (SSE) hasta `pending_approval` o `error`.
- Errores genéricos: BD o audit no disponibles → 503; nunca detalles internos.

HITL (M3-T4, F06). El rol aprobador sale de `acl.json → hitl_approvers` en cada petición (PAT-008):
- `POST /8d/{case_id}/approve` `{version, comment?, edits?}` y `POST /8d/{case_id}/reject`
  `{version, reason}`: la decisión se liga a la versión exacta (sha256 de D1–D4 que da `GET`). Caso
  ya decidido, no pendiente o versión distinta → 409. La decisión se guarda (una por caso, sin
  UPDATE: congelada) y después se reanuda el grafo, cuyo nodo `hitl_gate` la vuelve a validar.
- `GET /approvals`: bandeja (L03) con los casos pendientes de aprobación.
- `POST /8d/{case_id}/export`: 403 + `approval_denied` sin aprobación válida; 501 si la hay (M5-T6).
- Todo 403/409 de estas rutas se registra como `approval_denied` (salvo el rol en export: `auth`).
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
import uuid
from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from dataclasses import dataclass, field
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from solaris.agents.api import _read_upload
from solaris.agents.complaint import MAX_FILE_BYTES, ComplaintFileError, detect_format
from solaris.agents.eight_d import graph as g
from solaris.agents.eight_d import hitl
from solaris.agents.eight_d.nodes import ApprovalRequired, Deps
from solaris.agents.eight_d.store import open_store
from solaris.audit import record_safe
from solaris.auth.core import Principal
from solaris.auth.deps import CurrentUser, require_roles
from solaris.db import DbUnavailable
from solaris.rag.api import RateLimiter
from solaris.settings import Settings, get_settings

logger = logging.getLogger("solaris.eight_d.api")
router = APIRouter(tags=["8d"])
EIGHTD_LIMITER = RateLimiter()
_COMPLAINT_ID_RE = re.compile(r"^C-[A-Z]{4}-\d{4}-\d{4}$")
_VERSION_RE = re.compile(r"^[0-9a-f]{64}$")
MAX_DECISION_BODY = 64 * 1024
MAX_INBOX = 100
_TERMINAL = {"pending_approval", "error"}
SSE_POLL_S = 0.5
SSE_MAX_S = 300.0

_OPENAPI_BODY: dict[str, Any] = {"requestBody": {"required": True, "content": {
    "multipart/form-data": {"schema": {
        "type": "object", "required": ["file"], "additionalProperties": False,
        "properties": {"file": {"type": "string", "format": "binary",
                                "description": "Reclamación .pdf o .eml (≤ 10 MB)"}}}},
    "application/json": {"schema": {
        "type": "object", "required": ["complaint_id"], "additionalProperties": False,
        "properties": {"complaint_id": {"type": "string",
                                        "pattern": _COMPLAINT_ID_RE.pattern,
                                        "description": "Reclamación de la bandeja del demo"}}}},
}}}


@dataclass
class Runtime:
    """Dónde se guardan los casos y cómo se construyen las dependencias del grafo (tests)."""

    open_store: Callable[[Settings], AbstractAsyncContextManager[Any]]
    make_deps: Callable[[Principal, Settings, Any], Deps]
    tasks: set[asyncio.Task[Any]] = field(default_factory=set)

    def spawn(self, coro: Any) -> asyncio.Task[Any]:
        task = asyncio.create_task(coro)
        self.tasks.add(task)  # referencia fuerte hasta que termine
        task.add_done_callback(self.tasks.discard)
        return task


def _make_deps(principal: Principal, settings: Settings, store: Any) -> Deps:
    return Deps(principal=principal, settings=settings, load_file=store.load_file,
                decision_fn=store.get_decision)


RUNTIME = Runtime(open_store=open_store, make_deps=_make_deps)


def eightd_settings() -> Settings:
    return get_settings()


def eightd_runtime() -> Runtime:
    return RUNTIME


EightDSettings = Annotated[Settings, Depends(eightd_settings)]
EightDRuntime = Annotated[Runtime, Depends(eightd_runtime)]
QualityUser = Annotated[Principal, Depends(require_roles("calidad"))]


async def _read_body(request: Request, max_bytes: int) -> Any:
    if not request.headers.get("content-type", "").lower().startswith("application/json"):
        raise HTTPException(415, "Se espera application/json")
    length = request.headers.get("content-length")
    if length is None or not length.isdigit():
        raise HTTPException(411, "Falta Content-Length")
    if int(length) > max_bytes:
        raise HTTPException(413, "Cuerpo demasiado grande")
    raw = await request.body()
    if len(raw) > max_bytes:
        raise HTTPException(413, "Cuerpo demasiado grande")
    try:
        return json.loads(raw)
    except ValueError as exc:
        raise HTTPException(422, "JSON no válido") from exc


async def _read_json(request: Request) -> str:
    body = await _read_body(request, 1024)
    if not isinstance(body, dict) or set(body) != {"complaint_id"}:
        raise HTTPException(422, "Solo se admite el campo `complaint_id`")
    cid = body["complaint_id"]
    if not isinstance(cid, str) or not _COMPLAINT_ID_RE.fullmatch(cid):
        raise HTTPException(422, "complaint_id no válido")
    return cid


def _inbox_file(settings: Settings, complaint_id: str) -> tuple[bytes, str]:
    base = settings.complaint_inbox_dir.resolve()
    for ext in (".pdf", ".eml"):
        path = (base / f"{complaint_id}{ext}").resolve()
        if path.parent == base and path.is_file():
            if path.stat().st_size > MAX_FILE_BYTES:
                raise HTTPException(413, "Fichero demasiado grande (máximo 10 MB)")
            return path.read_bytes(), path.name
    raise HTTPException(404, "Reclamación no encontrada en la bandeja")


async def _run(runtime: Runtime, settings: Settings, principal: Principal, case_id: str) -> None:
    try:
        async with runtime.open_store(settings) as store:
            await g.run_case(store, runtime.make_deps(principal, settings, store), case_id)
    except Exception as exc:  # el caso queda sin checkpoint; GET lo verá como `queued`/`error`
        logger.warning("8d: el caso %s no se pudo ejecutar (%s)", case_id, type(exc).__name__)


@router.post("/8d", status_code=202, openapi_extra=_OPENAPI_BODY)
async def create_case(request: Request, principal: QualityUser, settings: EightDSettings,
                      runtime: EightDRuntime) -> Any:
    if not EIGHTD_LIMITER.allow(principal.user, settings.eightd_rate_limit_per_min):
        raise HTTPException(429, "Demasiados casos; espera un minuto")
    ctype = request.headers.get("content-type", "").lower()
    if ctype.startswith("application/json"):
        complaint_id = await _read_json(request)
        data, filename = _inbox_file(settings, complaint_id)
        source = "inbox"
    else:
        data, filename, _ = await _read_upload(request)
        complaint_id, source = None, "upload"
    try:
        detect_format(data, filename)
    except ComplaintFileError as exc:
        raise HTTPException({"unsupported": 415, "too_large": 413}.get(exc.kind, 422),
                            str(exc)) from exc
    try:
        async with runtime.open_store(settings) as store:
            case_id = await store.create_case(
                complaint_id=complaint_id, created_by=principal.user,
                created_role=principal.role, source=source, filename=filename or "upload",
                data=data)
    except DbUnavailable as exc:
        raise HTTPException(503, "Servicio no disponible temporalmente") from exc
    runtime.spawn(_run(runtime, settings, principal, case_id))
    return JSONResponse({"case_id": case_id, "status": "drafting",
                         "events": f"/8d/{case_id}/events"}, status_code=202)


def _case_id(value: str) -> str:
    try:
        return str(uuid.UUID(value))
    except ValueError as exc:
        raise HTTPException(404, "Caso no encontrado") from exc


async def _load(runtime: Runtime, settings: Settings, case_id: str) -> dict[str, Any]:
    try:
        async with runtime.open_store(settings) as store:
            row = await store.get_case(case_id)
            if row is None:
                raise HTTPException(404, "Caso no encontrado")
            v = await g.view(store, case_id)
    except DbUnavailable as exc:
        raise HTTPException(503, "Servicio no disponible temporalmente") from exc
    v["created_by"] = row.created_by
    v["created_at"] = row.created_at.isoformat() if hasattr(row.created_at, "isoformat") \
        else row.created_at
    v["file"] = {"filename": row.filename, "sha256": row.sha256, "size": row.size,
                 "source": row.source}
    return v


MAX_CASES = 50


def _list_item(row: Any, v: dict[str, Any]) -> dict[str, Any]:
    """Fila de la bandeja L01: solo metadatos y señales, nunca el texto de la reclamación (salvo
    los códigos que ya validó el parser)."""
    c = v["complaint"] or {}
    dl = c.get("requested_deadlines") or {}
    kinds = {w.get("type") for w in v["warnings"]}
    channels = sorted({f.get("channel") for w in v["warnings"]
                       if w.get("type") == "instruction_ignored"
                       for f in w.get("findings") or [] if f.get("channel")})
    return {
        "case_id": row.case_id, "complaint_id": v["complaint_id"] or row.complaint_id,
        "status": v["status"], "customer": v["customer"].get("code") or c.get("customer_code"),
        "customer_name": v["customer"].get("name"), "part_ref": c.get("part_ref"),
        "lot_codes": c.get("lot_codes") or [], "qty_affected": c.get("qty_affected"),
        "issued_date": c.get("issued_date"),
        "deadlines": {k: {"text": (dl.get(k) or {}).get("text"),
                          "due_date": (dl.get(k) or {}).get("due_date")}
                      for k in ("containment", "report_8d")},
        "filename": row.filename, "source": row.source, "created_by": row.created_by,
        "created_at": row.created_at.isoformat() if hasattr(row.created_at, "isoformat")
        else row.created_at,
        "injection_suspected": bool(c.get("injection_suspected")),
        "injection_channels": channels, "review_note": "model_flagged_text" in kinds,
        "warnings": sorted(k for k in kinds if k), "elapsed_s": v["elapsed_s"],
    }


@router.get("/8d")
async def list_cases(principal: QualityUser, settings: EightDSettings,
                     runtime: EightDRuntime) -> Any:
    """Bandeja L01 (M5-T3): los últimos casos 8D con su estado (en proceso, pendiente, aprobado,
    rechazado, error). Mismo permiso que leer un caso (calidad)."""
    items: list[dict[str, Any]] = []
    try:
        async with runtime.open_store(settings) as store:
            for row in await store.recent_cases(MAX_CASES):
                items.append(_list_item(row, await g.view(store, row.case_id)))
    except DbUnavailable as exc:
        raise HTTPException(503, "Servicio no disponible temporalmente") from exc
    return {"items": items, "count": len(items)}


@router.get("/8d/{case_id}")
async def get_case(case_id: str, principal: QualityUser, settings: EightDSettings,
                   runtime: EightDRuntime) -> Any:
    return await _load(runtime, settings, _case_id(case_id))


@router.get("/8d/{case_id}/events")
async def case_events(case_id: str, principal: QualityUser, settings: EightDSettings,
                      runtime: EightDRuntime) -> Any:
    cid = _case_id(case_id)
    await _load(runtime, settings, cid)  # 404 antes de abrir el flujo

    async def stream() -> AsyncIterator[str]:
        sent = 0
        t0 = time.monotonic()
        while True:
            try:
                v = await _load(runtime, settings, cid)
            except HTTPException:
                yield "event: error\ndata: {}\n\n"
                return
            for p in v["progress"][sent:]:
                yield f"event: progress\ndata: {json.dumps(p, ensure_ascii=False)}\n\n"
            sent = len(v["progress"])
            if v["status"] in _TERMINAL or time.monotonic() - t0 > SSE_MAX_S:
                yield (f"event: status\ndata: "
                       f"{json.dumps({'status': v['status'], 'elapsed_s': v['elapsed_s']})}\n\n")
                return
            await asyncio.sleep(SSE_POLL_S)

    return StreamingResponse(stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-store"})


# --- HITL (M3-T4, F06) ---------------------------------------------------------------------------

_DECISION_SCHEMAS: dict[str, dict[str, Any]] = {
    "approve": {"type": "object", "required": ["version"], "additionalProperties": False,
                "properties": {
                    "version": {"type": "string", "pattern": _VERSION_RE.pattern,
                                "description": "sha256 de D1–D4 que devuelve GET /8d/{case_id}"},
                    "comment": {"type": "string", "maxLength": hitl.MAX_COMMENT_CHARS},
                    "edits": {"type": "array", "maxItems": hitl.MAX_EDITS, "items": {
                        "type": "object", "required": ["path", "value"],
                        "additionalProperties": False, "properties": {
                            "path": {"type": "array", "minItems": 2,
                                     "maxItems": hitl.MAX_PATH_DEPTH,
                                     "items": {"anyOf": [{"type": "string"},
                                                         {"type": "integer"}]}},
                            "value": {"anyOf": [{"type": "string"}, {"type": "number"},
                                                {"type": "boolean"}, {"type": "null"}]}}}}}},
    "reject": {"type": "object", "required": ["version", "reason"], "additionalProperties": False,
               "properties": {
                   "version": {"type": "string", "pattern": _VERSION_RE.pattern},
                   "reason": {"type": "string", "minLength": 1,
                              "maxLength": hitl.MAX_COMMENT_CHARS}}},
}


def _body_doc(kind: str) -> dict[str, Any]:
    return {"requestBody": {"required": True, "content": {
        "application/json": {"schema": _DECISION_SCHEMAS[kind]}}}}


def _path_case(request: Request) -> str | None:
    try:
        return str(uuid.UUID(str(request.path_params.get("case_id"))))
    except ValueError:
        return None


def _deny(principal: Principal, settings: Settings, case_id: str | None, action: str,
          reason: str, status: int, detail: str, **extra: Any) -> HTTPException:
    """Registra `approval_denied` y devuelve la excepción HTTP (el llamante la lanza)."""
    record_safe("approval_denied", principal.actor,
                {"action": action, "reason": reason, "status": status, **extra},
                settings=settings, case_id=case_id)
    return HTTPException(status, detail)


def _approvers(settings: Settings) -> frozenset[str]:
    try:
        return hitl.approvers(settings.acl_file)
    except (OSError, ValueError) as exc:
        raise HTTPException(503, "Servicio no disponible temporalmente") from exc


def require_approver(action: str) -> Callable[..., Principal]:
    """Rol aprobador desde `acl.json → hitl_approvers`, releído en cada petición (PAT-008).
    Un 403 se registra como `approval_denied`. Va antes de leer el cuerpo."""

    def _dep(principal: CurrentUser, settings: EightDSettings, request: Request) -> Principal:
        allowed = _approvers(settings)
        if principal.role not in allowed:
            raise _deny(principal, settings, _path_case(request), action, "role_not_approver",
                        403, "Permiso insuficiente", path=request.url.path,
                        required=sorted(allowed))
        return principal

    _dep.__name__ = f"require_approver_{action}"
    return _dep


_CASE_LOCKS: dict[str, asyncio.Lock] = {}


@asynccontextmanager
async def _case_lock(case_id: str) -> AsyncIterator[None]:
    """Serializa las decisiones sobre un mismo caso en este proceso (la BD, además, solo admite
    una fila por caso)."""
    lock = _CASE_LOCKS.setdefault(case_id, asyncio.Lock())
    try:
        async with lock:
            yield
    finally:
        if not lock.locked() and _CASE_LOCKS.get(case_id) is lock:
            _CASE_LOCKS.pop(case_id, None)


def _parse_decision(body: Any, kind: str) -> dict[str, Any]:
    allowed = {"approve": {"version", "comment", "edits"}, "reject": {"version", "reason"}}[kind]
    if not isinstance(body, dict) or not set(body) <= allowed or "version" not in body:
        raise HTTPException(422, f"Campos admitidos: {', '.join(sorted(allowed))}")
    version = body["version"]
    if not isinstance(version, str) or not _VERSION_RE.fullmatch(version):
        raise HTTPException(422, "`version` debe ser el sha256 de D1–D4 que devuelve GET")
    out: dict[str, Any] = {"version": version, "comment": None, "reason": None, "edits": []}
    for key in ("comment", "reason"):
        val = body.get(key)
        if key == "reason" and kind == "reject" and (not isinstance(val, str) or not val.strip()):
            raise HTTPException(422, "Falta el motivo del rechazo")
        if val is not None and (not isinstance(val, str) or len(val) > hitl.MAX_COMMENT_CHARS):
            raise HTTPException(422, f"`{key}`: texto de como máximo {hitl.MAX_COMMENT_CHARS}")
        out[key] = val.strip() if isinstance(val, str) else None
    try:
        out["edits"] = hitl.validate_edits(body.get("edits"))
    except hitl.EditError as exc:
        raise HTTPException(422, str(exc)) from exc
    return out


async def _decide(request: Request, principal: Principal, settings: Settings, runtime: Runtime,
                  case_id: str, kind: str) -> Any:
    cid = _case_id(case_id)
    body = _parse_decision(await _read_body(request, MAX_DECISION_BODY), kind)
    action = kind
    decision = "approved" if kind == "approve" else "rejected"
    try:
        async with _case_lock(cid), runtime.open_store(settings) as store:
            if await store.get_case(cid) is None:
                raise HTTPException(404, "Caso no encontrado")
            if await store.get_decision(cid) is not None:
                raise _deny(principal, settings, cid, action, "already_decided", 409,
                            "El caso ya tiene una decisión: el borrador está congelado")
            v = await g.view(store, cid)
            if v["status"] != "pending_approval":
                raise _deny(principal, settings, cid, action, "not_pending", 409,
                            "El caso no está pendiente de aprobación", case_status=v["status"])
            if body["version"] != v["version"]:
                raise _deny(principal, settings, cid, action, "stale_version", 409,
                            "El borrador ha cambiado desde que lo viste: recarga y revisa",
                            version=body["version"], current_version=v["version"])
            original = hitl.draft_of(v["draft"])
            try:
                final, changed = hitl.apply_edits(original, body["edits"])
            except hitl.EditError as exc:
                raise HTTPException(422, str(exc)) from exc
            approved = decision == "approved"
            saved = await store.save_decision(
                cid, decision=decision, decided_by=principal.user, decided_role=principal.role,
                version=v["version"],
                approved_version=hitl.draft_hash(final) if approved else None,
                pct_edited=hitl.pct_edited(original, final) if approved else 0.0,
                edits=body["edits"] if approved else [], edited_paths=changed if approved else [],
                comment=body["comment"], reason=body["reason"], draft_original=original,
                draft_final=final if approved else None)
            if not saved:
                raise _deny(principal, settings, cid, action, "already_decided", 409,
                            "El caso ya tiene una decisión: el borrador está congelado")
            try:
                out = await g.resume_case(store, runtime.make_deps(principal, settings, store),
                                          cid)
            except ApprovalRequired as exc:  # el grafo ya lo registró (approval_denied)
                logger.warning("8d: hitl_gate rechazó la decisión del caso %s (%s)", cid, exc)
                raise HTTPException(409, "La decisión no se ha podido aplicar al borrador") \
                    from exc
    except DbUnavailable as exc:
        raise HTTPException(503, "Servicio no disponible temporalmente") from exc
    return await _enrich(out, runtime, settings, cid)


async def _enrich(v: dict[str, Any], runtime: Runtime, settings: Settings,
                  cid: str) -> dict[str, Any]:
    full = await _load(runtime, settings, cid)
    return {**full, **{k: v[k] for k in ("status", "approved", "approval", "version")}}


Approver = Annotated[Principal, Depends(require_approver("approve"))]
Rejecter = Annotated[Principal, Depends(require_approver("reject"))]
InboxUser = Annotated[Principal, Depends(require_approver("list"))]


@router.post("/8d/{case_id}/approve", openapi_extra=_body_doc("approve"))
async def approve_case(case_id: str, request: Request, principal: Approver,
                       settings: EightDSettings, runtime: EightDRuntime) -> Any:
    return await _decide(request, principal, settings, runtime, case_id, "approve")


@router.post("/8d/{case_id}/reject", openapi_extra=_body_doc("reject"))
async def reject_case(case_id: str, request: Request, principal: Rejecter,
                      settings: EightDSettings, runtime: EightDRuntime) -> Any:
    return await _decide(request, principal, settings, runtime, case_id, "reject")


@router.post("/8d/{case_id}/export")
async def export_case(case_id: str, principal: QualityUser, settings: EightDSettings,
                      runtime: EightDRuntime) -> Any:
    """Export a la plantilla del OEM (F07). Hoy solo la guarda: sin aprobación válida → 403 +
    `approval_denied`; con ella → 501 (el DOCX es M5-T6)."""
    cid = _case_id(case_id)
    try:
        async with runtime.open_store(settings) as store:
            if await store.get_case(cid) is None:
                raise HTTPException(404, "Caso no encontrado")
            rec = await store.get_decision(cid)
            v = await g.view(store, cid)
    except DbUnavailable as exc:
        raise HTTPException(503, "Servicio no disponible temporalmente") from exc
    valid = (rec is not None and rec.decision == "approved" and v["status"] == "approved"
             and rec.approved_version == v["version"])
    if not valid:
        raise _deny(principal, settings, cid, "export", "not_approved", 403,
                    "El 8D no está aprobado: no se puede exportar", case_status=v["status"])
    raise HTTPException(501, "Export DOCX pendiente (M5-T6)")


@router.get("/approvals")
async def approvals_inbox(principal: InboxUser, settings: EightDSettings,
                          runtime: EightDRuntime) -> Any:
    """Bandeja L03: casos 8D pendientes de aprobación (solo roles aprobadores)."""
    required = sorted(_approvers(settings))
    items: list[dict[str, Any]] = []
    try:
        async with runtime.open_store(settings) as store:
            for row in await store.undecided_cases(MAX_INBOX):
                v = await g.view(store, row.case_id)
                if v["status"] != "pending_approval":
                    continue
                c = v["complaint"]
                items.append({
                    "case_id": row.case_id, "complaint_id": v["complaint_id"],
                    "part_ref": c.get("part_ref"), "customer": v["customer"].get("code"),
                    "created_by": row.created_by,
                    "created_at": row.created_at.isoformat() if hasattr(
                        row.created_at, "isoformat") else row.created_at,
                    "draft": "D1-D4", "version": v["version"], "required_roles": required,
                    "can_approve": principal.role in required,
                    "injection_suspected": bool(c.get("injection_suspected")),
                    "warnings": sorted({w.get("type") for w in v["warnings"]}),
                    "elapsed_s": v["elapsed_s"]})
    except DbUnavailable as exc:
        raise HTTPException(503, "Servicio no disponible temporalmente") from exc
    return {"items": items, "count": len(items)}
