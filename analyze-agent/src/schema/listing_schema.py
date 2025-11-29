"""Listing schema definition."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Listing:
    """Structured representation of a property listing (TODO: validation)."""
    id: str
    city: str
    district: str
    community: str
    address: str
    total_price: float
    unit_price: float
    tax_included: Optional[bool]
    management_fee: Optional[float]
    bedrooms: Optional[int]
    livingrooms: Optional[int]
    bathrooms: Optional[int]
    area: Optional[float]
    usable_area: Optional[float]
    layout: Optional[str]
    floor: Optional[str]
    total_floors: Optional[int]
    orientation: Optional[str]
    building_type: Optional[str]
    year_built: Optional[int]
    elevator: Optional[bool]
    parking: Optional[bool]
    distance_to_subway: Optional[float]
    nearest_subway: Optional[str]
    distance_to_school: Optional[float]
    distance_to_park: Optional[float]
    lat: Optional[float]
    lon: Optional[float]
    company: Optional[str] = None  # 房源公司/中介方
    promotion_weight: Optional[float] = None  # 投送量/加权值，排序时可加权
    tags: List[str] = field(default_factory=list)
    renovation: Optional[str] = None
    school_district: Optional[str] = None
    noise_level: Optional[str] = None
    view_quality: Optional[str] = None
    description: Optional[str] = None
    community_intro: Optional[str] = None
    surrounding: Optional[str] = None
    quality_score: Optional[float] = None
    subway_score: Optional[float] = None
    school_score: Optional[float] = None


# TODO: add factory methods (from_df/from_dict) and validation helpers.
