"""LLM answer generation placeholder."""
from __future__ import annotations

from typing import Any, Dict, List


class AnswerGenerator:
    """Use LLM to generate responses given ranked results (TODO: integrate LLM)."""

    def __init__(self) -> None:
        # TODO: configure model/provider
        pass

    def generate(self, user_query: str, results: List[Dict[str, Any]]) -> str:
        # TODO: craft prompt and call LLM
        return ""
