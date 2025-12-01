"""预处理房源数据并写入 Parquet。"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from src.config import settings


def _normalize_tags(raw: Iterable[str]) -> list[str]:
    """清洗标签字段，按分隔符拆分，去空去重。"""
    tags = []
    for t in raw:
        if pd.isna(t):
            continue
        if isinstance(t, str):
            parts = [p.strip() for p in t.replace("/", ",").replace(";", ",").split(",") if p.strip()]
            tags.extend(parts)
        elif isinstance(t, list):
            tags.extend([str(x).strip() for x in t if str(x).strip()])
    return list(dict.fromkeys(tags))  # unique preserve order


def preprocess_dataframe(df_raw: pd.DataFrame) -> pd.DataFrame:
    """对原始 DataFrame 清洗并对齐标准字段。"""
    df = df_raw.copy()

    # 规范标签字段
    list_fields = ["tags"]
    for col in list_fields:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: _normalize_tags(x if isinstance(x, list) else [x]))

    # 布尔字段
    bool_fields = ["tax_included", "elevator", "parking", "school_district"]
    for col in bool_fields:
        if col in df.columns:
            df[col] = df[col].astype("boolean")

    # 数值字段
    numeric_cols = [
        "total_price",
        "unit_price",
        "management_fee",
        "bedrooms",
        "livingrooms",
        "bathrooms",
        "area",
        "usable_area",
        "floor",
        "total_floors",
        "year_built",
        "distance_to_subway",
        "distance_to_school",
        "distance_to_park",
        "lat",
        "lon",
        "quality_score",
        "subway_score",
        "school_score",
        "promotion_weight",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # 必填字段缺失则丢弃
    df.dropna(subset=["id", "city", "district"], inplace=True)
    return df


def preprocess(input_path: Path | None = None, output_path: Path | None = None) -> Path:
    """读取 Excel，清洗字段并写入 Parquet。"""
    src_path = input_path or settings.paths.raw_excel
    dst_path = output_path or settings.paths.processed_parquet
    dst_path.parent.mkdir(parents=True, exist_ok=True)

    df_raw = pd.read_excel(src_path)
    clean_df = preprocess_dataframe(df_raw)
    clean_df.to_parquet(dst_path, index=False)
    return dst_path


def main() -> None:
    """CLI 入口：执行预处理。"""
    saved = preprocess()
    print(f"Preprocessed data saved to {saved}")


if __name__ == "__main__":
    main()
