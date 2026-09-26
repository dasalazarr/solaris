"""M2-T5: recuperación híbrida con ACL en SQL, RRF, diversificación y rerank (F02).

BD aislada `solaris_test` con el corpus real ingerido con embeddings `fake` (sin descarga) y
rerank `fake`. Si test_rag_ingest ya lo ingirió en esta sesión, se reutiliza.
"""

import json
import re
import uuid
from collections import Counter
from collections.abc import Iterator

import psycopg
import pytest

from solaris.rag.acl import DEFAULT_ACL_FILE, resolve_role
from solaris.rag.retrieve import (
    Hit,
    RetrievalError,
    RetrievalTrace,
    RetrieveConfig,
    build_filters,
    doc_ref_codes,
    expand_sections,
    lexical_query,
    retrieve,
)

ACL = json.loads(DEFAULT_ACL_FILE.read_text(encoding="utf-8"))
PLANTA_FORBIDDEN = ("calidad/8d", "calidad/amfe", "calidad/reclamaciones", "calidad/plantillas",
                    "compras/", "direccion/")
LITERAL_QUERIES = [
    "8D grietas soldadura AR-1003 D4 root cause crack MIG weld seam",
    "Evaluación de proveedor Hilos y Gases Goierri S-GOIE-260117 PCN-GOIE-2026-04",
    "coste de no calidad margen por cliente dirección confidencial",
    "AMFE modo de fallo NPR severidad ocurrencia detección AR-1006",
    "Lack of fusion battery tray bracket C-OEMN-2025-0114",
]


# --- Sin BD ---------------------------------------------------------------------------------


def test_lexical_query_quotes_codes_and_drops_stopwords():
    q = lexical_query("¿Cada cuánto se cambia la boquilla en CR-01 y S-GOIE-260117?")
    assert q == '"cambia" or "boquilla" or "cr-01" or "s-goie-260117"'


def test_lexical_query_cannot_inject_operators():
    q = lexical_query('boquilla" & !x | (y) <-> "z\' ; DROP TABLE rag.chunks; --')
    assert re.fullmatch(r'("[\w-]+"( or "[\w-]+")*)?', q), q  # solo términos entre comillas
    assert lexical_query("   ¿?  ") == ""


def test_build_filters_rejects_unknown_keys_and_bad_values():
    with pytest.raises(RetrievalError):
        build_filters({"role": "admin"})  # el rol NUNCA llega por filtros
    with pytest.raises(RetrievalError):
        build_filters({"folder": "direccion' OR 1=1 --"})
    with pytest.raises(RetrievalError):
        build_filters({"doc_type": ["8d", 3]})
    sql, params = build_filters({"doc_type": "8D", "part_refs": ["ar-1003"], "folder": "calidad"})
    assert sql.count(" AND ") == 3 and "OR 1=1" not in sql
    assert params == {"f_doc_type": ["8d"], "f_part_refs": ["AR-1003"], "f_folder": ["calidad"]}


def test_resolve_role_from_acl_json(tmp_path):
    assert resolve_role("inaki.calidad") == "calidad"
    assert resolve_role("ander.turno") == "planta"
    assert resolve_role("nadie") is None
    assert resolve_role("") is None
    assert resolve_role("calidad") is None  # un nombre de rol no es un usuario
    bad = tmp_path / "acl.json"
    bad.write_text(json.dumps({"roles": ["calidad"], "users": {"x": {"role": "admin"}},
                               "folders": {}}))
    assert resolve_role("x", bad) is None  # rol no declarado → sin acceso


# --- Con BD (solaris_test) ------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _no_real_network():
    """psycopg usa libpq contra el Postgres local; embeddings y rerank son fakes."""
    yield


@pytest.fixture(scope="module")
def rag_settings(audit_settings):
    return audit_settings.model_copy(update={"embed_backend": "fake", "rerank_backend": "fake"})


@pytest.fixture(scope="module")
def conn(audit_settings, rag_settings) -> Iterator[psycopg.Connection]:
    from solaris.audit import testdb
    from solaris.rag.ingest import ingest

    with testdb._connect_to(audit_settings, testdb.TEST_DB, autocommit=True) as c:
        if c.execute("SELECT to_regclass('rag.chunks')").fetchone()[0] is None:
            pytest.skip("solaris_test sin esquema rag")
        if c.execute("SELECT count(*) FROM rag.documents").fetchone()[0] == 0:
            rep = ingest(c, settings=rag_settings, audit_settings=rag_settings)
            assert not rep.errors
        yield c


