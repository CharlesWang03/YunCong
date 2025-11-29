from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Listing:
    id: str
    city: str
    district: str
    price: float
    bedrooms: int
    bathrooms: int
    area_sqm: float
    property_type: str
    year_built: int
    has_parking: bool
    description: str
    listing_date: date
    score: Optional[float] = None
