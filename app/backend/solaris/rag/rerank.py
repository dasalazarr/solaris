"""Rerank con cross-encoder local (M2-T5, F02).

    from solaris.rag.rerank import rerank
    scores = rerank("pregunta", ["pasaje 1", "pasaje 2"])   # una puntuación por pasaje, mismo orden

Backends (`RERANK_BACKEND` en .env):
  * `fastembed` (por defecto): `BAAI/bge-reranker-base` en ONNX (XLM-RoBERTa, MIT, ~1,1 GB). Se
    descarga una vez, con revisión fijada, a `RERANK_MODEL_DIR` como ficheros reales (mismo motivo
    que en solaris.rag.embed: onnxruntime rechaza los symlinks de la caché de HF). Alternativa
    configurable: `jinaai/jina-reranker-v2-base-multilingual` (mejor multilingüe, CC-BY-NC-4.0).
  * `fake`: solapamiento de tokens consulta/pasaje, determinista (tests, sin descarga).
  * `none`: sin rerank (lo decide `solaris.rag.retrieve`).

Como los embeddings, corre en local: no pasa por OpenRouter ni por `llm.route()` (ADR-0003 regula
llamadas a LLM) y no sale ningún dato del equipo.
"""

import math
import re
import threading
from collections.abc import Sequence
from functools import lru_cache

from solaris.settings import Settings, get_settings

_TOKEN_RE = re.compile(r"\w+(?:-\w+)*", re.UNICODE)
_lock = threading.Lock()
_ALLOW = ["onnx/model.onnx", "*.json", "sentencepiece.bpe.model"]


class RerankError(RuntimeError):
    pass


def _fake_scores(query: str, passages: list[str]) -> list[float]:
    q = set(_TOKEN_RE.findall(query.lower()))
    norm = math.sqrt(len(q)) or 1.0
    return [len(q & set(_TOKEN_RE.findall(p.lower()))) / norm for p in passages]


def ensure_model(settings: Settings | None = None) -> None:
    """Descarga el modelo ONNX (revisión fijada) si aún no está en `rerank_model_dir`."""
    s = settings or get_settings()
    if (s.rerank_model_dir / "onnx" / "model.onnx").exists():
        return
    from huggingface_hub import snapshot_download

    snapshot_download(
        s.rerank_model_repo,
        revision=s.rerank_model_revision,
        local_dir=s.rerank_model_dir,
        allow_patterns=_ALLOW,
    )


@lru_cache(maxsize=2)
def _model(model: str, model_dir: str):
    from fastembed.rerank.cross_encoder import TextCrossEncoder

    return TextCrossEncoder(model, specific_model_path=model_dir)


def warmup(settings: Settings | None = None) -> None:
    """Carga el modelo (≈1 s) para que la primera consulta no pague la carga."""
    s = settings or get_settings()
    if s.rerank_backend == "fastembed":
        ensure_model(s)
        _model(s.rerank_model, str(s.rerank_model_dir))


def rerank(
    query: str, passages: Sequence[str], *, settings: Settings | None = None
) -> list[float]:
    """Puntuación de relevancia (logit, mayor = mejor) de cada pasaje para la consulta."""
    s = settings or get_settings()
    items = list(passages)
    if not items:
        return []
    if s.rerank_backend == "fake":
        out = _fake_scores(query, items)
    elif s.rerank_backend == "fastembed":
        ensure_model(s)
        with _lock:
            m = _model(s.rerank_model, str(s.rerank_model_dir))
            out = [float(x) for x in m.rerank(query, items, batch_size=16)]
    else:
        raise RerankError(f"Backend de rerank no utilizable: {s.rerank_backend!r}")
    if len(out) != len(items):
        raise RerankError(f"El backend {s.rerank_backend} no devolvió {len(items)} puntuaciones")
    return out
