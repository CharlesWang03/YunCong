"""LLM answer generation placeholder."""
from __future__ import annotations

from typing import Any, Dict, List


class AnswerGenerator:
    """Use LLM to generate responses given ranked results (template placeholder)."""

    def __init__(self) -> None:
        # TODO: configure model/provider and prompt templates
        pass

    def generate(self, user_query: str, results: List[Dict[str, Any]]) -> str:
        if not results:
            return "未找到匹配房源，请尝试放宽条件。"
        lines = [f"用户需求：{user_query}\n推荐房源："]
        for r in results:
            lines.append(
                f"- {r.get('city','')} {r.get('district','')} {r.get('community','')} | {r.get('layout','')} | 总价 {r.get('total_price','')} 万 | 评分 {r.get('fused_score',0):.3f}"
            )
        lines.append("(提示：可接入 LLM 生成更丰富的解释。)")
        return "\n".join(lines)
