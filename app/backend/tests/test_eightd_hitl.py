"""M3-T4 (F06): HITL del 8D. Sin aprobación no hay acción, reforzado en la API y en el grafo.

Cubre: versión = hash de D1–D4, ediciones del aprobador (solo valores, nunca trazabilidad) y %
editado;
el nodo `hitl_gate` revalida la decisión guardada en el servidor (sin decisión, rol no aprobador,
otro usuario, versión antigua o ediciones manipuladas → `approval_denied` y el caso sigue
pendiente); aprobado = congelado; `instruction_ignored` en intake; y la API: roles (planta, auditor
y admin → 403), aprobar dos veces, versión antigua, export sin aprobar, rechazo, bandeja y el rol
aprobador leído de acl.json en cada petición.
"""

from __future__ import annotations

import asyncio
import json
import time
from contextlib import asynccontextmanager
from typing import Any

import pytest
from fastapi.testclient import TestClient

from solaris.agents.eight_d import api as eapi
from solaris.agents.eight_d import graph as g
from solaris.agents.eight_d import hitl
from solaris.agents.eight_d.nodes import ApprovalRequired, Deps
from solaris.api import app
from solaris.auth import SESSIONS, THROTTLE, auth_settings
from solaris.auth.core import Principal
from tests.test_auth import PASSWORDS, with_auth
from tests.test_eightd import CANARY, INJECTION, Harness, _eml

USERS = ("inaki.calidad", "ander.turno", "auditora.ext", "jon.it")
D2_TEXT = ["d2", "problem_statement", "text"]


@pytest.fixture
def h(settings) -> Harness:
    return Harness(settings)


# --- funciones puras -----------------------------------------------------------------------------


def test_version_is_stable_hash_of_d1_d4():
    a = {"d1": {"x": 1, "y": "é"}, "d2": None, "d3": [], "d4": {}}
    b = {"d4": {}, "d3": [], "d2": None, "d1": {"y": "é", "x": 1}}
    assert hitl.draft_hash(a) == hitl.draft_hash(b) and len(hitl.draft_hash(a)) == 64
    assert hitl.draft_hash(a) != hitl.draft_hash({**a, "d2": {}})
    assert hitl.draft_of({"d1": 1, "d5": 2, "complaint": 3}) == {"d1": 1, "d2": None,
                                                                  "d3": None, "d4": None}


def test_edits_replace_existing_values_only():
    d = {"d1": {"note": "abc"}, "d2": {"rows": [{"text": "hola", "citations": [{"doc_id": "C"}]}]},
         "d3": {"qty": 3}, "d4": {"h": [{"title": "t"}]}}
    edits = hitl.validate_edits([{"path": ["d2", "rows", 0, "text"], "value": "hola mundo"},
                                 {"path": ["d3", "qty"], "value": 4}])
    final, changed = hitl.apply_edits(d, edits)
    assert final["d2"]["rows"][0]["text"] == "hola mundo" and final["d3"]["qty"] == 4
    assert d["d2"]["rows"][0]["text"] == "hola"  # el original no se toca
    assert changed == [["d2", "rows", 0, "text"], ["d3", "qty"]]
    same, none = hitl.apply_edits(d, hitl.validate_edits([{"path": ["d1", "note"],
                                                          "value": "abc"}]))
    assert none == [] and same == d
    bad = [
        [{"path": ["d2", "rows", 0, "citations", 0, "doc_id"], "value": "X"}],  # trazabilidad
        [{"path": ["d5", "x"], "value": "x"}],  # fuera de D1–D4
        [{"path": ["d1"], "value": "x"}],  # sección entera
        [{"path": ["d1", "note"], "value": {"a": 1}}],  # no escalar
        [{"path": ["d1", "note"], "value": "x" * (hitl.MAX_VALUE_CHARS + 1)}],
        [{"path": ["d1", "note"], "value": "x", "role": "admin"}],  # campo extra
        [{"path": ["d1", True], "value": "x"}],
        "no-lista",
        [{"path": ["d1", "note"], "value": "x"}] * (hitl.MAX_EDITS + 1),
    ]
    for b in bad:
        with pytest.raises(hitl.EditError):
            hitl.validate_edits(b)
    for path in (["d1", "nope"], ["d2", "rows", 5, "text"], ["d4", "h"], ["d2", "rows", "0"]):
        with pytest.raises(hitl.EditError):  # la ruta no existe o apunta a estructura
            hitl.apply_edits(d, hitl.validate_edits([{"path": path, "value": "x"}]))


