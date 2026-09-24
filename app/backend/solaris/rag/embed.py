"""Embeddings multilingües locales (M2-T3, F01). 1024 dimensiones = `vector(1024)` de 001_rag.

    from solaris.rag.embed import embed, embed_query
    vecs = embed(["texto del chunk", ...])      # pasajes (documentos)
    qvec = embed_query("pregunta del usuario")  # consultas (M2-T5)

Backends (`EMBED_BACKEND` en .env):
  * `fastembed` (por defecto): `intfloat/multilingual-e5-large` exportado a ONNX
    (repo `qdrant/multilingual-e5-large-onnx`, revisión fijada en Settings). Sin torch. El modelo
    se descarga una sola vez a `EMBED_MODEL_DIR` como ficheros reales (no symlinks de la caché de
    HF: onnxruntime ≥1.2x rechaza datos externos que "escapan" del directorio del modelo). e5 exige
    los prefijos "passage: " / "query: ", que añade este módulo.
  * `fake`: vector determinista por hashing de tokens (sin descarga ni red). Textos con palabras en
    común dan vectores con coseno > 0, así que sirve también para tests de recuperación.

Los embeddings NO pasan por OpenRouter ni por `llm.route()`: ADR-0003 regula las llamadas a LLM;
aquí no sale ningún dato del equipo (el modelo corre en local).
"""

import hashlib
import math
import re
import threading
from collections.abc import Sequence
from functools import lru_cache
from typing import Literal

from solaris.settings import Settings, get_settings

DIM = 1024
Kind = Literal["passage", "query"]
_TOKEN_RE = re.compile(r"\w+", re.UNICODE)
_lock = threading.Lock()


class EmbeddingError(RuntimeError):
    pass


# --- fake ------------------------------------------------------------------------------------


def _fake_vector(text: str) -> list[float]:
    """Bolsa de tokens con hashing (signo y cubo por sha256), normalizada L2. Determinista."""
    v = [0.0] * DIM
    tokens = _TOKEN_RE.findall(text.lower()) or [""]
    for tok in tokens:
        h = hashlib.sha256(tok.encode("utf-8")).digest()
        idx = int.from_bytes(h[:4], "big") % DIM
        v[idx] += 1.0 if h[4] & 1 else -1.0
    norm = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / norm for x in v]


# --- fastembed -------------------------------------------------------------------------------


def ensure_model(settings: Settings | None = None) -> None:
    """Descarga el modelo ONNX (revisión fijada) si aún no está en `embed_model_dir`."""
    s = settings or get_settings()
    marker = s.embed_model_dir / "model.onnx"
    if marker.exists():
        return
    from huggingface_hub import snapshot_download

    snapshot_download(
        s.embed_model_repo, revision=s.embed_model_revision, local_dir=s.embed_model_dir
    )


@lru_cache(maxsize=2)
def _fastembed_model(model: str, model_dir: str):
    from fastembed import TextEmbedding

    return TextEmbedding(model, specific_model_path=model_dir)


def _embed_fastembed(texts: list[str], s: Settings) -> list[list[float]]:
    ensure_model(s)
    with _lock:
        m = _fastembed_model(s.embed_model, str(s.embed_model_dir))
        return [v.tolist() for v in m.embed(texts, batch_size=s.embed_batch_size)]


# --- API -------------------------------------------------------------------------------------


def embed(
    texts: Sequence[str], *, kind: Kind = "passage", settings: Settings | None = None
) -> list[list[float]]:
    """Embeddings de 1024 dims, uno por texto y en el mismo orden."""
    s = settings or get_settings()
    items = list(texts)
    if not items:
        return []
    if s.embed_backend == "fake":
        out = [_fake_vector(t) for t in items]
    elif s.embed_backend == "fastembed":
        out = _embed_fastembed([f"{kind}: {t}" for t in items], s)
    else:  # pragma: no cover - Literal lo impide
        raise EmbeddingError(f"Backend de embeddings desconocido: {s.embed_backend!r}")
    if len(out) != len(items) or any(len(v) != DIM for v in out):
        raise EmbeddingError(f"El backend {s.embed_backend} no devolvió {len(items)}×{DIM}")
    return out


def embed_query(text: str, *, settings: Settings | None = None) -> list[float]:
    return embed([text], kind="query", settings=settings)[0]


def to_pgvector(v: Sequence[float]) -> str:
    """Literal de pgvector ('[x,y,...]') para pasar como parámetro con cast ::vector."""
    return "[" + ",".join(f"{x:.7g}" for x in v) + "]"
