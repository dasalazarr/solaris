"""Grafo LangGraph del 8D D1–D4 (M3-T3, F04). LangGraph solo como motor de estado.

    intake ─┬▶ D1_team ──┬▶ D4_root_cause ─┬▶ await_approval ▶ hitl_gate (interrupt) ▶ END
            ├▶ D3_contain ┘                 │
            └▶ D2_describe ─────────────────┘

- Hilo = `case_id`; checkpoints en Postgres (`eightd.*`, rol `eightd_app`) o en memoria (tests).
- El estado solo lleva datos JSON (sin objetos, sin secretos). El Principal y las dependencias
  viajan en `config.configurable.deps` y no se persisten.
- El grafo se detiene SIEMPRE en el interrupt de `hitl_gate` tras D4 (o en END si la
  reclamación no se puede procesar). M3-T4 (HITL): solo `resume_case` lo reanuda, y el nodo
  valida la decisión humana guardada en el servidor (el valor de reanudación se ignora). Con una
  decisión válida el caso queda `approved` (borrador congelado, con las ediciones del aprobador) o
  `rejected`; sin ella, `ApprovalRequired` y el caso sigue pendiente. D5–D8 irán tras `hitl_gate`.
"""

from __future__ import annotations

import logging
import operator
import time
from typing import Annotated, Any, TypedDict

from solaris.agents.eight_d import hitl, nodes
from solaris.agents.eight_d.nodes import Deps

logger = logging.getLogger("solaris.eight_d")

NODES = ("intake", "D1_team", "D2_describe", "D3_contain", "D4_root_cause", "await_approval",
         "hitl_gate")
_NOT_DRAFT = {"await_approval", "hitl_gate"}


class EightDState(TypedDict, total=False):
    case_id: str
    complaint_id: str | None
    status: str  # drafting | pending_approval | approved | rejected | error
    error: str | None
    complaint: dict[str, Any]
    customer: dict[str, Any]
    language: str
    claimed_lot: dict[str, Any]
    category: str
    similar_candidates: list[dict[str, Any]]
    history: list[dict[str, Any]]
    amfe_family: dict[str, Any]
    d1: dict[str, Any]
    d2: dict[str, Any]
    d3: dict[str, Any]
    d4: dict[str, Any]
    warnings: Annotated[list[dict[str, Any]], operator.add]
    erp_queries: Annotated[list[dict[str, Any]], operator.add]
    llm: Annotated[list[dict[str, Any]], operator.add]
    progress: Annotated[list[dict[str, Any]], operator.add]
    started_at: float
    approval: dict[str, Any]  # M3-T4: resumen de la decisión humana
    draft_original: dict[str, Any] | None  # D1–D4 antes de las ediciones del aprobador


def build_graph(checkpointer: Any) -> Any:
    from langgraph.graph import END, START, StateGraph

    g = StateGraph(EightDState)
    g.add_node("intake", nodes.intake)
    g.add_node("D1_team", nodes.d1_team)
    g.add_node("D2_describe", nodes.d2_describe)
    g.add_node("D3_contain", nodes.d3_contain)
    g.add_node("D4_root_cause", nodes.d4_root_cause)
    g.add_node("await_approval", nodes.await_approval)
    g.add_node("hitl_gate", nodes.hitl_gate)
    g.add_edge(START, "intake")
    g.add_conditional_edges("intake", nodes.after_intake,
                            ["D1_team", "D2_describe", "D3_contain", END])
    g.add_edge(["D1_team", "D3_contain"], "D4_root_cause")
    g.add_edge(["D2_describe", "D4_root_cause"], "await_approval")
    g.add_edge("await_approval", "hitl_gate")
    g.add_edge("hitl_gate", END)
    return g.compile(checkpointer=checkpointer)


def thread(case_id: str, deps: Deps | None = None) -> dict[str, Any]:
    cfg: dict[str, Any] = {"configurable": {"thread_id": case_id}}
    if deps is not None:
        cfg["configurable"]["deps"] = deps
    return cfg


