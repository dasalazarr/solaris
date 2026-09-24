"""Punto único de acceso a LLMs (ADR-0003). Nadie llama a un proveedor directamente."""

from solaris.llm.config import ModelCard, load_model_cards
from solaris.llm.errors import (
    LLMAuthError,
    LLMConfigError,
    LLMError,
    LLMProviderError,
    UnknownTaskError,
)
from solaris.llm.router import LLMResult, route

__all__ = [
    "LLMAuthError",
    "LLMConfigError",
    "LLMError",
    "LLMProviderError",
    "LLMResult",
    "ModelCard",
    "UnknownTaskError",
    "load_model_cards",
    "route",
]
