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
    RetrievalError,
    RetrievalTrace,
    RetrieveConfig,
    build_filters,
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


def _run(conn, s, query, user, k=8, filters=None, **cfg):
    return retrieve(query, user, k, filters, config=RetrieveConfig(**cfg), conn=conn, settings=s)


def test_planta_never_gets_forbidden_folders(conn, rag_settings):
    for q in LITERAL_QUERIES:
        for rerank in (True, False):
            hits = _run(conn, rag_settings, q, "ander.turno", k=50, rerank=rerank,
                        max_per_doc=0, candidates_per_doc=0)
            assert hits, q  # ve instrucciones, planes de control y mantenimiento
            bad = [h for h in hits if h.folder.startswith(PLANTA_FORBIDDEN)]
            assert bad == [], (q, [(h.doc_id, h.folder) for h in bad])
    allowed = {f for f, roles in ACL["folders"].items() if "planta" in roles}
    hits = _run(conn, rag_settings, " ".join(LITERAL_QUERIES), "ander.turno", k=50,
                max_per_doc=0, candidates_per_doc=0)
    assert {h.folder for h in hits} <= allowed


def test_calidad_never_gets_direccion_confidencial(conn, rag_settings):
    content = conn.execute(
        "SELECT content FROM rag.chunks WHERE doc_id = 'COST-DIR-01' ORDER BY chunk_no LIMIT 1"
    ).fetchone()[0]
    q = content[:300]
    admin = _run(conn, rag_settings, q, "jon.it", rerank=False)
    assert admin[0].doc_id == "COST-DIR-01"  # control positivo: el documento sí se recupera
    for rerank in (True, False):
        hits = _run(conn, rag_settings, q, "inaki.calidad", k=50, rerank=rerank,
                    max_per_doc=0, candidates_per_doc=0)
        assert all(not h.folder.startswith("direccion/") for h in hits)
        assert "COST-DIR-01" not in {h.doc_id for h in hits}


@pytest.mark.parametrize("user", ["nadie", "", "calidad", "admin", "inaki.calidad' OR '1'='1"])
def test_unknown_user_gets_nothing(conn, rag_settings, user):
    tr = RetrievalTrace(user, None)
    hits = retrieve("8D grietas AR-1003", user, conn=conn, settings=rag_settings, trace=tr)
    assert hits == [] and tr.role is None


def test_exact_code_found_by_lexical_branch(conn, rag_settings):
    hits = _run(conn, rag_settings, "S-GOIE-260117", "inaki.calidad", rerank=False)
    assert hits and hits[0].doc_id == "EVAL-SGOIE-01"
    assert hits[0].bm25 is not None and hits[0].lexical_rank == 1
    # El código exacto aparece en el chunk devuelto.
    assert "S-GOIE-260117" in hits[0].content
    # Planta no ve compras/: el mismo código no le devuelve la evaluación.
    planta = _run(conn, rag_settings, "S-GOIE-260117", "ander.turno", rerank=False)
    assert "EVAL-SGOIE-01" not in {h.doc_id for h in planta}


def test_diversification_caps_chunks_per_document(conn, rag_settings):
    q = "registro cambio boquilla tubo de contacto CR-01 turno noche"
    raw = _run(conn, rag_settings, q, "ander.turno", k=20, rerank=False,
               max_per_doc=0, candidates_per_doc=0)
    assert Counter(h.doc_id for h in raw)["REG-L2-CR01-01"] > 3  # el REG monopoliza sin tope
    for rerank in (True, False):
        for cap in (1, 2, 3):
            hits = _run(conn, rag_settings, q, "ander.turno", k=20, rerank=rerank,
                        max_per_doc=cap)
            counts = Counter(h.doc_id for h in hits)
            assert max(counts.values()) <= cap, counts
            assert len(counts) >= min(4, len(hits))
    ranks = [h.rank for h in hits]
    assert ranks == list(range(1, len(hits) + 1))


def test_filters_narrow_but_never_widen(conn, rag_settings):
    q = "grietas soldadura AR-1003 root cause"
    for f in ({"folder": "calidad/8d"}, {"doc_type": "8d"}, {"folder": "compras"},
              {"folder": "direccion/confidencial"}):
        assert _run(conn, rag_settings, q, "ander.turno", filters=f) == [], f
    assert _run(conn, rag_settings, q, "inaki.calidad", filters={"folder": "direccion"}) == []
    hits = _run(conn, rag_settings, q, "inaki.calidad", k=20, filters={"doc_type": "8d"})
    assert hits and {h.doc_type for h in hits} == {"8d"}
    hits = _run(conn, rag_settings, "rebaba agujero anclaje", "inaki.calidad", k=20,
                filters={"part_refs": ["AR-1007"]})
    refs = dict(conn.execute("SELECT doc_id, part_refs FROM rag.documents").fetchall())
    assert hits and all("AR-1007" in refs[h.doc_id] for h in hits)
    hits = _run(conn, rag_settings, q, "inaki.calidad", k=20, filters={"folder": "calidad"})
    assert hits and all(h.folder.startswith("calidad/") for h in hits)


def test_scores_and_rerank_flag(conn, rag_settings):
    q = "Soldadura MIG robotizada en la célula CR-01"
    on = _run(conn, rag_settings, q, "inaki.calidad")
    assert on and all(h.rerank is not None for h in on)
    assert all(h.fusion > 0 and (h.bm25 is not None or h.vector is not None) for h in on)
    assert [h.rerank for h in on] == sorted((h.rerank for h in on), reverse=True)
    off = _run(conn, rag_settings, q, "inaki.calidad", rerank=False)
    assert off and all(h.rerank is None for h in off)
    none_backend = rag_settings.model_copy(update={"rerank_backend": "none"})
    assert all(h.rerank is None for h in _run(conn, none_backend, q, "inaki.calidad"))
    h = on[0]
    assert h.citation() == {"doc_id": h.doc_id, "version": h.version, "locator": h.locator}
    assert h.title and h.content and h.locator


def test_retrieval_is_audited(conn, rag_settings, audit_settings):
    from solaris.audit import connect_reader

    tag = uuid.uuid4().hex[:12]
    q = f"boquilla CR-01 {tag}"
    hits = _run(conn, rag_settings, q, "inaki.calidad", k=5)
    retrieve(f"x {tag}", "intruso", conn=conn, settings=rag_settings)
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
