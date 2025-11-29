"""Structured filter engine."""
from __future__ import annotations

from typing import Any, Dict, Iterable

import pandas as pd


def _to_list(val: Any) -> Iterable:
    if val is None:
        return []
    if isinstance(val, (list, tuple, set)):
        return val
    return [val]


def apply_filters(df: pd.DataFrame, conditions: Dict[str, Any]) -> pd.DataFrame:
    """Apply hard filters to listings using boolean masks."""
    mask = pd.Series(True, index=df.index)

    if city := conditions.get("city"):
        mask &= df["city"] == city
    if districts := conditions.get("districts"):
        district_list = list(_to_list(districts))
        mask &= df["district"].isin(district_list)

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

    bedrooms_exact = conditions.get("bedrooms_exact")
    bedrooms_min = conditions.get("bedrooms")
    if bedrooms_exact is not None and "bedrooms" in df:
        mask &= df["bedrooms"] == bedrooms_exact
    elif bedrooms_min is not None and "bedrooms" in df:
        mask &= df["bedrooms"] >= bedrooms_min

    livingrooms_exact = conditions.get("livingrooms_exact")
    if livingrooms_exact is not None and "livingrooms" in df:
        mask &= df["livingrooms"] == livingrooms_exact

    if school_district := conditions.get("school_district"):
        mask &= df["school_district"] == school_district

    return df.loc[mask].reset_index(drop=True)