def test_pct_edited():
    d = {"d1": {"a": "a" * 90}, "d2": {"b": "b" * 10}, "d3": None, "d4": None}
    assert hitl.pct_edited(d, d) == 0.0
    f, _ = hitl.apply_edits(d, [{"path": ["d2", "b"], "value": "b" * 5 + "XXXXX"}])
    assert hitl.pct_edited(d, f) == 5.0
    f, _ = hitl.apply_edits(d, [{"path": ["d1", "a"], "value": ""}])
    assert hitl.pct_edited(d, f) == 90.0


def test_approvers_come_from_acl_and_fail_closed(tmp_path):
    from solaris.settings import get_settings

    assert hitl.approvers(get_settings().acl_file) == {"calidad"}
    p = tmp_path / "acl.json"
    p.write_text(json.dumps({"roles": ["calidad", "admin"], "users": {}}))
    assert hitl.approvers(p) == frozenset()  # sin la clave nadie aprueba
    p.write_text(json.dumps({"roles": ["calidad"], "users": {},
                             "hitl_approvers": ["calidad", "root", 3]}))
    assert hitl.approvers(p) == {"calidad"}  # roles no declarados fuera


# --- grafo: hitl_gate ----------------------------------------------------------------------------


def _decision(v: dict[str, Any], *, user: str = "inaki.calidad", role: str = "calidad",
              edits: list[dict[str, Any]] | None = None, **over: Any) -> dict[str, Any]:
    original = hitl.draft_of(v["draft"])
    final, changed = hitl.apply_edits(original, edits or [])
    d = {"decision": "approved", "decided_by": user, "decided_role": role,
         "version": v["version"], "approved_version": hitl.draft_hash(final),
         "pct_edited": hitl.pct_edited(original, final), "edits": edits or [],
         "edited_paths": changed, "comment": "ok", "reason": None,
         "draft_original": original, "draft_final": final}
    return {**d, **over}


def _resume(h: Harness, case_id: str, principal: Principal | None = None) -> dict[str, Any]:
    deps = h.deps() if principal is None else Deps(**{**h.deps().__dict__,
                                                       "principal": principal})
    return asyncio.run(g.resume_case(h.store, deps, case_id))


def _denied(h: Harness) -> list[str]:
    return [p["reason"] for et, p, _ in h.audit if et == "approval_denied"]


def test_gate_without_decision_denies_and_stays_pending(h):
    case_id, _ = h.run()
    with pytest.raises(ApprovalRequired):
        _resume(h, case_id)
    assert _denied(h) == ["no_decision"]
    v = asyncio.run(g.view(h.store, case_id))
    assert v["status"] == "pending_approval" and v["approved"] is False


@pytest.mark.parametrize("over,principal,reason", [
    ({"decided_role": "planta", "decided_by": "ander.turno"},
     Principal("ander.turno", "planta", "s"), "role_not_approver"),
    ({"decided_role": "admin", "decided_by": "jon.it"}, Principal("jon.it", "admin", "s"),
     "role_not_approver"),
    ({"decided_role": "calidad", "decided_by": "ander.turno"},  # rol falseado en el registro
     Principal("ander.turno", "planta", "s"), "role_not_approver"),
    ({}, Principal("otra.persona", "calidad", "s"), "principal_mismatch"),
    ({"version": "a" * 64}, None, "version_mismatch"),
    ({"approved_version": "b" * 64}, None, "approved_version_mismatch"),
    ({"decision": "maybe"}, None, "unknown_decision"),
])
def test_gate_rechecks_the_saved_decision(h, over, principal, reason):
    case_id, v = h.run()
    asyncio.run(h.store.save_decision(case_id, **_decision(v, **over)))
    with pytest.raises(ApprovalRequired):
        _resume(h, case_id, principal)
    assert _denied(h) == [reason]
    after = asyncio.run(g.view(h.store, case_id))
    assert after["status"] == "pending_approval" and after["draft"] == v["draft"]


def test_gate_detects_draft_changed_after_decision(h):
    """El borrador cambia después de guardar la decisión (checkpoint manipulado) → no avanza."""
    case_id, v = h.run()
    asyncio.run(h.store.save_decision(case_id, **_decision(v)))

    async def tamper():
        graph = g.build_graph(h.store.saver)
        d2 = dict(v["draft"]["d2"], problem_statement={"text": "otro", "citations": []})
        await graph.aupdate_state(g.thread(case_id), {"d2": d2}, as_node="await_approval")
    asyncio.run(tamper())
    with pytest.raises(ApprovalRequired):
        _resume(h, case_id)
    assert _denied(h) == ["version_mismatch"]


