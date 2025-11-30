"""Gradio app for user search with multiple modes."""
from __future__ import annotations

import gradio as gr
import pandas as pd

# ==== 关键补丁：修复 Gradio 4.x 在生成 API schema 时遇到 bool schema 直接报错的问题 ====
try:
    from gradio_client import utils as gc_utils

    _orig_json_schema_to_python_type = gc_utils.json_schema_to_python_type

    def safe_json_schema_to_python_type(schema, *args, **kwargs):
        """
        修复 gradio_client 在解析 JSON Schema 时遇到 True/False 这种布尔 schema 会直接崩溃的问题。
        - 如果 schema 本身是 bool，直接返回 "Any"。
        - 如果原始实现抛异常，也兜底返回 "Any"，避免把整套 FastAPI/Gradio 服务打崩。
        """
        # gradio 有时候会传进来 True / False
        if isinstance(schema, bool):
            print("[schema-patch] hit boolean schema:", schema)
            return "Any"
        try:
            return _orig_json_schema_to_python_type(schema, *args, **kwargs)
        except Exception as e:
            print(
                "[schema-patch] json_schema_to_python_type failed:",
                repr(e),
                "schema:",
                schema,
            )
            return "Any"

    gc_utils.json_schema_to_python_type = safe_json_schema_to_python_type
except Exception as e:
    # 补丁失败不影响主流程，最多就是照旧报原来的错
    print(
        "[schema-patch] Failed to patch gradio_client.json_schema_to_python_type:",
        repr(e),
    )

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

# Gradio 4.x 某些版本在生成 API schema 时会因布尔 schema 触发解析错误；
# 尝试调用原始实现，失败时返回空 schema 以避免崩溃，不影响前端功能。
try:
    import gradio.blocks as gr_blocks

    _orig_get_api_info = gr_blocks.Blocks.get_api_info

    def _safe_api_info(self, include_dependencies: bool | None = None):
        try:
            return _orig_get_api_info(self, include_dependencies)
        except Exception:
            # 返回空 schema，前端 API 文档功能会缺失，但界面与调用不受影响
            print("[api-info-patch] get_api_info failed, return empty dict")
            return {}

    gr_blocks.Blocks.get_api_info = _safe_api_info  # type: ignore
except Exception:
    pass


def get_orch() -> Orchestrator:
    global _orch
    if _orch is None:
        _orch = Orchestrator.create()
    return _orch


def load_data() -> pd.DataFrame:
    global _data
    if _data is None:
        if settings.paths.processed_parquet.exists():
            _data = pd.read_parquet(settings.paths.processed_parquet)
        else:
            _data = pd.DataFrame()
    return _data


