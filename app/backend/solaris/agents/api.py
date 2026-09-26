"""`POST /complaints/parse`: sube una reclamación (.pdf / .eml) y devuelve sus campos (M3-T2).

- Identidad solo por token y **solo el rol calidad** (`require_roles`, PAT-008). La autorización
  va ANTES de leer el cuerpo: el endpoint no declara parámetros de formulario (FastAPI los leería
  antes de resolver las dependencias); lee el multipart a mano tras autorizar.
- Límites antes de leer: `Content-Length` obligatorio y ≤ 10 MB + margen (411/413), multipart con
  un único fichero y ningún otro campo (ni `user`, ni `role`...). Después: tamaño real ≤ 10 MB
  (413), extensión .pdf/.eml + firma del contenido (415) y fichero legible (422).
- Límite por usuario (`COMPLAINT_RATE_LIMIT_PER_MIN`, 10/min) → 429.
- Errores genéricos: audit o BD no disponibles → 503. Un fallo del LLM o del ERP no es error: el
  parser devuelve los campos deterministas con un aviso en `warnings`.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Annotated, Any

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.datastructures import UploadFile
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.formparsers import MultiPartException

from solaris.agents.complaint import (
    MAX_FILE_BYTES,
    ComplaintFileError,
    ComplaintParsed,
    parse_async,
)
from solaris.audit import AuditError
from solaris.auth.core import Principal
from solaris.auth.deps import require_roles
from solaris.db import DbUnavailable
from solaris.rag.api import RateLimiter
from solaris.settings import Settings, get_settings

logger = logging.getLogger("solaris.complaints")
router = APIRouter(tags=["complaints"])

MAX_REQUEST_BYTES = MAX_FILE_BYTES + 64 * 1024  # cabeceras del multipart
# Tipos declarados por el cliente que se aceptan (el tipo real lo decide la firma del contenido).
ALLOWED_CONTENT_TYPES = frozenset({
    "application/pdf", "application/x-pdf", "message/rfc822", "application/octet-stream",
    "text/plain", "",
})
COMPLAINT_LIMITER = RateLimiter()
_KIND_STATUS = {"unsupported": 415, "too_large": 413, "invalid": 422}

_OPENAPI_BODY: dict[str, Any] = {"requestBody": {"required": True, "content": {
    "multipart/form-data": {"schema": {
        "type": "object", "required": ["file"], "additionalProperties": False,
        "properties": {"file": {"type": "string", "format": "binary",
                                "description": "Reclamación .pdf o .eml (≤ 10 MB)"}}}}}}}


def complaint_settings() -> Settings:
    return get_settings()


def complaint_engine() -> Callable[..., Any]:
    """Pipeline del parser (se sustituye en tests para no tocar LLM, MCP ni BD)."""
    return parse_async


ComplaintSettings = Annotated[Settings, Depends(complaint_settings)]
ComplaintEngine = Annotated[Callable[..., Any], Depends(complaint_engine)]
QualityUser = Annotated[Principal, Depends(require_roles("calidad"))]


async def _read_upload(request: Request) -> tuple[bytes, str, str]:
    ctype = request.headers.get("content-type", "")
    if not ctype.lower().startswith("multipart/form-data"):
        raise HTTPException(415, "Envía el fichero como multipart/form-data (campo `file`)")
    length = request.headers.get("content-length")
    if length is None or not length.isdigit():
        raise HTTPException(411, "Falta Content-Length")
    if int(length) > MAX_REQUEST_BYTES:
        raise HTTPException(413, "Fichero demasiado grande (máximo 10 MB)")
    try:
        form = await request.form(max_files=1, max_fields=0)
    except (MultiPartException, StarletteHTTPException) as exc:  # Starlette lo convierte en 400
        raise HTTPException(422, "Formulario no válido: solo se admite el campo `file`") from exc
    try:
        if set(form.keys()) != {"file"} or len(form.getlist("file")) != 1:
            raise HTTPException(422, "Formulario no válido: solo se admite el campo `file`")
        upload = form.get("file")
        if not isinstance(upload, UploadFile):
            raise HTTPException(422, "Falta el fichero")
        declared = (upload.content_type or "").split(";")[0].strip().lower()
        if declared not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(415, "Tipo de fichero no admitido (solo .pdf y .eml)")
        data = await upload.read(MAX_FILE_BYTES + 1)
        if len(data) > MAX_FILE_BYTES:
            raise HTTPException(413, "Fichero demasiado grande (máximo 10 MB)")
        return data, upload.filename or "", declared
    finally:
        await form.close()


@router.post("/complaints/parse", response_model=ComplaintParsed, openapi_extra=_OPENAPI_BODY)
async def parse_complaint(request: Request, principal: QualityUser, settings: ComplaintSettings,
                          engine: ComplaintEngine) -> Any:
    if not COMPLAINT_LIMITER.allow(principal.user, settings.complaint_rate_limit_per_min):
        raise HTTPException(429, "Demasiados ficheros; espera un minuto")
    data, filename, _ = await _read_upload(request)
    try:
        return await engine(data, filename, principal, settings=settings)
    except ComplaintFileError as exc:
        raise HTTPException(_KIND_STATUS.get(exc.kind, 422), str(exc)) from exc
    except (DbUnavailable, psycopg.OperationalError, AuditError) as exc:
        logger.warning("complaints: servicio no disponible (%s)", type(exc).__name__)
        raise HTTPException(503, "Servicio no disponible temporalmente") from exc