def test_valid_approval_applies_edits_freezes_and_audits(h):
    case_id, v = h.run()
    edit = [{"path": D2_TEXT, "value": "Three brackets broke at MIG weld seam W2 (3 pcs)."}]
    rec = _decision(v, edits=edit)
    asyncio.run(h.store.save_decision(case_id, **rec))
    out = _resume(h, case_id)
    assert out["status"] == "approved" and out["approved"] is True
    assert out["draft"]["d2"]["problem_statement"]["text"].endswith("(3 pcs).")
    assert out["draft_original"] == hitl.draft_of(v["draft"])
    assert out["version"] == rec["approved_version"] != v["version"]
    assert out["approval"]["pct_edited"] > 0 and out["approval"]["decided_by"] == "inaki.calidad"
    assert out["interrupt"] is None and "hitl_gate" in {p["node"] for p in out["progress"]}
    assert out["elapsed_s"] == v["elapsed_s"]  # el tiempo humano no cuenta como borrador
    (ev,) = [p for et, p, _ in h.audit if et == "approval"]
    assert ev["decision"] == "approved" and ev["version"] == v["version"]
    assert ev["approved_version"] == rec["approved_version"] and ev["pct_edited"] > 0
    assert ev["edited_paths"] == [D2_TEXT] and ev["comment"] == "ok"
    # Congelado: reanudar otra vez no cambia nada ni vuelve a registrar.
    again = _resume(h, case_id)
    assert again["draft"] == out["draft"] and again["status"] == "approved"
    assert sum(et == "approval" for et, _, _ in h.audit) == 1
    assert asyncio.run(h.store.save_decision(case_id, **rec)) is False


def test_injection_records_instruction_ignored_event(h):
    case_id, _ = h.run(_eml(INJECTION))
    (ev,) = [(p, kw) for et, p, kw in h.audit if et == "instruction_ignored"]
    payload, kw = ev
    assert kw["case_id"] == case_id and payload["stage"] == "8d_intake"
    assert payload["findings"] and payload["findings"][0]["channel"] == "visible"
    assert CANARY not in json.dumps(payload)  # solo metadatos, nunca el texto


def test_no_instruction_ignored_without_injection(h):
    h.run()
    assert not [et for et, _, _ in h.audit if et == "instruction_ignored"]


# --- API -----------------------------------------------------------------------------------------


@pytest.fixture
def api(settings, h, monkeypatch):
    s = with_auth(settings).model_copy(update={"audit_writer_password": None})
    SESSIONS.clear()
    THROTTLE.clear()
    eapi.EIGHTD_LIMITER.clear()
    events: list[tuple[str, str | None, dict[str, Any], str | None]] = []
    monkeypatch.setattr(eapi, "record_safe", lambda et, actor, payload, **kw: events.append(
        (et, actor.user, payload, kw.get("case_id"))))

    @asynccontextmanager
    async def open_store(_s):
        yield h.store

    rt = eapi.Runtime(open_store=open_store,
                      make_deps=lambda principal, st, store: Deps(
                          **{**h.deps().__dict__, "principal": principal, "settings": st}))
    state = {"settings": s}
    app.dependency_overrides[auth_settings] = lambda: s
    app.dependency_overrides[eapi.eightd_settings] = lambda: state["settings"]
    app.dependency_overrides[eapi.eightd_runtime] = lambda: rt
    with TestClient(app) as c:
        tok = {}
        for u in USERS:
            r = c.post("/auth/login", json={"username": u, "password": PASSWORDS[u]})
            tok[u] = {"Authorization": f"Bearer {r.json()['access_token']}"}
        yield c, tok, events, state
    app.dependency_overrides.clear()
    SESSIONS.clear()


def _new_case(c, tok, data: bytes | None = None) -> dict[str, Any]:
    r = c.post("/8d", files={"file": ("c.eml", data or _eml(), "message/rfc822")},
               headers=tok["inaki.calidad"])
    assert r.status_code == 202, r.text
    case_id = r.json()["case_id"]
    for _ in range(200):
        v = c.get(f"/8d/{case_id}", headers=tok["inaki.calidad"]).json()
        if v["status"] in ("pending_approval", "error"):
            return v
        time.sleep(0.05)
    raise AssertionError("el caso no terminó")


def _reasons(events, et: str = "approval_denied") -> list[str]:
    return [p["reason"] for e, _, p, _ in events if e == et]


