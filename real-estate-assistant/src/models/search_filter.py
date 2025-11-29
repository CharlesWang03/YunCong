from dataclasses import dataclass
from typing import Optional, Sequence


@dataclass
class SearchFilter:
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_area: Optional[float] = None
    max_area: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    cities: Optional[Sequence[str]] = None
    districts: Optional[Sequence[str]] = None
    property_types: Optional[Sequence[str]] = None
    has_parking: Optional[bool] = None
    keywords: Optional[Sequence[str]] = None
