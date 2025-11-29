"""Ranking orchestrator."""
from __future__ import annotations

import pandas as pd

from src.ranking.scoring import fuse_scores


class Ranker:
    """Combine scores and return sorted top-N results."""

    def __init__(self, weights: dict | None = None) -> None:
        self.weights = weights or {}

    def rank(self, df: pd.DataFrame, top_k: int = 10) -> pd.DataFrame:
        scored = fuse_scores(df, weights=self.weights)
        return scored.sort_values("fused_score", ascending=False).head(top_k).reset_index(drop=True)
