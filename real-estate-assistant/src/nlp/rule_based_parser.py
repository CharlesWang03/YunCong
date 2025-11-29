"""Very small rule-based parser from text to SearchFilter."""
from __future__ import annotations

import re
from typing import List, Optional, Sequence

from src.models import SearchFilter

PRICE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*[mM]")
PRICE_RE_CN = re.compile(r"(\d+(?:\.\d+)?)\s*万")
BED_RE = re.compile(r"(\d+)\s*bed")
BED_RE_CN = re.compile(r"(\d+)\s*室")
BATH_RE = re.compile(r"(\d+)\s*bath")
BATH_RE_CN = re.compile(r"(\d+)\s*卫")


def parse_query(text: str) -> SearchFilter:
    """从简短文本中解析价格/卧室/卫/关键词等，构造 SearchFilter。"""
    normalized = text.lower()
    min_price = None
    if match := PRICE_RE.search(normalized):
        min_price = float(match.group(1)) * 1_000_000
    elif match := PRICE_RE_CN.search(normalized):
        min_price = float(match.group(1)) * 10_000

    bedrooms = int(match.group(1)) if (match := BED_RE.search(normalized)) else None
    if bedrooms is None and (match := BED_RE_CN.search(text)):
        bedrooms = int(match.group(1))

    bathrooms = int(match.group(1)) if (match := BATH_RE.search(normalized)) else None
    if bathrooms is None and (match := BATH_RE_CN.search(text)):
        bathrooms = int(match.group(1))

    keywords: List[str] = []
    for kw in ["parking", "subway", "garden", "school", "地铁", "学校", "公园", "车位"]:
        if kw in text.lower() or kw in text:
            keywords.append(kw)

    has_parking: Optional[bool] = True if ("parking" in normalized or "车位" in text) else None

    return SearchFilter(
        min_price=min_price,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        has_parking=has_parking,
        keywords=keywords or None,
    )


def parse_fuzzy_query(text: str, catalog: dict[str, Sequence[str]]) -> SearchFilter:
    """
    更口语化的模糊解析：识别城市/城区/户型、卧室卫数、价格（万），常见需求词。
    仅根据单一输入构造筛选条件，适配中文描述。
    """
    normalized = text.lower()

    city = next((c for c in catalog.get("cities", []) if c in text), None)
    district = next((d for d in catalog.get("districts", []) if d in text), None)
    prop = next((p for p in catalog.get("property_types", []) if p.lower() in normalized or p in text), None)

    min_price = None
    if match := PRICE_RE_CN.search(text):
        min_price = float(match.group(1)) * 10_000
    elif match := PRICE_RE.search(normalized):
        min_price = float(match.group(1)) * 1_000_000

    bedrooms = int(match.group(1)) if (match := BED_RE_CN.search(text)) else None
    bathrooms = int(match.group(1)) if (match := BATH_RE_CN.search(text)) else None

    has_parking: Optional[bool] = True if ("车位" in text or "停车" in text or "parking" in normalized) else None

    keywords: List[str] = []
    for kw in ["学校", "学区", "地铁", "公园", "商场", "医院"]:
        if kw in text:
            keywords.append(kw)

    return SearchFilter(
        min_price=min_price,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        has_parking=has_parking,
        cities=[city] if city else None,
        districts=[district] if district else None,
        property_types=[prop] if prop else None,
        keywords=keywords or None,
    )
