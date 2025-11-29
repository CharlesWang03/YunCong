import pandas as pd

from src.data_pipeline.preprocess import preprocess_listings


def test_preprocess_listings(tmp_path):
    """写入示例 Excel 并运行清洗，校验输出行数与关键字段类型。"""
    src = tmp_path / "raw.xlsx"
    dst = tmp_path / "out.parquet"
    sample = pd.DataFrame(
        {
            "id": ["L1", "L2"],
            "city": ["A", "B"],
            "district": ["X", "Y"],
            "price": [1_000_000, 2_000_000],
            "bedrooms": [2, 3],
            "bathrooms": [1, 2],
            "area_sqm": [80, 120],
            "property_type": ["apartment", "house"],
            "year_built": [2000, 2010],
            "has_parking": [True, False],
            "description": ["Nice", "Great"],
            "listing_date": ["2024-01-01", "2024-02-01"],
        }
    )
    sample.to_excel(src, index=False)

    saved_path = preprocess_listings(input_path=src, output_path=dst)
    processed = pd.read_parquet(saved_path)

    assert len(processed) == 2
    assert processed["price"].dtype.kind in {"i", "f"}
    assert processed["listing_date"].notna().all()
