"""`POST /ask`: respuesta citada para el usuario autenticado (M2-T6, F02).

- Identidad solo por token (`CurrentUser`, PAT-008). El cuerpo no admite campos extra: ni `user`,
  ni `role`, ni nada anidado que no esté en el esquema (S2).
- Todos los roles pueden preguntar; cada uno solo recupera lo que su ACL deja ver (PAT-005).
- Límite en memoria por usuario (`ASK_RATE_LIMIT_PER_MIN`, 10/min por defecto) → 429.
- Errores genéricos (spec §4.4): proveedor LLM → 502, BD o audit no disponibles → 503. El detalle
  queda en el log y en el audit, nunca en la respuesta HTTP.
"""

from __future__ import annotations

import logging
import threading
import time
from collections import deque
from collections.abc import Callable
from typing import Annotated, Any

import psycopg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from solaris.audit import AuditError
from solaris.auth.deps import CurrentUser
from solaris.db import DbUnavailable
from solaris.llm import LLMError
from solaris.rag.answer import answer_question
from solaris.rag.retrieve import MAX_QUERY_CHARS, RetrievalError
from solaris.settings import Settings, get_settings

logger = logging.getLogger("solaris.ask")
router = APIRouter(tags=["ask"])

Code = Annotated[str, Field(min_length=1, max_length=64)]


class AskFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    doc_type: Annotated[list[Code], Field(max_length=20)] | None = None
    part_refs: Annotated[list[Code], Field(max_length=20)] | None = None
    folder: Annotated[list[Annotated[str, Field(min_length=1, max_length=200)]],
                      Field(max_length=20)] | None = None


class AskIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: Annotated[str, Field(min_length=1, max_length=MAX_QUERY_CHARS)]
    filters: AskFilters | None = None


class Citation(BaseModel):
    doc_id: str
    version: str
    title: str
    locator: dict[str, Any]
    folder: str


class AskOut(BaseModel):
    answer: str
    citations: list[Citation]
    not_found: bool
    warnings: list[dict[str, Any]]
    ai_generated: bool = True
    model: str | None
    latency_ms: float


class RateLimiter:
    """Ventana deslizante por usuario, en memoria (un proceso; suficiente para el demo)."""

    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def allow(self, key: str, limit: int, window_s: float = 60.0) -> bool:
        if limit <= 0:
            return True
        now = time.monotonic()
        with self._lock:
            q = self._hits.setdefault(key, deque())
            while q and now - q[0] >= window_s:
                q.popleft()
            if len(q) >= limit:
                return False
            q.append(now)
            return True

    def clear(self) -> None:
        with self._lock:
            self._hits.clear()


ASK_LIMITER = RateLimiter()


def ask_settings() -> Settings:
    return get_settings()


def ask_engine() -> Callable[..., Any]:
    """Pipeline de respuesta (se sustituye en tests para no tocar BD ni LLM)."""
    return answer_question


AskSettings = Annotated[Settings, Depends(ask_settings)]
AskEngine = Annotated[Callable[..., Any], Depends(ask_engine)]


@router.post("/ask", response_model=AskOut)
def ask(body: AskIn, principal: CurrentUser, settings: AskSettings, engine: AskEngine) -> Any:
    if not ASK_LIMITER.allow(principal.user, settings.ask_rate_limit_per_min):
        raise HTTPException(429, "Demasiadas consultas; espera un minuto")
    filters = body.filters.model_dump(exclude_none=True) if body.filters else None
    try:
        result = engine(principal, body.question, filters or None,
                        settings=settings)
    except RetrievalError as exc:
        raise HTTPException(422, "Filtros no válidos") from exc
    except LLMError as exc:
        logger.warning("ask: fallo del proveedor LLM (%s)", type(exc).__name__)
        raise HTTPException(502, "El servicio de respuesta no está disponible") from exc
    except (DbUnavailable, psycopg.OperationalError, AuditError) as exc:
        logger.warning("ask: servicio no disponible (%s)", type(exc).__name__)
        raise HTTPException(503, "Servicio no disponible temporalmente") from exc
    return result.public()

