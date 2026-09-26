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
from collections.abc import Callable, Sequence
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
MAX_ALT_QUERIES = 2
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
    # M2-T7 · Referencia explícita a un documento: si la consulta nombra un doc_id visible
    # ("causa raíz del 8D-ARGA-2025-011"), sus chunks entran en el pool del rerank (como mucho
    # `doc_ref_pool` por documento) y, con `doc_ref_first`, van por delante en el top-k.
    doc_ref: bool = True
    doc_ref_pool: int = 6
    doc_ref_first: bool = True
    # M2-T7 · Expansión por sección: cuando un documento de `expand_doc_types` entra en el top-k
    # sin ninguna de `expand_sections`, se añaden esas secciones (con su locator) justo detrás de
    # su mejor chunk. Para los 8D, la D4 (causa raíz) es lo que piden las preguntas de antecedentes.
    # Como mucho `expand_max_docs` documentos y `expand_parts` partes por sección (las últimas
    # primero: en el 8D la conclusión de la causa raíz va al final de la D4). El top-k no crece.
    expand_sections: tuple[str, ...] = ("D4",)
    expand_doc_types: tuple[str, ...] = ("8d",)
    expand_max_docs: int = 3
    expand_parts: int = 2
    # True: el documento expandido conserva su mejor chunk + la sección añadida (se retiran sus
    # otros chunks, p. ej. cabecera o D2), para no desplazar a otros documentos del top-k.
    expand_replace: bool = True
    # M2-T7 · Consultas alternativas (traducción): peso de sus listas en la fusión RRF.
    w_alt: float = 1.0


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
    via: str = "search"  # search | doc_ref (documento nombrado en la consulta) | expand (sección)

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
    alt_queries: list[str] = field(default_factory=list)  # consultas alternativas usadas
    translate_status: str | None = None  # recuperación cruzada: ok | empty | timeout | error


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


# Documentos nombrados en la consulta (comparación exacta del doc_id, sin LIKE) y secciones de
# expansión: mismas funciones visible_* y mismos filtros `{f}` que las ramas de búsqueda.
_SQL_DOCREF = (
    "SELECT c.id FROM rag.visible_chunks(%(role)s) c"
    " JOIN rag.visible_documents(%(role)s) d ON d.doc_id = c.doc_id AND d.version = c.version"
    " WHERE upper(c.doc_id) = ANY(%(codes)s::text[]){f} ORDER BY c.id LIMIT %(n)s"
)
_SQL_EXPAND = (
    "SELECT c.id FROM rag.visible_chunks(%(role)s) c"
    " JOIN rag.visible_documents(%(role)s) d ON d.doc_id = c.doc_id AND d.version = c.version"
    " WHERE c.doc_id = ANY(%(docs)s::text[]) AND d.doc_type = ANY(%(types)s::text[])"
    " AND c.locator->>'section' = ANY(%(secs)s::text[]){f} ORDER BY c.id"
)
_DOCREF_MAX_CHUNKS = 200


def doc_ref_codes(query: str, max_codes: int = 10) -> list[str]:
    """Códigos candidatos a doc_id en la consulta (tokens con guion y dígito), en mayúsculas."""
    out: list[str] = []
    for tok in _TERM_RE.findall(query):
        t = tok.upper()
        if "-" in t and any(ch.isdigit() for ch in t) and len(t) <= 64 and t not in out:
            out.append(t)
        if len(out) >= max_codes:
            break
    return out


def _section(h: Hit) -> str | None:
    sec = h.locator.get("section") if isinstance(h.locator, dict) else None
    return sec if isinstance(sec, str) else None


