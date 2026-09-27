"""M3-T6 (security, S-T3-2): los checkpoints del 8D se leen con el serializador en modo estricto.

Quien pudiera escribir en `eightd.checkpoint_*` no debe conseguir que, al cargar un checkpoint, se
reconstruya un tipo arbitrario por módulo y nombre (con el modo por defecto de LangGraph solo se
avisa). El estado del 8D es JSON, y lo que LangGraph guarda por su cuenta (`Interrupt`, fechas,
UUID) está en la lista segura de la librería.
"""

from __future__ import annotations

import asyncio
import datetime
import os
import uuid
from dataclasses import dataclass

from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.types import Interrupt

from solaris.agents.eight_d.store import PgCaseStore, strict_serde


@dataclass
class _Gadget:
    """Tipo ajeno a la lista segura (simula un objeto inyectado en la tabla de checkpoints)."""

    cmd: str = "no-op"


def test_strict_serde_does_not_rebuild_unlisted_types():
    blob = JsonPlusSerializer().dumps_typed(_Gadget())  # lo que escribiría un atacante
    out = strict_serde().loads_typed(blob)
    assert not isinstance(out, _Gadget)
    assert out == {"cmd": "no-op"}  # queda como datos planos


def test_strict_serde_keeps_what_the_graph_stores():
    s = strict_serde()
    for obj in (Interrupt(value={"case_id": "x", "status": "pending_approval"}, id="i1"),
                {"d": datetime.date(2026, 9, 27), "u": uuid.uuid4(), "txt": "D1–D4",
                 "n": [1, 2.5]}):
        assert s.loads_typed(s.dumps_typed(obj)) == obj
    assert s.pickle_fallback is False


def test_pg_store_uses_the_strict_serde():
    class _Conn:  # AsyncPostgresSaver solo guarda la conexión al construirse
        pass

    async def build() -> PgCaseStore:  # el saver asíncrono necesita un bucle de eventos
        return PgCaseStore(_Conn())  # type: ignore[arg-type]

    store = asyncio.run(build())
    blob = JsonPlusSerializer().dumps_typed(_Gadget())
    assert not isinstance(store.saver.serde.loads_typed(blob), _Gadget)


def test_langsmith_tracing_is_off_even_if_the_environment_enables_it():
    """M3-T6 (S-T3-3): el grafo no manda trazas a LangSmith aunque el entorno lo pida."""
    import subprocess
    import sys

    code = ("import solaris.agents.eight_d.graph\n"
            "from langsmith.utils import tracing_is_enabled\n"
            "from langchain_core.tracers.context import _tracing_v2_is_enabled\n"
            "print(bool(tracing_is_enabled()), bool(_tracing_v2_is_enabled()))\n")
    env = {**os.environ, "LANGSMITH_TRACING": "true", "LANGCHAIN_TRACING_V2": "true",
           "LANGSMITH_API_KEY": "lsv2-test-not-a-key"}
    out = subprocess.run([sys.executable, "-c", code], env=env,  # noqa: S603 (argv fijo)
                         capture_output=True, text=True, check=True, timeout=60)
    assert out.stdout.split() == ["False", "False"]