def test_api_approve_flow(api, h):
    c, tok, events, _ = api
    v = _new_case(c, tok)
    cid, url = v["case_id"], f"/8d/{v['case_id']}"
    assert v["status"] == "pending_approval" and v["approved"] is False
    q = tok["inaki.calidad"]

    # Bandeja L03.
    inbox = c.get("/approvals", headers=q).json()
    (item,) = [x for x in inbox["items"] if x["case_id"] == cid]
    assert item["version"] == v["version"] and item["required_roles"] == ["calidad"]
    assert item["can_approve"] is True and item["draft"] == "D1-D4"

    # 3. Exportar sin aprobar → 403 + approval_denied.
    r = c.post(f"{url}/export", headers=q)
    assert r.status_code == 403 and "no está aprobado" in r.json()["detail"]
    assert _reasons(events) == ["not_approved"]

    # Roles no aprobadores (admin tampoco) → 403 + approval_denied, antes de leer el cuerpo.
    body = {"version": v["version"], "comment": "ok"}
    for u in ("ander.turno", "auditora.ext", "jon.it"):
        r = c.post(f"{url}/approve", json=body, headers={**tok[u], "X-Role": "calidad"},
                   params={"role": "calidad"})
        assert r.status_code == 403, (u, r.text)
        assert c.post(f"{url}/reject", json={**body, "reason": "x"},
                      headers=tok[u]).status_code == 403
        assert c.get("/approvals", headers=tok[u]).status_code == 403
        assert c.post(f"{url}/approve", content=b"x" * 10_000_000,
                      headers={**tok[u], "Content-Type": "application/json"}).status_code == 403
    denied = [(u, p) for e, u, p, case in events if e == "approval_denied"
              and p["reason"] == "role_not_approver"]
    assert {u for u, _ in denied} == {"ander.turno", "auditora.ext", "jon.it"}
    assert all(p["required"] == ["calidad"] for _, p in denied)

    # Versión antigua o inventada → 409; cuerpo y ediciones no válidos → 422.
    r = c.post(f"{url}/approve", json={"version": "f" * 64}, headers=q)
    assert r.status_code == 409 and "stale_version" in _reasons(events)
    for bad in ({"version": "xyz"}, {"comment": "sin versión"},
                {"version": v["version"], "role": "admin"},
                {"version": v["version"], "edits": [{"path": ["d2", "problem_statement",
                                                             "citations", 0, "doc_id"],
                                                    "value": "X"}]},
                {"version": v["version"], "edits": [{"path": ["d2", "nope"], "value": "X"}]}):
        assert c.post(f"{url}/approve", json=bad, headers=q).status_code == 422, bad
    assert c.post(f"{url}/approve", content=b"{}", headers={**q, "Content-Type": "text/plain"}
                  ).status_code == 415
    assert c.post(f"{url}/approve", content=b"x" * (eapi.MAX_DECISION_BODY + 1),
                  headers={**q, "Content-Type": "application/json"}).status_code == 413
    assert h.store.decisions == {}  # nada guardado hasta aquí

    # 4. Aprobar con una edición pequeña → 200 y % editado > 0.
    edit = {"path": D2_TEXT, "value": "Three brackets broke at weld seam W2 (lot 02)."}
    r = c.post(f"{url}/approve", json={**body, "edits": [edit]}, headers=q)
    assert r.status_code == 200, r.text
    out = r.json()
    assert out["status"] == "approved" and out["approved"] is True
    ap = out["approval"]
    assert ap["decided_by"] == "inaki.calidad" and ap["decided_role"] == "calidad"
    assert ap["version"] == v["version"] and ap["approved_version"] == out["version"]
    assert 0 < ap["pct_edited"] < 10 and ap["edited_paths"] == [D2_TEXT]
    assert out["draft"]["d2"]["problem_statement"]["text"] == edit["value"]
    assert out["draft_original"]["d2"] == v["draft"]["d2"]
    got = c.get(url, headers=q).json()
    assert got["approval"]["pct_edited"] == ap["pct_edited"] and got["status"] == "approved"
    assert got["created_by"] == "inaki.calidad"
    saved = h.store.decisions[cid]
    assert saved.version == v["version"] and saved.draft_final == out["draft"]

    # 5. Aprobar de nuevo (misma versión o la nueva) → 409; rechazar tras aprobar → 409.
    assert c.post(f"{url}/approve", json=body, headers=q).status_code == 409
    assert c.post(f"{url}/approve", json={"version": out["version"]},
                  headers=q).status_code == 409
    assert c.post(f"{url}/reject", json={"version": out["version"], "reason": "x"},
                  headers=q).status_code == 409
    assert _reasons(events).count("already_decided") == 3
    assert c.get(url, headers=q).json()["draft"] == out["draft"]  # congelado

    # Export con aprobación válida → 501 (M5-T6). La bandeja ya no lo lista.
    r = c.post(f"{url}/export", headers=q)
    assert r.status_code == 501 and "M5-T6" in r.json()["detail"]
    assert all(x["case_id"] != cid for x in c.get("/approvals", headers=q).json()["items"])
    # El evento `approval` lo escribe el grafo (hitl_gate), con el principal real.
    (ev,) = [p for et, p, _ in h.audit if et == "approval"]
    assert ev["pct_edited"] == ap["pct_edited"] and ev["version"] == v["version"]


