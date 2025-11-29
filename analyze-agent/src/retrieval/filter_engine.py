"""Structured filter engine."""
from __future__ import annotations

from typing import Any, Dict

import pandas as pd


def apply_filters(df: pd.DataFrame, conditions: Dict[str, Any]) -> pd.DataFrame:
    """Apply hard filters to listings using boolean masks."""
    mask = pd.Series(True, index=df.index)

    if city := conditions.get("city"):
        mask &= df["city"] == city
    if districts := conditions.get("districts"):
        mask &= df["district"].isin(districts)

    min_price = conditions.get("min_price")
    max_price = conditions.get("max_price")
    if min_price is not None:
        mask &= df["total_price"] >= min_price
    if max_price is not None:
        mask &= df["total_price"] <= max_price

    min_area = conditions.get("min_area")
    max_area = conditions.get("max_area")
    if min_area is not None:
        mask &= df["area"] >= min_area
    if max_area is not None:
        mask &= df["area"] <= max_area

    bedrooms = conditions.get("bedrooms")
    if bedrooms is not None:
        mask &= df["bedrooms"] >= bedrooms

    if school_district := conditions.get("school_district"):
        mask &= df["school_district"] == school_district

    return df.loc[mask].reset_index(drop=True)
