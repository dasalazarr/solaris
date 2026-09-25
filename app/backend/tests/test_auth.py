"""M4-T1 (F09): login, JWT, inactividad, rol desde acl.json y escalado negativo. Sin BD."""

import json
import time

import jwt
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from solaris.api import app
from solaris.auth import SESSIONS, THROTTLE, auth_settings
from solaris.auth.core import (
    ALGORITHM,
    AUDIENCE,
    ISSUER,
    AuthError,
    AuthUnavailable,
    Principal,
    authenticate,
    issue_token,
    password_field,
)
from solaris.settings import REPO_ROOT

SECRET = "test-secret-" + "x" * 40
PASSWORDS = {
    "inaki.calidad": "pw-calidad-0123456789",
    "ander.turno": "pw-planta-0123456789",
    "auditora.ext": "pw-auditor-0123456789",
    "jon.it": "pw-admin-0123456789",
}


def with_auth(settings, **extra):
    upd = {
        "auth_jwt_secret": SecretStr(SECRET),
        **{password_field(u): SecretStr(p) for u, p in PASSWORDS.items()},
        **extra,
    }
    return settings.model_copy(update=upd)


@pytest.fixture(autouse=True)
def _clean_sessions():
    SESSIONS.clear()
    THROTTLE.clear()
    yield
    SESSIONS.clear()
    THROTTLE.clear()


@pytest.fixture
def s(settings):
    return with_auth(settings)


@pytest.fixture
def client(s):
    app.dependency_overrides[auth_settings] = lambda: s
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def _login(client, user, password=None):
    body = {"username": user, "password": password or PASSWORDS[user]}
    return client.post("/auth/login", json=body)


def _bearer(token):
    return {"Authorization": f"Bearer {token}"}


def test_password_fields_exist_for_every_acl_user(settings):
    users = json.loads((REPO_ROOT / "app/data/synthetic/acl.json").read_text())["users"]
    for u in users:
        assert password_field(u) in type(settings).model_fields, u


@pytest.mark.parametrize("user,role", [
    ("inaki.calidad", "calidad"), ("ander.turno", "planta"),
    ("auditora.ext", "auditor"), ("jon.it", "admin"),
])
def test_login_ok_role_from_acl(client, user, role):
    r = _login(client, user)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["role"] == role and body["token_type"] == "bearer"
    claims = jwt.decode(body["access_token"], options={"verify_signature": False})
    assert "role" not in claims  # el rol no viaja en el token: se resuelve en el servidor
    assert claims["exp"] - claims["iat"] == 1800
    me = client.get("/auth/me", headers=_bearer(body["access_token"]))
    assert me.json() == {"user": user, "role": role}


@pytest.mark.parametrize("user,password", [
    ("inaki.calidad", "incorrecta-0123456789"),
    ("nadie", "pw-calidad-0123456789"),
    ("inaki.calidad", ""),
])
def test_login_bad_credentials_generic_401(client, user, password):
    r = client.post("/auth/login", json={"username": user, "password": password})
    assert r.status_code in (401, 422)
    if r.status_code == 401:
        assert r.json()["detail"] == "Credenciales no válidas"


def test_user_without_configured_password_cannot_login(settings):
    s2 = with_auth(settings, **{password_field("jon.it"): None})
    app.dependency_overrides[auth_settings] = lambda: s2
    try:
        assert _login(TestClient(app), "jon.it").status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_short_password_is_rejected_even_if_it_matches(settings):
    s2 = with_auth(settings, **{password_field("jon.it"): SecretStr("corta")})
    app.dependency_overrides[auth_settings] = lambda: s2
    try:
        assert _login(TestClient(app), "jon.it", "corta").status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_no_secret_fails_closed(settings):
    s2 = with_auth(settings, auth_jwt_secret=None)
    app.dependency_overrides[auth_settings] = lambda: s2
    try:
        c = TestClient(app)
        assert _login(c, "jon.it").status_code == 503
        assert c.get("/auth/me", headers=_bearer("x.y.z")).status_code == 503
    finally:
        app.dependency_overrides.clear()
    with pytest.raises(AuthUnavailable):
        issue_token("jon.it", "sid", with_auth(settings, auth_jwt_secret=SecretStr("short")))


def test_lockout_after_repeated_failures(client):
    for _ in range(5):
        assert _login(client, "jon.it", "mala-mala-mala-mala").status_code == 401
    assert _login(client, "jon.it").status_code == 429  # ni con la buena
    THROTTLE.clear()
    assert _login(client, "jon.it").status_code == 200


# --- token: firma, algoritmo, claims -----------------------------------------------------------


def _claims(**over):
    t = int(time.time())
    return {"iss": ISSUER, "aud": AUDIENCE, "sub": "jon.it", "sid": "x", "iat": t, "nbf": t,
            "exp": t + 600, **over}


