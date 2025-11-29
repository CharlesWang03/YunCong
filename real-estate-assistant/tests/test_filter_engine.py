import pandas as pd

from src.models import SearchFilter
from src.search.filter_engine import apply_filters


def test_apply_filters_by_price_and_bedrooms():
    """按最低价格、卧室数、车位筛选后应仅剩符合条件的房源。"""
    df = pd.DataFrame(
        {
            "id": ["L1", "L2", "L3"],
            "price": [500_000, 1_500_000, 3_000_000],
            "bedrooms": [1, 2, 4],
            "bathrooms": [1, 2, 3],
            "area_sqm": [50, 90, 150],
            "has_parking": [False, True, True],
            "district": ["A", "B", "C"],
            "city": ["X", "Y", "Z"],
            "property_type": ["apartment", "house", "apartment"],
            "year_built": [2000, 2010, 2015],
            "description": ["near subway", "parking", "garden"],
            "listing_date": pd.to_datetime(["2024-01-01", "2024-02-01", "2024-03-01"]),
        }
    )

    filters = SearchFilter(min_price=1_000_000, bedrooms=2, has_parking=True)
    result = apply_filters(df, filters)

    assert len(result) == 2
    assert set(result["id"]) == {"L2", "L3"}
