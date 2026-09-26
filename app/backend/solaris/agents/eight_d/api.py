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
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
import uuid
from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass, field
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from solaris.agents.api import _read_upload
from solaris.agents.complaint import MAX_FILE_BYTES, ComplaintFileError, detect_format
from solaris.agents.eight_d import graph as g
from solaris.agents.eight_d.nodes import Deps
from solaris.agents.eight_d.store import open_store
from solaris.auth.core import Principal
from solaris.auth.deps import require_roles
from solaris.db import DbUnavailable
from solaris.rag.api import RateLimiter
from solaris.settings import Settings, get_settings

logger = logging.getLogger("solaris.eight_d.api")
router = APIRouter(tags=["8d"])
EIGHTD_LIMITER = RateLimiter()
_COMPLAINT_ID_RE = re.compile(r"^C-[A-Z]{4}-\d{4}-\d{4}$")
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
    return Deps(principal=principal, settings=settings, load_file=store.load_file)


RUNTIME = Runtime(open_store=open_store, make_deps=_make_deps)


def eightd_settings() -> Settings:
    return get_settings()


def eightd_runtime() -> Runtime:
    return RUNTIME


EightDSettings = Annotated[Settings, Depends(eightd_settings)]
EightDRuntime = Annotated[Runtime, Depends(eightd_runtime)]
QualityUser = Annotated[Principal, Depends(require_roles("calidad"))]


async def _read_json(request: Request) -> str:
    length = request.headers.get("content-length")
    if length is None or not length.isdigit():
        raise HTTPException(411, "Falta Content-Length")
    if int(length) > 1024:
        raise HTTPException(413, "Cuerpo demasiado grande")
    try:
        body = json.loads(await request.body())
    except ValueError as exc:
        raise HTTPException(422, "JSON no válido") from exc
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
