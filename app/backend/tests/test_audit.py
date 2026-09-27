"""M4-T2 (F08): audit log de solo anexar con cadena de hash. Tests contra Postgres real
(`solaris_test`, recreada por sesión; ver conftest.audit_settings)."""

import json
from concurrent.futures import ThreadPoolExecutor
from itertools import pairwise

import httpx
import psycopg
import pytest
import respx
from pydantic import SecretStr

from solaris.audit import (
    GENESIS,
    Actor,
    AuditError,
    connect_reader,
    connect_writer,
    record,
    redact_payload,
    verify_chain,
)
from solaris.db.migrate import MIGRATIONS_DIR, discover
from solaris.llm import load_model_cards, route
from solaris.settings import DEFAULT_MODELS_FILE, Settings

from .conftest import FAKE_KEY

URL = "https://openrouter.ai/api/v1/chat/completions"
CALIDAD = Actor("inaki.calidad", "calidad")


@pytest.fixture(autouse=True)
def _no_real_network():
    yield  # psycopg usa libpq (solo Postgres local); httpx lo intercepta respx


def _rows(settings, where="", params=()):
    with connect_reader(settings) as c:
        cur = c.cursor(row_factory=psycopg.rows.dict_row)
        cols = "id, actor_user, event_type, case_id, model, provider, payload, " \
            "payload::text AS payload_text, prev_hash, hash"
        q = f"SELECT {cols} FROM audit.events {where} ORDER BY id"  # noqa: S608  # literales de test
        return cur.execute(q, params).fetchall()


def _max_id(settings) -> int:
    with connect_reader(settings) as c:
        return c.execute("SELECT coalesce(max(id), 0) FROM audit.events").fetchone()[0]


# --- sin BD -----------------------------------------------------------------------------------


def test_migration_003_without_secrets_and_with_triggers():
    mig = {m.version: m for m in discover(MIGRATIONS_DIR)}["003_audit"]
    code = "\n".join(
        ln for ln in mig.sql.splitlines() if not ln.lstrip().startswith("--")
    ).upper()
    assert "PASSWORD" not in code
    assert "BEFORE UPDATE OR DELETE OR TRUNCATE ON AUDIT.EVENTS" in code
    assert "GRANT INSERT ON AUDIT.EVENTS TO AUDIT_WRITER" in code
    assert "GRANT SELECT ON AUDIT.EVENTS TO AUDIT_READER" in code


def test_redaction_rules_without_db():
    s = Settings(_env_file=None, openrouter_api_key=SecretStr("zz-custom-secret-value-42"))
    out = redact_payload(
        {
            "api_key": "whatever",
            "Authorization": "Bearer abcdefghijkl",
            "note": "usa zz-custom-secret-value-42 y sk-or-v1-abcdef123456 en "
            "postgresql://solaris:hunter2pass@127.0.0.1/solaris",
            "prompt_tokens": 12,
            "messages": [{"role": "user", "content": "x" * 1000}],
            "sources": [{"doc_id": "8D-2025-014", "chunk": 3, "content": "y" * 3000}],
            "tools": [{"name": "get_lot", "args": {"lot_code": "L26241-AR1003-02"}}],
        },
        s,
    )
    text = json.dumps(out)
    for secret in ("whatever", "abcdefghijkl", "zz-custom-secret-value-42", "sk-or-v1", "hunter2"):
        assert secret not in text
    assert out["prompt_tokens"] == 12  # "tokens" no es un secreto
    assert "postgresql://solaris:[REDACTED]@" in out["note"]
    msg = out["messages"][0]
    assert msg["role"] == "user" and len(msg["sha256"]) == 64 and msg["chars"] == 1000
    assert len(msg["excerpt"]) == s.audit_prompt_max_chars and msg["truncated"] is True
    assert out["sources"][0]["content"] == "y" * 3000  # fuentes: siempre completas
    assert out["tools"][0]["args"] == {"lot_code": "L26241-AR1003-02"}

    hashed = redact_payload({"prompt": "secreto de negocio"}, s.model_copy(
        update={"audit_prompt_mode": "hash"}))
    assert set(hashed["prompt"]) == {"sha256", "chars"}