def test_forged_tokens_rejected(client, s):
    tok = _login(client, "ander.turno").json()["access_token"]
    sid = jwt.decode(tok, options={"verify_signature": False})["sid"]
    forged = [
        jwt.encode(_claims(sub="jon.it", sid=sid), "otra-clave-" + "y" * 40, algorithm=ALGORITHM),
        jwt.encode(_claims(sub="jon.it", sid=sid), None, algorithm="none"),
        jwt.encode(_claims(sub="jon.it", sid=sid, aud="otra"), SECRET, algorithm=ALGORITHM),
        jwt.encode(_claims(sub="jon.it", sid=sid, exp=int(time.time()) - 60), SECRET,
                   algorithm=ALGORITHM),
        # firma válida pero sid de la sesión de OTRO usuario: no sirve para suplantar a jon.it
        jwt.encode(_claims(sub="jon.it", sid=sid), SECRET, algorithm=ALGORITHM),
        # firma válida y sid inventado: no hay sesión
        jwt.encode(_claims(sub="jon.it", sid="inventado"), SECRET, algorithm=ALGORITHM),
        tok + "x",
    ]
    for f in forged:
        assert client.get("/auth/me", headers=_bearer(f)).status_code == 401, f
        with pytest.raises(AuthError):
            authenticate(f, s)
    assert client.get("/auth/me", headers=_bearer(tok)).json()["role"] == "planta"


def test_missing_or_wrong_scheme_is_401(client):
    assert client.get("/auth/me").status_code == 401
    tok = _login(client, "jon.it").json()["access_token"]
    assert client.get("/auth/me", headers={"Authorization": f"Basic {tok}"}).status_code == 401
    assert client.get("/auth/me", params={"token": tok}).status_code == 401


# --- sesión: inactividad, logout, rol vivo -----------------------------------------------------


def test_idle_timeout_closes_session(client):
    tok = _login(client, "inaki.calidad").json()["access_token"]
    sid = jwt.decode(tok, options={"verify_signature": False})["sid"]
    assert client.get("/auth/me", headers=_bearer(tok)).status_code == 200
    SESSIONS.age_idle(sid, 899)  # justo por debajo: sigue viva y se renueva
    assert client.get("/auth/me", headers=_bearer(tok)).status_code == 200
    SESSIONS.age_idle(sid, 901)
    assert client.get("/auth/me", headers=_bearer(tok)).status_code == 401
    assert client.get("/auth/me", headers=_bearer(tok)).status_code == 401  # ya no revive


def test_logout_revokes_token(client):
    tok = _login(client, "inaki.calidad").json()["access_token"]
    assert client.post("/auth/logout", headers=_bearer(tok)).status_code == 204
    assert client.get("/auth/me", headers=_bearer(tok)).status_code == 401


def test_role_change_in_acl_applies_immediately(tmp_path, settings):
    acl = json.loads((REPO_ROOT / "app/data/synthetic/acl.json").read_text())
    path = tmp_path / "acl.json"
    path.write_text(json.dumps(acl))
    s2 = with_auth(settings, acl_file=path)
    app.dependency_overrides[auth_settings] = lambda: s2
    try:
        c = TestClient(app)
        tok = _login(c, "jon.it").json()["access_token"]
        acl["users"]["jon.it"]["role"] = "planta"  # degradado
        path.write_text(json.dumps(acl))
        assert c.get("/auth/me", headers=_bearer(tok)).json()["role"] == "planta"
        del acl["users"]["jon.it"]  # baja
        path.write_text(json.dumps(acl))
        assert c.get("/auth/me", headers=_bearer(tok)).status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_principal_actor_is_the_real_user():
    p = Principal("ander.turno", "planta", "sid")
    assert (p.actor.user, p.actor.role) == ("ander.turno", "planta")


def test_llm_route_audits_the_authenticated_actor(settings, monkeypatch):
    """llm.route(actor=principal.actor) registra al usuario real en `llm_call`."""
    import httpx
    import respx

    from solaris.llm import route

    seen = []
    p = Principal("inaki.calidad", "calidad", "sid")
    with respx.mock(base_url=settings.openrouter_base_url) as mock:
        mock.post("/chat/completions").mock(return_value=httpx.Response(200, json={
            "id": "x", "model": "m", "provider": "p",
            "choices": [{"message": {"role": "assistant", "content": "ok"}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }))
        from solaris.llm.config import load_model_cards

        task = next(iter(load_model_cards(settings.models_file)))
        route(task, [{"role": "user", "content": "hola"}], settings=settings, actor=p.actor,
              audit=lambda *a, **k: seen.append(a))
    assert seen and seen[0][0] == "llm_call" and seen[0][1] == p.actor