async def run_case(store: Any, deps: Deps, case_id: str) -> dict[str, Any]:
    """Ejecuta el grafo hasta el interrupt (o END). Un fallo no esperado deja el caso en `error`
    con un mensaje genérico (el detalle, solo en el log)."""
    graph = build_graph(store.saver)
    cfg = thread(case_id, deps)
    try:
        await graph.ainvoke({"case_id": case_id, "status": "drafting",
                             "started_at": time.time()}, cfg)
    except Exception as exc:
        logger.exception("8d: fallo del grafo en el caso %s (%s)", case_id, type(exc).__name__)
        try:
            await graph.aupdate_state(cfg, {"status": "error",
                                            "error": "No se ha podido completar el borrador."})
        except Exception:
            logger.warning("8d: no se pudo marcar el error del caso %s", case_id)
    return await view(store, case_id)


async def resume_case(store: Any, deps: Deps, case_id: str) -> dict[str, Any]:
    """Reanuda el hilo tras una decisión humana guardada (M3-T4). `hitl_gate` la valida; si no
    vale lanza `nodes.ApprovalRequired` (el caso sigue pendiente). El valor de reanudación no
    lleva datos: el grafo no confía en él."""
    from langgraph.types import Command

    graph = build_graph(store.saver)
    await graph.ainvoke(Command(resume={"case_id": case_id}), thread(case_id, deps))
    return await view(store, case_id)


async def view(store: Any, case_id: str) -> dict[str, Any]:
    """Estado público del caso: borrador D1–D4 con citas, consultas ERP, hipótesis y avisos."""
    graph = build_graph(store.saver)
    snap = await graph.aget_state(thread(case_id))
    v: dict[str, Any] = dict(snap.values or {})
    interrupts = [i.value for t in snap.tasks for i in (t.interrupts or ())]
    status = v.get("status") or "queued"
    if status in ("approved", "rejected"):
        pass  # decisión humana: estado final (congelado)
    elif interrupts:
        status = "pending_approval"
    elif status == "pending_approval":
        status = "drafting"  # D4 terminó pero el interrupt aún no se ha registrado
    done = {p["node"] for p in v.get("progress") or []}
    progress = v.get("progress") or []
    started = v.get("started_at")
    drafting = [p for p in progress if p["node"] not in _NOT_DRAFT]  # sin el tiempo humano
    elapsed = (max(p["at"] for p in drafting) - started) if drafting and started else None
    c = v.get("complaint") or {}
    return {
        "case_id": case_id, "complaint_id": v.get("complaint_id"), "status": status,
        "error": v.get("error"), "language": v.get("language"),
        "customer": {k: (v.get("customer") or {}).get(k) for k in (
            "code", "name", "report_template", "report_language", "containment_hours",
            "report_days")},
        "complaint": {k: c.get(k) for k in (
            "complaint_id", "customer_code", "part_ref", "drawing_no", "lot_codes",
            "delivery_notes", "qty_affected", "issued_date", "defect_description", "evidence",
            "requested_deadlines", "language", "injection_suspected", "source")},
        "draft": {"d1": v.get("d1"), "d2": v.get("d2"), "d3": v.get("d3"), "d4": v.get("d4")},
        "erp_queries": v.get("erp_queries") or [],
        "warnings": v.get("warnings") or [],
        "progress": progress,
        "pending_nodes": [n for n in NODES if n not in done and n not in _NOT_DRAFT],
        "interrupt": interrupts[0] if interrupts else None,
        "llm": [{k: x.get(k) for k in ("node", "prompt_version", "model", "provider",
                                       "latency_ms", "prompt_tokens", "completion_tokens",
                                       "cost_usd", "used_fallback", "error", "discarded")}
                for x in v.get("llm") or []],
        "elapsed_s": round(elapsed, 1) if elapsed is not None else None,
        "ai_generated": True,
        # M3-T4: versión = sha256 de D1–D4 (la que hay que enviar a approve/reject).
        "version": hitl.draft_hash(hitl.draft_of(v)),
        "approved": status == "approved",
        "approval": v.get("approval"),
        "draft_original": v.get("draft_original"),
    }