def test_audit_required_without_writer_fails_closed(settings):
    strict = settings.model_copy(update={"audit_required": True})
    with pytest.raises(AuditError):
        route("rag_answer", [{"role": "user", "content": "hola"}], settings=strict)


# --- con BD -----------------------------------------------------------------------------------


def test_insert_and_chain(audit_settings):
    start = _max_id(audit_settings)
    for i in range(3):
        record("auth", CALIDAD, {"i": i}, case_id="8D-T-CHAIN", settings=audit_settings)
    # un escritor no puede fijar id, ts ni hashes: el trigger los sobrescribe
    with connect_writer(audit_settings, autocommit=True) as w:
        w.execute(
            "INSERT INTO audit.events (id, ts, event_type, payload, prev_hash, hash) "
            "VALUES (1, '2000-01-01', 'auth', '{\"forged\": true}', %s, %s)",
            (GENESIS, "f" * 64),
        )
    rows = _rows(audit_settings, "WHERE id > %s", (start,))
    assert [r["payload"].get("i") for r in rows] == [0, 1, 2, None]
    assert rows[-1]["id"] > rows[-2]["id"] > 1 and rows[-1]["hash"] != "f" * 64
    for a, b in pairwise(rows):
        assert b["prev_hash"] == a["hash"]
    first = _rows(audit_settings, "WHERE id = (SELECT min(id) FROM audit.events)")[0]
    assert first["prev_hash"] == GENESIS
    rep = verify_chain(settings=audit_settings)
    assert rep.ok and rep.head_hash == rows[-1]["hash"] and rep.checked >= 4


def test_writer_has_insert_only(audit_settings):
    record("auth", CALIDAD, {"x": 1}, settings=audit_settings)
    for stmt in (
        "UPDATE audit.events SET actor_user = 'x'",
        "DELETE FROM audit.events",
        "TRUNCATE audit.events",
        "SELECT * FROM audit.events",
        "INSERT INTO audit.events (event_type) VALUES ('auth') RETURNING hash",
        "SELECT nextval('audit.events_id_seq')",
    ):
        with (
            connect_writer(audit_settings, autocommit=True) as w,
            pytest.raises(psycopg.errors.InsufficientPrivilege),
        ):
            w.execute(stmt)


def test_reader_has_select_only(audit_settings):
    for stmt in (
        "INSERT INTO audit.events (event_type) VALUES ('auth')",
        "UPDATE audit.events SET actor_user = 'x'",
        "DELETE FROM audit.events",
    ):
        with (
            connect_reader(audit_settings) as r,
            pytest.raises(
                (psycopg.errors.InsufficientPrivilege, psycopg.errors.ReadOnlySqlTransaction)
            ),
        ):
            r.execute(stmt)


def test_catalog_only_owner_can_mutate(audit_su):
    rows = audit_su.execute(
        "SELECT grantee, privilege_type FROM information_schema.role_table_grants "
        "WHERE table_schema = 'audit' AND table_name = 'events'"
    ).fetchall()
    grants = {(g, p) for g, p in rows}
    mutators = {g for g, p in grants if p in ("UPDATE", "DELETE", "TRUNCATE")}
    assert mutators == {"audit_owner"}
    assert ("audit_writer", "INSERT") in grants and ("audit_reader", "SELECT") in grants
    assert {p for g, p in grants if g == "audit_writer"} == {"INSERT"}
    assert {p for g, p in grants if g == "audit_reader"} == {"SELECT"}
    assert not {g for g, _ in grants} & {"PUBLIC", "erp_reader"}
    owner_login = audit_su.execute(
        "SELECT rolcanlogin FROM pg_roles WHERE rolname = 'audit_owner'"
    ).fetchone()[0]
    assert owner_login is False


@pytest.mark.parametrize("as_owner", [False, True], ids=["superuser", "owner"])
@pytest.mark.parametrize(
    "stmt",
    ["UPDATE audit.events SET actor_user = 'x'", "DELETE FROM audit.events",
     "TRUNCATE audit.events"],
)
def test_trigger_blocks_owner_and_superuser(audit_settings, audit_su, as_owner, stmt):
    record("auth", CALIDAD, {"x": 1}, settings=audit_settings)
    if as_owner:
        audit_su.execute("SET LOCAL ROLE audit_owner")
    with (
        pytest.raises(psycopg.errors.InsufficientPrivilege, match="solo anexar"),
        audit_su.transaction(),
    ):
        audit_su.execute(stmt)


