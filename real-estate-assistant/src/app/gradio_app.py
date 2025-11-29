"""Simple Gradio front-end for exploring listings."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional, Sequence

import gradio as gr
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src import config
from src.data_pipeline.generator import save_to_excel
from src.data_pipeline.preprocess import preprocess_listings
from src.data_pipeline.repository import DataRepository
from src.models import SearchFilter
from src.nlp import parse_fuzzy_query, parse_query
from src.search.ranking import apply_ranking


def _ensure_data() -> None:
    """若不存在处理后数据，则生成原始 Excel 并执行清洗。"""
    processed = Path(config.PROCESSED_LISTINGS_PATH)
    raw = Path(config.RAW_LISTINGS_PATH)
    if processed.exists():
        return
    if not raw.exists():
        save_to_excel()
    preprocess_listings()


def _load_filter_options() -> dict:
    """加载过滤选项（城市/城区/户型）。"""
    _ensure_data()
    repo = DataRepository()
    df = repo.load()
    return {
        "cities": sorted(df["city"].dropna().unique().tolist()),
        "districts": sorted(df["district"].dropna().unique().tolist()),
        "property_types": sorted(df["property_type"].dropna().unique().tolist()),
    }


def search_listings(
    mode: str,
    query: str,
    min_price: Optional[float],
    max_price: Optional[float],
    min_area: Optional[float],
    max_area: Optional[float],
    bedrooms: Optional[int],
    bathrooms: Optional[int],
    has_parking: bool,
    cities: Sequence[str] | None,
    districts: Sequence[str] | None,
    property_types: Sequence[str] | None,
    ranking: str,
) -> pd.DataFrame:
    """接收 UI 输入，合并规则解析结果，执行筛选与排序，返回用于展示的 DataFrame。"""
    _ensure_data()
    repo = DataRepository()

    def _none_if_blank(v: Optional[float]):
        return None if v in (None, 0) else v

    def _none_if_blank_int(v: Optional[int]):
        return None if v in (None, 0) else v

    if mode == "fuzzy":
        catalog = _load_filter_options()
        parsed = parse_fuzzy_query(query, catalog)
        filters = parsed
    else:
        parsed = parse_query(query)
        filters = SearchFilter(
            min_price=_none_if_blank(parsed.min_price if parsed.min_price else min_price),
            max_price=_none_if_blank(max_price),
            min_area=_none_if_blank(min_area),
            max_area=_none_if_blank(max_area),
            bedrooms=_none_if_blank_int(bedrooms or parsed.bedrooms),
            bathrooms=_none_if_blank_int(bathrooms or parsed.bathrooms),
            has_parking=has_parking if has_parking else parsed.has_parking,
            cities=list(cities) if cities else None,
            districts=list(districts) if districts else None,
            property_types=list(property_types) if property_types else None,
            keywords=parsed.keywords,
        )

    results = repo.search(filters)
    ranked = apply_ranking(results, strategy=ranking)
    display_cols = [
        "id",
        "city",
        "district",
        "price",
        "bedrooms",
        "bathrooms",
        "area_sqm",
        "property_type",
        "year_built",
        "has_parking",
        "distance_to_center_km",
        "distance_to_school_km",
        "listing_date",
        "description",
    ]
    if "score" in ranked.columns:
        display_cols.insert(4, "score")
    return ranked[display_cols]


def build_app() -> gr.Blocks:
    """搭建 Gradio 界面并绑定查询逻辑，返回 Blocks 实例。"""
    opts = _load_filter_options()
    with gr.Blocks(title="Real Estate Assistant") as demo:
        gr.Markdown("# Real Estate Assistant\n模式选择：结构化筛选 or 模糊关键词（如“北京海淀 两室一卫 离学校近”）。")
        with gr.Row():
            mode = gr.Radio([
                ("结构化筛选", "structured"),
                ("模糊关键词", "fuzzy"),
            ], value="structured", label="查询模式")
            query = gr.Textbox(label="Query", placeholder="3m 3 bed parking / 北京海淀 两室一卫 离学校近")
            ranking = gr.Radio(
                [
                    "price_low_to_high",
                    "price_high_to_low",
                    "newest",
                    "quality_score",
                ],
                value="quality_score",
                label="Ranking",
            )
        with gr.Row():
            min_price = gr.Number(label="Min price (留空为不限)", value=None)
            max_price = gr.Number(label="Max price (留空为不限)", value=None)
            min_area = gr.Number(label="Min area (sqm, 留空为不限)", value=None)
            max_area = gr.Number(label="Max area (sqm, 留空为不限)", value=None)
        with gr.Row():
            bedrooms = gr.Number(label="Bedrooms", value=None, precision=0)
            bathrooms = gr.Number(label="Bathrooms", value=None, precision=0)
            has_parking = gr.Checkbox(label="Require parking", value=False)
        with gr.Row():
            cities = gr.Dropdown(choices=opts["cities"], multiselect=True, label="城市", value=[])
            districts = gr.Dropdown(choices=opts["districts"], multiselect=True, label="城区", value=[])
            property_types = gr.Dropdown(choices=opts["property_types"], multiselect=True, label="户型", value=[])

        run_btn = gr.Button("Search")
        results = gr.Dataframe(interactive=False)

        run_btn.click(
            fn=search_listings,
            inputs=[
                mode,
                query,
                min_price,
                max_price,
                min_area,
                max_area,
                bedrooms,
                bathrooms,
                has_parking,
                cities,
                districts,
                property_types,
                ranking,
            ],
            outputs=results,
        )
    return demo


if __name__ == "__main__":
    app = build_app()
    app.launch()
