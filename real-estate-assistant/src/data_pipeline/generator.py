"""Generate synthetic real estate listings to Excel."""
from __future__ import annotations

import random
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from faker import Faker

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src import config

fake = Faker("zh_CN")
Faker.seed(config.RANDOM_SEED)
random.seed(config.RANDOM_SEED)
np.random.seed(config.RANDOM_SEED)

CITIES = {
    "北京": {"districts": ["朝阳", "海淀", "丰台", "通州", "昌平"], "base_price_m": 8.5},
    "上海": {"districts": ["浦东", "徐汇", "静安", "杨浦", "嘉定"], "base_price_m": 7.8},
    "深圳": {"districts": ["南山", "福田", "罗湖", "宝安", "龙华"], "base_price_m": 7.2},
    "广州": {"districts": ["天河", "越秀", "海珠", "番禺", "黄埔"], "base_price_m": 5.2},
    "杭州": {"districts": ["西湖", "拱墅", "滨江", "余杭", "临平"], "base_price_m": 4.6},
}
PROPERTY_TYPES = {
    "公寓": 1.0,
    "洋房": 1.08,
    "别墅": 1.35,
    "LOFT": 0.95,
    "复式": 1.15,
}


def _sample_city() -> tuple[str, str, float]:
    """随机选择城市/城区并返回对应的百万级基准价。"""
    city = random.choice(list(CITIES.keys()))
    district = random.choice(CITIES[city]["districts"])
    base_price_m = CITIES[city]["base_price_m"]  # 百万级别的基准总价
    return city, district, base_price_m


def _random_listing(i: int) -> dict:
    """按价格模型生成单条房源字典，包含距离、中文描述等。"""
    city, district, base_price_m = _sample_city()
    distance_center_km = float(np.clip(np.random.normal(8, 5), 0.5, 35))
    distance_school_km = float(np.clip(np.random.exponential(1.1), 0.1, 10))
    bedrooms = random.randint(1, 5)
    bathrooms = random.randint(1, 4)
    area_sqm = float(np.clip(np.random.normal(100, 35), 50, 260))
    year_built = random.randint(1970, date.today().year)
    has_parking = random.random() < 0.6
    property_type = random.choice(list(PROPERTY_TYPES.keys()))
    property_factor = PROPERTY_TYPES[property_type]
    listing_date = date.today() - timedelta(days=random.randint(0, 365))

    # 价格模型：以城市基准价为中心，考虑到市中心与学校距离的衰减/加成
    location_factor = np.exp(-0.045 * distance_center_km) * (1 + 0.32 / (distance_school_km + 0.4))
    size_factor = area_sqm / 100  # 以 100 平为基准线性放大
    room_factor = 1 + 0.05 * (bedrooms - 2) + 0.03 * (bathrooms - 1)
    noise = np.clip(np.random.normal(1.0, 0.06), 0.88, 1.18)

    total_price = base_price_m * location_factor * size_factor * room_factor * property_factor * noise
    total_price *= 1_000_000  # 转为货币单位

    description = (
        f"{city}{district} · {property_type} · {bedrooms}室{bathrooms}卫 · {int(area_sqm)}平 · "
        f"距中心{distance_center_km:.1f}km · 距学校{distance_school_km:.1f}km · {year_built}年建 · "
        f"{'含车位' if has_parking else '无车位'}"
    )

    return {
        "id": f"L{i:05d}",
        "city": city,
        "district": district,
        "price": round(float(total_price), 2),
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "area_sqm": round(float(area_sqm), 2),
        "property_type": property_type,
        "year_built": year_built,
        "has_parking": has_parking,
        "distance_to_center_km": round(distance_center_km, 2),
        "distance_to_school_km": round(distance_school_km, 2),
        "description": description,
        "listing_date": listing_date,
    }


def generate_listings(n: int = config.DEFAULT_LISTING_COUNT) -> pd.DataFrame:
    """生成包含 n 条中文合成房源的 DataFrame。"""
    records: Iterable[dict] = (_random_listing(i) for i in range(1, n + 1))
    df = pd.DataFrame.from_records(records)
    return df


def save_to_excel(path: str | None = None, n: int = config.DEFAULT_LISTING_COUNT) -> str:
    """生成房源并写入 Excel；返回写入路径字符串。"""
    output_path = config.RAW_LISTINGS_PATH if path is None else path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = generate_listings(n)
    df.to_excel(output_path, index=False)
    return str(output_path)


if __name__ == "__main__":
    saved_path = save_to_excel()
    print(f"Generated listings to {saved_path}")