def test_insert_rejected_outside_read_committed(audit_settings):
    with connect_writer(audit_settings) as w:
        w.isolation_level = psycopg.IsolationLevel.SERIALIZABLE
        with pytest.raises(psycopg.errors.FeatureNotSupported):
            record("auth", CALIDAD, {}, conn=w, settings=audit_settings)


def test_verify_chain_detects_tampering(audit_settings, audit_su):
    for i in range(3):
        record("approval", CALIDAD, {"step": i}, case_id="8D-T-TAMPER", settings=audit_settings)
    ids = [r["id"] for r in _rows(audit_settings, "WHERE case_id = '8D-T-TAMPER'")]
    head = verify_chain(settings=audit_settings)
    assert head.ok

    # un superusuario desactiva el trigger (acción explícita) y edita una fila: se detecta
    audit_su.execute("ALTER TABLE audit.events DISABLE TRIGGER audit_events_immutable")
    with audit_su.transaction(force_rollback=True):
        audit_su.execute(
            "UPDATE audit.events SET payload = '{\"step\": 99}' WHERE id = %s", (ids[1],)
        )
        rep = verify_chain(conn=audit_su)
        assert not rep.ok and rep.first_broken_id == ids[1] and "contenido" in rep.reason
    # borrar una fila intermedia rompe el enlace de la siguiente
    with audit_su.transaction(force_rollback=True):
        audit_su.execute("DELETE FROM audit.events WHERE id = %s", (ids[1],))
        rep = verify_chain(conn=audit_su)
        assert not rep.ok and rep.first_broken_id == ids[2] and "enlaza" in rep.reason
    # truncar la cola NO lo detecta la cadena sola; sí contra un ancla guardada fuera de la BD
    with audit_su.transaction(force_rollback=True):
        audit_su.execute("DELETE FROM audit.events WHERE id >= %s", (ids[2],))
        assert verify_chain(conn=audit_su).ok
        rep = verify_chain(conn=audit_su, anchor=(head.head_id, head.head_hash))
        assert not rep.ok and rep.first_broken_id == head.head_id
    # tras el rollback, todo intacto
    assert verify_chain(settings=audit_settings, anchor=(head.head_id, head.head_hash)).ok


def test_concurrent_inserts_keep_chain(audit_settings):
    start = _max_id(audit_settings)
    n = 40

    def one(i: int) -> None:
        record("retrieval", Actor(f"user{i % 4}", "calidad"), {"i": i}, settings=audit_settings)

    with ThreadPoolExecutor(max_workers=10) as pool:
        list(pool.map(one, range(n)))
    rows = _rows(audit_settings, "WHERE id > %s", (start,))
    assert sorted(r["payload"]["i"] for r in rows) == list(range(n))
    assert len({r["prev_hash"] for r in rows}) == n  # sin bifurcaciones
    rep = verify_chain(settings=audit_settings)
    assert rep.ok, rep


def test_api_key_never_stored(audit_settings):
    s = audit_settings.model_copy(update={"openrouter_api_key": SecretStr(FAKE_KEY)})
    record(
        "llm_call",
        CALIDAD,
        {
            "api_key": FAKE_KEY,
            "headers": {"Authorization": f"Bearer {FAKE_KEY}"},
            "error": f"fallo con la clave {FAKE_KEY}",
            "messages": [{"role": "user", "content": f"mi clave es {FAKE_KEY}"}],
        },
        case_id="8D-T-REDACT",
        settings=s,
    )
    row = _rows(audit_settings, "WHERE case_id = '8D-T-REDACT'")[-1]
    assert FAKE_KEY not in row["payload_text"]
    assert "sk-or-test" not in row["payload_text"]
    assert row["payload"]["api_key"] == "[REDACTED]"


