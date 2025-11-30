"""Generate synthetic listings with stratified coverage."""
from __future__ import annotations

import random
from datetime import date
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
from faker import Faker

from src.config import settings

fake = Faker("zh_CN")
random.seed(42)
np.random.seed(42)

CITIES = {
    "上海": ["徐汇", "浦东", "静安", "长宁", "杨浦", "普陀"],
    "北京": ["海淀", "朝阳", "东城", "西城", "丰台", "通州"],
    "深圳": ["南山", "福田", "罗湖", "宝安", "龙华"],
}
ORIENTATIONS = ["南北", "朝南", "朝东", "朝西", "朝北"]
BUILDING_TYPES = ["板楼", "塔楼", "洋房", "别墅"]
RENOVATIONS = ["精装修", "简装", "毛坯"]
COMPANIES = ["链家", "我爱我家", "德佑", "自营"]
BEDROOM_BUCKETS = [1, 2, 3, 4]


def _mock_listing(
    i: int,
    city: str | None = None,
    district: str | None = None,
    bedrooms: int | None = None,
) -> dict:
    """生成单条房源；可强制城市/城区/卧室数用于分层覆盖。"""
    city = city or random.choice(list(CITIES.keys()))
    district = district or random.choice(CITIES[city])
    community = fake.street_name()
    address = fake.address()

    area = float(np.clip(np.random.normal(90, 30), 45, 200))
    bedrooms = bedrooms if bedrooms is not None else random.randint(1, 4)
    livingrooms = 1
    bathrooms = random.randint(1, 2)
    layout = f"{bedrooms}室{livingrooms}厅{bathrooms}卫"

    total_price = round(random.uniform(200, 1200), 2)  # 万
    unit_price = round((total_price * 10000) / area, 2)
    tax_included = random.choice([True, False])
    management_fee = round(random.uniform(1.5, 6.0), 2)

    floor = random.randint(1, 30)
    total_floors = random.randint(max(floor, 6), 34)
    orientation = random.choice(ORIENTATIONS)
    building_type = random.choice(BUILDING_TYPES)
    year_built = random.randint(1995, date.today().year)
    elevator = random.choice([True, False])
    parking = random.choice([True, False])

    distance_to_subway = round(random.uniform(0.2, 3.5), 2)
    nearest_subway = fake.street_suffix() + "站"
    distance_to_school = round(random.uniform(0.2, 3.0), 2)
    distance_to_park = round(random.uniform(0.1, 2.5), 2)
    lat = round(30 + random.random() * 10, 6)
    lon = round(120 + random.random() * 10, 6)

    tags: List[str] = random.sample(
        ["近地铁", "满五唯一", "南北通透", "精装修", "学区房", "配套成熟", "采光好", "低噪音"],
        k=random.randint(2, 4),
    )
    renovation = random.choice(RENOVATIONS)
    school_district = random.choice([True, False])
    noise_level = random.randint(1, 5)
    view_quality = random.randint(1, 5)

    description = fake.text(max_nb_chars=180)
    community_intro = fake.text(max_nb_chars=120)
    surrounding = fake.text(max_nb_chars=120)

    quality_score = round(random.uniform(0.3, 0.95), 3)
    subway_score = round(max(0, 1 - distance_to_subway / 3.5), 3)
    school_score = round(max(0, 1 - distance_to_school / 3.0), 3)

    company = random.choice(COMPANIES)
    promotion_weight = round(random.uniform(0, 1.0), 3)

    return {
        "id": f"L{i:06d}",
        "city": city,
        "district": district,
        "community": community,
        "address": address,
        "total_price": total_price,
        "unit_price": unit_price,
        "tax_included": tax_included,
        "management_fee": management_fee,
        "bedrooms": bedrooms,
        "livingrooms": livingrooms,
        "bathrooms": bathrooms,
        "area": round(area, 2),
        "usable_area": round(area * random.uniform(0.7, 0.95), 2),
        "layout": layout,
        "floor": floor,
        "total_floors": total_floors,
        "orientation": orientation,
        "building_type": building_type,
        "year_built": year_built,
        "elevator": elevator,
        "parking": parking,
        "distance_to_subway": distance_to_subway,
        "nearest_subway": nearest_subway,
        "distance_to_school": distance_to_school,
        "distance_to_park": distance_to_park,
        "lat": lat,
        "lon": lon,
        "tags": tags,
        "renovation": renovation,
        "school_district": school_district,
        "noise_level": noise_level,
        "view_quality": view_quality,
        "description": description,
        "community_intro": community_intro,
        "surrounding": surrounding,
        "quality_score": quality_score,
        "subway_score": subway_score,
        "school_score": school_score,
        "company": company,
        "promotion_weight": promotion_weight,
    }


def generate_listings(n: int = 2000, coverage_per_bedroom: int = 8) -> pd.DataFrame:
    """按城市/城区/户型分层覆盖并补充随机样本，生成房源数据。"""
    records: List[dict] = []
    idx = 1
    # Coverage block: ensure each city/district/bedroom bucket has samples
    for city, districts in CITIES.items():
        for district in districts:
            for br in BEDROOM_BUCKETS:
                for _ in range(coverage_per_bedroom):
                    records.append(_mock_listing(idx, city=city, district=district, bedrooms=br))
                    idx += 1
    # Fill remaining with fully random samples
    remaining = max(0, n - len(records))
    for _ in range(remaining):
        records.append(_mock_listing(idx))
        idx += 1
    random.shuffle(records)
    return pd.DataFrame.from_records(records)


def save_to_excel(path: Path | None = None, n: int = 2000, coverage_per_bedroom: int = 8) -> Path:
    """生成房源并保存到 Excel（原始数据）。"""
    output = path or settings.paths.raw_excel
    output.parent.mkdir(parents=True, exist_ok=True)
    df = generate_listings(n=n, coverage_per_bedroom=coverage_per_bedroom)
    df.to_excel(output, index=False)
    return output


def main() -> None:
    """入口：生成并落盘 Excel。"""
    saved = save_to_excel()
    print(f"Generated listings to {saved}")


if __name__ == "__main__":
    main()
