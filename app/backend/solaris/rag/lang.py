"""Detección mínima de idioma ES/EN (texto fijo de "no encontrado" y recuperación cruzada)."""

from __future__ import annotations

import re

_EN_TXT = """the what which who how is are was were of for to does do did and on in with after
    must when why"""
_ES_TXT = """el la los las qué que cuál cuáles quién cómo es son de del para por en con y hay se
    tiene cada"""
_EN_WORDS = frozenset(_EN_TXT.split())
_ES_WORDS = frozenset(_ES_TXT.split())


def guess_lang(text: str) -> str:
    words = re.findall(r"[a-záéíóúñü]+", text.lower())
    en = sum(w in _EN_WORDS for w in words)
    es = sum(w in _ES_WORDS for w in words) + (2 if re.search(r"[¿¡ñáéíóú]", text.lower()) else 0)
    return "en" if en > es else "es"
