"""M4-T1 (F09): matriz de acceso endpoint × rol, y guardas estructurales de la API.

Toda ruta nueva de `solaris.api.app` debe añadirse a MATRIX (test_every_route_is_in_the_matrix) y
ninguna puede recibir la identidad (user/role) como parámetro (test_no_route_takes_identity_params).

M2-T6 (S2 de M2-T8): la guarda recorre de forma recursiva los `$ref`, `properties`, `items`,
`allOf/anyOf/oneOf` y `additionalProperties` de TODOS los content-types del cuerpo, y normaliza los
nombres (minúsculas, sin `x-`, partidos por `_`/`-`) para comprobar sus tokens contra
IDENTITY_TOKENS. Así caen `X-User`/`X-Role` como cabecera y `{context: {user: ...}}` anidado.
"""

import re

import pytest
from fastapi import FastAPI, Header
from fastapi.testclient import TestClient
from pydantic import BaseModel

from solaris.agents.api import COMPLAINT_LIMITER, complaint_engine
from solaris.agents.api import complaint_settings as complaint_settings_dep
from solaris.agents.complaint import prepare
from solaris.api import app
from solaris.audit.api import audit_settings as audit_settings_dep
from solaris.auth import SESSIONS, THROTTLE, auth_settings
from solaris.rag.answer import AskResult
from solaris.rag.api import ASK_LIMITER, ask_engine
from solaris.rag.api import ask_settings as ask_settings_dep
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
    ("POST", "/ask"): ALL,  # M2-T6: cada rol recupera solo lo que su ACL deja ver
    ("POST", "/complaints/parse"): {"calidad"},  # M3-T2: solo Calidad sube reclamaciones
}
# Tokens de identidad (S2). Un nombre coincide si alguno de sus tokens normalizados está aquí.
IDENTITY_TOKENS = {"user", "users", "username", "role", "roles", "actor", "sub", "principal",
                   "obo", "behalf", "impersonate", "as"}
# Excepciones explícitas: el login recibe `username` (es donde se declara quién eres) y /audit
# filtra por `actor_user`/`actor_role` (son filtros de lectura del auditor, no identidad).
IDENTITY_ALLOW = {
    ("POST", "/auth/login"): {"username"},
    ("GET", "/audit"): {"actor_user", "actor_role"},
}


def _operations():
    """(método, ruta, operación) desde el esquema OpenAPI (API pública de FastAPI; incluye los
    parámetros declarados por dependencias y los routers incluidos)."""
    spec = app.openapi()
    for path, item in spec["paths"].items():
        for method, op in item.items():
            yield method.upper(), path, op, spec


def _name_tokens(name: str) -> set[str]:
    n = name.lower()
    n = n.removeprefix("x-")
    toks = set(re.split(r"[_\-.\s]+", n)) - {""}
    toks |= {re.sub(r"[_\-.\s]", "", n)}  # "onbehalfof", "asuser"…
    return toks


def is_identity_name(name: str) -> bool:
    toks = _name_tokens(name)
    return bool(toks & IDENTITY_TOKENS) or any(
        t.startswith(("onbehalf", "asuser", "asrole", "impersonat")) for t in toks
    )


def _schema_fields(schema, spec, seen=None) -> set[str]:
    """Nombres de propiedad (a cualquier profundidad) de un esquema OpenAPI."""
    seen = set() if seen is None else seen
    out: set[str] = set()
    if not isinstance(schema, dict):
        return out
    ref = schema.get("$ref")
    if ref:
        if ref in seen:
            return out
        seen.add(ref)
        name = ref.rsplit("/", 1)[-1]
        return _schema_fields(spec["components"]["schemas"][name], spec, seen)
    for k, v in (schema.get("properties") or {}).items():
        out.add(k)
        out |= _schema_fields(v, spec, seen)
    for key in ("items", "additionalProperties", "not"):
        out |= _schema_fields(schema.get(key), spec, seen)
    for key in ("allOf", "anyOf", "oneOf", "prefixItems"):
        for sub in schema.get(key) or []:
            out |= _schema_fields(sub, spec, seen)
    return out


def _body_fields(op, spec):
    out: set[str] = set()
    for media in (op.get("requestBody", {}).get("content") or {}).values():
        out |= _schema_fields(media.get("schema"), spec)
    return out


