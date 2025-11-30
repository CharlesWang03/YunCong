"""Listing summary analytics."""
from __future__ import annotations

from typing import Dict, Any

import pandas as pd


def summarize_listings(listings: pd.DataFrame, user_filter: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """对候选房源做统计分析，返回可供 LLM/前端使用的字典。"""
    if listings.empty:
        return {"count": 0}

    user_filter = user_filter or {}
    df = listings.copy()

    summary: Dict[str, Any] = {
        "count": len(df),
        "price_min": float(df["total_price"].min(skipna=True)),
        "price_max": float(df["total_price"].max(skipna=True)),
        "price_avg": float(df["total_price"].mean(skipna=True)),
        "price_median": float(df["total_price"].median(skipna=True)),
        "unit_price_avg": float(df["unit_price"].mean(skipna=True)) if "unit_price" in df else None,
        "area_min": float(df["area"].min(skipna=True)) if "area" in df else None,
        "area_max": float(df["area"].max(skipna=True)) if "area" in df else None,
        "area_avg": float(df["area"].mean(skipna=True)) if "area" in df else None,
        "bedrooms_distribution": df["bedrooms"].value_counts(dropna=True).to_dict() if "bedrooms" in df else {},
        "distance_to_subway_avg": float(df["distance_to_subway"].mean(skipna=True)) if "distance_to_subway" in df else None,
        "distance_to_subway_min": float(df["distance_to_subway"].min(skipna=True)) if "distance_to_subway" in df else None,
        "school_district_ratio": float((df.get("school_district", pd.Series(False))).fillna(False).mean()),
        "year_built_min": int(df["year_built"].min(skipna=True)) if "year_built" in df else None,
        "year_built_max": int(df["year_built"].max(skipna=True)) if "year_built" in df else None,
        "year_built_avg": float(df["year_built"].mean(skipna=True)) if "year_built" in df else None,
        "user_filter": user_filter,
    }

    return summary