@pytest.fixture(scope="module")
def app(conn, rag_settings) -> Iterator[psycopg.Connection]:
    """Las recuperaciones corren como `solaris_app` (M4-T1): sin SELECT directo sobre rag.*."""
    from solaris.audit import testdb
    from solaris.db import connect_app

    if rag_settings.solaris_app_password is None:
        pytest.skip("Falta SOLARIS_APP_PASSWORD en .env")
    s = rag_settings.model_copy(update={"app_db_name": testdb.TEST_DB})
    with connect_app(s, autocommit=True) as c:
        assert c.execute("SELECT current_user").fetchone()[0] == "solaris_app"
        yield c


def _run(conn, s, query, user, k=8, filters=None, **cfg):
    return retrieve(query, user, k, filters, config=RetrieveConfig(**cfg), conn=conn, settings=s)


def test_planta_never_gets_forbidden_folders(conn, app, rag_settings):
    for q in LITERAL_QUERIES:
        for rerank in (True, False):
            hits = _run(app, rag_settings, q, "ander.turno", k=50, rerank=rerank,
                        max_per_doc=0, candidates_per_doc=0)
            assert hits, q  # ve instrucciones, planes de control y mantenimiento
            bad = [h for h in hits if h.folder.startswith(PLANTA_FORBIDDEN)]
            assert bad == [], (q, [(h.doc_id, h.folder) for h in bad])
    allowed = {f for f, roles in ACL["folders"].items() if "planta" in roles}
    hits = _run(app, rag_settings, " ".join(LITERAL_QUERIES), "ander.turno", k=50,
                max_per_doc=0, candidates_per_doc=0)
    assert {h.folder for h in hits} <= allowed


def test_calidad_never_gets_direccion_confidencial(conn, app, rag_settings):
    content = conn.execute(
        "SELECT content FROM rag.chunks WHERE doc_id = 'COST-DIR-01' ORDER BY chunk_no LIMIT 1"
    ).fetchone()[0]
    q = content[:300]
    admin = _run(app, rag_settings, q, "jon.it", rerank=False)
    assert admin[0].doc_id == "COST-DIR-01"  # control positivo: el documento sí se recupera
    for rerank in (True, False):
        hits = _run(app, rag_settings, q, "inaki.calidad", k=50, rerank=rerank,
                    max_per_doc=0, candidates_per_doc=0)
        assert all(not h.folder.startswith("direccion/") for h in hits)
        assert "COST-DIR-01" not in {h.doc_id for h in hits}


@pytest.mark.parametrize("user", ["nadie", "", "calidad", "admin", "inaki.calidad' OR '1'='1"])
def test_unknown_user_gets_nothing(conn, app, rag_settings, user):
    tr = RetrievalTrace(user, None)
    hits = retrieve("8D grietas AR-1003", user, conn=app, settings=rag_settings, trace=tr)
    assert hits == [] and tr.role is None


def test_exact_code_found_by_lexical_branch(conn, app, rag_settings):
    hits = _run(app, rag_settings, "S-GOIE-260117", "inaki.calidad", rerank=False)
    assert hits and hits[0].doc_id == "EVAL-SGOIE-01"
    assert hits[0].bm25 is not None and hits[0].lexical_rank == 1
    # El código exacto aparece en el chunk devuelto.
    assert "S-GOIE-260117" in hits[0].content
    # Planta no ve compras/: el mismo código no le devuelve la evaluación.
    planta = _run(app, rag_settings, "S-GOIE-260117", "ander.turno", rerank=False)
    assert "EVAL-SGOIE-01" not in {h.doc_id for h in planta}


def test_diversification_caps_chunks_per_document(conn, app, rag_settings):
    q = "registro cambio boquilla tubo de contacto CR-01 turno noche"
    raw = _run(app, rag_settings, q, "ander.turno", k=20, rerank=False,
               max_per_doc=0, candidates_per_doc=0)
    assert Counter(h.doc_id for h in raw)["REG-L2-CR01-01"] > 3  # el REG monopoliza sin tope
    for rerank in (True, False):
        for cap in (1, 2, 3):
            hits = _run(app, rag_settings, q, "ander.turno", k=20, rerank=rerank,
                        max_per_doc=cap)
            counts = Counter(h.doc_id for h in hits)
            assert max(counts.values()) <= cap, counts
            assert len(counts) >= min(4, len(hits))
    ranks = [h.rank for h in hits]
    assert ranks == list(range(1, len(hits) + 1))


def test_filters_narrow_but_never_widen(conn, app, rag_settings):
    q = "grietas soldadura AR-1003 root cause"
    for f in ({"folder": "calidad/8d"}, {"doc_type": "8d"}, {"folder": "compras"},
              {"folder": "direccion/confidencial"}):
        assert _run(app, rag_settings, q, "ander.turno", filters=f) == [], f
    assert _run(app, rag_settings, q, "inaki.calidad", filters={"folder": "direccion"}) == []
    hits = _run(app, rag_settings, q, "inaki.calidad", k=20, filters={"doc_type": "8d"})
    assert hits and {h.doc_type for h in hits} == {"8d"}
    hits = _run(app, rag_settings, "rebaba agujero anclaje", "inaki.calidad", k=20,
                filters={"part_refs": ["AR-1007"]})
    refs = dict(conn.execute("SELECT doc_id, part_refs FROM rag.documents").fetchall())
    assert hits and all("AR-1007" in refs[h.doc_id] for h in hits)
    hits = _run(app, rag_settings, q, "inaki.calidad", k=20, filters={"folder": "calidad"})
    assert hits and all(h.folder.startswith("calidad/") for h in hits)


