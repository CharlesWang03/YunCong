"""Query parsing (simple rule-based)."""
from __future__ import annotations

import re
from typing import Dict, List


PRICE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*万")
BED_RE = re.compile(r"(\d+)\s*室")
AREA_RE = re.compile(r"(\d+)\s*平")


class QueryParser:
    """Parse user input into structured filters and keyword hints."""

    def parse(self, text: str) -> Dict[str, object]:
        normalized = text.strip()
        min_price = None
        max_price = None
        if match := PRICE_RE.search(normalized):
            min_price = float(match.group(1))

        bedrooms = int(match.group(1)) if (match := BED_RE.search(normalized)) else None
        min_area = int(match.group(1)) if (match := AREA_RE.search(normalized)) else None

        keywords: List[str] = []
        for kw in ["地铁", "学校", "公园", "安静", "景观"]:
            if kw in normalized:
                keywords.append(kw)

        return {
            "min_price": min_price,
            "max_price": max_price,
            "bedrooms": bedrooms,
            "min_area": min_area,
            "keywords": keywords,
            "raw": text,
        }
