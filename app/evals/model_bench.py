"""Microbenchmark de latencia por (modelo, proveedor) con las llamadas reales del 8D (M3-T5).

Todas las llamadas pasan por `solaris.llm.route()` (ADR-0003) con una ficha temporal por tupla:
modelo sin fallback y `provider = {data_collection: deny, only: [proveedor],
allow_fallbacks: false}`. Si el proveedor no cumple `data_collection: deny`, OpenRouter no tiene
endpoint y la tupla queda descartada (se registra el error, no se reintenta con otro proveedor).

Entrada: un JSON de llamadas capturadas del grafo (tarea, mensajes y opciones `response_format` y
`max_tokens`), p. ej. las 4 de un 8D: parser (intake), D2, D4_similar y D4_hypotheses. Los mensajes
son del corpus sintético (ADR-0004) y no se versionan: se capturan con `--capture` (el parser
llama al LLM de la ficha por defecto; las llamadas `8d_draft` se graban y no se envían).

Métricas por tupla: tiempo total por llamada (p50/p95), TTFT y tiempo de generación según las
estadísticas de generación de OpenRouter (`GET /generation?id=`, solo metadatos), tokens, coste,
JSON válido y camino crítico LLM del 8D estimado = parser + max(D4_similar, D4_hypotheses) (D2
corre en paralelo con D1/D3/D4, ver graph.py).

Uso (desde la raíz del repo):
    uv run --project app/backend python app/evals/model_bench.py --capture 8D-CASE-01 --calls x.json
    uv run --project app/backend python app/evals/model_bench.py --calls x.json \
        --tuple deepseek/deepseek-chat@deepinfra --tuple mistralai/mistral-large-2512@mistral \
        --out raw/eval-runs/AAAA-MM-DD_model_bench.json
"""

from __future__ import annotations

import argparse
import asyncio
import functools
import json
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import yaml

EVALS_DIR = Path(__file__).resolve().parent
REPO_ROOT = EVALS_DIR.parents[1]
CASES_FILE = EVALS_DIR / "golden" / "8d_cases.jsonl"
CRITICAL_PARALLEL = ("D4_similar", "D4_hypotheses")


def percentile(values: list[float], q: float) -> float | None:
    """Percentil por el método del rango más cercano (n pequeño, sin interpolar)."""
    vals = sorted(v for v in values if v is not None)
    if not vals:
        return None
    k = max(0, min(len(vals) - 1, round(q / 100 * len(vals) + 0.5) - 1))
    return vals[k]


def parse_tuple(spec: str) -> tuple[str, str]:
    """`modelo@proveedor` → (modelo, proveedor). El proveedor es el slug/tag de OpenRouter."""
    model, sep, provider = spec.partition("@")
    if not sep or not model.strip() or not provider.strip():
        raise ValueError(f"Tupla inválida '{spec}': se espera modelo@proveedor")
    return model.strip(), provider.strip()


def bench_cards(model: str, provider: str, tasks: list[str], base: dict[str, Any]) -> dict:
    """Ficha temporal: mismas tareas y límites que la ficha base, modelo fijo, un proveedor."""
    out: dict[str, Any] = {"tasks": {}}
    for t in tasks:
        b = dict(base["tasks"][t])
        out["tasks"][t] = {
            "model": model,
            "provider_policy": {"data_collection": "deny", "only": [provider],
                                "allow_fallbacks": False},
            "provenance": {"organization": "bench", "country": "--"},
            "max_tokens": b.get("max_tokens", 2048),
            "temperature": b.get("temperature", 0.2),
        }
    return out


def critical_path_ms(calls: list[dict[str, Any]]) -> float | None:
    """Parser + max(D4_similar, D4_hypotheses) de un caso: la espera LLM del camino crítico."""
    by = {c["node"]: c.get("latency_ms") for c in calls if c.get("ok")}
    if by.get("intake_parse") is None or not any(by.get(n) for n in CRITICAL_PARALLEL):
        return None
    return by["intake_parse"] + max(by.get(n) or 0 for n in CRITICAL_PARALLEL)