def test_api_reject_flow(api):
    c, tok, events, _ = api
    v = _new_case(c, tok)
    url, q = f"/8d/{v['case_id']}", tok["inaki.calidad"]
    assert c.post(f"{url}/reject", json={"version": v["version"]}, headers=q).status_code == 422
    assert c.post(f"{url}/reject", json={"version": v["version"], "reason": "  "},
                  headers=q).status_code == 422
    r = c.post(f"{url}/reject", json={"version": v["version"], "reason": "D3 incompleto"},
               headers=q)
    assert r.status_code == 200 and r.json()["status"] == "rejected"
    assert r.json()["approval"]["reason"] == "D3 incompleto" and r.json()["approved"] is False
    assert c.post(f"{url}/export", headers=q).status_code == 403
    assert c.post(f"{url}/approve", json={"version": v["version"]}, headers=q).status_code == 409
    assert _reasons(events) == ["not_approved", "already_decided"]


def test_api_injection_case_is_flagged_in_inbox(api, h):
    c, tok, _, _ = api
    v = _new_case(c, tok, _eml(INJECTION))
    (item,) = [x for x in c.get("/approvals", headers=tok["inaki.calidad"]).json()["items"]
               if x["case_id"] == v["case_id"]]
    assert item["injection_suspected"] is True and "instruction_ignored" in item["warnings"]
    assert [et for et, _, _ in h.audit].count("instruction_ignored") == 1


def test_api_approver_role_is_read_from_acl_each_request(api, tmp_path, settings):
    """Cambiar `hitl_approvers` en acl.json tiene efecto inmediato (PAT-008)."""
    from solaris.settings import get_settings

    c, tok, _, state = api
    v = _new_case(c, tok)
    acl = json.loads(get_settings().acl_file.read_text(encoding="utf-8"))
    acl["hitl_approvers"] = ["planta"]
    p = tmp_path / "acl.json"
    p.write_text(json.dumps(acl), encoding="utf-8")
    state["settings"] = state["settings"].model_copy(update={"acl_file": p})
    url = f"/8d/{v['case_id']}/approve"
    assert c.post(url, json={"version": v["version"]},
                  headers=tok["inaki.calidad"]).status_code == 403
    r = c.post(url, json={"version": v["version"]}, headers=tok["ander.turno"])
    assert r.status_code == 200 and r.json()["approval"]["decided_role"] == "planta"


# --- M5-T3: bandeja L01 (`GET /8d`) --------------------------------------------------------------


def test_api_case_list_shows_status_and_signals(api, h):
    c, tok, _, _ = api
    q = tok["inaki.calidad"]
    clean = _new_case(c, tok)
    hostile = _new_case(c, tok, _eml(INJECTION))
    rej = _new_case(c, tok)
    assert c.post(f"/8d/{rej['case_id']}/reject",
                  json={"version": rej["version"], "reason": "no"}, headers=q).status_code == 200
    r = c.get("/8d", headers=q)
    assert r.status_code == 200
    items = {x["case_id"]: x for x in r.json()["items"]}
    assert r.json()["count"] == len(items) >= 3
    assert [x["case_id"] for x in r.json()["items"]][:3] == [
        rej["case_id"], hostile["case_id"], clean["case_id"]]  # más reciente primero
    a, b, x = items[clean["case_id"]], items[hostile["case_id"]], items[rej["case_id"]]
    assert a["status"] == "pending_approval" and a["injection_suspected"] is False
    assert a["complaint_id"] == clean["complaint_id"] and a["part_ref"]
    assert a["created_by"] == "inaki.calidad" and a["injection_channels"] == []
    assert set(a["deadlines"]) == {"containment", "report_8d"}
    assert b["injection_suspected"] is True and b["injection_channels"]
    assert "instruction_ignored" in b["warnings"]
    assert x["status"] == "rejected"
    # Ni el texto del documento ni el borrador salen en la lista.
    body = r.text
    assert CANARY not in body and "draft" not in body and "segments" not in body
    for u in ("ander.turno", "auditora.ext", "jon.it"):
        assert c.get("/8d", headers={**tok[u], "X-Role": "calidad"}).status_code == 403
    assert c.get("/8d").status_code == 401