def expand_sections(top: list[Hit], extra: dict[str, list[Hit]], config: RetrieveConfig,
                    k: int) -> list[Hit]:
    """Añade tras el mejor chunk de cada documento expandible sus secciones `expand_sections`
    (de `extra`, en orden de parte) si no están ya en el top. Devuelve como mucho k resultados."""
    if not config.expand_sections or config.expand_max_docs <= 0 or config.expand_parts <= 0:
        return top[:k]
    out = list(top)
    done: set[str] = set()
    for h in top:
        if len(done) >= config.expand_max_docs:
            break
        if h.doc_type not in config.expand_doc_types or h.doc_id in done:
            continue
        doc_hits = [x for x in out if x.doc_id == h.doc_id]
        if any(_section(x) in config.expand_sections for x in doc_hits):
            continue
        have = {x.chunk_id for x in out}
        parts = [x for x in extra.get(h.doc_id, []) if x.chunk_id not in have]
        add = sorted(parts[-config.expand_parts:], key=lambda x: x.chunk_id)
        if not add:
            continue
        if config.expand_replace:
            out = [x for x in out if x.doc_id != h.doc_id or x is h]
            pos = out.index(h) + 1
        else:
            pos = out.index(doc_hits[-1]) + 1
        for a in add:
            a.via = "expand"
        out[pos:pos] = add
        done.add(h.doc_id)
    return out[:k]


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
        "alt_queries": [summarize_text(a, s) for a in trace.alt_queries],
        "sources": [
            {"rank": h.rank, "doc_id": h.doc_id, "version": h.version,
             "locator": h.locator, "folder": h.folder, "via": h.via}
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
    alt_queries: Sequence[str] | Callable[[], Sequence[str]] | None = None,
) -> list[Hit]:
    """Top-k de chunks visibles para `user`, citables con `{doc_id, version, locator}`.

    `alt_queries`: reformulaciones de la misma consulta (p. ej. su traducción, ver
    solaris.rag.crosslingual) que solo aportan candidatos (el audit las registra resumidas). Si es
    un callable, se llama tras puntuar la consulta original (la traducción corre en paralelo)."""
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

    # Consultas alternativas (M2-T7, recuperación cruzada ES↔EN): la traducción de la pregunta
    # genera candidatos en sus propias ramas léxica y vectorial y se fusiona por RRF. No amplía la
    # visibilidad (mismas funciones visible_* y filtros) y no se usa para citar. Si llega como
    # callable, se resuelve DESPUÉS de puntuar los candidatos de la consulta original: la
    # traducción (LLM, E/S) corre en paralelo con el embedding, el SQL y el rerank (CPU).
    use_rerank = config.rerank and s.rerank_backend != "none"
    cand = _Candidates()
    scored: dict[int, float] = {}
    pool: list[Hit] = []
    own = conn is None
    if own:
        from solaris.db import connect_app

        conn = connect_app(s)  # solaris_app: mínimo privilegio (PAT-005)
    try:
        _gather(conn, [query], role, where, fparams, config, s, tr, cand, doc_ref=config.doc_ref)
        if use_rerank:
            pool = _select_pool(cand, config, k)
            _rerank_into(query, pool, scored, config, s, tr)
        t = time.perf_counter()
        raw_alts = alt_queries() if callable(alt_queries) else alt_queries
        if callable(alt_queries):
            tr.timings_ms["alt_wait"] = round((time.perf_counter() - t) * 1000, 1)
        alts: list[str] = []
        for a in raw_alts or ():
            a = a.strip()[:MAX_QUERY_CHARS] if isinstance(a, str) else ""
            if a and a.lower() != query.lower() and a not in alts:
                alts.append(a)
        tr.alt_queries = alts[:MAX_ALT_QUERIES]
        if tr.alt_queries:
            _gather(conn, tr.alt_queries, role, where, fparams, config, s, tr, cand,
                    doc_ref=False)
            if use_rerank:  # mismo pool que en serie; solo se puntúan los candidatos nuevos
                pool = _select_pool(cand, config, k)
                _rerank_into(query, [h for h in pool if h.chunk_id not in scored], scored,
                             config, s, tr)
    finally:
        if own:
            conn.close()

    fused = cand.fused()
    tr.candidates = len(fused)
    if use_rerank:
        ordered = sorted(pool, key=lambda h: (-(h.rerank or 0.0), -h.fusion, h.chunk_id))
        tr.reranked = True
    else:
        ordered = fused
    if cand.named and config.doc_ref_first:  # la referencia explícita manda sobre la similitud
        ordered = [h for h in ordered if h.doc_id in cand.named] + [
            h for h in ordered if h.doc_id not in cand.named]
    top = expand_sections(_cap_per_doc(ordered, config.max_per_doc, k), cand.extra, config, k)
    for i, h in enumerate(top, 1):
        h.rank = i
    tr.timings_ms["total"] = round((time.perf_counter() - t0) * 1000, 1)
    _audit(tr.user, role, query, k, filters, top, tr, s)
    return top


