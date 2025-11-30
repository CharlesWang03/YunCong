"""LLM answer generation (report-style)."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import pandas as pd

from src.analytics.summary import summarize_listings


class AnswerGenerator:
    """生成报告风格的回答，支持占位或接入真实 LLM。"""

    def __init__(self, llm_client: Any | None = None) -> None:
        # TODO: 注入真实 LLM client（如 OpenAI），并加载 prompts/answer_template.md
        self.llm_client = llm_client

    def _format_table(self, df: pd.DataFrame, max_rows: int = 5) -> str:
        cols = ["id", "city", "district", "community", "layout", "total_price", "area", "unit_price"]
        df = df[cols] if not df.empty else df
        return df.head(max_rows).to_json(force_ascii=False, orient="records")

    def generate_report(
        self,
        user_query: str,
        user_filter: Dict[str, Any],
        listings: pd.DataFrame,
        summary_stats: Dict[str, Any],
    ) -> str:
        """生成结构化分析报告；无 LLM 时使用模板化占位。"""
        if listings.empty:
            return "当前条件下没有找到合适的房源，建议放宽预算/面积/地段后再试。"

        if self.llm_client is not None:
            # TODO: 读取 prompts/answer_template.md，填充变量后调用 llm_client
            pass

        # 占位：简单拼接统计与推荐列表
        lines: List[str] = []
        lines.append("总体结论：")
        lines.append(
            f"共找到 {summary_stats.get('count')} 套房源，价格区间 {summary_stats.get('price_min')} - {summary_stats.get('price_max')} 万，"
            f"均价 {summary_stats.get('price_avg'):.1f} 万，单价均值 {summary_stats.get('unit_price_avg')} 元/平。"
        )
        lines.append("")
        lines.append("价格与户型分析：")
        lines.append(
            f"面积区间 {summary_stats.get('area_min')} - {summary_stats.get('area_max')} 平，平均 {summary_stats.get('area_avg')} 平；"
            f"户型分布：{summary_stats.get('bedrooms_distribution')}"
        )
        lines.append("")
        lines.append("地段与通勤：")
        lines.append(
            f"距地铁均值 {summary_stats.get('distance_to_subway_avg')} km，最小 {summary_stats.get('distance_to_subway_min')} km；"
            f"学区占比 {summary_stats.get('school_district_ratio'):.2f}；建成年份 {summary_stats.get('year_built_min')} - {summary_stats.get('year_built_max')}。"
        )
        lines.append("")
        lines.append("重点推荐：")
        for _, r in listings.head(5).iterrows():
            lines.append(
                f"- {r.get('id')} | {r.get('city','')}{r.get('district','')} {r.get('community','')} | {r.get('layout','')} | 总价 {r.get('total_price','')} 万"
            )
        lines.append("")
        lines.append("风险与建议：")
        lines.append("如预算紧张或房龄偏老，可考虑放宽预算/面积或更远地段，或减少学区/地铁硬条件。")

        return "\n".join(lines)

    def generate(self, user_query: str, results: List[Dict[str, Any]]) -> str:
        """兼容旧接口的简版回答。"""
        if not results:
            return "未找到匹配房源，请尝试放宽条件。"
        lines = [f"用户需求：{user_query}\n推荐房源："]
        for r in results:
            lines.append(
                f"- {r.get('city','')} {r.get('district','')} {r.get('community','')} | {r.get('layout','')} | 总价 {r.get('total_price','')} 万 | 评分 {r.get('fused_score',0):.3f}"
            )
        lines.append("(提示：可接入 LLM 生成更丰富的解释。)")
        return "\n".join(lines)
