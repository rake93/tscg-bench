"""Independent token counter — does not trust the TSCG bridge's self-reported counts.

Uses tiktoken if installed; falls back to a 4-char heuristic otherwise.
"""

from __future__ import annotations

import json
from typing import Any

try:
    import tiktoken
    _TIKTOKEN_AVAILABLE = True
except ImportError:
    _TIKTOKEN_AVAILABLE = False


_ENCODING_CACHE: dict[str, Any] = {}


def _encoding(model: str):
    if not _TIKTOKEN_AVAILABLE:
        return None
    if model in _ENCODING_CACHE:
        return _ENCODING_CACHE[model]
    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")
    _ENCODING_CACHE[model] = enc
    return enc


def count_tokens(text: str, model: str = "gpt-4o") -> int:
    if _TIKTOKEN_AVAILABLE:
        enc = _encoding(model)
        if enc is not None:
            return len(enc.encode(text))
    return max(1, len(text) // 4)


def count_schema_tokens(schema: list[dict[str, Any]], model: str = "gpt-4o") -> int:
    return count_tokens(json.dumps(schema, separators=(",", ":")), model=model)


def tiktoken_available() -> bool:
    return _TIKTOKEN_AVAILABLE
