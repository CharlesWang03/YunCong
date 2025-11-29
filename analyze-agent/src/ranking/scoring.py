"""Quality and relevance scoring."""
from __future__ import annotations

import pandas as pd

from src.config import settings


def compute_quality_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Compute heuristic quality scores (in-place copy)."""
    scored = df.copy()

    # Normalize helpful fields
    def norm(series: pd.Series) -> pd.Series:
        if series.isna().all():
            return pd.Series(0.5, index=series.index)
        s = series.fillna(series.median())
        min_v, max_v = s.min(), s.max()
        if max_v == min_v:
            return pd.Series(0.5, index=series.index)
        return (s - min_v) / (max_v - min_v)

    price_norm = norm(scored["unit_price"]) if "unit_price" in scored else pd.Series(0, index=scored.index)
    area_norm = norm(scored["area"]) if "area" in scored else pd.Series(0, index=scored.index)
    year_norm = norm(scored["year_built"]) if "year_built" in scored else pd.Series(0, index=scored.index)
    subway_norm = norm(scored.get("distance_to_subway", pd.Series(0, index=scored.index)))
    school_norm = norm(scored.get("distance_to_school", pd.Series(0, index=scored.index)))
    promotion = scored.get("promotion_weight", pd.Series(0, index=scored.index)).fillna(0)

    scored["quality_score"] = scored.get("quality_score", pd.Series(0.5, index=scored.index)).fillna(0.5)
    scored["subway_score"] = scored.get("subway_score", 1 - subway_norm).fillna(0.0)
    scored["school_score"] = scored.get("school_score", 1 - school_norm).fillna(0.0)

    scored["promotion_score"] = promotion

    # Higher better: larger area, newer year, closer subway/school, lower unit price
    scored["computed_quality"] = (
        (1 - price_norm) * 0.3
        + area_norm * 0.15
        + year_norm * 0.1
        + (1 - subway_norm) * 0.15
        + (1 - school_norm) * 0.1
        + scored["quality_score"] * 0.2
    )
    return scored


def fuse_scores(df: pd.DataFrame, weights: dict | None = None) -> pd.DataFrame:
    w = weights or {
        "quality": settings.weights.quality,
        "bm25": settings.weights.bm25,
        "semantic": settings.weights.semantic,
        "promotion": settings.weights.promotion,
    }
    fused = df.copy()
    fused = compute_quality_scores(fused)
    fused["bm25_score"] = fused.get("bm25_score", 0).fillna(0)
    fused["semantic_score"] = fused.get("semantic_score", 0).fillna(0)
    fused["promotion_score"] = fused.get("promotion_score", 0).fillna(0)

    fused["fused_score"] = (
        fused["computed_quality"] * w.get("quality", 0)
        + fused["bm25_score"] * w.get("bm25", 0)
        + fused["semantic_score"] * w.get("semantic", 0)
        + fused["promotion_score"] * w.get("promotion", 0)
    )
    return fused
