"""M4-T2 (F08) + M4-T1 (F09): GET /audit y GET /audit/export.csv contra `solaris_test`, con auth."""

import csv
import io

import pytest
from fastapi.testclient import TestClient

from solaris.api import app
from solaris.audit import Actor, record
from solaris.audit.api import audit_settings as audit_settings_dep
from solaris.auth import SESSIONS, THROTTLE, auth_settings
from tests.test_auth import PASSWORDS, with_auth


@pytest.fixture(autouse=True)
def _no_real_network():
    yield  # solo Postgres local vía libpq


def _override(s):
    app.dependency_overrides[audit_settings_dep] = lambda: s
    app.dependency_overrides[auth_settings] = lambda: s


def _token(c, user):
    r = c.post("/auth/login", json={"username": user, "password": PASSWORDS[user]})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def anon(audit_settings):
    SESSIONS.clear()
    THROTTLE.clear()
    _override(with_auth(audit_settings))
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        SESSIONS.clear()


@pytest.fixture
def client(anon):
    """Cliente autenticado como auditora (rol auditor)."""
    anon.headers.update(_token(anon, "auditora.ext"))
    return anon


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


def test_unavailable_without_reader_credentials(client, audit_settings):
    broken = with_auth(audit_settings).model_copy(update={"audit_reader_password": None})
    app.dependency_overrides[audit_settings_dep] = lambda: broken
    assert client.get("/audit").status_code == 503
    assert client.get("/audit/export.csv").status_code == 503


def test_audit_requires_admin_or_auditor(anon):
    """Antes xfail estricto (M4-T2); M4-T1 lo cierra: sin token 401, calidad/planta 403."""
    assert anon.get("/audit").status_code == 401
    assert anon.get("/audit/export.csv").status_code == 401
    for user in ("inaki.calidad", "ander.turno"):
        h = _token(anon, user)
        assert anon.get("/audit", headers=h).status_code == 403
        assert anon.get("/audit/export.csv", headers=h).status_code == 403
    for user in ("auditora.ext", "jon.it"):
        assert anon.get("/audit", headers=_token(anon, user)).status_code == 200


def test_export_actor_is_authenticated_user_and_forbidden_is_audited(anon):
    h_admin = _token(anon, "jon.it")
    assert anon.get("/audit/export.csv", headers=h_admin).status_code == 200
    last = anon.get("/audit", params={"event_type": "export", "limit": 1},
                    headers=h_admin).json()["items"][0]
    assert (last["actor_user"], last["actor_role"]) == ("jon.it", "admin")
    # El intento de planta queda en el audit como `auth` forbidden, con su identidad real.
    assert anon.get("/audit", headers=_token(anon, "ander.turno")).status_code == 403
    items = anon.get("/audit", params={"event_type": "auth", "actor_user": "ander.turno",
                                       "limit": 5}, headers=h_admin).json()["items"]
    assert any(i["payload"].get("outcome") == "forbidden" and i["payload"]["path"] == "/audit"
               for i in items)
