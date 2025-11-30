"""Excel parser for uploaded listings."""
from __future__ import annotations

from typing import IO, Union

import pandas as pd

from src.pipeline.preprocess import preprocess_dataframe

# 简单的列名映射：中文/常见别名 -> 内部字段
COLUMN_MAP = {
    "城市": "city",
    "区": "district",
    "行政区": "district",
    "城区": "district",
    "小区": "community",
    "小区名称": "community",
    "地址": "address",
    "总价": "total_price",
    "总价(万)": "total_price",
    "单价": "unit_price",
    "单价(元/平)": "unit_price",
    "物业费": "management_fee",
    "卧室": "bedrooms",
    "厅": "livingrooms",
    "客厅": "livingrooms",
    "卫生间": "bathrooms",
    "面积": "area",
    "建筑面积": "area",
    "套内面积": "usable_area",
    "楼层": "floor",
    "总楼层": "total_floors",
    "朝向": "orientation",
    "建筑类型": "building_type",
    "建成年份": "year_built",
    "电梯": "elevator",
    "停车": "parking",
    "距地铁": "distance_to_subway",
    "最近地铁": "nearest_subway",
    "距学校": "distance_to_school",
    "距公园": "distance_to_park",
    "纬度": "lat",
    "经度": "lon",
    "标签": "tags",
    "装修": "renovation",
    "学区": "school_district",
    "描述": "description",
    "小区介绍": "community_intro",
    "周边": "surrounding",
}


def parse_uploaded_excel(file: Union[str, IO[bytes]]) -> pd.DataFrame:
    """读取用户上传的 Excel 文件，重命名列并清洗，返回 DataFrame。"""
    df_raw = pd.read_excel(file)
    # 重命名列
    rename_map = {col: COLUMN_MAP.get(col, col) for col in df_raw.columns}
    df_raw = df_raw.rename(columns=rename_map)

    # 填充必需字段缺失的 id
    if "id" not in df_raw.columns:
        df_raw["id"] = [f"UP{i:06d}" for i in range(1, len(df_raw) + 1)]

    # 调用预处理逻辑
    df_clean = preprocess_dataframe(df_raw)
    return df_clean
