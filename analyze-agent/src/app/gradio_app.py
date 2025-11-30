"""Gradio app for user search with multiple modes."""
from __future__ import annotations

import gradio as gr
import pandas as pd

from src.agent.orchestrator import Orchestrator
from src.agent.answer_generator import AnswerGenerator
from src.config import settings

_orch: Orchestrator | None = None
_data: pd.DataFrame | None = None


def get_orch() -> Orchestrator:
    global _orch
    if _orch is None:
        _orch = Orchestrator.create()
    return _orch


def load_data() -> pd.DataFrame:
    global _data
    if _data is None:
        _data = pd.read_parquet(settings.paths.processed_parquet) if settings.paths.processed_parquet.exists() else pd.DataFrame()
    return _data


def _format_table(df: pd.DataFrame) -> pd.DataFrame:
    display_cols = [
        "id",
        "city",
        "district",
        "community",
        "layout",
        "total_price",
        "area",
        "unit_price",
        "fused_score",
    ]
    return df[display_cols] if not df.empty else df


def search_free(query: str, top_k: int = 10):
    df = load_data()
    if df.empty:
        return "数据未准备，请先运行生成/预处理管线。", pd.DataFrame()
    orch = get_orch()
    result = orch.run(query, df, top_k=top_k)
    ranked = result["results"]
    answer = AnswerGenerator().generate(query, ranked.to_dict(orient="records"))
    return answer, _format_table(ranked)


def search_filters(
    city: str,
    district: str,
    min_price: float | None,
    max_price: float | None,
    min_area: float | None,
    max_area: float | None,
    bedrooms: int | None,
    livingrooms: int | None,
    school_district: bool,
    top_k: int,
):
    df = load_data()
    if df.empty:
        return pd.DataFrame()
    conditions = {
        "city": city or None,
        "districts": [district] if district else None,
        "min_price": min_price or None,
        "max_price": max_price or None,
        "min_area": min_area or None,
        "max_area": max_area or None,
        "bedrooms_exact": int(bedrooms) if bedrooms else None,
        "livingrooms_exact": int(livingrooms) if livingrooms else None,
        "school_district": school_district if school_district else None,
    }
    orch = get_orch()
    result = orch.run(user_query="", df=df, top_k=top_k, conditions=conditions)
    ranked = result["results"]
    return _format_table(ranked)


def main() -> None:
    with gr.Blocks(title="Analyze Agent") as demo:
        gr.Markdown("# Analyze Agent\n选择模式体验过滤 / 搜索 / 智能助手。")

        with gr.Tab("Filter 过滤模式"):
            with gr.Row():
                city = gr.Textbox(label="城市", placeholder="北京")
                district = gr.Textbox(label="城区", placeholder="海淀")
            with gr.Row():
                min_price = gr.Number(label="最低总价(万)", value=None)
                max_price = gr.Number(label="最高总价(万)", value=None)
            with gr.Row():
                min_area = gr.Number(label="最小面积(平)", value=None)
                max_area = gr.Number(label="最大面积(平)", value=None)
            with gr.Row():
                bedrooms = gr.Number(label="卧室数(精确)", value=None, precision=0)
                livingrooms = gr.Number(label="客厅数(精确)", value=None, precision=0)
                school_district = gr.Checkbox(label="学区", value=False)
            top_k_filter = gr.Slider(5, 100, value=20, step=1, label="Top K")
            run_filter = gr.Button("运行过滤")
            table_filter = gr.Dataframe(interactive=False)
            run_filter.click(
                fn=search_filters,
                inputs=[city, district, min_price, max_price, min_area, max_area, bedrooms, livingrooms, school_district, top_k_filter],
                outputs=table_filter,
            )

        with gr.Tab("Search 搜索模式"):
            query_search = gr.Textbox(label="搜索描述", placeholder="北京海淀 两室 学区 靠地铁")
            top_k_search = gr.Slider(5, 50, value=10, step=1, label="Top K")
            run_search = gr.Button("搜索")
            answer_search = gr.Textbox(label="提示", lines=3)
            table_search = gr.Dataframe(interactive=False)
            run_search.click(fn=search_free, inputs=[query_search, top_k_search], outputs=[answer_search, table_search])

        with gr.Tab("Assistant 智能助手模式"):
            query_assist = gr.Textbox(label="对话/需求", placeholder="我想要北京海淀两室靠地铁的房子")
            top_k_assist = gr.Slider(5, 50, value=10, step=1, label="Top K")
            run_assist = gr.Button("生成回答")
            answer_assist = gr.Textbox(label="回答", lines=6)
            table_assist = gr.Dataframe(interactive=False)
            run_assist.click(fn=search_free, inputs=[query_assist, top_k_assist], outputs=[answer_assist, table_assist])

    demo.launch()


if __name__ == "__main__":
    main()
