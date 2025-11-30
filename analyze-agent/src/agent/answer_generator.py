"""LLM answer generation (report-style)."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from src.config import settings

try:
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover
    OpenAI = None  # noqa: N816


class AnswerGenerator:
    """生成分析报告的回答器，支持 LLM 与本地回退模板。"""

    def __init__(self, llm_client: Any | None = None) -> None:
        # 如未显式传入 client，尝试读取环境变量构建 OpenAI 客户端
        self.llm_client = llm_client or self._build_default_client()
        self.template = self._load_template()

    def _build_default_client(self):
        api_key = settings.llm_api_key or os.getenv(settings.llm_api_key_env)
        if api_key and OpenAI is not None:
            return OpenAI(api_key=api_key)
        return None

    def _load_template(self) -> str:
        # 模板位于仓库根目录下的 prompts/answer_template.md
        tmpl_path = Path(__file__).resolve().parents[2] / "prompts" / "answer_template.md"
        if tmpl_path.exists():
            return tmpl_path.read_text(encoding="utf-8")
        return ""

    def _format_table(self, df: pd.DataFrame, max_rows: int = 5) -> str:
        cols = ["id", "city", "district", "community", "layout", "total_price", "area", "unit_price"]
        df = df[cols] if not df.empty else df
        return df.head(max_rows).to_json(force_ascii=False, orient="records")

    def _render_prompt(self, user_query: str, user_filter: Dict[str, Any], summary_stats: Dict[str, Any], listings: pd.DataFrame) -> str:
        return self.template.format(
            user_query=user_query,
            user_filter_json=json.dumps(user_filter, ensure_ascii=False),
            summary_stats_json=json.dumps(summary_stats, ensure_ascii=False),
            top_listings_table=self._format_table(listings),
        )

    def generate_report(
        self,
        user_query: str,
        user_filter: Dict[str, Any],
        listings: pd.DataFrame,
        summary_stats: Dict[str, Any],
    ) -> str:
        """生成结构化的报告；支持 LLM 或本地模板回退。"""
        if listings.empty:
            return "当前条件下没有找到合适的房源，请尝试放宽预算/面积/地段等。"

        formatted_summary = self._format_summary(summary_stats)

        if self.llm_client is not None and self.template:
            prompt = self._render_prompt(user_query, user_filter, formatted_summary, listings)
            try:
                print(f"[LLM] calling {settings.llm_model} via OpenAI client...")
                resp = self.llm_client.chat.completions.create(
                    model=settings.llm_model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "你是一名购房分析助手，基于提供的数据输出客观、贴心的建议。"
                                "突出房源特点（如学区、地铁距离、总价/单价、面积、性价比），"
                                "给出简洁、可行动的推荐理由。"
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.7,
                    top_p=0.9,
                    presence_penalty=0.2,
                    frequency_penalty=0.2,
                )
                return resp.choices[0].message.content.strip()
            except Exception as exc:  # pragma: no cover - LLM 调用失败时回退
                return f"(LLM 调用失败，使用本地模板。原因: {exc})\n" + self._fallback_report(user_query, listings, formatted_summary)

        prefix = ""
        if self.llm_client is None:
            prefix = "(未检测到 OPENAI_API_KEY，使用本地模板生成简报)\n"
        elif not self.template:
            prefix = "(未找到回答模板，使用本地简报)\n"
        return prefix + self._fallback_report(user_query, listings, formatted_summary)

    def _format_summary(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """数值字段做一位小数的格式化，便于阅读。"""

        def r(x, ndigits=1):
            try:
                return round(float(x), ndigits)
            except Exception:
                return x

        formatted = dict(summary)
        for k in [
            "price_min",
            "price_max",
            "price_avg",
            "price_median",
            "unit_price_avg",
            "area_min",
            "area_max",
            "area_avg",
            "distance_to_subway_avg",
            "distance_to_subway_min",
        ]:
            if k in formatted:
                formatted[k] = r(formatted[k], 1)
        return formatted

    def _fallback_report(self, user_query: str, listings: pd.DataFrame, summary_stats: Dict[str, Any]) -> str:
        """本地回退报告（无 LLM 时使用）。"""
        lines: List[str] = []
        lines.append("12123总体结论：")
        lines.append(
            f"共找到 {summary_stats.get('count')} 套，价格 {summary_stats.get('price_min')} - {summary_stats.get('price_max')} 万，"
            f"均价 {summary_stats.get('price_avg')} 万，单价均值 {summary_stats.get('unit_price_avg')} 元/平。"
        )
        lines.append("")
        lines.append("价格与户型：")
        lines.append(
            f"面积 {summary_stats.get('area_min')} - {summary_stats.get('area_max')} 平，均值 {summary_stats.get('area_avg')} 平；"
            f"户型分布：{summary_stats.get('bedrooms_distribution')}"
        )
        lines.append("")
        lines.append("地段与通勤：")
        lines.append(
            f"距地铁均值 {summary_stats.get('distance_to_subway_avg')} km，最小 {summary_stats.get('distance_to_subway_min')} km；"
            f"学区占比 {summary_stats.get('school_district_ratio')}; "
            f"建成年份 {summary_stats.get('year_built_min')} - {summary_stats.get('year_built_max')}。"
        )
        lines.append("")
        lines.append("重点推荐：")
        for _, r in listings.head(5).iterrows():
            lines.append(
                f"- {r.get('id')} | {r.get('city','')}{r.get('district','')} {r.get('community','')} | {r.get('layout','')} | "
                f"总价 {r.get('total_price','')} 万"
            )
        lines.append("")
        lines.append("风险与建议：")
        lines.append("如预算紧张或房龄偏老，可考虑放宽预算/面积或更远地段，或减少学区/地铁硬条件。")
        return "\n".join(lines)

    def generate(self, user_query: str, results: List[Dict[str, Any]]) -> str:
        """模式2/列表场景的简短提示（无 LLM）。"""
        if not results:
            return "未找到匹配房源，请尝试放宽条件。"
        lines = [f"用户需求：{user_query}\n推荐房源："]
        for r in results:
            lines.append(
                f"- {r.get('city','')} {r.get('district','')} {r.get('community','')} | {r.get('layout','')} | "
                f"总价 {r.get('total_price','')} 万 | 评分 {r.get('fused_score',0):.3f}"
            )
        lines.append("(提示：可接入 LLM 生成更丰富的解释。)")
        return "\n".join(lines)
