"""Quality and relevance scoring with normalized components."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import numpy as np
import pandas as pd

from src.config import settings


@dataclass
class QualityComponents:
    price: float
    area: float
    age: float
    subway: float
    school: float
    floor: float
    orientation: float
    renovation: float


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


def _linear_norm(value: float, min_v: float, max_v: float) -> float:
    if max_v == min_v:
        return 0.5
    return _clip01((value - min_v) / (max_v - min_v))


def _compute_quality_components(row: pd.Series, user_filters: Dict[str, any]) -> QualityComponents:
    """按各维度生成 0~1 的质量子分数。"""
    # 价格：贴近预算上限/区间越高
    budget_max = user_filters.get("max_price")
    budget_min = user_filters.get("min_price")
    price = row.get("total_price")
    if price is None or np.isnan(price):
        price_score = 0.5
    elif budget_max is None:
        price_score = 1 - _clip01(price / (np.nanmax([price, 1]) + 1e-6)) * 0.2  # 没预算略偏中性
    else:
        if price > budget_max * 1.2:
            price_score = 0.0
        else:
            target = budget_max if budget_min is None else (budget_min + budget_max) / 2
            price_score = 1 - abs(price - target) / (budget_max * 0.2 + 1e-6)
            price_score = _clip01(price_score)

    # 面积：落在期望区间越高，超出区间平滑下降
    area = row.get("area")
    area_min = user_filters.get("min_area")
    area_max = user_filters.get("max_area")
    if area is None or np.isnan(area):
        area_score = 0.5
    elif area_min is None and area_max is None:
        area_score = _clip01(area / 120)  # 120 平以上趋于饱和
    else:
        target = (area_min or area) if area_max is None else (area_min or 0 + area_max) / 2 if area_min else area_max
        area_score = 1 - abs(area - target) / ((area_max or area) * 0.3 + 1e-6)
        area_score = _clip01(area_score)

    # 年代：越新越高
    year_built = row.get("year_built")
    age_score = 0.5 if year_built is None or np.isnan(year_built) else _linear_norm(year_built, 1990, 2025)

    # 地铁 / 学区
    dist_subway = row.get("distance_to_subway")
    subway_score = 1.0 if dist_subway is None or np.isnan(dist_subway) else _clip01((2.0 - dist_subway) / 1.8)
    school_score = 1.0 if row.get("school_district") else 0.0

    # 楼层：中高层适中，极高/极低扣分
    floor = row.get("floor") or 0
    total_floors = row.get("total_floors") or max(floor, 1)
    if total_floors <= 1:
        floor_score = 0.5
    else:
        ratio = floor / total_floors
        floor_score = 1 - abs(ratio - 0.5) * 1.5  # 中间层高，顶/底稍降
        floor_score = _clip01(floor_score)

    # 朝向
    orient = str(row.get("orientation") or "")
    if "南" in orient:
        orientation_score = 1.0
    elif "东" in orient or "西" in orient:
        orientation_score = 0.6
    else:
        orientation_score = 0.4

    # 装修
    reno = str(row.get("renovation") or "")
    if "精" in reno:
        renovation_score = 1.0
    elif "简" in reno:
        renovation_score = 0.7
    elif "毛" in reno:
        renovation_score = 0.4
    else:
        renovation_score = 0.5

    return QualityComponents(
        price=price_score,
        area=area_score,
        age=age_score,
        subway=subway_score,
        school=school_score,
        floor=floor_score,
        orientation=orientation_score,
        renovation=renovation_score,
    )


def compute_quality_scores(df: pd.DataFrame, user_filters: Optional[Dict[str, any]] = None) -> pd.DataFrame:
    """计算质量子分数并融合为 quality_score。"""
    user_filters = user_filters or {}
    records = []
    for _, row in df.iterrows():
        comp = _compute_quality_components(row, user_filters)
        w = settings.quality_weights
        quality_score = (
            comp.price * w.get("price", 0)
            + comp.area * w.get("area", 0)
            + comp.age * w.get("age", 0)
            + comp.subway * w.get("subway", 0)
            + comp.school * w.get("school", 0)
            + comp.floor * w.get("floor", 0)
            + comp.orientation * w.get("orientation", 0)
            + comp.renovation * w.get("renovation", 0)
        )
        quality_score = _clip01(quality_score)
        record = row.to_dict()
        record.update({
            "quality_score": quality_score,
            "price_score": comp.price,
            "area_score": comp.area,
            "age_score": comp.age,
            "subway_score": comp.subway,
            "school_score": comp.school,
            "floor_score": comp.floor,
            "orientation_score": comp.orientation,
            "renovation_score": comp.renovation,
        })
        records.append(record)
    return pd.DataFrame(records)


def _normalize_scores(scores: pd.Series) -> pd.Series:
    if scores.empty:
        return scores
    min_v = scores.min()
    max_v = scores.max()
    if max_v == min_v:
        return pd.Series(0.0, index=scores.index)
    return (scores - min_v) / (max_v - min_v)


def fuse_scores(df: pd.DataFrame, weights: dict | None = None, query_context: Optional[Dict[str, any]] = None) -> pd.DataFrame:
    """归一化 BM25/语义，融合质量分并应用 promotion 乘性提升。"""
    w = weights or {
        "quality": settings.weights.quality,
        "bm25": settings.weights.bm25,
        "semantic": settings.weights.semantic,
        "promotion_max_boost": settings.weights.promotion,
    }

    # 质量分
    fused = compute_quality_scores(df)

    # 归一化 BM25 / 语义
    fused["bm25_score"] = fused.get("bm25_score", 0).fillna(0)
    fused["semantic_score"] = fused.get("semantic_score", 0).fillna(0)
    fused["bm25_norm"] = _normalize_scores(fused["bm25_score"])
    fused["semantic_norm"] = _normalize_scores(fused["semantic_score"])

    # 基础融合
    base_score = (
        fused["quality_score"] * w.get("quality", 0)
        + fused["bm25_norm"] * w.get("bm25", 0)
        + fused["semantic_norm"] * w.get("semantic", 0)
    )

    # promotion 乘性加成（限制上限）
    promo_raw = fused.get("promotion_weight", 0).fillna(0)
    promo_score = np.sqrt(promo_raw)  # 平滑压缩
    promotion_factor = 1.0 + w.get("promotion_max_boost", 0) * promo_score.clip(0, 1)

    fused["fused_score"] = base_score * promotion_factor
    fused["base_score"] = base_score
    fused["promotion_factor"] = promotion_factor
    return fused
