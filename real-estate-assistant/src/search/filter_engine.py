"""Filter listings using SearchFilter criteria."""
from __future__ import annotations

import pandas as pd

from src.models import SearchFilter


def apply_filters(df: pd.DataFrame, filters: SearchFilter) -> pd.DataFrame:
    """在 DataFrame 上应用 SearchFilter 各项条件，返回筛选后的副本。"""
    mask = pd.Series([True] * len(df))

    if filters.min_price is not None:
        mask &= df["price"] >= filters.min_price
    if filters.max_price is not None:
        mask &= df["price"] <= filters.max_price
    if filters.min_area is not None:
        mask &= df["area_sqm"] >= filters.min_area
    if filters.max_area is not None:
        mask &= df["area_sqm"] <= filters.max_area
    if filters.bedrooms is not None:
        mask &= df["bedrooms"] >= filters.bedrooms
    if filters.bathrooms is not None:
        mask &= df["bathrooms"] >= filters.bathrooms
    if filters.has_parking is not None:
        mask &= df["has_parking"] == filters.has_parking
    if filters.cities:
        mask &= df["city"].isin(filters.cities)
    if filters.districts:
        mask &= df["district"].isin(filters.districts)
    if filters.property_types:
        mask &= df["property_type"].isin(filters.property_types)
    if filters.keywords:
        keyword_mask = pd.Series([True] * len(df))
        for kw in filters.keywords:
            keyword_mask &= df["description"].str.contains(kw, case=False, na=False)
        mask &= keyword_mask

    return df.loc[mask].reset_index(drop=True)
