"""Registro estructurado de llamadas (permitidas, denegadas, escrituras rechazadas).

`AuditSink` es la interfaz: M4-T2 (audit real, F08) la sustituye por un sink append-only en BD sin
tocar las herramientas. De momento, `JsonlAuditSink` escribe una línea JSON por evento en
`app/mcp/erp_mock/logs/` (ignorado por git).
"""

import json
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol


class AuditSink(Protocol):
    def emit(self, event: dict[str, Any]) -> None: ...


class JsonlAuditSink:
    def __init__(self, log_dir: Path, filename: str = "erp_mock.jsonl") -> None:
        self.path = Path(log_dir) / filename
        self._lock = threading.Lock()

    def emit(self, event: dict[str, Any]) -> None:
        record = {"ts": datetime.now(UTC).isoformat(timespec="milliseconds"), **event}
        line = json.dumps(record, ensure_ascii=False, default=str)
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")


class MemoryAuditSink:
    """Sink en memoria para tests."""

    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def emit(self, event: dict[str, Any]) -> None:
        self.events.append(event)
