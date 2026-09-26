"""Nodos del grafo 8D (M3-T3, F04). Cada nodo: E/S (MCP, RAG, LLM) + dominio en `domain.py`.

Dependencias de ejecución (`Deps`) por `config["configurable"]["deps"]`: nunca se guardan en el
estado ni en los checkpoints (el estado solo lleva datos JSON). El Principal es SIEMPRE el del
usuario autenticado: las llamadas al MCP pasan por `mcp_obo` y la recuperación por `retrieve_as`.

Garantías que no dependen del modelo:
- La reclamación llega al LLM solo con sus segmentos visibles NO sospechosos (M3-T2); lo oculto,
  los metadatos y lo marcado por el detector quedan fuera y se muestran como aviso
  (`instruction_ignored`), nunca como instrucción.
- Los datos del ERP salen del MCP con su consulta; si el ERP falla, D3 lo dice y no inventa lotes.
- Citas: solo ids enviados (C/S/F/E); las inventadas se descartan y se registran.
- AMFE: un vínculo solo es válido si apunta a una fila enviada; sin AMFE de la pieza, todas las
  hipótesis quedan "fuera del AMFE" con el hueco declarado.
- Ningún nodo tiene herramientas de escritura ni de aprobación: el grafo termina en un interrupt.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field, replace
from datetime import date
from typing import Any

from langchain_core.runnables import RunnableConfig

from solaris.agents.complaint import SessionFactory, parse_async
from solaris.agents.eight_d import domain as dom
from solaris.agents.eight_d import envelope as env
from solaris.agents.eight_d import sources as src
from solaris.audit import record_safe
from solaris.auth.core import Principal
from solaris.llm import LLMError, route
from solaris.prompts import load_prompt
from solaris.prompts.untrusted import neutralize, new_nonce
from solaris.rag.answer import _DeferredAudit, leaks_prompt
from solaris.rag.crosslingual import retrieve_bilingual
from solaris.rag.retrieve import DEFAULT_CONFIG
from solaris.settings import Settings

logger = logging.getLogger("solaris.eight_d")

TASK = "8d_draft"
PROMPT_DESCRIBE = "8d_describe.v1"
# v1 por defecto: mejor medida (pasada 1: 3/5 casos PASS). v2 (campo "comparison" antes de
# "relation", una sola regla nueva, PAT-010) dio 2/5 en la pasada 2: queda versionado, no por
# defecto. Ver raw/eval-runs/2026-09-26_8d_deepseek-deepseek-chat_pasada{1,2}.json.
PROMPT_SIMILAR = "8d_similar.v1"
SIMILAR_WITH_COMPARISON = {"8d_similar.v2"}
PROMPT_HYPOTHESES = "8d_hypotheses.v1"
MAX_CANDIDATES = 6
MAX_RAG_CANDIDATES = 2
# Antecedente por similitud semántica (otra pieza o analogía): rerank mínimo. Medido en M3-T3 con
# las 5 reclamaciones: los antecedentes reales quedan en [-5,4; 3,5] y el ruido por debajo de -6.
MIN_RAG_RERANK = -6.0
D2_KEYS = ("what", "where", "when", "who", "which", "how", "how_many")
D2_LABELS = {"ES": {"what": "Qué", "where": "Dónde", "when": "Cuándo", "who": "Quién",
                    "which": "Cuál", "how": "Cómo", "how_many": "Cuántos"},
             "EN": {"what": "What", "where": "Where", "when": "When", "who": "Who",
                    "which": "Which", "how": "How", "how_many": "How many"}}


# --- dependencias --------------------------------------------------------------------------------


def _default_session_factory() -> Any:
    from solaris.mcp_stdio import StdioToolSession

    return StdioToolSession.erp_mock(timeout_s=30.0, client_name="solaris-8d")


@dataclass
class Deps:
    principal: Principal
    settings: Settings
    load_file: Callable[[str], Awaitable[tuple[bytes, str]]]
    route_fn: Callable[..., Any] = route
    retrieve_fn: Callable[..., list[Any]] = retrieve_bilingual
    fmea_docs_fn: Callable[..., dict[str, Any]] = src.fmea_documents
    fmea_rows_fn: Callable[..., list[dict[str, Any]]] = src.fmea_rows
    session_factory: SessionFactory = _default_session_factory
    parse_fn: Callable[..., Any] = parse_async
    audit: Callable[..., None] | None = None  # escritor del audit (tests); None = record_safe
    today: date = field(default_factory=date.today)


def deps_of(config: Any) -> Deps:
    d = (config or {}).get("configurable", {}).get("deps")
    if not isinstance(d, Deps):
        raise RuntimeError("Falta Deps en config.configurable (el Principal lo pone la API)")
    return d


def _audit(deps: Deps, case_id: str, node: str, outcome: str, t0: float, **meta: Any) -> None:
    payload = {"node": node, "outcome": outcome,
               "duration_ms": round((time.perf_counter() - t0) * 1000, 1), **meta}
    kw = {"settings": deps.settings, "case_id": case_id}
    if deps.audit is not None:
        deps.audit("agent_step", deps.principal.actor, payload, **kw)
    else:
        record_safe("agent_step", deps.principal.actor, payload, **kw)


def _progress(node: str, t0: float, outcome: str = "ok") -> list[dict[str, Any]]:
    return [{"node": node, "outcome": outcome,
             "ms": round((time.perf_counter() - t0) * 1000, 1), "at": time.time()}]


class Erp:
    """Llamadas al MCP erp-mock como el usuario (mcp_obo). Guarda herramienta, argumentos y SQL."""

    def __init__(self, session: Any, deps: Deps, node: str, base_index: int = 0) -> None:
        self.session, self.deps, self.node = session, deps, node
        self.calls: list[dict[str, Any]] = []
        self.base = base_index

    async def call(self, tool: str, args: dict[str, Any]) -> tuple[int, dict[str, Any] | None]:
        from solaris.mcp_obo import call_erp_tool

        res = await call_erp_tool(self.session, self.deps.principal, tool, args,
                                  settings=self.deps.settings)
        is_err = bool(getattr(res, "is_error", False)) or (
            isinstance(res, dict) and bool(res.get("isError")))
        payload = getattr(res, "data", res)
        payload = payload if isinstance(payload, dict) else {}
        idx = self.base + len(self.calls)
        self.calls.append({"index": idx, "node": self.node, "tool": tool, "arguments": args,
                           "ok": not is_err, "query": payload.get("query") if not is_err else None,
                           "user": self.deps.principal.user})
        data = payload.get("data") if not is_err else None
        return idx, data if isinstance(data, dict) else None


def _complaint_ref(c: dict[str, Any]) -> dict[str, Any]:
    return {"kind": "complaint", "doc_id": (c.get("source") or {}).get("filename"),
            "complaint_id": c.get("complaint_id"), "version": "upload"}


def _visible_segments(c: dict[str, Any]) -> list[dict[str, Any]]:
    return [s for s in c.get("segments") or []
            if s.get("channel") == "visible" and not s.get("suspicious")]


def _defect_text(c: dict[str, Any]) -> str:
    parts = [c.get("defect_description") or ""]
    segs = _visible_segments(c)
    if not parts[0] and segs:
        parts.append(" ".join(s["text"] for s in segs)[:1200])
    return " ".join(p for p in parts if p).strip()


def _full_text(c: dict[str, Any]) -> str:
    """Descripción + todo el texto visible no sospechoso (para reglas de dominio, nunca al LLM)."""
    return " ".join([c.get("defect_description") or ""]
                    + [s["text"] for s in _visible_segments(c)])


def _find_segment(c: dict[str, Any], value: str) -> dict[str, Any] | None:
    for s in _visible_segments(c):
        if value and value in s.get("text", ""):
            return s
    return None


def _seg_ref(c: dict[str, Any], s: dict[str, Any] | None) -> list[dict[str, Any]]:
    return [{**_complaint_ref(c), "locator": s.get("location") or {}}] if s else []


# --- intake --------------------------------------------------------------------------------------


async def intake(state: dict[str, Any], config: RunnableConfig) -> dict[str, Any]:
    deps = deps_of(config)
    case_id = state["case_id"]
    t0 = time.perf_counter()
    data, filename = await deps.load_file(case_id)
    parsed = await deps.parse_fn(data, filename, deps.principal, settings=deps.settings)
    c = parsed.model_dump(mode="json")
    warnings: list[dict[str, Any]] = []
    if c.get("injection_suspected"):
        # Aviso visible, nunca instrucción: ubicación, regla y extracto neutralizado (≤120).
        warnings.append({
            "type": "instruction_ignored", "node": "intake",
            "message": "El documento contiene instrucciones dirigidas al asistente que se han "
                       "ignorado.",
            "findings": [{"channel": f["channel"], "location": f["location"], "rule": f["rule"],
                          "excerpt": neutralize(f["excerpt"], 120)}
                         for f in c.get("injection_findings") or []]})
    for w in c.get("warnings") or []:
        if w.get("type") != "instruction_ignored":
            warnings.append({**w, "node": "intake"})
    out: dict[str, Any] = {"complaint": c, "complaint_id": c.get("complaint_id"),
                           "status": "drafting", "warnings": warnings}
    lot_code = (c.get("lot_codes") or [None])[0]
    calls: list[dict[str, Any]] = []
    customer: dict[str, Any] = {}
    claimed: dict[str, Any] = {}
    try:
        async with deps.session_factory() as session:
            erp = Erp(session, deps, "intake")
            if c.get("customer_code"):
                _, d = await erp.call("get_customer", {"code": c["customer_code"]})
                customer = (d or {}).get("customer") or {}
            if lot_code:
                idx, d = await erp.call("get_lot", {"lot_code": lot_code})
                if d and d.get("found"):
                    claimed = {**d, "query_index": idx}
                    # get_lot da la célula en el lote; la ficha de pieza la necesita el dominio.
                    part_d = dict(claimed.get("part") or {})
                    part_d.setdefault("weld_cell", (claimed.get("lot") or {}).get("weld_cell"))
                    claimed["part"] = part_d
            calls = erp.calls
    except Exception as exc:  # MCP caído o identidad rechazada: el caso sigue, con aviso
        logger.warning("8d intake: ERP no disponible (%s)", type(exc).__name__)
        warnings.append({"type": "erp_unavailable", "node": "intake",
                         "message": "No se ha podido consultar el ERP."})
    lang = dom.norm_lang(customer.get("report_language") or c.get("language"))
    part = claimed.get("part") or {"ref": c.get("part_ref")}
    category = dom.classify_defect(_full_text(c), part)
    out.update(customer=customer, language=lang, claimed_lot=claimed, category=category,
               erp_queries=calls, progress=_progress("intake", t0))
    if not c.get("part_ref") or not c.get("complaint_id"):
        out.update(status="error", error="La reclamación no identifica pieza o número: no se "
                                         "puede generar el 8D.")
    _audit(deps, case_id, "intake", "ok" if out["status"] != "error" else "error", t0,
           complaint_id=c.get("complaint_id"), sha256=(c.get("source") or {}).get("sha256"),
           injection_suspected=bool(c.get("injection_suspected")),
           injection_channels=sorted({f["channel"] for f in c.get("injection_findings") or []}),
           language=lang, category=category,
           tools=[{"tool": x["tool"], "ok": x["ok"]} for x in calls])
    return out


def after_intake(state: dict[str, Any]) -> list[str] | str:
    """D1, D2 y D3 no dependen entre sí: se ejecutan en paralelo (D4 espera a D1 y D3)."""
    return "end" if state.get("status") == "error" else ["D1_team", "D2_describe", "D3_contain"]


# --- D1 ------------------------------------------------------------------------------------------


async def d1_team(state: dict[str, Any], config: RunnableConfig) -> dict[str, Any]:
    deps = deps_of(config)
    case_id, c, lang = state["case_id"], state["complaint"], state.get("language", "ES")
    t0 = time.perf_counter()
    claimed = state.get("claimed_lot") or {}
    part = claimed.get("part") or {"ref": c.get("part_ref")}
    lot = claimed.get("lot") or {}
    part_ref = c["part_ref"]
    warnings: list[dict[str, Any]] = []

    # Familia de AMFE (piezas que comparten el AMFE de pieza) → antecedentes en el ERP.
    fam = await asyncio.to_thread(deps.fmea_docs_fn, deps.principal, part_ref,
                                  state.get("category", "other"), settings=deps.settings)
    family = [p for p in fam.get("family") or [part_ref]][:4]
    candidates: list[dict[str, Any]] = []
    calls: list[dict[str, Any]] = []
    history: list[dict[str, Any]] = []
    try:
        async with deps.session_factory() as session:
            erp = Erp(session, deps, "D1_team", base_index=100)  # índices por nodo (ramas
            # paralelas): intake 0…, D1 100…, D3 200…
            for p in family:
                idx, d = await erp.call("search_complaints", {"part_ref": p})
                for row in (d or {}).get("complaints") or []:
                    if row.get("complaint_id") == c.get("complaint_id"):
                        continue
                    history.append({**row, "query_index": idx})
                    if row.get("report_8d_id") and row.get("status") == "closed":
                        candidates.append({
                            "doc_id": row["report_8d_id"], "part_ref": row["part_ref"],
                            "complaint_id": row["complaint_id"], "date": row["received_date"],
                            "lot_code": row.get("lot_code"),
                            "reason": "erp_same_part" if p == part_ref else "erp_amfe_family",
                            "query_index": idx})
            calls = erp.calls
    except Exception as exc:
        logger.warning("8d D1: ERP no disponible (%s)", type(exc).__name__)
        warnings.append({"type": "erp_unavailable", "node": "D1_team",
                         "message": "No se han podido consultar las reclamaciones anteriores."})
    # Antecedentes por similitud (otras piezas, analogías), recuperados COMO el usuario.
    query = f"{_defect_text(c)[:600]} {part_ref} {part.get('special_char') or ''}".strip()
    cfg = replace(DEFAULT_CONFIG, max_per_doc=1, expand_sections=())
    hits = await asyncio.to_thread(deps.retrieve_fn, deps.principal, query, 8,
                                   {"doc_type": "8d"}, settings=deps.settings, config=cfg)
    known = {x["doc_id"] for x in candidates}
    extra = 0
    for h in hits:
        if h.doc_id in known or extra >= MAX_RAG_CANDIDATES:
            continue
        if h.rerank is not None and h.rerank < MIN_RAG_RERANK:
            continue
        known.add(h.doc_id)
        extra += 1
        candidates.append({"doc_id": h.doc_id, "part_ref": None, "complaint_id": None,
                           "date": None, "lot_code": None, "reason": "rag_similarity",
                           "title": h.title, "rerank": h.rerank})
    candidates = candidates[:MAX_CANDIDATES]

    # Equipo: roles por cliente, pieza y lote; nombres solo de la D1 de 8D visibles (con cita).
    _, material_code = dom.choose_material(state.get("category", "other"),
                                                       _full_text(c), lot)
    supplier = (material_code or "").rsplit("-", 1)[0] if material_code else None
    roles = dom.team_roles(state.get("category", "other"), part, lot, supplier,
                           dom.mentions_weld(_full_text(c)))
    d1_hits: list[Any] = []
    if candidates:
        ids = " ".join(x["doc_id"] for x in candidates)
        cfg1 = replace(DEFAULT_CONFIG, max_per_doc=1, expand_sections=(), doc_ref_pool=4)
        got = await asyncio.to_thread(deps.retrieve_fn, deps.principal,
                                      f"D1 Team equipo {ids}", 8, {"doc_type": "8d"},
                                      settings=deps.settings, config=cfg1)
        d1_hits = [h for h in got if (h.locator or {}).get("section") == "D1"]
    dom.match_names(roles, d1_hits)
    team = [{"role": dom.role_label(r["key"], r["params"], lang), "key": r["key"],
             "required": r["required"], "suggested": r["suggested"],
             "citation": r["citation"], "status": "suggested" if r["suggested"] else "to_assign"}
            for r in roles]
    contact = c.get("contact") or {}
    d1 = {"team": team, "customer_contact": {
        **contact, "citations": _seg_ref(c, _find_segment(c, contact.get("email") or ""))},
        "note": {"ES": "Nombres propuestos a partir de 8D anteriores; confirmar disponibilidad.",
                 "EN": "Names proposed from previous 8D reports; confirm availability."}[lang]}
    _audit(deps, case_id, "D1_team", "ok", t0, roles=len(team),
           named=sum(1 for x in team if x["suggested"]),
           candidates=[{"doc_id": x["doc_id"], "reason": x["reason"]} for x in candidates],
           tools=[{"tool": x["tool"], "ok": x["ok"]} for x in calls])
    return {"d1": d1, "similar_candidates": candidates, "history": history,
            "amfe_family": fam, "erp_queries": calls, "warnings": warnings,
            "progress": _progress("D1_team", t0)}


# --- LLM común -----------------------------------------------------------------------------------


@dataclass
class LlmOut:
    data: dict[str, Any] | None
    sent: dict[str, env.Item]
    guard: env.TextGuard
    meta: dict[str, Any]
    finish: Callable[[dict[str, Any]], None]


def _item_audit(it: env.Item) -> dict[str, Any]:
    r = it.ref
    return {"id": it.id, "kind": it.kind, "doc_id": r.get("doc_id"), "version": r.get("version"),
            "locator": r.get("locator"), "tool": r.get("tool"), "suspicious": it.suspicious}


async def call_llm(deps: Deps, case_id: str, node: str, prompt_version: str,
                   context: dict[str, Any], items: list[env.Item], fmt: dict[str, Any],
                   max_tokens: int) -> LlmOut:
    """Una llamada `route("8d_draft")` con la especificación de prompts de M2-T8 §4."""
    prompt = load_prompt(prompt_version)
    nonce = new_nonce()
    user_msg, sent = env.build(context, items, nonce)
    by_id = {x.id: x for x in sent}
    guard = env.TextGuard(user_msg)
    deferred = _DeferredAudit()
    security = {"prompt_version": prompt.version, "prompt_sha256": prompt.sha256,
                "nonce_sha256": hashlib.sha256(nonce.encode()).hexdigest()[:16]}
    audit_meta = {"node": node, "sources": [_item_audit(x) for x in sent],
                  "security": dict(security)}
    messages = [{"role": "system", "content": prompt.text},
                {"role": "user", "content": user_msg}]
    meta: dict[str, Any] = {"node": node, "prompt_version": prompt.version, "sent": len(sent)}

    def finish(post: dict[str, Any]) -> None:
        heur = [{"source_id": x.id, **{k: v for k, v in _item_audit(x).items() if k != "id"},
                 "detector": "heuristic", "pattern": ",".join(x.patterns)}
                for x in sent if x.suspicious]
        deferred.flush(deps.audit, deps.settings, {"instruction_ignored": heur, **post})

    try:
        result = await asyncio.to_thread(
            deps.route_fn, TASK, messages, settings=deps.settings, actor=deps.principal.actor,
            case_id=case_id, audit=deferred, audit_meta=audit_meta, response_format=fmt,
            max_tokens=max_tokens)
    except LLMError as exc:
        logger.warning("8d %s: LLM no disponible (%s)", node, type(exc).__name__)
        meta["error"] = "llm_unavailable"
        return LlmOut(None, by_id, guard, meta, finish)
    meta.update(model=result.model, provider=result.provider, latency_ms=result.latency_ms,
                prompt_tokens=result.prompt_tokens, completion_tokens=result.completion_tokens,
                cost_usd=result.cost_usd, used_fallback=result.used_fallback)
    data = env.parse_json(result.content)
    if data is None:
        meta["discarded"] = "invalid_output"
    elif leaks_prompt(json.dumps(data, ensure_ascii=False), nonce, prompt):
        meta["discarded"] = "prompt_leak"
        data = None
    return LlmOut(data, by_id, guard, meta, finish)


def _refs(ids: list[str], sent: dict[str, env.Item]) -> list[dict[str, Any]]:
    return [dict(sent[i].ref) for i in ids if i in sent]


def _model_ignored(data: dict[str, Any] | None, sent: dict[str, env.Item]) -> list[str]:
    out = []
    for it in (data or {}).get("ignored_instructions") or []:
        if isinstance(it, dict) and isinstance(it.get("source"), str):
            sid = it["source"].strip().strip("[]").upper()[:8]
            if sid in sent and sid not in out:
                out.append(sid)
    return out


def _complaint_items(c: dict[str, Any], start: int = 1) -> list[env.Item]:
    ref = _complaint_ref(c)
    return [env.complaint_item(n, s, ref) for n, s in enumerate(_visible_segments(c), start)]


def _complaint_context(c: dict[str, Any]) -> dict[str, Any]:
    keys = ("complaint_id", "customer_code", "part_ref", "drawing_no", "lot_codes",
            "delivery_notes", "qty_affected", "issued_date", "defect_description", "evidence",
            "requested_deadlines", "language")
    return {k: c.get(k) for k in keys}


def _lot_context(claimed: dict[str, Any]) -> dict[str, Any]:
    lot, part = claimed.get("lot") or {}, claimed.get("part") or {}
    keys = ("lot_code", "production_date", "shift", "press", "weld_cell", "qty_produced",
            "qty_scrap", "status", "steel_lot_code", "wire_lot_code", "nut_lot_code",
            "ecoat_lot_code")
    return {**{k: lot.get(k) for k in keys},
            "part": {k: part.get(k) for k in ("ref", "part_description", "customer_code",
                                              "special_char", "char_class", "die", "routing")}}


def _erp_lot_items(claimed: dict[str, Any], start: int = 1) -> list[env.Item]:
    items = []
    if not claimed:
        return items
    qi = claimed.get("query_index")
    items.append(env.erp_item(start, "get_lot", json.dumps(_lot_context(claimed),
                                                           ensure_ascii=False, default=str), qi))
    for kind, m in (claimed.get("material_lots") or {}).items():
        if m:
            txt = json.dumps({"kind": kind, **{k: m.get(k) for k in (
                "lot_code", "supplier_code", "material", "received_date", "certificate_ok",
                "notes")}}, ensure_ascii=False, default=str)
            items.append(env.erp_item(start + len(items), "get_lot", txt, qi))
    return items


# --- D2 ------------------------------------------------------------------------------------------

D2_FORMAT = env.schema("eightd_describe", {
    "problem_statement": env.CITED_TEXT,
    "rows": {"type": "array", "items": {
        "type": "object", "additionalProperties": False, "required": ["key", "text", "citations"],
        "properties": {"key": {"type": "string", "enum": list(D2_KEYS)},
                       "text": {"type": "string"},
                       "citations": {"type": "array", "items": {"type": "string"}}}}},
    "ignored_instructions": env.IGNORED_SCHEMA,
})


def _d2_facts(c: dict[str, Any], customer: dict[str, Any]) -> dict[str, Any]:
    """Hechos deterministas (regex del parser) con la cita del segmento donde aparecen."""
    def fact(value: Any, literal: str | None = None) -> dict[str, Any]:
        seg = _find_segment(c, literal if literal is not None else str(value or ""))
        return {"value": value, "citations": _seg_ref(c, seg)}

    dl = c.get("requested_deadlines") or {}
    return {
        "complaint_id": fact(c.get("complaint_id")),
        "part_ref": fact(c.get("part_ref")),
        "lot_codes": [fact(x) for x in c.get("lot_codes") or []],
        "delivery_notes": [fact(x) for x in c.get("delivery_notes") or []],
        "qty_affected": {"value": c.get("qty_affected"), "citations": []},
        "issued_date": {"value": c.get("issued_date"), "citations": []},
        "deadlines": {
            "containment": {**(dl.get("containment") or {}),
                            "customer_standard_hours": customer.get("containment_hours")},
            "report_8d": {**(dl.get("report_8d") or {}),
                          "customer_standard_working_days": customer.get("report_days")},
        },
        "template": {"customer_template": customer.get("report_template"),
                     "template_ref": c.get("template_ref"),
                     "language": customer.get("report_language")},
    }


async def d2_describe(state: dict[str, Any], config: RunnableConfig) -> dict[str, Any]:
    deps = deps_of(config)
    case_id, c, lang = state["case_id"], state["complaint"], state.get("language", "ES")
    t0 = time.perf_counter()
    claimed = state.get("claimed_lot") or {}
    items = _complaint_items(c) + _erp_lot_items(claimed)
    ctx = {"report_language": lang, "complaint": _complaint_context(c),
           "claimed_lot": _lot_context(claimed) if claimed else None}
    out = await call_llm(deps, case_id, "D2_describe", PROMPT_DESCRIBE, ctx, items, D2_FORMAT,
                         1400)
    warnings: list[dict[str, Any]] = []
    rows: dict[str, dict[str, Any]] = {}
    dropped: list[str] = []
    statement = {"text": "", "citations": []}
    if out.data is not None:
        ps = out.data.get("problem_statement") or {}
        kept, drop = env.validate_ids(ps.get("citations"), set(out.sent))
        dropped += drop
        statement = {"text": out.guard.clean(ps.get("text"), 350, "problem_statement"),
                     "citations": _refs(kept, out.sent)}
        for r in out.data.get("rows") or []:
            if not isinstance(r, dict) or r.get("key") not in D2_KEYS or r["key"] in rows:
                continue
            kept, drop = env.validate_ids(r.get("citations"), set(out.sent))
            dropped += drop
            text = out.guard.clean(r.get("text"), 300, f"d2.{r['key']}")
            rows[r["key"]] = {"key": r["key"], "text": text, "citations": _refs(kept, out.sent),
                              "source": "llm" if kept else "llm_uncited"}
    else:
        warnings.append({"type": "d2_llm_unavailable", "node": "D2_describe",
                         "reason": out.meta.get("error") or out.meta.get("discarded")})
    facts = _d2_facts(c, state.get("customer") or {})
    # Fallback determinista por fila (sin LLM o sin cita válida): solo hechos del parser.
    fb = {
        "which": ", ".join([c.get("part_ref") or ""] + (c.get("lot_codes") or [])
                           + (c.get("delivery_notes") or [])).strip(", "),
        "how_many": str(c.get("qty_affected")) if c.get("qty_affected") is not None else "",
        "what": c.get("defect_description") or "",
    }
    final = []
    for k in D2_KEYS:
        r = rows.get(k)
        if r is None or not r["text"] or not r["citations"]:
            seg = _find_segment(c, (c.get("lot_codes") or [""])[0] if k == "which" else "")
            txt = fb.get(k) or dom.t("not_in_complaint", lang)
            r = {"key": k, "text": neutralize(txt, 300),
                 "citations": _seg_ref(c, seg) if fb.get(k) else [],
                 "source": "parser" if fb.get(k) else "not_found",
                 **({"model_text": r["text"]} if r and r["text"] else {})}
        final.append({**r, "label": D2_LABELS[lang][k]})
    if dropped:
        warnings.append({"type": "citations_dropped", "node": "D2_describe",
                         "count": len(dropped)})
    if out.guard.removed:
        warnings.append({"type": "text_removed", "node": "D2_describe",
                         "count": len(out.guard.removed)})
    ignored = _model_ignored(out.data, out.sent)
    out.finish({"citations_dropped": len(dropped), "citations_dropped_ids": dropped,
                "text_removed": out.guard.removed[:20], "model_declared": ignored,
                "output_discarded": out.meta.get("discarded")})
    d2 = {"problem_statement": statement, "rows": final, "facts": facts, "language": lang}
    _audit(deps, case_id, "D2_describe", "ok" if out.data is not None else "degraded", t0,
           rows_cited=sum(1 for r in final if r["citations"]), citations_dropped=len(dropped),
           prompt_version=PROMPT_DESCRIBE, model=out.meta.get("model"))
    return {"d2": d2, "warnings": warnings, "llm": [out.meta],
            "progress": _progress("D2_describe", t0)}


# --- D3 ------------------------------------------------------------------------------------------


async def d3_contain(state: dict[str, Any], config: RunnableConfig) -> dict[str, Any]:
    deps = deps_of(config)
    case_id, c = state["case_id"], state["complaint"]
    t0 = time.perf_counter()
    claimed = state.get("claimed_lot") or {}
    lot, part = claimed.get("lot") or {}, claimed.get("part") or {}
    category = state.get("category", "other")
    notified = c.get("issued_date")
    notified_d = date.fromisoformat(notified) if notified else None
    claimed_code = lot.get("lot_code")
    shift = lot.get("shift") if lot.get("shift") == "noche" else None
    warnings: list[dict[str, Any]] = []
    base = 200  # índice de consulta propio del nodo (D1 corre en paralelo)
    d3: dict[str, Any] = {"criterion": {}, "summary": {}, "lots": [], "verify_before_release": [],
                          "material": None, "error": None, "query_indexes": []}
    calls: list[dict[str, Any]] = []
    if not lot:
        d3["error"] = "claimed_lot_not_found"
        d3["message"] = "No se ha podido leer el lote reclamado en el ERP; contención a completar."
        warnings.append({"type": "d3_without_erp", "node": "D3_contain"})
    else:
        try:
            async with deps.session_factory() as session:
                erp = Erp(session, deps, "D3_contain", base_index=base)
                kind, code = dom.choose_material(category, _full_text(c), lot)
                scope_rows: list[dict[str, Any]] = []
                ships: list[dict[str, Any]] = []
                if kind and code:
                    i1, wu = await erp.call("material_where_used", {"material_lot_code": code})
                    parts = dom.select_scope_parts(category, kind, part,
                                                   (wu or {}).get("parts") or [])
                    i2, cs = await erp.call("containment_scope",
                                            {"part_refs": parts, "material_lot_code": code})
                    for p in (cs or {}).get("parts") or []:
                        scope_rows += p.get("lot_detail") or []
                        ships += p.get("shipment_detail") or []
                    mat = (claimed.get("material_lots") or {}).get(kind) or {}
                    d3["material"] = {"kind": kind, "lot_code": code,
                                      "supplier_code": mat.get("supplier_code"),
                                      "received_date": mat.get("received_date"),
                                      "certificate_ok": mat.get("certificate_ok"),
                                      "notes": neutralize(mat.get("notes") or "", 300) or None,
                                      "query_index": claimed.get("query_index")}
                    d3["criterion"] = {"type": "material_lot", "material_kind": kind,
                                       "material_lot_code": code, "part_refs": parts,
                                       "query_indexes": [i1, i2]}
                # Lote reclamado y posteriores de la misma pieza (criterio mínimo / de utillaje).
                start = lot.get("production_date")
                i3, fl = await erp.call("find_lots", {"part_ref": part.get("ref") or c["part_ref"],
                                                      "from_date": start,
                                                      "to_date": deps.today.isoformat()})
                later = (fl or {}).get("lots") or []
                i4, sh = await erp.call("get_shipments", {
                    "part_ref": part.get("ref") or c["part_ref"], "from_date": start,
                    "to_date": deps.today.isoformat()})
                later_ships = (sh or {}).get("shipments") or []
                calls = erp.calls
            if scope_rows:
                in_scope = {x["lot_code"] for x in scope_rows}
                rows = [dom.lot_row(x, ships=ships, claimed=claimed_code, priority_shift=shift,
                                    notified=notified_d) for x in scope_rows]
                d3["verify_before_release"] = [
                    dom.lot_row(x, ships=later_ships, claimed=claimed_code, priority_shift=None,
                                notified=notified_d) for x in later
                    if x["lot_code"] not in in_scope]
                all_ships = ships
                d3["query_indexes"] = [*d3["criterion"]["query_indexes"], i3, i4]
            else:
                rows = [dom.lot_row(x, ships=later_ships, claimed=claimed_code,
                                    priority_shift=shift, notified=notified_d) for x in later]
                all_ships = later_ships
                d3["criterion"] = {"type": "claimed_and_later_lots",
                                   "part_refs": [part.get("ref") or c["part_ref"]],
                                   "from_date": start, "to_date": deps.today.isoformat(),
                                   "query_indexes": [i3, i4],
                                   **({"note": "material_scope_empty"} if kind else {})}
                d3["query_indexes"] = [i3, i4]
            d3["lots"] = sorted(rows, key=lambda r: (r["part_ref"] or "", r["production_date"]
                                                     or "", r["lot_code"]))
            d3["summary"] = dom.summarize_scope(d3["lots"], all_ships)
        except Exception as exc:
            logger.warning("8d D3: ERP no disponible (%s)", type(exc).__name__)
            d3 = {**d3, "lots": [], "summary": {}, "error": "erp_unavailable",
                  "message": "No se ha podido consultar el ERP; contención sin datos, a completar."}
            warnings.append({"type": "erp_unavailable", "node": "D3_contain",
                             "message": d3["message"]})
    _audit(deps, case_id, "D3_contain", "ok" if not d3["error"] else "degraded", t0,
           criterion=d3.get("criterion"), lots=len(d3["lots"]),
           shipped_qty=(d3.get("summary") or {}).get("shipped_qty"),
           qty_not_shipped=(d3.get("summary") or {}).get("qty_not_shipped"),
           tools=[{"tool": x["tool"], "ok": x["ok"], "arguments": x["arguments"]}
                  for x in calls])
    return {"d3": d3, "erp_queries": calls, "warnings": warnings,
            "progress": _progress("D3_contain", t0)}


# --- D4 ------------------------------------------------------------------------------------------

SIMILAR_FORMAT = env.schema("eightd_similar", {
    "similar": {"type": "array", "items": {
        "type": "object", "additionalProperties": False,
        "required": ["doc_id", "relation", "cause_summary", "action_summary",
                     "discriminating_evidence", "citations"],
        "properties": {"doc_id": {"type": "string"},
                       "relation": {"type": "string", "enum": list(dom.RELATIONS)},
                       "cause_summary": {"type": "string"}, "action_summary": {"type": "string"},
                       "discriminating_evidence": {"type": "string"},
                       "citations": {"type": "array", "items": {"type": "string"}}}}},
    "recurrence": {"type": "object", "additionalProperties": False,
                   "required": ["confirmed", "summary", "citations"],
                   "properties": {"confirmed": {"type": "boolean"},
                                  "summary": {"type": "string"},
                                  "citations": {"type": "array", "items": {"type": "string"}}}},
    "ignored_instructions": env.IGNORED_SCHEMA,
})
def similar_format(prompt_version: str) -> dict[str, Any]:
    """Esquema de salida de `prompt_version` (v2 añade `comparison` antes de `relation`)."""
    if prompt_version not in SIMILAR_WITH_COMPARISON:
        return SIMILAR_FORMAT
    fmt = json.loads(json.dumps(SIMILAR_FORMAT))
    item = fmt["json_schema"]["schema"]["properties"]["similar"]["items"]
    item["properties"] = {"doc_id": item["properties"]["doc_id"],
                          "comparison": {"type": "string"},
                          **{k: v for k, v in item["properties"].items() if k != "doc_id"}}
    item["required"] = ["doc_id", "comparison", *item["required"][1:]]
    return fmt


HYP_FORMAT = env.schema("eightd_hypotheses", {
    "hypotheses": {"type": "array", "items": {
        "type": "object", "additionalProperties": False,
        "required": ["title", "category", "mechanism", "status", "rationale", "evidence",
                     "fmea_row", "fmea_gap", "verification"],
        "properties": {"title": {"type": "string"},
                       "category": {"type": "string", "enum": list(dom.CATEGORIES_6M)},
                       "mechanism": {"type": "string", "enum": list(dom.MECHANISMS)},
                       "status": {"type": "string", "enum": list(dom.STATUSES)},
                       "rationale": {"type": "string"},
                       "evidence": {"type": "array", "items": {"type": "string"}},
                       "fmea_row": {"type": "string"}, "fmea_gap": {"type": "string"},
                       "verification": {"type": "string"}}}},
    "amfe_gap": {"type": "string"},
    "ignored_instructions": env.IGNORED_SCHEMA,
})


def _history_items(history: list[dict[str, Any]], start: int) -> list[env.Item]:
    items = []
    for n, h in enumerate(history[:6], start):
        txt = json.dumps({k: h.get(k) for k in ("complaint_id", "customer_code", "part_ref",
                                                "lot_code", "received_date", "defect",
                                                "status", "report_8d_id")},
                         ensure_ascii=False, default=str)
        items.append(env.erp_item(n, "search_complaints", txt, h.get("query_index")))
    return items


def _scope_item(d3: dict[str, Any], n: int) -> list[env.Item]:
    s = d3.get("summary") or {}
    if not s:
        return []
    shifts: dict[str, int] = {}
    for r in d3.get("lots") or []:
        shifts[r.get("shift") or "?"] = shifts.get(r.get("shift") or "?", 0) + 1
    txt = json.dumps({"criterion": d3.get("criterion"), "lots": s.get("lots"),
                      "per_part": s.get("per_part"), "shipped_qty": s.get("shipped_qty"),
                      "lots_by_shift": shifts, "material": d3.get("material")},
                     ensure_ascii=False, default=str)
    return [env.erp_item(n, "containment_scope", txt,
                         (d3.get("criterion") or {}).get("query_indexes", [None])[-1])]


def _section_rank(h: Any) -> int:
    sec = str((h.locator or {}).get("section") or "")
    return {"D4": 0, "D2": 1, "D7": 2, "D5": 3, "D6": 4, "D3": 5}.get(sec, 6)


async def d4_root_cause(state: dict[str, Any], config: RunnableConfig) -> dict[str, Any]:
    deps = deps_of(config)
    case_id, c, lang = state["case_id"], state["complaint"], state.get("language", "ES")
    t0 = time.perf_counter()
    claimed = state.get("claimed_lot") or {}
    lot, part = claimed.get("lot") or {}, claimed.get("part") or {}
    part_ref = c["part_ref"]
    candidates = state.get("similar_candidates") or []
    fam = state.get("amfe_family") or {}
    d3 = state.get("d3") or {}
    warnings: list[dict[str, Any]] = []
    defect = _defect_text(c)

    fmea_docs = (fam.get("part_docs") or []) + (fam.get("line_docs") or [])
    rows = await asyncio.to_thread(deps.fmea_rows_fn, deps.principal, fmea_docs,
                                   settings=deps.settings, case_id=case_id) if fmea_docs else []
    fmea_available = bool(rows)

    ids = [x["doc_id"] for x in candidates]
    q8d = f"{' '.join(ids)} root cause causa raíz D4 {defect[:500]}"
    cfg8 = replace(DEFAULT_CONFIG, max_per_doc=2, expand_max_docs=6, doc_ref_pool=8)
    cell = lot.get("weld_cell") or part.get("die") or ""
    mat = d3.get("material") or {}
    qproc = f"{defect[:500]} {part_ref} {cell} {mat.get('supplier_code') or ''}".strip()
    cfgp = replace(DEFAULT_CONFIG, max_per_doc=2)
    h8d, hproc = await asyncio.gather(
        asyncio.to_thread(deps.retrieve_fn, deps.principal, q8d, 12, {"doc_type": "8d"},
                          settings=deps.settings, config=cfg8) if ids else asyncio.sleep(0, []),
        asyncio.to_thread(deps.retrieve_fn, deps.principal, qproc, 6,
                          {"doc_type": ["it", "reg", "pc", "eval", "proc"]},
                          settings=deps.settings, config=cfgp))
    order = {d: i for i, d in enumerate(ids)}
    h8d = sorted([h for h in h8d if h.doc_id in order],
                 key=lambda h: (order[h.doc_id], _section_rank(h)))

    c_items = _complaint_items(c)
    history = state.get("history") or []
    e_lot = _erp_lot_items(claimed)
    e_hist = _history_items(history, len(e_lot) + 1)
    e_scope = _scope_item(d3, len(e_lot) + len(e_hist) + 1)
    s_similar = [env.document_item(n, h) for n, h in enumerate(h8d[:env.MAX_DOC_SOURCES], 1)]
    # Hipótesis: la D4 de los antecedentes (≤ 4) + documentos de proceso (≤ 4).
    top_d4 = [h for h in h8d if _section_rank(h) == 0][:4] or h8d[:4]
    docs_h = top_d4 + [h for h in hproc if h not in top_d4][:env.MAX_DOC_SOURCES - len(top_d4)]
    s_hyp = [env.document_item(n, h) for n, h in enumerate(docs_h, 1)]
    f_items = [env.fmea_item(n, r) for n, r in enumerate(rows[:env.MAX_FMEA_ROWS], 1)]

    cand_ctx = [{k: x.get(k) for k in ("doc_id", "date", "part_ref", "complaint_id", "reason")}
                for x in candidates]
    ctx_common = {"report_language": lang, "complaint": _complaint_context(c),
                  "claimed_lot": _lot_context(claimed) if claimed else None}
    ctx_sim = {**ctx_common, "candidates": cand_ctx}
    ctx_hyp = {**ctx_common, "similar_8d": cand_ctx,
               "fmea": {"available": fmea_available,
                        "documents": [{"doc_id": d["doc_id"], "version": d["version"]}
                                      for d in fmea_docs]}}
    sim_task = call_llm(deps, case_id, "D4_similar", PROMPT_SIMILAR, ctx_sim,
                        c_items[:3] + s_similar + e_hist, similar_format(PROMPT_SIMILAR),
                        1500) if candidates else None
    hyp_task = call_llm(deps, case_id, "D4_hypotheses", PROMPT_HYPOTHESES, ctx_hyp,
                        c_items + s_hyp + f_items + e_lot + e_hist[:3] + e_scope, HYP_FORMAT,
                        2200)
    if sim_task is not None:
        sim, hyp = await asyncio.gather(sim_task, hyp_task)
    else:
        sim, hyp = None, await hyp_task

    similar, recurrence, sim_dropped = _validate_similar(sim, candidates, lang)
    hypotheses, amfe_gap, hyp_dropped, hyp_flags = _validate_hypotheses(
        hyp, part_ref, fmea_available, lang)
    if not fmea_available:
        warnings.append({"type": "amfe_missing", "node": "D4_root_cause",
                         "message": dom.t("no_fmea", lang, part=part_ref)})
    if len(hypotheses) < 2:
        warnings.append({"type": "hypotheses_below_minimum", "node": "D4_root_cause",
                         "count": len(hypotheses)})
    if sim is not None and sim.data is None:
        warnings.append({"type": "similar_llm_unavailable", "node": "D4_root_cause"})
    if hyp.data is None:
        warnings.append({"type": "hypotheses_llm_unavailable", "node": "D4_root_cause",
                         "reason": hyp.meta.get("error") or hyp.meta.get("discarded")})
    for o, dropped in ((sim, sim_dropped), (hyp, hyp_dropped)):
        if o is None:
            continue
        o.finish({"citations_dropped": len(dropped), "citations_dropped_ids": dropped,
                  "text_removed": o.guard.removed[:20],
                  "model_declared": _model_ignored(o.data, o.sent),
                  "output_discarded": o.meta.get("discarded"), "server_flags": hyp_flags
                  if o is hyp else []})
        if dropped:
            warnings.append({"type": "citations_dropped", "node": o.meta["node"],
                             "count": len(dropped)})
    d4 = {"similar": [x for x in similar if x["relation"] != "no_relacionado"],
          "similar_discarded": [x for x in similar if x["relation"] == "no_relacionado"],
          "recurrence": recurrence, "hypotheses": hypotheses,
          "fmea": {"available": fmea_available,
                   "documents": [{"doc_id": d["doc_id"], "version": d["version"],
                                  "title": d.get("title")} for d in fmea_docs],
                   "gap": amfe_gap or (None if fmea_available
                                       else dom.t("no_fmea", lang, part=part_ref))},
          "language": lang}
    _audit(deps, case_id, "D4_root_cause", "ok" if hyp.data is not None else "degraded", t0,
           similar=[{"doc_id": x["doc_id"], "relation": x["relation"]} for x in similar],
           recurrence=recurrence.get("confirmed"),
           hypotheses=[{"status": h["status"], "fmea_row": (h["fmea_link"] or {}).get("row"),
                        "outside_fmea": h["outside_fmea"],
                        "evidence": [e.get("doc_id") for e in h["evidence"]]}
                       for h in hypotheses],
           fmea_available=fmea_available, server_flags=hyp_flags,
           prompt_versions=[PROMPT_SIMILAR, PROMPT_HYPOTHESES])
    return {"d4": d4, "warnings": warnings,
            "llm": [x.meta for x in (sim, hyp) if x is not None],
            "status": "pending_approval", "progress": _progress("D4_root_cause", t0)}


def _validate_similar(out: LlmOut | None, candidates: list[dict[str, Any]],
                      lang: str) -> tuple[list[dict[str, Any]], dict[str, Any], list[str]]:
    by_doc = {x["doc_id"]: x for x in candidates}
    dropped: list[str] = []
    result: dict[str, dict[str, Any]] = {}
    for s in ((out.data or {}).get("similar") or []) if out else []:
        if not isinstance(s, dict) or s.get("doc_id") not in by_doc or s["doc_id"] in result:
            continue
        kept, drop = env.validate_ids(s.get("citations"), set(out.sent))
        dropped += drop
        own = [i for i in kept if out.sent[i].ref.get("doc_id") == s["doc_id"]]
        relation = s.get("relation") if s.get("relation") in dom.RELATIONS else "no_relacionado"
        flags = []
        # Servidor: sin evidencia del propio 8D no se afirma misma causa.
        if relation == "misma_causa_probable" and not own:
            relation, flags = "sintoma_similar_causa_distinta", ["same_cause_without_evidence"]
        cand = by_doc[s["doc_id"]]
        result[s["doc_id"]] = {
            **{k: cand.get(k) for k in ("doc_id", "date", "part_ref", "complaint_id", "reason")},
            "relation": relation,
            "presented_as_same_cause": relation == "misma_causa_probable",
            "cause_summary": out.guard.clean(s.get("cause_summary"), 200, "similar.cause"),
            "action_summary": out.guard.clean(s.get("action_summary"), 200, "similar.action"),
            "discriminating_evidence": out.guard.clean(s.get("discriminating_evidence"), 250,
                                                       "similar.discriminating"),
            "comparison": out.guard.clean(s.get("comparison"), 350, "similar.comparison"),
            "citations": _refs(kept, out.sent), "flags": flags}
    for d, cand in by_doc.items():  # candidatos sin valoración del modelo: se muestran sin juicio
        if d not in result:
            result[d] = {**{k: cand.get(k) for k in ("doc_id", "date", "part_ref",
                                                     "complaint_id", "reason")},
                         "relation": "sin_valorar", "presented_as_same_cause": False,
                         "cause_summary": "", "action_summary": "", "discriminating_evidence": "",
                         "citations": [], "flags": ["not_assessed"]}
    similar = list(result.values())
    same = sorted([x for x in similar if x["presented_as_same_cause"]],
                  key=lambda x: str(x.get("date") or ""))
    rec = (out.data or {}).get("recurrence") if out else None
    rec = rec if isinstance(rec, dict) else {}
    kept, drop = env.validate_ids(rec.get("citations"), set(out.sent)) if out else ([], [])
    dropped += drop
    confirmed = bool(rec.get("confirmed")) and bool(same)
    recurrence = {"confirmed": confirmed, "count": len(same),
                  "timeline": [{"doc_id": x["doc_id"], "date": x.get("date"),
                                "complaint_id": x.get("complaint_id")} for x in same],
                  "summary": out.guard.clean(rec.get("summary"), 350, "recurrence")
                  if out and confirmed else "",
                  "citations": _refs(kept, out.sent) if out and confirmed else []}
    return similar, recurrence, dropped


def _validate_hypotheses(out: LlmOut, part_ref: str, fmea_available: bool,
                         lang: str) -> tuple[list[dict[str, Any]], str, list[str], list[str]]:
    hyps: list[dict[str, Any]] = []
    dropped: list[str] = []
    flags_all: list[str] = []
    for n, h in enumerate((out.data or {}).get("hypotheses") or [], 1):
        if not isinstance(h, dict) or len(hyps) >= 6:
            continue
        kept, drop = env.validate_ids(h.get("evidence"), set(out.sent))
        dropped += drop
        flags: list[str] = []
        status = h.get("status") if h.get("status") in dom.STATUSES else "a_verificar"
        evidence = kept
        if not evidence:
            if status != "a_verificar":
                flags.append("status_downgraded_no_evidence")
            status = "a_verificar"
        link = None
        fid = str(h.get("fmea_row") or "").strip().strip("[]").upper()
        gap = out.guard.clean(h.get("fmea_gap"), 200, f"h{n}.fmea_gap")
        if fid:
            item = out.sent.get(fid)
            if item is not None and item.kind == "fmea_row":
                p = item.payload
                link = {"doc_id": item.ref["doc_id"], "version": item.ref["version"],
                        "sheet": p.get("sheet"), "row": p.get("row"),
                        "failure_mode": p.get("failure_mode"), "cause": p.get("cause"),
                        "severity": p.get("severity"), "occurrence": p.get("occurrence"),
                        "detection": p.get("detection"), "rpn": p.get("rpn")}
                gap = ""
            else:
                flags.append("fmea_link_dropped")
                dropped.append(fid[:8])
                gap = dom.t("link_dropped", lang)
        if link is None:
            if not fmea_available:
                gap = dom.t("no_fmea", lang, part=part_ref)
            elif not gap:
                gap = dom.t("gap_default", lang)
        title = out.guard.clean(h.get("title"), 200, f"h{n}.title")
        if not title:
            continue
        flags_all += flags
        hyps.append({
            "id": f"H{len(hyps) + 1}", "title": title,
            "category": h.get("category") if h.get("category") in dom.CATEGORIES_6M else None,
            "mechanism": h.get("mechanism") if h.get("mechanism") in dom.MECHANISMS else None,
            "status": status,
            "rationale": out.guard.clean(h.get("rationale"), 400, f"h{n}.rationale"),
            "verification": out.guard.clean(h.get("verification"), 250, f"h{n}.verification"),
            "evidence": _refs(evidence, out.sent), "fmea_link": link,
            "outside_fmea": link is None, "fmea_gap": gap or None, "flags": flags})
    amfe_gap = out.guard.clean((out.data or {}).get("amfe_gap"), 250, "amfe_gap")
    return hyps, amfe_gap, dropped, flags_all


# --- espera de aprobación ------------------------------------------------------------------------


async def await_approval(state: dict[str, Any], config: RunnableConfig) -> dict[str, Any]:
    """Interrupt de LangGraph: el borrador queda pendiente de aprobación humana (F06).

    El HITL completo (quién aprueba, versión, audit `approval`) es M3-T4. Hasta entonces, reanudar
    el hilo NO avanza el caso: cualquier valor de reanudación se rechaza."""
    from langgraph.types import interrupt

    deps = deps_of(config)
    t0 = time.perf_counter()
    _audit(deps, state["case_id"], "await_approval", "interrupt", t0,
           status=state.get("status"), warnings=sorted({w.get("type") for w in
                                                        state.get("warnings") or []}))
    interrupt({"case_id": state["case_id"], "status": "pending_approval",
               "required_role": "calidad", "draft": "D1-D4", "version": 1})
    raise PermissionError("HITL no implementado (M3-T4): el 8D no avanza sin aprobación")
