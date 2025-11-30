"""Gradio app for user search with multiple modes."""
from __future__ import annotations

import gradio as gr
import pandas as pd

from src.pipeline.context import SessionDataContext
from src.pipeline.excel_parser import parse_uploaded_excel
from src.pipeline.build_bm25 import build_bm25_from_dataframe
from src.pipeline.build_vectors import build_vectors_from_dataframe
from src.app.assistant_api import search_assistant
from src.agent.orchestrator import Orchestrator
from src.agent.answer_generator import AnswerGenerator
from src.config import settings

_orch: Orchestrator | None = None
_data: pd.DataFrame | None = None
_session_context: SessionDataContext | None = None


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


def search_assistant_upload(query: str, top_k: int = 10):
    """助手模式（使用上传的 Excel 数据上下文）。"""
    global _session_context
    if _session_context is None:
        return "尚未上传或解析 Excel 文件，请先上传待售房产列表。", pd.DataFrame()
    orch = get_orch()
    result = orch.run_assistant(user_query=query, df=_session_context.df, top_k=top_k, context=_session_context)
    ranked = result.get("results", pd.DataFrame())
    answer = result.get("answer", "")
    return answer, _format_table(ranked)


def on_file_uploaded(file):
    """解析上传的 Excel，构建临时索引并存入会话上下文。"""
    global _session_context
    df_clean = parse_uploaded_excel(file)
    bm25_bundle = build_bm25_from_dataframe(df_clean)
    vector_index, vector_model = build_vectors_from_dataframe(df_clean)
    _session_context = SessionDataContext(df=df_clean, bm25_index=bm25_bundle, vector_index={"index": vector_index, "model": vector_model})
    return f"已成功载入 {len(df_clean)} 条房源数据，用于本次分析。"


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
        "city": None if city == _DEF_OPTION else city,
        "districts": None if district == _DEF_OPTION else [district],
        "min_price": min_price or None,
        "max_price": max_price or None,
        "min_area": min_area or None,
        "max_area": max_area or None,
        "bedrooms_exact": int(bedrooms) if bedrooms else None,
        "livingrooms_exact": int(livingrooms) if livingrooms else None,
        "school_district": school_district if school_district else None,
    }
    orch = get_orch()
    result = orch.run(user_query="", df=df, top_k=top_k, conditions=conditions, use_bm25=False, use_semantic=False)
    ranked = result["results"]
    return _format_table(ranked)


_DEF_OPTION = "全部"


def _build_options():
    df = load_data()
    if df.empty:
        return [_DEF_OPTION], [_DEF_OPTION]
    cities = sorted(df["city"].dropna().unique().tolist())
    districts = sorted(df["district"].dropna().unique().tolist())
    return [_DEF_OPTION] + cities, [_DEF_OPTION] + districts


_CITIES_OPTS, _DISTRICTS_OPTS = _build_options()


def main() -> None:
    with gr.Blocks(title="Analyze Agent") as demo:
        gr.Markdown("# Analyze Agent\n选择模式体验过滤 / 搜索 / 智能助手。")

        with gr.Tab("Filter 过滤模式"):
            with gr.Row():
                city = gr.Dropdown(choices=_CITIES_OPTS, value=_DEF_OPTION, label="城市")
                district = gr.Dropdown(choices=_DISTRICTS_OPTS, value=_DEF_OPTION, label="城区")
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
            run_assist.click(fn=search_assistant, inputs=[query_assist, top_k_assist], outputs=[answer_assist, table_assist])

        with gr.Tab("模式4：上传 Excel 分析"):
            upload_info = gr.Markdown("上传一份待售房产 Excel，系统将在该文件上完成过滤/检索/分析。")
            file_uploader = gr.File(label="上传 Excel", file_types=[".xls", ".xlsx"])
            load_btn = gr.Button("加载 Excel")
            load_status = gr.Textbox(label="加载状态", interactive=False)
            query_upload = gr.Textbox(label="对话/需求", placeholder="请给我一个北京两室的推荐报告")
            top_k_upload = gr.Slider(5, 50, value=10, step=1, label="Top K")
            run_upload = gr.Button("生成报告")
            answer_upload = gr.Textbox(label="回答", lines=8)
            table_upload = gr.Dataframe(interactive=False)

            load_btn.click(fn=on_file_uploaded, inputs=[file_uploader], outputs=[load_status])
            run_upload.click(fn=search_assistant_upload, inputs=[query_upload, top_k_upload], outputs=[answer_upload, table_upload])

    demo.launch()


if __name__ == "__main__":
    main()