@dataclass
class _Candidates:
    """Candidatos acumulados de una o varias consultas (original + alternativas)."""

    hits: dict[int, Hit] = field(default_factory=dict)
    lex_lists: list[list[tuple[int, float]]] = field(default_factory=list)
    vec_lists: list[list[tuple[int, float]]] = field(default_factory=list)
    named: set[str] = field(default_factory=set)  # doc_id nombrados en la consulta
    extra: dict[str, list[Hit]] = field(default_factory=dict)  # secciones de expansión por doc
    expanded_docs: set[str] = field(default_factory=set)

    def fused(self) -> list[Hit]:
        return sorted(self.hits.values(), key=lambda h: (-h.fusion, h.chunk_id))


def _mk_hit(r: Any) -> Hit:
    return Hit(doc_id=r[1], version=r[2], title=r[3], locator=r[4] or {}, folder=r[5],
               content=r[6], doc_type=r[7], chunk_id=r[0], doc_chunks=int(r[8]))


def _gather(conn: psycopg.Connection, queries: list[str], role: str, where: str,
            fparams: dict[str, Any], config: RetrieveConfig, s: Settings, tr: RetrievalTrace,
            cand: _Candidates, *, doc_ref: bool) -> None:
    """Ramas léxica y vectorial (y referencia a documento) de `queries` → `cand` + fusión."""
    t = time.perf_counter()
    qvecs = [to_pgvector(embed_query(q, settings=s)) for q in queries]
    tr.timings_ms["embed"] = round(tr.timings_ms.get("embed", 0.0)
                                   + (time.perf_counter() - t) * 1000, 1)
    t = time.perf_counter()
    with conn.transaction(), conn.cursor() as cur:
        # pgvector ≥0.8: si el filtro deja fuera candidatos, el HNSW sigue buscando.
        cur.execute("SET LOCAL hnsw.iterative_scan = strict_order")
        per_doc = config.candidates_per_doc if config.candidates_per_doc > 0 else MAX_SCAN
        base = {"role": role, "scan": max(config.scan, config.n_lexical, config.n_vector),
                "per_doc": per_doc, **fparams}
        new_ids: set[int] = set()
        for q, qvec in zip(queries, qvecs, strict=True):
            lexq = lexical_query(q)
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
            cand.lex_lists.append(lex)
            cand.vec_lists.append(vec)
            new_ids |= {i for i, _ in lex} | {i for i, _ in vec}
        ref_ids: list[int] = []
        codes = doc_ref_codes(queries[0]) if doc_ref else []
        if codes:
            cur.execute(
                _SQL_DOCREF.format(f=where),  # type: ignore[arg-type]  # fragmentos fijos
                {**base, "codes": codes, "n": _DOCREF_MAX_CHUNKS},
            )
            ref_ids = [r[0] for r in cur.fetchall()]
            new_ids |= set(ref_ids)
        missing = sorted(new_ids - set(cand.hits))
        if missing:
            cur.execute(_SQL_DETAIL, {"role": role, "ids": missing})
            for r in cur.fetchall():
                cand.hits[r[0]] = _mk_hit(r)
        cand.named |= {cand.hits[i].doc_id for i in ref_ids if i in cand.hits}
        exp_docs = sorted({h.doc_id for h in cand.hits.values()
                           if h.doc_type in config.expand_doc_types} - cand.expanded_docs)
        if config.expand_sections and config.expand_max_docs > 0 and exp_docs:
            cur.execute(
                _SQL_EXPAND.format(f=where),  # type: ignore[arg-type]  # fragmentos fijos
                {**base, "docs": exp_docs, "types": list(config.expand_doc_types),
                 "secs": list(config.expand_sections)},
            )
            exp_ids = [r[0] for r in cur.fetchall()]
            parts = {i: cand.hits[i] for i in exp_ids if i in cand.hits}
            fetch = [i for i in exp_ids if i not in parts]
            if fetch:
                cur.execute(_SQL_DETAIL, {"role": role, "ids": fetch})
                parts |= {r[0]: _mk_hit(r) for r in cur.fetchall()}
            for i in sorted(parts):  # orden de parte (id de ingesta)
                cand.extra.setdefault(parts[i].doc_id, []).append(parts[i])
            cand.expanded_docs |= set(exp_docs)
    tr.timings_ms["sql"] = round(tr.timings_ms.get("sql", 0.0)
                                 + (time.perf_counter() - t) * 1000, 1)
    _fuse(cand, config)


