"""Query parsing placeholder (structured + fuzzy)."""
from __future__ import annotations

from typing import Dict


class QueryParser:
    """Parse user input into structured filters and soft signals (TODO: implement NLP)."""

    def parse(self, text: str) -> Dict[str, object]:
        """Return dict of hard/soft conditions from user query."""
        # TODO: implement rule-based/LLM parsing
        return {}
