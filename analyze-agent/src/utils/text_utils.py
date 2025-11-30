"""Text utilities for tokenization/normalization."""
from __future__ import annotations

import re
from typing import Iterable

import jieba


def normalize_text(text: str) -> str:
    """Basic cleanup: strip whitespace and unify spaces."""
    return re.sub(r"\s+", " ", text.strip()) if isinstance(text, str) else ""


def tokenize(text: str) -> list[str]:
    """Tokenize Chinese text using jieba; fallback to simple split if empty."""
    norm = normalize_text(text)
    if not norm:
        return []
    return [t for t in jieba.lcut(norm) if t.strip()]


def join_tokens(tokens: Iterable[str]) -> str:
    """Join tokens with spaces for vectorizers that expect whitespace-separated tokens."""
    return " ".join(t for t in tokens if t)
