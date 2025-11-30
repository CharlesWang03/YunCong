"""Query parsing (rule-based with city/district detection and exact room parsing)."""
from __future__ import annotations

import re
from typing import Dict, List

CITY_DISTRICTS = {
    "北京": ["海淀", "朝阳", "东城", "西城", "丰台", "通州"],
    "上海": ["徐汇", "浦东", "静安", "长宁", "杨浦", "普陀"],
    "深圳": ["南山", "福田", "罗湖", "宝安", "龙华"],
}
ALL_DISTRICTS = [d for districts in CITY_DISTRICTS.values() for d in districts]

PRICE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*万")
BED_LIVING_RE = re.compile(r"(\d+)\s*室\s*(\d+)\s*厅")
BED_RE = re.compile(r"(\d+)\s*室")
AREA_RE = re.compile(r"(\d+)\s*平")


class QueryParser:
    """解析用户输入，转为结构化过滤条件与关键词。"""

    def parse(self, text: str) -> Dict[str, object]:
        normalized = normalize_cn_numbers(text.strip())
        min_price = None
        max_price = None
        if match := PRICE_RE.search(normalized):
            min_price = float(match.group(1))

        bedrooms_exact = None
        livingrooms_exact = None
        if match := BED_LIVING_RE.search(normalized):
            bedrooms_exact = int(match.group(1))
            livingrooms_exact = int(match.group(2))
        elif match := BED_RE.search(normalized):
            bedrooms_exact = int(match.group(1))

        min_area = int(match.group(1)) if (match := AREA_RE.search(normalized)) else None

        city = None
        for c in CITY_DISTRICTS.keys():
            if c in normalized:
                city = c
                break

        district = None
        district_candidates = CITY_DISTRICTS.get(city, ALL_DISTRICTS)
        for d in district_candidates:
            if d in normalized:
                district = d
                break

        keywords: List[str] = []
        for kw in ["地铁", "学校", "公园", "安静", "景观", "学区"]:
            if kw in normalized:
                keywords.append(kw)

        return {
            "city": city,
            "districts": [district] if district else None,
            "min_price": min_price,
            "max_price": max_price,
            "bedrooms_exact": bedrooms_exact,
            "livingrooms_exact": livingrooms_exact,
            "min_area": min_area,
            "keywords": keywords,
            "raw": text,
        }


CN_NUM_MAP = {
    "零": "0",
    "〇": "0",
    "一": "1",
    "两": "2",
    "二": "2",
    "三": "3",
    "四": "4",
    "五": "5",
    "六": "6",
    "七": "7",
    "八": "8",
    "九": "9",
    "十": "10",
}


def normalize_cn_numbers(text: str) -> str:
    """Convert simple中文数字（含“两”）到阿拉伯数字，便于正则匹配。"""
    for cn, digit in CN_NUM_MAP.items():
        text = text.replace(cn, digit)
    text = text.replace("居", "室")
    return text
