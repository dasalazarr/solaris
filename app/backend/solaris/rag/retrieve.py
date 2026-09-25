"""Recuperación híbrida con ACL en SQL, fusión RRF, diversificación y rerank (M2-T5, F02).

    from solaris.rag.retrieve import retrieve
    hits = retrieve("8D de grietas en la soldadura de AR-1003", user="inaki.calidad", k=8)

Uso (diagnóstico, desde app/backend):
    uv run python -m solaris.rag.retrieve "<consulta>" --user inaki.calidad [-k 8] [--no-rerank]
        [--doc-type 8d] [--part-ref AR-1003] [--folder calidad/8d] [--max-per-doc 2] [--json]

Flujo:
  1. **Rol** = `acl.json` (users → role) a partir de `user` (solaris.rag.acl.resolve_role). Nunca
     un parámetro libre ni la salida del LLM (PAT-005). Usuario desconocido → [] y evento de audit.
  2. **ACL en SQL antes del ranking:** las dos ramas leen de `rag.visible_chunks(role)` (inline:
     el EXISTS sobre folder_acl va en el mismo WHERE que el ORDER BY/LIMIT). `filters` solo añade
     condiciones AND dentro de lo visible: nunca amplía la visibilidad.
  3. **Léxica:** tsvector `simple` + `websearch_to_tsquery` con los términos en OR. Los códigos
     (AR-1003, S-GOIE-260117, MT-07) van entre comillas → consulta de frase exacta.
     **Vectorial:** e5-large con prefijo "query: ", coseno (HNSW con `iterative_scan`).
  4. **RRF:** fusión = Σ 1/(rrf_k + rank) de cada rama (solo rangos: no mezcla escalas).
  5. **Diversificación:** penalización opcional por tamaño del documento (fusión × n_chunks^-β),
     tope por documento en el pool del rerank (`pool_per_doc`) y en el top-k (`max_per_doc`). Así el
     registro de boquillas REG-L2-CR01-01 (94 de 340 chunks) no monopoliza el resultado.
  6. **Rerank:** cross-encoder local (solaris.rag.rerank) sobre el pool; se puede desactivar.
  7. **Audit:** evento `retrieval` con usuario, rol, consulta resumida según AUDIT_PROMPT_MODE
     (sha256 + extracto o solo hash) y los doc_id/versión/locator devueltos (nunca el contenido).

On-behalf-of (M4-T1, F09): los endpoints llaman a `retrieve_as(principal, ...)` con el usuario de
`current_user()` (JWT verificado); nunca pasan un `user` recibido en la petición.
`retrieve(user=...)` queda como API interna (CLI de diagnóstico del operador, evals) y no se
expone por HTTP.
Conexión en runtime como `solaris_app` (PAT-005): sin SELECT sobre rag.*, solo EXECUTE sobre
`rag.visible_chunks/visible_documents` (SECURITY DEFINER). Ninguna consulta de este módulo lee una
tabla de `rag` directamente (test_rag_retrieve::test_sql_only_uses_visible_functions).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING, Any

import psycopg

from solaris.audit import Actor, record_safe, summarize_text
from solaris.rag.acl import DEFAULT_ACL_FILE, resolve_role
from solaris.rag.embed import embed_query, to_pgvector
from solaris.rag.locator import loc_label as _loc_label
from solaris.rag.rerank import rerank

if TYPE_CHECKING:
    from solaris.auth.core import Principal
from solaris.settings import Settings, get_settings

MAX_QUERY_CHARS = 2000
MAX_K = 50
MAX_SCAN = 10_000
_TERM_RE = re.compile(r"\w+(?:-\w+)*", re.UNICODE)
_FOLDER_RE = re.compile(r"^[a-z0-9_-]+(/[a-z0-9_-]+)*$")
_SIMPLE_RE = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")
FILTER_KEYS = frozenset({"doc_type", "part_refs", "folder"})
# Palabras vacías ES/EN: la configuración `simple` no las quita y, en OR, solo meten ruido.
_STOPWORDS_TXT = """\
    a al algo como con cual cuales cuando cuanto cuánto cuánta cada de del desde donde el
    ella en entre era es esa ese eso esta este esto está están fue ha han hay la las le les lo
    los más mas me mi muy no nos o para pero por que qué quien quién se ser si sí sin sobre son
    su sus tiene un una uno unos unas y ya
    an and are as at be by can did do does for from has have how in is it its of on or that the
    their this to was were what when where which who why will with"""
STOPWORDS = frozenset(_STOPWORDS_TXT.split())


class RetrievalError(ValueError):
    pass


@dataclass(frozen=True)
class RetrieveConfig:
    """Parámetros del ranking. Los valores por defecto salen de las consultas reales de M2-T5."""

    n_lexical: int = 50  # candidatos de la rama léxica
    n_vector: int = 50  # candidatos de la rama vectorial
    scan: int = 400  # filas que ordena el índice antes del tope por documento
    candidates_per_doc: int = 5  # tope por documento en cada rama (0 = sin tope)
    rrf_k: int = 60  # constante de RRF (Cormack et al. 2009)
    w_lexical: float = 1.0
    w_vector: float = 1.0
    doc_size_penalty: float = 0.0  # β: fusión × n_chunks_doc^-β (0 = sin penalización)
    pool_per_doc: int = 3  # tope por documento en el pool del rerank
    rerank_pool: int = 12  # candidatos que ve el cross-encoder (24 → ~2,9 s; 12 → ~1,6 s en CPU)
    max_per_doc: int = 2  # tope por documento en el top-k final (0 = sin tope)
    rerank: bool = True  # False = solo fusión RRF (también si RERANK_BACKEND=none)
    rerank_max_chars: int = 1500


DEFAULT_CONFIG = RetrieveConfig()


@dataclass
class Hit:
    doc_id: str
    version: str
    title: str
    locator: dict[str, Any]
    folder: str
    content: str
    doc_type: str
    chunk_id: int
    rank: int = 0
    bm25: float | None = None  # ts_rank_cd (None si no salió en la rama léxica)
    vector: float | None = None  # similitud coseno (None si no salió en la rama vectorial)
    fusion: float = 0.0  # RRF (tras la penalización por tamaño, si la hay)
    rerank: float | None = None  # logit del cross-encoder (None sin rerank)
    lexical_rank: int | None = None
    vector_rank: int | None = None
    doc_chunks: int = 0

    def citation(self) -> dict[str, Any]:
        return {"doc_id": self.doc_id, "version": self.version, "locator": self.locator}


@dataclass
class RetrievalTrace:
    """Detalle de la última recuperación (diagnóstico y evals, M2-T7)."""

    user: str
    role: str | None
    timings_ms: dict[str, float] = field(default_factory=dict)
    candidates: int = 0
    reranked: bool = False


# --- consulta léxica ----------------------------------------------------------------------------


def lexical_query(query: str, max_terms: int = 32) -> str:
    """Cadena para `websearch_to_tsquery('simple', ...)`: términos en OR, códigos como frase.

    Solo salen tokens `\\w+(-\\w+)*` (sin comillas ni operadores del usuario), así que la consulta
    no puede inyectar sintaxis; websearch_to_tsquery además nunca lanza errores de sintaxis.
    """
    terms: list[str] = []
    for tok in _TERM_RE.findall(query):
        t = tok.lower()
        is_code = "-" in t or any(ch.isdigit() for ch in t)
        if not is_code and (len(t) < 3 or t in STOPWORDS):
            continue
        if t not in terms:
            terms.append(t)
        if len(terms) >= max_terms:
            break
    return " or ".join(f'"{t}"' for t in terms)


# --- filtros ------------------------------------------------------------------------------------


def _as_list(v: Any, key: str) -> list[str]:
    items = [v] if isinstance(v, str) else v
    if not isinstance(items, list | tuple) or not items or len(items) > 20:
        raise RetrievalError(f"filtro {key!r}: se espera un texto o una lista (1–20)")
    if not all(isinstance(x, str) for x in items):
        raise RetrievalError(f"filtro {key!r}: solo textos")
    return list(items)


def build_filters(filters: dict[str, Any] | None) -> tuple[str, dict[str, Any]]:
    """Fragmento SQL fijo (solo AND) + parámetros. Claves o valores inválidos → RetrievalError."""
    if not filters:
        return "", {}
    unknown = set(filters) - FILTER_KEYS
    if unknown:
        raise RetrievalError(f"filtros desconocidos: {sorted(unknown)}")
    sql: list[str] = []
    params: dict[str, Any] = {}
    if filters.get("doc_type") is not None:
        vals = [x.lower() for x in _as_list(filters["doc_type"], "doc_type")]
        if not all(_SIMPLE_RE.match(x) for x in vals):
            raise RetrievalError("filtro 'doc_type' no válido")
        sql.append("d.doc_type = ANY(%(f_doc_type)s::text[])")
        params["f_doc_type"] = vals
    if filters.get("part_refs") is not None:
        vals = [x.upper() for x in _as_list(filters["part_refs"], "part_refs")]
        if not all(_SIMPLE_RE.match(x) for x in vals):
            raise RetrievalError("filtro 'part_refs' no válido")
        sql.append("d.part_refs && %(f_part_refs)s::text[]")
        params["f_part_refs"] = vals
    if filters.get("folder") is not None:
        vals = [x.strip("/") for x in _as_list(filters["folder"], "folder")]
        if not all(_FOLDER_RE.match(x) for x in vals):
            raise RetrievalError("filtro 'folder' no válido")
        # Carpeta exacta o subcarpeta (prefijo con '/'); sin LIKE, para no tratar '_' como comodín.
        sql.append(
            "EXISTS (SELECT 1 FROM unnest(%(f_folder)s::text[]) f"
            " WHERE c.folder = f OR starts_with(c.folder, f || '/'))"
        )
        params["f_folder"] = vals
    return "".join(f" AND {s}" for s in sql), params


# --- SQL ----------------------------------------------------------------------------------------
# Todas las lecturas pasan por rag.visible_chunks(role): la ACL va en el mismo WHERE que el
# ranking (PAT-005). `{f}` solo recibe fragmentos fijos de build_filters() (valores parametrizados).

# Diversificación ya en la generación de candidatos: el subquery interno ordena con el índice
# (GIN / HNSW) y corta en `scan`; fuera, row_number() por documento deja como mucho `per_doc`
# chunks de cada uno antes del LIMIT final. Sin esto, con "boquilla CR-01" los 50+50 candidatos
# de las dos ramas eran TODOS del registro REG-L2-CR01-01 (94 chunks casi iguales).
_SQL_LEX = (
    "SELECT id, s FROM (SELECT id, s, row_number() OVER (PARTITION BY doc_id"
    " ORDER BY s DESC, id) AS rn FROM (SELECT c.id, c.doc_id, ts_rank_cd(c.tsv, q.tsq, 1) AS s "
    "FROM rag.visible_chunks(%(role)s) c"
    " JOIN rag.visible_documents(%(role)s) d ON d.doc_id = c.doc_id AND d.version = c.version"
    " CROSS JOIN websearch_to_tsquery('simple', %(lexq)s) AS q(tsq)"
    " WHERE c.tsv @@ q.tsq{f} ORDER BY s DESC, c.id LIMIT %(scan)s) i) t"
    " WHERE rn <= %(per_doc)s ORDER BY s DESC, id LIMIT %(n)s"
)
_SQL_VEC = (
    "SELECT id, s FROM (SELECT id, s, row_number() OVER (PARTITION BY doc_id"
    " ORDER BY s DESC, id) AS rn FROM (SELECT c.id, c.doc_id,"
    " 1 - (c.embedding <=> %(qvec)s::vector) AS s "
    "FROM rag.visible_chunks(%(role)s) c"
    " JOIN rag.visible_documents(%(role)s) d ON d.doc_id = c.doc_id AND d.version = c.version"
    " WHERE c.embedding IS NOT NULL{f}"
    " ORDER BY c.embedding <=> %(qvec)s::vector, c.id LIMIT %(scan)s) i) t"
    " WHERE rn <= %(per_doc)s ORDER BY s DESC, id LIMIT %(n)s"
)
# El recuento de chunks por documento se hace sobre lo visible: la ACL es por carpeta y todos los
# chunks de un documento comparten carpeta, así que coincide con el total del documento.
_SQL_DETAIL = (
    "WITH v AS MATERIALIZED (SELECT id, doc_id, version, locator, folder, content"
    " FROM rag.visible_chunks(%(role)s)),"
    " n AS (SELECT doc_id, version, count(*) AS n FROM v GROUP BY doc_id, version) "
    "SELECT c.id, c.doc_id, c.version, d.title, c.locator, c.folder, c.content, d.doc_type, n.n "
    "FROM v c"
    " JOIN rag.visible_documents(%(role)s) d ON d.doc_id = c.doc_id AND d.version = c.version"
    " JOIN n ON n.doc_id = c.doc_id AND n.version = c.version"
    " WHERE c.id = ANY(%(ids)s::bigint[])"
)


def _cap_per_doc(hits: list[Hit], cap: int, limit: int) -> list[Hit]:
    if cap <= 0:
        return hits[:limit]
    seen: dict[str, int] = {}
    out: list[Hit] = []
    for h in hits:
        if seen.get(h.doc_id, 0) >= cap:
            continue
        seen[h.doc_id] = seen.get(h.doc_id, 0) + 1
        out.append(h)
        if len(out) >= limit:
            break
    return out


def _rerank_text(h: Hit, max_chars: int) -> str:
    return f"{h.title}\n{_loc_label(h.locator)}\n{h.content[:max_chars]}"


def _audit(
    user: str, role: str | None, query: str, k: int, filters: dict[str, Any] | None,
    hits: list[Hit], trace: RetrievalTrace, s: Settings, denied: str | None = None,
) -> None:
    payload: dict[str, Any] = {
        "query": summarize_text(query, s),  # sha256 + extracto (truncate) o solo hash (hash)
        "k": k,
        "filters": filters or {},
        "reranked": trace.reranked,
        "rerank_model": s.rerank_model if trace.reranked else None,
        "candidates": trace.candidates,
        "latency_ms": trace.timings_ms,
        "sources": [
            {"rank": h.rank, "doc_id": h.doc_id, "version": h.version,
             "locator": h.locator, "folder": h.folder}
            for h in hits
        ],
    }
    if denied:
        payload["denied"] = denied
    record_safe("retrieval", Actor(user, role), payload, settings=s)


def retrieve(
    query: str,
    user: str,
    k: int = 8,
    filters: dict[str, Any] | None = None,
    *,
    config: RetrieveConfig = DEFAULT_CONFIG,
    conn: psycopg.Connection | None = None,
    settings: Settings | None = None,
    acl_file=DEFAULT_ACL_FILE,
    trace: RetrievalTrace | None = None,
) -> list[Hit]:
    """Top-k de chunks visibles para `user`, citables con `{doc_id, version, locator}`."""
    s = settings or get_settings()
    t0 = time.perf_counter()
    tr = trace if trace is not None else RetrievalTrace(user=str(user)[:200], role=None)
    tr.user = str(user)[:200]
    if not isinstance(query, str):
        raise RetrievalError("la consulta debe ser texto")
    query = query.strip()[:MAX_QUERY_CHARS]
    k = max(1, min(int(k), MAX_K))
    where, fparams = build_filters(filters)  # antes de tocar la BD: filtros inválidos → error

    role = resolve_role(user, acl_file) if isinstance(user, str) else None
    tr.role = role
    if role is None:
        tr.timings_ms["total"] = round((time.perf_counter() - t0) * 1000, 1)
        _audit(tr.user, None, query, k, filters, [], tr, s, denied="unknown_user")
        return []
    if not query:
        tr.timings_ms["total"] = round((time.perf_counter() - t0) * 1000, 1)
        _audit(tr.user, role, query, k, filters, [], tr, s, denied="empty_query")
        return []

    t = time.perf_counter()
    qvec = to_pgvector(embed_query(query, settings=s))
    tr.timings_ms["embed"] = round((time.perf_counter() - t) * 1000, 1)
    lexq = lexical_query(query)

    t = time.perf_counter()
    own = conn is None
    if own:
        from solaris.db import connect_app

        conn = connect_app(s)  # solaris_app: mínimo privilegio (PAT-005)
    try:
        with conn.transaction(), conn.cursor() as cur:
            # pgvector ≥0.8: si el filtro deja fuera candidatos, el HNSW sigue buscando.
            cur.execute("SET LOCAL hnsw.iterative_scan = strict_order")
            per_doc = config.candidates_per_doc if config.candidates_per_doc > 0 else MAX_SCAN
            base = {"role": role, "scan": max(config.scan, config.n_lexical, config.n_vector),
                    "per_doc": per_doc, **fparams}
            lex: list[tuple[int, float]] = []
            if lexq:
                cur.execute(
                    _SQL_LEX.format(f=where),  # type: ignore[arg-type]  # fragmentos fijos
                    {**base, "lexq": lexq, "n": config.n_lexical},
                )
                lex = [(r[0], float(r[1])) for r in cur.fetchall()]
            cur.execute(
                _SQL_VEC.format(f=where),  # type: ignore[arg-type]  # fragmentos fijos
                {**base, "qvec": qvec, "n": config.n_vector},
            )
            vec = [(r[0], float(r[1])) for r in cur.fetchall()]
            ids = list({i for i, _ in lex} | {i for i, _ in vec})
            rows = []
            if ids:
                cur.execute(_SQL_DETAIL, {"role": role, "ids": ids})
                rows = cur.fetchall()
    finally:
        if own:
            conn.close()
    tr.timings_ms["sql"] = round((time.perf_counter() - t) * 1000, 1)

    # --- fusión RRF + penalización por tamaño ---------------------------------------------------
    hits: dict[int, Hit] = {
        r[0]: Hit(doc_id=r[1], version=r[2], title=r[3], locator=r[4] or {}, folder=r[5],
                  content=r[6], doc_type=r[7], chunk_id=r[0], doc_chunks=int(r[8]))
        for r in rows
    }
    for rank, (cid, score) in enumerate(lex, 1):
        if cid in hits:
            hits[cid].bm25, hits[cid].lexical_rank = score, rank
            hits[cid].fusion += config.w_lexical / (config.rrf_k + rank)
    for rank, (cid, score) in enumerate(vec, 1):
        if cid in hits:
            hits[cid].vector, hits[cid].vector_rank = score, rank
            hits[cid].fusion += config.w_vector / (config.rrf_k + rank)
    if config.doc_size_penalty > 0:
        for h in hits.values():
            h.fusion *= max(h.doc_chunks, 1) ** -config.doc_size_penalty
    fused = sorted(hits.values(), key=lambda h: (-h.fusion, h.chunk_id))
    tr.candidates = len(fused)

    # --- pool diversificado + rerank ------------------------------------------------------------
    use_rerank = config.rerank and s.rerank_backend != "none"
    if use_rerank:
        pool = _cap_per_doc(fused, config.pool_per_doc, max(config.rerank_pool, k))
        t = time.perf_counter()
        scores = rerank(
            query, [_rerank_text(h, config.rerank_max_chars) for h in pool], settings=s
        )
        tr.timings_ms["rerank"] = round((time.perf_counter() - t) * 1000, 1)
        for h, sc in zip(pool, scores, strict=True):
            h.rerank = sc
        ordered = sorted(pool, key=lambda h: (-(h.rerank or 0.0), -h.fusion, h.chunk_id))
        tr.reranked = True
    else:
        ordered = fused
    top = _cap_per_doc(ordered, config.max_per_doc, k)
    for i, h in enumerate(top, 1):
        h.rank = i
    tr.timings_ms["total"] = round((time.perf_counter() - t0) * 1000, 1)
    _audit(tr.user, role, query, k, filters, top, tr, s)
    return top


def retrieve_as(
    principal: Principal,
    query: str,
    k: int = 8,
    filters: dict[str, Any] | None = None,
    **kwargs: Any,
) -> list[Hit]:
    """Punto de entrada para endpoints: la identidad es la del usuario autenticado (on-behalf-of).

    `principal` sale de `solaris.auth.current_user()`. El rol se vuelve a resolver desde acl.json
    dentro de `retrieve()`, así que un Principal obsoleto no conserva un rol retirado.
    """
    from solaris.auth.core import Principal as _Principal

    if not isinstance(principal, _Principal):
        raise TypeError("retrieve_as exige el Principal de current_user()")
    if "user" in kwargs:
        raise TypeError("retrieve_as no acepta `user`: la identidad es la del Principal")
    s = kwargs.get("settings") or get_settings()
    kwargs.setdefault("acl_file", s.acl_file)
    return retrieve(query, principal.user, k, filters, **kwargs)


# --- CLI de diagnóstico -------------------------------------------------------------------------


def _fmt(v: float | None, spec: str = ".3f") -> str:
    return "—" if v is None else format(v, spec)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m solaris.rag.retrieve", description=__doc__.split(
        "\n")[0])
    p.add_argument("query")
    p.add_argument("--user", required=True, help="usuario de acl.json (el rol sale de ahí)")
    p.add_argument("-k", type=int, default=8)
    p.add_argument("--no-rerank", action="store_true")
    p.add_argument("--max-per-doc", type=int, default=DEFAULT_CONFIG.max_per_doc)
    p.add_argument("--doc-size-penalty", type=float, default=DEFAULT_CONFIG.doc_size_penalty)
    p.add_argument("--doc-type", action="append")
    p.add_argument("--part-ref", action="append")
    p.add_argument("--folder", action="append")
    p.add_argument("--json", action="store_true", help="salida JSON (sin contenido completo)")
    a = p.parse_args(argv)

    filters = {k: v for k, v in (("doc_type", a.doc_type), ("part_refs", a.part_ref),
                                 ("folder", a.folder)) if v}
    cfg = RetrieveConfig(rerank=not a.no_rerank, max_per_doc=a.max_per_doc,
                         doc_size_penalty=a.doc_size_penalty)
    tr = RetrievalTrace(user=a.user, role=None)
    hits = retrieve(a.query, a.user, a.k, filters or None, config=cfg, trace=tr)
    if a.json:
        out = [{**asdict(h), "content": h.content[:200]} for h in hits]
        print(json.dumps({"role": tr.role, "timings_ms": tr.timings_ms, "hits": out},
                         ensure_ascii=False, indent=1))
        return 0
    print(f"usuario={a.user} rol={tr.role} candidatos={tr.candidates} rerank={tr.reranked} "
          f"latencia_ms={tr.timings_ms}")
    if tr.role is None:
        print("Usuario desconocido: sin resultados.")
    for h in hits:
        snippet = " ".join(h.content.split())[:110]
        print(f"{h.rank:>2}. {h.doc_id} {h.version} [{_loc_label(h.locator)}] {h.folder}\n"
              f"    bm25={_fmt(h.bm25)} (r{h.lexical_rank or '—'}) vec={_fmt(h.vector)} "
              f"(r{h.vector_rank or '—'}) rrf={_fmt(h.fusion, '.4f')} "
              f"rerank={_fmt(h.rerank, '.2f')}\n    {snippet}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
