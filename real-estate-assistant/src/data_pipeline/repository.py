"""Data access layer for listings."""
from __future__ import annotations

import pandas as pd

from src import config
from src.models import SearchFilter
from src.search.filter_engine import apply_filters


class DataRepository:
    def __init__(self, parquet_path: str | None = None) -> None:
        """保存处理后数据的 Parquet 路径，可在初始化时覆盖默认路径。"""
        self.parquet_path = config.PROCESSED_LISTINGS_PATH if parquet_path is None else parquet_path

    def load(self) -> pd.DataFrame:
        """读取处理后房源并返回 DataFrame。"""
        return pd.read_parquet(self.parquet_path)

    def search(self, filters: SearchFilter) -> pd.DataFrame:
        """加载数据并基于给定 SearchFilter 进行筛选。"""
        df = self.load()
        return apply_filters(df, filters)
