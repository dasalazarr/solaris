"""Errores del router LLM. Los mensajes nunca incluyen la clave ni el contenido enviado."""


class LLMError(Exception):
    """Base de errores del router."""


class LLMConfigError(LLMError):
    """Configuración inválida o incompleta (clave ausente, yaml mal formado...)."""


class UnknownTaskError(LLMConfigError):
    """La tarea no tiene ficha en models.yaml."""


class LLMAuthError(LLMError):
    """OpenRouter rechaza la clave (401/403). No se intenta el fallback."""


class LLMProviderError(LLMError):
    """Fallo del proveedor tras agotar reintentos (5xx, 429, timeout, respuesta inválida)."""

    def __init__(self, message: str, *, attempts: int = 0) -> None:
        super().__init__(message)
        self.attempts = attempts
