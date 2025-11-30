from __future__ import annotations

import pandas as pd

from src.agent.orchestrator import Orchestrator
from src.agent.answer_generator import AnswerGenerator


def search_assistant(query: str, top_k: int = 10):
    from src.app.gradio_app import load_data, _format_table  # avoid circular import

    df = load_data()
    if df.empty:
        return "数据未准备，请先运行生成/预处理管线。", pd.DataFrame()
    orch = Orchestrator.create()
    result = orch.run_assistant(user_query=query, df=df, top_k=top_k)
    ranked = result.get("results", pd.DataFrame())
    answer = result.get("answer", "")
    return answer, _format_table(ranked)