def test_scores_and_rerank_flag(conn, app, rag_settings):
    q = "Soldadura MIG robotizada en la célula CR-01"
    on = _run(app, rag_settings, q, "inaki.calidad")
    assert on and all(h.rerank is not None for h in on)
    assert all(h.fusion > 0 and (h.bm25 is not None or h.vector is not None) for h in on)
    assert [h.rerank for h in on] == sorted((h.rerank for h in on), reverse=True)
    off = _run(app, rag_settings, q, "inaki.calidad", rerank=False)
    assert off and all(h.rerank is None for h in off)
    none_backend = rag_settings.model_copy(update={"rerank_backend": "none"})
    assert all(h.rerank is None for h in _run(app, none_backend, q, "inaki.calidad"))
    h = on[0]
    assert h.citation() == {"doc_id": h.doc_id, "version": h.version, "locator": h.locator}
    assert h.title and h.content and h.locator


def test_retrieval_is_audited(conn, app, rag_settings, audit_settings):
    from solaris.audit import connect_reader

    tag = uuid.uuid4().hex[:12]
    q = f"boquilla CR-01 {tag}"
    hits = _run(app, rag_settings, q, "inaki.calidad", k=5)
    retrieve(f"x {tag}", "intruso", conn=app, settings=rag_settings)
    with connect_reader(audit_settings) as c:
        rows = c.execute(
            "SELECT actor_user, actor_role, payload FROM audit.events"
            " WHERE event_type = 'retrieval' AND payload->'query'->>'excerpt' LIKE %s"
            " ORDER BY id",
            (f"%{tag}%",),
        ).fetchall()
    assert len(rows) == 2
    (u1, r1, p1), (u2, r2, p2) = rows
    assert (u1, r1) == ("inaki.calidad", "calidad")
    assert len(p1["query"]["sha256"]) == 64 and p1["query"]["chars"] == len(q)
    assert [s["doc_id"] for s in p1["sources"]] == [h.doc_id for h in hits]
    assert [s["locator"] for s in p1["sources"]] == [h.locator for h in hits]
    assert "denied" not in p1 and "total" in p1["latency_ms"]
    # Nunca el contenido de los chunks en el audit.
    blob = json.dumps(p1, ensure_ascii=False)
    assert all(h.content[:80] not in blob for h in hits)
    assert (u2, r2, p2["denied"], p2["sources"]) == ("intruso", None, "unknown_user", [])


# --- On-behalf-of y mínimo privilegio (M4-T1) --------------------------------------------------


def test_sql_only_uses_visible_functions():
    """Ninguna consulta del módulo lee una tabla de rag directamente (PAT-005)."""
    from solaris.rag import retrieve as mod

    for name in ("_SQL_LEX", "_SQL_VEC", "_SQL_DETAIL", "_SQL_DOCREF", "_SQL_EXPAND"):
        sql = getattr(mod, name)
        assert not re.search(r"rag\.(chunks|documents|fmea_rows|folder_acl)\b", sql), name
        assert "rag.visible_chunks(" in sql and "rag.visible_documents(" in sql, name


def test_retrieve_as_requires_principal_and_uses_its_identity(conn, app, rag_settings):
    from solaris.auth.core import Principal
    from solaris.rag.retrieve import retrieve_as

    with pytest.raises(TypeError):
        retrieve_as("jon.it", "x", conn=app, settings=rag_settings)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        retrieve_as(Principal("ander.turno", "planta", "s"), "x", user="jon.it", conn=app,
                    settings=rag_settings)
    tr = RetrievalTrace(user="", role=None)
    hits = retrieve_as(Principal("ander.turno", "planta", "s"), LITERAL_QUERIES[0], k=20,
                       conn=app, settings=rag_settings, trace=tr)
    assert tr.user == "ander.turno" and tr.role == "planta"
    assert hits and not any(h.folder.startswith(PLANTA_FORBIDDEN) for h in hits)
    # Un Principal con rol "admin" falsificado en memoria no amplía nada: el rol sale de acl.json.
    tr2 = RetrievalTrace(user="", role=None)
    retrieve_as(Principal("ander.turno", "admin", "s"), "coste dirección confidencial",
                conn=app, settings=rag_settings, trace=tr2)
    assert tr2.role == "planta"