def summarize(calls: list[dict[str, Any]]) -> dict[str, Any]:
    ok = [c for c in calls if c.get("ok")]
    lat = [c["latency_ms"] for c in ok]
    ttft = [c["ttft_ms"] for c in ok if c.get("ttft_ms") is not None]
    tps = [c["completion_tokens"] / (c["generation_ms"] / 1000) for c in ok
           if c.get("generation_ms") and c.get("completion_tokens")]
    cases = sorted({c["case_id"] for c in calls})
    crit = [critical_path_ms([c for c in calls if c["case_id"] == k]) for k in cases]
    return {
        "calls": len(calls), "ok": len(ok), "json_valid": sum(1 for c in ok if c.get("json_valid")),
        "errors": sorted({c["error"] for c in calls if c.get("error")}),
        "providers_seen": sorted({c["provider"] for c in ok if c.get("provider")}),
        "latency_ms": {"p50": percentile(lat, 50), "p95": percentile(lat, 95),
                       "max": max(lat) if lat else None},
        "ttft_ms": {"p50": percentile(ttft, 50), "p95": percentile(ttft, 95)},
        "tokens_per_s": {"p50": percentile(tps, 50)},
        "completion_tokens": sum(c.get("completion_tokens") or 0 for c in ok),
        "reasoning_tokens": sum(c.get("reasoning_tokens") or 0 for c in ok),
        "cost_usd": round(sum(c.get("cost_usd") or 0 for c in ok), 5),
        "critical_path_llm_ms": [x for x in crit if x is not None],
    }


# --- captura ------------------------------------------------------------------------------------


