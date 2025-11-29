"""Quality and relevance scoring placeholder."""
from __future__ import annotations

import pandas as pd


def compute_quality_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Compute structural quality scores (TODO: price/area/distance heuristics)."""
    # TODO: implement quality scoring logic
    return df


def fuse_scores(df: pd.DataFrame, weights: dict | None = None) -> pd.DataFrame:
    """Fuse BM25/semantic/quality scores (TODO: configurable weights)."""
    # TODO: implement score fusion
    return df
