"""Ranking orchestrator placeholder."""
from __future__ import annotations

import pandas as pd


class Ranker:
    """Combine scores and return sorted top-N results (TODO: implement)."""

    def __init__(self) -> None:
        # TODO: inject scorers/weights
        pass

    def rank(self, df: pd.DataFrame, top_k: int = 10) -> pd.DataFrame:
        # TODO: apply fuse_scores and sort
        return df.head(top_k)
