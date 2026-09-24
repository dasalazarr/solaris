"""Endpoints del audit log: `GET /audit` y `GET /audit/export.csv` (M4-T2, F08).

TODO(M4-T1, seguridad): SIN AUTENTICACIÓN TODAVÍA. Ambos endpoints deben exigir un usuario
autenticado con rol `admin` o `auditor` (derivado de la sesión, nunca de parámetros). Hasta
entonces el backend solo escucha en local. Test que lo recuerda (xfail estricto):
tests/test_audit_api.py::test_audit_requires_admin_or_auditor.

Solo leen con el rol de BD `audit_reader` (SELECT). La exportación se registra como `export`.
"""

import json
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from solaris.audit.store import (
    EVENT_TYPES,
    Actor,
    AuditUnavailable,
    connect_reader,
    iter_export_csv,
    query_events,
    record_safe,
)
from solaris.settings import Settings, get_settings

router = APIRouter(prefix="/audit", tags=["audit"])


def audit_settings() -> Settings:
    return get_settings()


SettingsDep = Annotated[Settings, Depends(audit_settings)]
Text = Annotated[str | None, Query(max_length=200)]


def _unavailable() -> HTTPException:
    return HTTPException(status_code=503, detail="Audit log no disponible")


def _serialize(row: dict[str, Any]) -> dict[str, Any]:
    return {**row, "ts": row["ts"].isoformat(), "payload": json.loads(row["payload"])}


@router.get("")
def list_events(
    settings: SettingsDep,
    event_type: Annotated[str | None, Query()] = None,
    actor_user: Text = None,
    actor_role: Text = None,
    case_id: Text = None,
    source: Text = None,
    from_ts: Annotated[datetime | None, Query(alias="from")] = None,
    to_ts: Annotated[datetime | None, Query(alias="to")] = None,
    before_id: Annotated[int | None, Query(ge=1)] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> dict[str, Any]:
    # TODO(M4-T1): exigir rol admin o auditor.
    if event_type is not None and event_type not in EVENT_TYPES:
        raise HTTPException(status_code=422, detail=f"event_type no válido: {sorted(EVENT_TYPES)}")
    try:
        rows = query_events(
            limit=limit, settings=settings, event_type=event_type, actor_user=actor_user,
            actor_role=actor_role, case_id=case_id, source=source, from_ts=from_ts,
            to_ts=to_ts, before_id=before_id,
        )
    except AuditUnavailable as exc:
        raise _unavailable() from exc
    items = [_serialize(r) for r in rows]
    next_before = items[-1]["id"] if len(items) == limit else None
    return {"items": items, "next_before_id": next_before}


@router.get("/export.csv")
def export(
    settings: SettingsDep,
    from_ts: Annotated[datetime | None, Query(alias="from")] = None,
    to_ts: Annotated[datetime | None, Query(alias="to")] = None,
) -> StreamingResponse:
    # TODO(M4-T1): exigir rol admin o auditor y registrar el usuario real como actor.
    try:
        conn = connect_reader(settings)
    except AuditUnavailable as exc:
        raise _unavailable() from exc
    record_safe(
        "export",
        Actor(None, None),  # TODO(M4-T1): usuario autenticado
        {"what": "audit_csv", "from": from_ts, "to": to_ts},
        settings=settings,
    )

    def body():
        with conn:
            yield from iter_export_csv(from_ts, to_ts, conn=conn)

    return StreamingResponse(
        body(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="solaris-audit.csv"'},
    )
