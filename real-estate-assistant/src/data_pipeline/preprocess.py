"""Preprocess generated Excel listings into clean Parquet."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src import config


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    """基础清洗：去重、数值/日期转换、必填列空值剔除。"""
    df = df.copy()
    df.drop_duplicates(subset=["id"], inplace=True)
    numeric_cols = ["price", "bedrooms", "bathrooms", "area_sqm", "year_built"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["has_parking"] = df["has_parking"].astype(bool)
    df["listing_date"] = pd.to_datetime(df["listing_date"], errors="coerce")
    df.dropna(subset=["id", "price", "area_sqm"], inplace=True)
    return df


def preprocess_listings(
    input_path: str | None = None, output_path: str | None = None
) -> str:
    """读取 Excel，调用清洗逻辑并输出 Parquet，返回保存路径字符串。"""
    src_path = config.RAW_LISTINGS_PATH if input_path is None else input_path
    dst_path = config.PROCESSED_LISTINGS_PATH if output_path is None else output_path
    dst_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_excel(src_path)
    clean_df = _clean(df)
    clean_df.to_parquet(dst_path, index=False)
    return str(dst_path)


if __name__ == "__main__":
    saved = preprocess_listings()
    print(f"Preprocessed listings to {saved}")