@respx.mock
def test_llm_route_emits_llm_call_with_fallback(audit_settings):
    s = audit_settings.model_copy(
        update={
            "openrouter_api_key": SecretStr(FAKE_KEY),
            "models_file": DEFAULT_MODELS_FILE,
            "llm_max_retries": 1,
            "llm_backoff_s": 0.0,
            "llm_timeout_s": 1.0,
        }
    )
    card = load_model_cards(DEFAULT_MODELS_FILE)["rag_answer"]

    def responder(request: httpx.Request) -> httpx.Response:
        model = json.loads(request.content)["model"]
        if model == card.model:
            return httpx.Response(503)
        return httpx.Response(
            200,
            json={
                "model": model,
                "provider": "FallbackProv",
                "choices": [{"message": {"role": "assistant", "content": "respuesta"}}],
                "usage": {"prompt_tokens": 7, "completion_tokens": 3, "total_tokens": 10,
                          "cost": 0.0002},
            },
        )

    respx.post(URL).mock(side_effect=responder)
    msgs = [
        {"role": "system", "content": "Eres un asistente de calidad."},
        {"role": "user", "content": "<complaint>Par bajo en AR-1003</complaint>"},
    ]
    res = route(
        "rag_answer", msgs, settings=s, actor=CALIDAD, case_id="8D-T-LLM",
        audit_meta={"sources": [{"doc_id": "8D-2025-014", "chunk": 2}], "tools": []},
    )
    assert res.used_fallback is True

    row = _rows(audit_settings, "WHERE case_id = '8D-T-LLM'")[-1]
    p = row["payload"]
    assert row["event_type"] == "llm_call" and row["actor_user"] == "inaki.calidad"
    assert row["model"] == card.fallback and row["provider"] == "FallbackProv"
    assert p["fallback_used"] is True and p["outcome"] == "ok"
    assert p["requested_model"] == card.model and p["model_used"] == card.fallback
    assert (p["prompt_tokens"], p["completion_tokens"], p["total_tokens"]) == (7, 3, 10)
    assert p["cost_usd"] == 0.0002 and p["latency_ms"] >= 0 and p["attempts"] == 3
    assert p["provider_policy"]["data_collection"] == "deny"
    assert p["sources"] == [{"doc_id": "8D-2025-014", "chunk": 2}]
    assert len(p["messages"]) == 2 and len(p["messages"][1]["sha256"]) == 64
    assert p["response"]["chars"] == len("respuesta")
    assert any("HTTP 503" in e for e in p["errors"])
    assert FAKE_KEY not in row["payload_text"]
    assert verify_chain(settings=audit_settings).ok


@respx.mock
def test_llm_route_failure_is_audited(audit_settings):
    s = audit_settings.model_copy(
        update={"openrouter_api_key": SecretStr(FAKE_KEY), "llm_max_retries": 0,
                "llm_backoff_s": 0.0}
    )
    respx.post(URL).mock(return_value=httpx.Response(500))
    from solaris.llm import LLMProviderError

    with pytest.raises(LLMProviderError):
        route("rag_answer", [{"role": "user", "content": "x"}], settings=s, case_id="8D-T-FAIL")
    row = _rows(audit_settings, "WHERE case_id = '8D-T-FAIL'")[-1]
    assert row["payload"]["outcome"] == "error" and row["payload"]["model_used"] is None


def test_every_event_type_is_accepted_by_the_db_check(audit_settings):
    """M3-T4 (migración 010): el CHECK de audit.events coincide con EVENT_TYPES, incluidos
    `approval_denied` e `instruction_ignored`."""
    from solaris.audit import EVENT_TYPES

    assert {"approval_denied", "instruction_ignored", "approval"} <= EVENT_TYPES
    # `ingest` fuera: test_rag_ingest exige que todos sus eventos sean de svc.ingest (y la 004 ya
    # lo cubre).
    types = EVENT_TYPES - {"ingest"}
    for et in sorted(types):
        record(et, CALIDAD, {"check": et}, case_id="8D-T-TYPES", settings=audit_settings)
    got = {r["event_type"] for r in _rows(audit_settings, "WHERE case_id = %s", ("8D-T-TYPES",))}
    assert got == types
    with (connect_writer(audit_settings, autocommit=True) as w,
          pytest.raises(psycopg.errors.CheckViolation)):
        w.execute("INSERT INTO audit.events (event_type) VALUES ('approval_forged')")