def identity_violations(application: FastAPI) -> list[tuple[str, str, str]]:
    spec = application.openapi()
    bad = []
    for path, item in spec["paths"].items():
        for method, op in item.items():
            names = {p["name"] for p in op.get("parameters", [])} | _body_fields(op, spec)
            allow = IDENTITY_ALLOW.get((method.upper(), path), set())
            bad += [(method.upper(), path, n) for n in sorted(names)
                    if n.lower() not in allow and is_identity_name(n)]
    return bad


def test_every_route_is_in_the_matrix():
    assert {(m, p) for m, p, _, _ in _operations()} == set(MATRIX)


def test_no_route_takes_identity_params():
    """La identidad sale del token; ningún endpoint la acepta en query, cabecera, cookie ni cuerpo
    (a ninguna profundidad). /auth/login recibe `username` en su cuerpo: es el único punto donde
    se declara quién eres."""
    assert identity_violations(app) == []
    for m, path, op, spec in _operations():
        if (m, path) == ("POST", "/auth/login"):
            assert _body_fields(op, spec) == {"username", "password"}
            continue
        if MATRIX[(m, path)] != "public":
            assert op.get("security"), (m, path)  # exige Bearer


def test_identity_guard_catches_nested_headers_and_forms():
    """S2: la guarda detecta los huecos de M4-T1 en una app de prueba."""
    class Ctx(BaseModel):
        user: str

    class Body(BaseModel):
        question: str
        context: Ctx

    class Inline(BaseModel):
        items: list[dict[str, Ctx]]

    bad = FastAPI()

    @bad.post("/nested")
    def nested(body: Body): ...

    @bad.post("/deep")
    def deep(body: Inline): ...

    @bad.get("/hdr")
    def hdr(x_user: str = Header(), x_role: str = Header()): ...

    @bad.get("/sub")
    def sub_(principal_id: str = "", sub: str = ""): ...

    got = {(p, n.lower()) for _, p, n in identity_violations(bad)}
    assert ("/nested", "user") in got
    assert ("/deep", "user") in got
    assert {("/hdr", "x-user"), ("/hdr", "x-role")} <= got
    # Cuerpo form/multipart con esquema en línea (sin $ref): FastAPI necesita python-multipart
    # para declararlo, así que se prueba sobre el fragmento de OpenAPI equivalente.
    form_op = {"requestBody": {"content": {"multipart/form-data": {"schema": {
        "type": "object", "properties": {"file": {"type": "string"},
                                         "meta": {"type": "object", "properties": {
                                             "on_behalf_of": {"type": "string"}}}}}}}}}
    assert "on_behalf_of" in _body_fields(form_op, {"components": {"schemas": {}}})
    assert is_identity_name("on_behalf_of") and is_identity_name("X-Solaris-Role")
    assert {("/sub", "principal_id"), ("/sub", "sub")} <= got
    # y no confunde nombres legítimos
    assert not is_identity_name("question") and not is_identity_name("filters")
    assert not is_identity_name("part_refs") and not is_identity_name("password")


@pytest.fixture(scope="module")
def tokens(audit_settings):
    s = with_auth(audit_settings)
    SESSIONS.clear()
    THROTTLE.clear()
    app.dependency_overrides[audit_settings_dep] = lambda: s
    app.dependency_overrides[auth_settings] = lambda: s
    app.dependency_overrides[ask_settings_dep] = lambda: s
    # /ask sin BD ni LLM: la matriz prueba la autorización, no el pipeline (test_ask_api.py).
    app.dependency_overrides[ask_engine] = lambda: _fake_engine
    ASK_LIMITER.clear()
    app.dependency_overrides[complaint_settings_dep] = lambda: s
    app.dependency_overrides[complaint_engine] = lambda: _fake_complaint_engine
    COMPLAINT_LIMITER.clear()
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


def _fake_engine(principal, question, filters=None, **_):
    return AskResult(answer="No encontrado", citations=[], not_found=True, warnings=[],
                     model=None, latency_ms=0.0)


async def _fake_complaint_engine(data, filename, principal, **_):
    return prepare(data, filename).parsed


_MIN_EML = (b"From: q@cust.example\r\nSubject: [C-TEST-2026-0009] AR-1003\r\n"
            b"Date: Fri, 18 Sep 2026 09:42:00 +0200\r\n\r\nComplaint no. C-TEST-2026-0009\r\n")


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
    if path == "/ask":
        kwargs["json"] = {"question": "¿Cada cuánto se cambia la boquilla?"}
    if path == "/complaints/parse":
        kwargs["files"] = {"file": ("c.eml", _MIN_EML, "message/rfc822")}
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
