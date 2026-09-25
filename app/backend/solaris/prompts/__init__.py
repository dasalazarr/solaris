"""Prompts de sistema versionados (spec §4.1 de M2-T8).

Cada prompt es un fichero estático `<nombre>.v<N>.md` en este directorio. **No se interpola nada**
en él (ni la petición, ni el corpus, ni el ERP): se envía byte a byte como mensaje `system`. Su
versión y su sha256 van al audit (`audit_meta.security.prompt_version/prompt_sha256`).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class SystemPrompt:
    version: str  # p. ej. "rag_answer.v1"
    text: str
    sha256: str

    def leak_lines(self, min_chars: int = 40) -> list[str]:
        """Líneas del prompt lo bastante largas y específicas como para detectar que el modelo las
        ha copiado en su salida (spec §4.4: revelar el prompt de sistema)."""
        out = []
        for line in self.text.splitlines():
            s = line.strip().lstrip("-*#> ").strip()
            if len(s) >= min_chars:
                out.append(s)
        return out


@lru_cache
def load_prompt(version: str) -> SystemPrompt:
    """Carga `<version>.md` (p. ej. `rag_answer.v1`). Solo nombres del directorio, sin rutas."""
    if not version.replace(".", "").replace("_", "").isalnum() or "/" in version:
        raise ValueError(f"versión de prompt no válida: {version!r}")
    path = PROMPTS_DIR / f"{version}.md"
    raw = path.read_bytes()
    return SystemPrompt(version=version, text=raw.decode("utf-8"),
                        sha256=hashlib.sha256(raw).hexdigest())
