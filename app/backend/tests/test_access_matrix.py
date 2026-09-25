"""M4-T1 (F09): matriz de acceso endpoint × rol, y guardas estructurales de la API.

Toda ruta nueva de `solaris.api.app` debe añadirse a MATRIX (test_every_route_is_in_the_matrix) y
ninguna puede recibir la identidad (user/role) como parámetro (test_no_route_takes_identity_params).
"""

import pytest
from fastapi.testclient import TestClient

from solaris.api import app
from solaris.audit.api import audit_settings as audit_settings_dep
from solaris.auth import SESSIONS, THROTTLE, auth_settings
from tests.test_auth import PASSWORDS, with_auth

ROLES_USERS = {
    "anon": None,
    "calidad": "inaki.calidad",
    "planta": "ander.turno",
    "auditor": "auditora.ext",
    "admin": "jon.it",
}
ALL = {"calidad", "planta", "auditor", "admin"}
# (método, ruta) -> roles con acceso. "public" = sin autenticación.
MATRIX: dict[tuple[str, str], set[str] | str] = {
    ("GET", "/health"): "public",
    ("POST", "/auth/login"): "public",
    ("GET", "/auth/me"): ALL,
    ("POST", "/auth/logout"): ALL,
    ("GET", "/audit"): {"auditor", "admin"},
    ("GET", "/audit/export.csv"): {"auditor", "admin"},
}
IDENTITY_PARAMS = {"user", "username", "role", "actor", "actor_role_override", "as_user"}


def _operations():
    """(método, ruta, operación) desde el esquema OpenAPI (API pública de FastAPI; incluye los
    parámetros declarados por dependencias y los routers incluidos)."""
    spec = app.openapi()
    for path, item in spec["paths"].items():
        for method, op in item.items():
            yield method.upper(), path, op, spec


def _body_fields(op, spec):
    ref = (op.get("requestBody", {}).get("content", {}).get("application/json", {})
           .get("schema", {}).get("$ref"))
    if not ref:
        return set()
    schema = spec["components"]["schemas"][ref.rsplit("/", 1)[-1]]
    return {k.lower() for k in schema.get("properties", {})}


def test_every_route_is_in_the_matrix():
    assert {(m, p) for m, p, _, _ in _operations()} == set(MATRIX)


def test_no_route_takes_identity_params():
    """La identidad sale del token; ningún endpoint la acepta en query, cabecera, cookie ni cuerpo.
    (/auth/login recibe `username` en su cuerpo: es el único punto donde se declara quién eres.)"""
    for m, path, op, spec in _operations():
        names = {p["name"].lower() for p in op.get("parameters", [])} | _body_fields(op, spec)
        if (m, path) == ("POST", "/auth/login"):
            assert names == {"username", "password"}
            continue
        assert not names & IDENTITY_PARAMS, (m, path, names)
        if MATRIX[(m, path)] != "public":
            assert op.get("security"), (m, path)  # exige Bearer


@pytest.fixture(scope="module")
def tokens(audit_settings):
    s = with_auth(audit_settings)
    SESSIONS.clear()
    THROTTLE.clear()
    app.dependency_overrides[audit_settings_dep] = lambda: s
    app.dependency_overrides[auth_settings] = lambda: s
    c = TestClient(app)
    toks = {}
    for role, user in ROLES_USERS.items():
        if user is None:
            toks[role] = {}
            continue
        r = c.post("/auth/login", json={"username": user, "password": PASSWORDS[user]})
        assert r.status_code == 200
        toks[role] = {"Authorization": f"Bearer {r.json()['access_token']}"}
    yield c, toks
    app.dependency_overrides.clear()
    SESSIONS.clear()


CASES = [(m, p, role) for (m, p) in MATRIX if (m, p) != ("POST", "/auth/logout")
         for role in ROLES_USERS]


@pytest.mark.parametrize("method,path,role", CASES)
def test_access_matrix(tokens, method, path, role):
    c, toks = tokens
    allowed = MATRIX[(method, path)]
    kwargs = {}
    if path == "/auth/login":
        user = ROLES_USERS[role] or "inaki.calidad"
        kwargs["json"] = {"username": user, "password": PASSWORDS[user]}
    # Intentos de escalado que NO deben influir: cabeceras y parámetros con un rol "admin".
    headers = {**toks[role], "X-Role": "admin", "X-User": "jon.it", "X-Solaris-Role": "admin"}
    r = c.request(method, path, headers=headers, params={"role": "admin", "user": "jon.it"},
                  **kwargs)
    if allowed == "public" or role in allowed:
        assert r.status_code == 200, (method, path, role, r.text)
    elif role == "anon":
        assert r.status_code == 401, (method, path, role)
    else:
        assert r.status_code == 403, (method, path, role)


def test_logout_matrix(tokens):
    c, _ = tokens
    assert c.post("/auth/logout").status_code == 401
    for user in ROLES_USERS.values():
        if user is None:
            continue
        r = c.post("/auth/login", json={"username": user, "password": PASSWORDS[user]})
        h = {"Authorization": f"Bearer {r.json()['access_token']}"}
        assert c.post("/auth/logout", headers=h).status_code == 204
        assert c.get("/auth/me", headers=h).status_code == 401
