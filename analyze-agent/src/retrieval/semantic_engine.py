"""Semantic retrieval placeholder."""
from __future__ import annotations

from typing import List

import pandas as pd


class SemanticEngine:
    """Vector/LLM-based semantic search wrapper (TODO: init with embeddings/index)."""

    def __init__(self) -> None:
        # TODO: load embeddings/index or configure online service
        pass

    def search(self, query: str, top_k: int = 20) -> List[int]:
        """Return candidate row indices ranked by semantic similarity (TODO)."""
        return []

    def attach_scores(self, df: pd.DataFrame, query: str, top_k: int = 20) -> pd.DataFrame:
        """Run semantic search and merge scores into a DataFrame copy."""
        # TODO: implement score merge
        return df
