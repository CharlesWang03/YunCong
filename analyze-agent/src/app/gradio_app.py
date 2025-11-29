"""Gradio app for user search."""
from __future__ import annotations

import gradio as gr
import pandas as pd

from src.agent.orchestrator import Orchestrator
from src.agent.answer_generator import AnswerGenerator
from src.config import settings


def load_data() -> pd.DataFrame:
    return pd.read_parquet(settings.paths.processed_parquet) if settings.paths.processed_parquet.exists() else pd.DataFrame()


def search(query: str, top_k: int = 10):
    df = load_data()
    if df.empty:
        return "数据未准备，请先运行生成/预处理管线。", pd.DataFrame()
    orch = Orchestrator.create()
    result = orch.run(query, df, top_k=top_k)
    ranked = result["results"]
    answer = AnswerGenerator().generate(query, ranked.to_dict(orient="records"))
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
    ranked_display = ranked[display_cols] if not ranked.empty else ranked
    return answer, ranked_display


def main() -> None:
    with gr.Blocks(title="Analyze Agent") as demo:
        gr.Markdown("# Analyze Agent\n混合检索 + 排序 + 模板回答。")
        with gr.Row():
            query = gr.Textbox(label="需求描述", placeholder="北京海淀 两室 500万内 靠地铁")
            top_k = gr.Slider(5, 50, value=10, step=1, label="Top K")
        run_btn = gr.Button("搜索")
        answer = gr.Textbox(label="回答", lines=4)
        table = gr.Dataframe(interactive=False)

        run_btn.click(fn=search, inputs=[query, top_k], outputs=[answer, table])
    demo.launch()


if __name__ == "__main__":
    main()
