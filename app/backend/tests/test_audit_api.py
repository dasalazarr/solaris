"""M4-T2 (F08): GET /audit y GET /audit/export.csv contra `solaris_test`."""

import csv
import io

import pytest
from fastapi.testclient import TestClient

from solaris.api import app
from solaris.audit import Actor, record
from solaris.audit.api import audit_settings as audit_settings_dep


@pytest.fixture(autouse=True)
def _no_real_network():
    yield  # solo Postgres local vía libpq


@pytest.fixture
def client(audit_settings):
    app.dependency_overrides[audit_settings_dep] = lambda: audit_settings
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_list_filters_and_pagination(client, audit_settings):
    for i in range(3):
        record("approval", Actor("inaki.calidad", "calidad"), {"step": i},
               case_id="8D-T-API", settings=audit_settings)
    r = client.get("/audit", params={"case_id": "8D-T-API", "limit": 2})
    assert r.status_code == 200
    body = r.json()
    assert [it["payload"]["step"] for it in body["items"]] == [2, 1]  # más recientes primero
    assert all(it["event_type"] == "approval" and len(it["hash"]) == 64 for it in body["items"])
    r2 = client.get(
        "/audit", params={"case_id": "8D-T-API", "limit": 2, "before_id": body["next_before_id"]}
    )
    assert [it["payload"]["step"] for it in r2.json()["items"]] == [0]
    assert r2.json()["next_before_id"] is None


def test_list_rejects_bad_filters(client):
    assert client.get("/audit", params={"event_type": "drop_table"}).status_code == 422
    assert client.get("/audit", params={"limit": 1000}).status_code == 422


def test_export_csv_escapes_formulas_and_is_audited(client, audit_settings):
    record("auth", Actor("=HYPERLINK(\"http://x\")", "calidad"), {"ok": True},
           case_id="8D-T-CSV", settings=audit_settings)
    r = client.get("/audit/export.csv")
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/csv")
    rows = list(csv.DictReader(io.StringIO(r.text)))
    mine = [x for x in rows if x["case_id"] == "8D-T-CSV"]
    assert mine and mine[0]["actor_user"].startswith("'=")
    assert all(len(x["hash"]) == 64 for x in rows)
    last = client.get("/audit", params={"event_type": "export", "limit": 1}).json()["items"][0]
    assert last["payload"]["what"] == "audit_csv"


def test_unavailable_without_reader_credentials(audit_settings):
    broken = audit_settings.model_copy(update={"audit_reader_password": None})
    app.dependency_overrides[audit_settings_dep] = lambda: broken
    try:
        c = TestClient(app)
        assert c.get("/audit").status_code == 503
        assert c.get("/audit/export.csv").status_code == 503
    finally:
        app.dependency_overrides.clear()


@pytest.mark.xfail(
    strict=True,
    reason="TODO(M4-T1): /audit y /audit/export.csv deben exigir usuario autenticado con rol "
    "admin o auditor. Cuando llegue la auth este test pasará: quitar el xfail.",
)
def test_audit_requires_admin_or_auditor(client):
    assert client.get("/audit").status_code in (401, 403)
    assert client.get("/audit/export.csv").status_code in (401, 403)