def _format_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    统一控制前端展示的列，如果有列缺失，不抛错，只展示存在的列。
    """
    if df.empty:
        return df
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
    cols = [c for c in display_cols if c in df.columns]
    return df[cols]


def search_free(query: str, top_k: int = 10):
    """
    模式 2：自由文本搜索模式。
    - 使用现有数据 df（Parquet 预处理结果）。
    - orchestrator.run 做过滤 + 排序。
    - AnswerGenerator 做一个简要提示。
    """
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
    """
    模式 1：Filter 过滤模式。
    - 只做硬过滤 + 质量/综合排序。
    - 不跑 BM25 / 语义检索，以保证速度。
    """
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
    result = orch.run(
        user_query="",
        df=df,
        top_k=top_k,
        conditions=conditions,
        use_bm25=False,
        use_semantic=False,
    )
    ranked = result["results"]
    return _format_table(ranked)


def search_assistant_upload(query: str, top_k: int = 10):
    """
    模式 4：助手模式（使用上传的 Excel 数据上下文）。
    - 依赖 _session_context（df + bm25 + 向量索引）。
    - Orchestrator.run_assistant 负责 RAG + 回答编排。
    """
    global _session_context
    if _session_context is None:
        return "尚未上传或解析 Excel 文件，请先上传待售房产列表。", pd.DataFrame()
    orch = get_orch()
    result = orch.run_assistant(
        user_query=query,
        df=_session_context.df,
        top_k=top_k,
        context=_session_context,
    )
    ranked = result.get("results", pd.DataFrame())
    answer = result.get("answer", "")
    return answer, _format_table(ranked)


def on_file_uploaded(file):
    """
    解析上传的 Excel，构建临时索引并存入会话上下文。
    - parse_uploaded_excel: 负责将用户给的 Excel 映射到统一字段结构。
    - build_bm25_from_dataframe: 针对该 df 构建 BM25 索引。
    - build_vectors_from_dataframe: 针对该 df 构建语义向量索引（FAISS + 模型）。
    """
    global _session_context
    df_clean = parse_uploaded_excel(file)
    bm25_bundle = build_bm25_from_dataframe(df_clean)
    vector_index, vector_model = build_vectors_from_dataframe(df_clean)
    _session_context = SessionDataContext(
        df=df_clean,
        bm25_index=bm25_bundle,
        vector_index={"index": vector_index, "model": vector_model},
    )
    return f"已成功载入 {len(df_clean)} 条房源数据，用于本次分析。"


def build_options():
    """
    初始化城市/城区下拉框选项。
    如果目前还没有 Parquet 数据，则只提供“全部”。
    """
    df = load_data()
    if df.empty:
        return [_DEF_OPTION], [_DEF_OPTION]
    cities = sorted(df["city"].dropna().unique().tolist())
    districts = sorted(df["district"].dropna().unique().tolist())
    return [_DEF_OPTION] + cities, [_DEF_OPTION] + districts


_DEF_OPTION = "全部"
_CITIES_OPTS, _DISTRICTS_OPTS = build_options()


def main() -> None:
    with gr.Blocks(title="Analyze Agent") as demo:
        gr.Markdown("# Analyze Agent\n选择模式体验过滤 / 搜索 / 智能助手。")

        # 模式 1：Filter
        with gr.Tab("Filter 过滤模式"):
            with gr.Row():
                city = gr.Dropdown(
                    choices=_CITIES_OPTS,
                    value=_DEF_OPTION,
                    label="城市",
                )
                district = gr.Dropdown(
                    choices=_DISTRICTS_OPTS,
                    value=_DEF_OPTION,
                    label="城区",
                )
            with gr.Row():
                min_price = gr.Number(label="最低总价(万)", value=None)
                max_price = gr.Number(label="最高总价(万)", value=None)
            with gr.Row():
                min_area = gr.Number(label="最小面积(平)", value=None)
                max_area = gr.Number(label="最大面积(平)", value=None)
            with gr.Row():
                bedrooms = gr.Number(
                    label="卧室数(精确)",
                    value=None,
                    precision=0,
                )
                livingrooms = gr.Number(
                    label="客厅数(精确)",
                    value=None,
                    precision=0,
                )
                school_district = gr.Checkbox(label="学区", value=False)
            top_k_filter = gr.Slider(5, 100, value=20, step=1, label="Top K")
            run_filter = gr.Button("运行过滤")
            table_filter = gr.Dataframe(interactive=False)
            run_filter.click(
                fn=search_filters,
                inputs=[
                    city,
                    district,
                    min_price,
                    max_price,
                    min_area,
                    max_area,
                    bedrooms,
                    livingrooms,
                    school_district,
                    top_k_filter,
                ],
                outputs=table_filter,
            )

        # 模式 2：Search（自由搜索）
        with gr.Tab("Search 搜索模式"):
            query_search = gr.Textbox(
                label="搜索描述",
                placeholder="北京海淀 两室 学区 靠地铁",
            )
            top_k_search = gr.Slider(5, 50, value=10, step=1, label="Top K")
            run_search = gr.Button("搜索")
            answer_search = gr.Textbox(label="提示", lines=3)
            table_search = gr.Dataframe(interactive=False)
            run_search.click(
                fn=search_free,
                inputs=[query_search, top_k_search],
                outputs=[answer_search, table_search],
            )

        # 模式 3：Assistant（默认数据源助手）
        with gr.Tab("Assistant 智能助手模式"):
            query_assist = gr.Textbox(
                label="对话/需求",
                placeholder="我想要北京海淀两室靠地铁的房子",
            )
            top_k_assist = gr.Slider(5, 50, value=10, step=1, label="Top K")
            run_assist = gr.Button("生成回答")
            answer_assist = gr.Textbox(label="回答", lines=6)
            table_assist = gr.Dataframe(interactive=False)
            run_assist.click(
                fn=search_assistant,
                inputs=[query_assist, top_k_assist],
                outputs=[answer_assist, table_assist],
            )

        # 模式 4：上传 Excel 分析
        with gr.Tab("模式4：上传 Excel 分析"):
            gr.Markdown("上传一份待售房产 Excel，系统将在该文件上完成过滤/检索/分析。")
            file_uploader = gr.File(
                label="上传 Excel",
                file_types=[".xls", ".xlsx"],
            )
            load_btn = gr.Button("加载 Excel")
            load_status = gr.Textbox(label="加载状态", interactive=False)
            query_upload = gr.Textbox(
                label="对话/需求",
                placeholder="请给我一个北京两室的推荐报告",
            )
            top_k_upload = gr.Slider(5, 50, value=10, step=1, label="Top K")
            run_upload = gr.Button("生成报告")
            answer_upload = gr.Textbox(label="回答", lines=8)
            table_upload = gr.Dataframe(interactive=False)

            load_btn.click(
                fn=on_file_uploaded,
                inputs=[file_uploader],
                outputs=[load_status],
            )
            run_upload.click(
                fn=search_assistant_upload,
                inputs=[query_upload, top_k_upload],
                outputs=[answer_upload, table_upload],
            )

    # queue 保持开启；show_api=False 避免自动生成 API 文档时再去折腾 schema
    demo.queue()
    demo.launch(
        show_api=False,
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
    )


if __name__ == "__main__":
    main()
