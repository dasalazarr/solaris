"""Carga de la ficha de modelo por tarea (F10) desde config/models.yaml."""

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from solaris.llm.errors import LLMConfigError


class ProviderPolicy(BaseModel):
    """Preferencias de proveedor de OpenRouter (objeto `provider` del payload)."""

    model_config = ConfigDict(extra="forbid")

    # Guardarraíl: la ficha no puede permitir retención/entrenamiento (ADR-0003).
    data_collection: Literal["deny"] = "deny"
    zdr: bool | None = None
    order: list[str] | None = None
    allow_fallbacks: bool | None = None
    only: list[str] | None = None
    ignore: list[str] | None = None
    # M2-T6: orden de preferencia DENTRO del pool que ya filtran data_collection/only/ignore (no lo
    # amplía). "throughput" evita los proveedores lentos (medido: 4–27 s frente a ~5 s).
    sort: Literal["price", "throughput", "latency"] | None = None

    def to_payload(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True)


class Provenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    organization: str
    country: str


class ModelCard(BaseModel):
    """Ficha de modelo de una tarea."""

    model_config = ConfigDict(extra="forbid")

    task: str
    model: str
    fallback: str | None = None
    provider_policy: ProviderPolicy = Field(default_factory=ProviderPolicy)
    provenance: Provenance
    fallback_provenance: Provenance | None = None
    region_note: str = ""
    max_tokens: int = Field(default=2048, gt=0)
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    eval_score: float | None = None


def load_model_cards(path: Path) -> dict[str, ModelCard]:
    try:
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise LLMConfigError(f"No se puede leer la ficha de modelos {path}: {exc}") from exc
    if not isinstance(raw, dict) or not isinstance(raw.get("tasks"), dict):
        raise LLMConfigError(f"{path}: se esperaba una clave raíz 'tasks' con un mapa de tareas")
    cards: dict[str, ModelCard] = {}
    for task, spec in raw["tasks"].items():
        try:
            cards[task] = ModelCard.model_validate({**(spec or {}), "task": task})
        except ValidationError as exc:
            raise LLMConfigError(f"{path}: ficha inválida para la tarea '{task}': {exc}") from exc
    return cards