def _fuse(cand: _Candidates, config: RetrieveConfig) -> None:
    """RRF sobre todas las listas (la 1.ª de cada rama es la consulta original; las alternativas
    pesan `w_alt`). bm25/vector y sus rangos son los de la primera lista en que sale el chunk."""
    for h in cand.hits.values():
        h.fusion, h.bm25, h.lexical_rank, h.vector, h.vector_rank = 0.0, None, None, None, None
        if h.doc_id in cand.named:
            h.via = "doc_ref"
    for lists, w0, kind in ((cand.lex_lists, config.w_lexical, "lex"),
                            (cand.vec_lists, config.w_vector, "vec")):
        for qi, lst in enumerate(lists):
            w = w0 * (1.0 if qi == 0 else config.w_alt)
            for rank, (cid, score) in enumerate(lst, 1):
                h = cand.hits.get(cid)
                if h is None:
                    continue
                if kind == "lex" and h.lexical_rank is None:
                    h.bm25, h.lexical_rank = score, rank
                elif kind == "vec" and h.vector_rank is None:
                    h.vector, h.vector_rank = score, rank
                h.fusion += w / (config.rrf_k + rank)
    if config.doc_size_penalty > 0:
        for h in cand.hits.values():
            h.fusion *= max(h.doc_chunks, 1) ** -config.doc_size_penalty


def _select_pool(cand: _Candidates, config: RetrieveConfig, k: int) -> list[Hit]:
    """Pool del rerank: chunks de los documentos nombrados (≤ doc_ref_pool por documento) y el
    resto por fusión, diversificado por documento (`pool_per_doc`)."""
    fused = cand.fused()
    ref_pool = _cap_per_doc([h for h in fused if h.doc_id in cand.named], config.doc_ref_pool,
                            len(fused))
    rest = [h for h in fused if h.doc_id not in cand.named]
    return ref_pool + _cap_per_doc(
        rest, config.pool_per_doc, max(max(config.rerank_pool, k) - len(ref_pool), k))


def _rerank_into(query: str, pool: list[Hit], scored: dict[int, float],
                 config: RetrieveConfig, s: Settings, tr: RetrievalTrace) -> None:
    if not pool:
        return
    t = time.perf_counter()
    scores = rerank(query, [_rerank_text(h, config.rerank_max_chars) for h in pool], settings=s)
    for h, sc in zip(pool, scores, strict=True):
        h.rerank = sc
        scored[h.chunk_id] = sc
    tr.timings_ms["rerank"] = round(tr.timings_ms.get("rerank", 0.0)
                                    + (time.perf_counter() - t) * 1000, 1)


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
