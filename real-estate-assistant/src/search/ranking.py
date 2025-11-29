"""Ranking strategies for filtered listings."""
from __future__ import annotations

import pandas as pd


def _safe_norm(series: pd.Series) -> pd.Series:
    """Min-max 归一化，缺失用中位数填充，避免除零返回 0.5。"""
    s = series.fillna(series.median())
    min_v = s.min()
    max_v = s.max()
    if max_v == min_v:
        return pd.Series([0.5] * len(series), index=series.index)
    return (s - min_v) / (max_v - min_v)


def apply_quality_score(df: pd.DataFrame) -> pd.DataFrame:
    """根据价格/面积、距离、市政年限、车位等打分，分值越高越优。"""
    scored = df.copy()
    scored["price_per_sqm"] = scored["price"] / scored["area_sqm"].replace(0, pd.NA)

    price_norm = _safe_norm(scored["price_per_sqm"]).clip(0, 1)
    center_norm = _safe_norm(scored.get("distance_to_center_km", pd.Series([0] * len(df)))).clip(0, 1)
    school_norm = _safe_norm(scored.get("distance_to_school_km", pd.Series([0] * len(df)))).clip(0, 1)
    year_norm = _safe_norm(scored.get("year_built", pd.Series([scored["year_built"].median()] * len(df))))
    area_norm = _safe_norm(scored["area_sqm"])
    bedrooms_norm = _safe_norm(scored["bedrooms"])
    parking_bonus = scored["has_parking"].fillna(False).astype(float) * 0.05

    scored["score"] = (
        (1 - price_norm) * 0.32
        + (1 - center_norm) * 0.18
        + (1 - school_norm) * 0.12
        + year_norm * 0.12
        + area_norm * 0.10
        + bedrooms_norm * 0.06
        + parking_bonus
    )
    return scored


def apply_ranking(df: pd.DataFrame, strategy: str = "price_low_to_high") -> pd.DataFrame:
    """按给定策略排序房源，默认价格从低到高。未知策略则保持原顺序。"""
    if strategy == "price_low_to_high":
        return df.sort_values("price", ascending=True).reset_index(drop=True)
    if strategy == "price_high_to_low":
        return df.sort_values("price", ascending=False).reset_index(drop=True)
    if strategy == "newest":
        return df.sort_values("listing_date", ascending=False).reset_index(drop=True)
    if strategy == "quality_score":
        scored = apply_quality_score(df)
        return scored.sort_values("score", ascending=False).reset_index(drop=True)
    return df.reset_index(drop=True)