# --- M2-T7: referencia a documento, expansión D4 y consultas alternativas ---------------------


def _h(doc, sec, cid, doc_type="8d"):
    return Hit(doc_id=doc, version="v1", title=doc, locator={"section": sec}, folder="calidad/8d",
               content="x", doc_type=doc_type, chunk_id=cid)


def test_doc_ref_codes():
    assert doc_ref_codes("¿Causa raíz del 8d-arga-2025-011 y del AR-1003?") == [
        "8D-ARGA-2025-011", "AR-1003"]
    assert doc_ref_codes("boquilla cada 8 h") == []


def test_expand_sections_adds_d4_after_best_hit_without_growing_k():
    a2, ah, b4 = _h("A", "D2", 1), _h("A", "header", 2), _h("B", "D4", 3)
    it = _h("IT", "3. Método", 4, doc_type="it")
    top = [a2, it, ah, b4]
    extra = {"A": [_h("A", "D4", 10), _h("A", "D4", 11)], "B": [b4]}
    cfg = RetrieveConfig(expand_parts=1)
    out = expand_sections(top, extra, cfg, k=4)
    # A: se conserva su mejor chunk y se añade la ÚLTIMA parte de su D4 (retira la cabecera)
    assert [(h.doc_id, h.chunk_id) for h in out] == [("A", 1), ("A", 11), ("IT", 4), ("B", 3)]
    assert out[1].via == "expand" and out[0].via == "search"
    # B ya tenía D4: no se toca. Sin expansión (tupla vacía) el top no cambia.
    assert expand_sections(top, extra, RetrieveConfig(expand_sections=()), 4) == top
    ins = expand_sections(top, extra, RetrieveConfig(expand_parts=2, expand_replace=False), 8)
    assert [h.chunk_id for h in ins] == [1, 4, 2, 10, 11, 3]
    assert len(expand_sections(top, extra, RetrieveConfig(expand_parts=2), 3)) == 3


def test_named_document_goes_first_and_respects_acl(conn, app, rag_settings):
    q = "¿Cuál fue la causa raíz del 8D-ARGA-2025-011?"
    hits = _run(app, rag_settings, q, "inaki.calidad")
    assert hits[0].doc_id == "8D-ARGA-2025-011" and hits[0].via == "doc_ref"
    off = _run(app, rag_settings, q, "inaki.calidad", doc_ref=False)
    assert all(h.via != "doc_ref" for h in off)
    # Nombrar un documento no visible no lo trae (la referencia pasa por rag.visible_*).
    for user in ("ander.turno",):
        got = _run(app, rag_settings, q, user, k=20, max_per_doc=0)
        assert not any(h.folder.startswith(PLANTA_FORBIDDEN) for h in got)
    cost = _run(app, rag_settings, "Datos de COST-DIR-01", "inaki.calidad", k=20)
    assert "COST-DIR-01" not in {h.doc_id for h in cost}


def test_8d_hits_are_expanded_with_their_d4(conn, app, rag_settings):
    q = "8D grietas soldadura AR-1003"
    hits = _run(app, rag_settings, q, "inaki.calidad", k=8)
    by_doc: dict[str, set] = {}
    for h in hits:
        if h.doc_type == "8d":
            by_doc.setdefault(h.doc_id, set()).add(h.locator.get("section"))
    expanded = [h for h in hits if h.via == "expand"]
    assert expanded and all(h.locator.get("section") == "D4" for h in expanded)
    assert len(hits) <= 8 and [h.rank for h in hits] == list(range(1, len(hits) + 1))
    # Planta nunca recibe 8D, tampoco por expansión.
    planta = _run(app, rag_settings, q, "ander.turno", k=8)
    assert not any(h.folder.startswith(PLANTA_FORBIDDEN) for h in planta)


def test_alt_queries_add_candidates_but_never_widen_acl(conn, app, rag_settings):
    q = "tuercas soldadas que giran"
    alt = "weld nut spins at torque"
    tr = RetrievalTrace("", None)
    calls = []

    def later():
        calls.append(1)
        return [alt, "", q]  # vacías y la propia consulta se ignoran

    both = retrieve(q, "inaki.calidad", 20, config=RetrieveConfig(max_per_doc=0), conn=app,
                    settings=rag_settings, trace=tr, alt_queries=later)
    assert calls == [1] and tr.alt_queries == [alt]
    only = _run(app, rag_settings, q, "inaki.calidad", k=20, max_per_doc=0)
    assert {h.chunk_id for h in both} != {h.chunk_id for h in only}
    planta = retrieve(q, "ander.turno", 20, conn=app, settings=rag_settings,
                      alt_queries=[alt, "8D weld nut A/C compressor bracket AR-1006"])
    assert not any(h.folder.startswith(PLANTA_FORBIDDEN) for h in planta)
