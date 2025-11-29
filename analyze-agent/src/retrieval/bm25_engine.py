"""BM25 retrieval placeholder."""
from __future__ import annotations

from typing import List

import pandas as pd


class BM25Engine:
    """Wrap BM25 index for lexical relevance (TODO: load/build index)."""

    def __init__(self) -> None:
        # TODO: load BM25 index and corpus metadata
        pass

    def search(self, query: str, top_k: int = 20) -> List[int]:
        """Return candidate row indices ranked by BM25 (TODO: implement)."""
        return []

    def attach_scores(self, df: pd.DataFrame, query: str, top_k: int = 20) -> pd.DataFrame:
        """Run search and merge BM25 scores into a DataFrame copy."""
        # TODO: implement score merge
        return df
