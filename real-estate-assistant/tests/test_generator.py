import pandas as pd

from src.data_pipeline.generator import generate_listings


def test_generate_listings_shape():
    """生成 10 条房源后，行数正确且包含关键字段。"""
    df = generate_listings(n=10)
    assert len(df) == 10
    expected_cols = {
        "id",
        "city",
        "district",
        "price",
        "bedrooms",
        "bathrooms",
        "area_sqm",
        "property_type",
        "year_built",
        "has_parking",
        "description",
        "listing_date",
    }
    assert expected_cols.issubset(df.columns)
    assert pd.api.types.is_numeric_dtype(df["price"])