async def capture(case_ids: list[str], out: Path) -> None:
    from solaris.agents.complaint import parse_async
    from solaris.agents.eight_d import graph as g
    from solaris.agents.eight_d.nodes import Deps
    from solaris.agents.eight_d.store import open_store
    from solaris.auth.core import Principal
    from solaris.llm import LLMProviderError, route
    from solaris.rag.acl import resolve_role
    from solaris.settings import get_settings

    settings = get_settings()
    cases = [json.loads(x) for x in CASES_FILE.open(encoding="utf-8")]
    captured: list[dict[str, Any]] = []
    for case in [c for c in cases if c["case_id"] in case_ids]:
        def rec(task: str, messages: list[dict[str, Any]], *, _real: bool, _cid: str = case[
                "case_id"], **kw: Any) -> Any:
            node = "intake_parse" if _real else (kw.get("audit_meta") or {}).get("node")
            captured.append({"case_id": _cid, "task": task, "node": node, "messages": messages,
                             "opts": {k: kw[k] for k in ("response_format", "max_tokens")
                                      if k in kw}})
            if _real:
                return route(task, messages, **kw)
            raise LLMProviderError("captura: llamada 8d_draft no enviada")

        role = resolve_role(case["user"], settings.acl_file)
        p = Principal(case["user"], role or "", "eval-bench-capture")
        path = REPO_ROOT / case["complaint_file"]
        async with open_store(settings) as store:
            cid = await store.create_case(complaint_id=case["complaint_id"], created_by=p.user,
                                          created_role=p.role, source="inbox",
                                          filename=path.name, data=path.read_bytes())
            deps = Deps(principal=p, settings=settings, load_file=store.load_file,
                        route_fn=functools.partial(rec, _real=False),
                        parse_fn=functools.partial(parse_async,
                                                   route_fn=functools.partial(rec, _real=True)))
            v = await g.run_case(store, deps, cid)
        print(case["case_id"], v["status"], {x["node"]: x["ms"] for x in v["progress"]})
    out.write_text(json.dumps(captured, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"→ {out} ({len(captured)} llamadas)")


# --- benchmark ----------------------------------------------------------------------------------


def fill_generation_stats(rows: list[dict[str, Any]], settings: Any) -> None:
    """TTFT (`latency`), tiempo de generación y tokens de razonamiento de OpenRouter. Las
    estadísticas tardan unos segundos en aparecer: se piden al final, con reintentos."""
    import httpx

    key = settings.openrouter_api_key.get_secret_value().strip()
    headers = {"Authorization": f"Bearer {key}"}
    pending = [r for r in rows if r.get("generation_id")]
    with httpx.Client() as http:
        for wait in (5.0, 10.0, 20.0):
            if not pending:
                break
            time.sleep(wait)
            left = []
            for r in pending:
                g = http.get("https://openrouter.ai/api/v1/generation",
                             params={"id": r["generation_id"]}, headers=headers, timeout=20)
                if g.status_code != 200:
                    left.append(r)
                    continue
                d = (g.json() or {}).get("data") or {}
                r.update(ttft_ms=d.get("latency"), generation_ms=d.get("generation_time"),
                         reasoning_tokens=d.get("native_tokens_reasoning"),
                         provider_stats=d.get("provider_name"))
            pending = left


def run_tuple(model: str, provider: str, calls: list[dict[str, Any]], base: dict[str, Any],
              settings: Any) -> list[dict[str, Any]]:
    import httpx
    from solaris.llm import LLMError, route

    tasks = sorted({c["task"] for c in calls})
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as fh:
        yaml.safe_dump(bench_cards(model, provider, tasks, base), fh)
        cards_path = Path(fh.name)
    s = settings.model_copy(update={"models_file": cards_path, "llm_max_retries": 0,
                                    "llm_timeout_s": 150.0})
    ids: list[str] = []

    def hook(resp: Any) -> None:
        resp.read()
        try:
            ids.append(resp.json().get("id") or "")
        except ValueError:
            ids.append("")

    rows: list[dict[str, Any]] = []
    with httpx.Client(event_hooks={"response": [hook]}) as http:
        for c in calls:
            ids.clear()
            row: dict[str, Any] = {"case_id": c["case_id"], "node": c["node"], "task": c["task"],
                                   "ok": False}
            try:
                res = route(c["task"], c["messages"], settings=s, client=http,
                            audit=lambda *a, **k: None, **c["opts"])
            except LLMError as exc:
                row["error"] = str(exc)[:200]
                rows.append(row)
                print(f"  {model}@{provider} {c['node']}: ERROR {row['error']}")
                continue
            try:
                json.loads(res.content)
                valid = True
            except ValueError:
                valid = False
            row.update(ok=True, provider=res.provider, latency_ms=res.latency_ms,
                       prompt_tokens=res.prompt_tokens, completion_tokens=res.completion_tokens,
                       cost_usd=res.cost_usd, json_valid=valid, generation_id=ids[-1] if ids
                       else None)
            rows.append(row)
            print(f"  {model}@{provider} {c['node']}: {res.provider} {res.latency_ms:.0f} ms "
                  f"out={res.completion_tokens} json={valid} ${res.cost_usd}")
    cards_path.unlink(missing_ok=True)
    return rows


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Microbenchmark (modelo, proveedor) del 8D (M3-T5)")
    p.add_argument("--capture", nargs="*", default=None, help="case_ids a capturar")
    p.add_argument("--calls", type=Path, required=True, help="JSON de llamadas capturadas")
    p.add_argument("--tuple", action="append", default=[], help="modelo@proveedor (repetible)")
    p.add_argument("--nodes", default=None, help="filtra nodos (coma), p. ej. D4_hypotheses")
    p.add_argument("--out", type=Path, default=None)
    a = p.parse_args(argv)
    if a.capture is not None:
        asyncio.run(capture(a.capture, a.calls))
        return 0
    from solaris.settings import get_settings

    settings = get_settings()
    if settings.openrouter_api_key is None or not settings.openrouter_api_key.get_secret_value():
        print("Requiere OPENROUTER_API_KEY en .env")
        return 2
    base = yaml.safe_load(settings.models_file.read_text(encoding="utf-8"))
    calls = json.loads(a.calls.read_text(encoding="utf-8"))
    if a.nodes:
        keep = {x.strip() for x in a.nodes.split(",")}
        calls = [c for c in calls if c["node"] in keep]
    result: dict[str, Any] = {"calls_file_nodes": [(c["case_id"], c["node"]) for c in calls],
                              "tuples": {}}
    for spec in a.tuple:
        model, provider = parse_tuple(spec)
        result["tuples"][spec] = {"model": model, "provider": provider,
                                  "calls": run_tuple(model, provider, calls, base, settings)}
    fill_generation_stats([r for t in result["tuples"].values() for r in t["calls"]], settings)
    for spec, t in result["tuples"].items():
        t["summary"] = summarize(t["calls"])
        print(spec, json.dumps(t["summary"], ensure_ascii=False))
    if a.out:
        a.out.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"→ {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
