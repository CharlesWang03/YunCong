"""Agent orchestrator."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import pandas as pd

from src.config import settings
from src.ranking.ranker import Ranker
from src.retrieval.bm25_engine import BM25Engine
from src.retrieval.filter_engine import apply_filters
from src.retrieval.query_parser import QueryParser
from src.retrieval.semantic_engine import SemanticEngine
from src.analytics.summary import summarize_listings
from src.agent.answer_generator import AnswerGenerator


@dataclass
class Orchestrator:
    """Coordinate parsing, retrieval, scoring, and response generation."""

    bm25: Optional[BM25Engine]
    semantic: Optional[SemanticEngine]
    parser: QueryParser
    ranker: Ranker

    @classmethod
    def create(cls) -> "Orchestrator":
        return cls(
            bm25=None,
            semantic=None,
            parser=QueryParser(),
            ranker=Ranker(),
        )

    def _get_bm25(self) -> BM25Engine:
        if self.bm25 is None:
            self.bm25 = BM25Engine()
        return self.bm25

    def _get_semantic(self) -> SemanticEngine:
        if self.semantic is None:
            self.semantic = SemanticEngine()
        return self.semantic

    def run(
        self,
        user_query: str,
        df: pd.DataFrame,
        top_k: int = 10,
        conditions: Dict[str, Any] | None = None,
        use_bm25: bool = True,
        use_semantic: bool = True,
    ) -> Dict[str, Any]:
        """端到端：解析/条件→过滤→检索→融合排序。"""
        parsed = conditions or self.parser.parse(user_query)
        filtered = apply_filters(df, parsed)

        if filtered.empty:
            return {"results": pd.DataFrame(), "parsed": parsed}

        if use_bm25:
            filtered = self._get_bm25().attach_scores(filtered, user_query, top_k=top_k * 2)
        else:
            filtered = filtered.copy()
            filtered["bm25_score"] = 0.0
        if use_semantic:
            filtered = self._get_semantic().attach_scores(filtered, user_query, top_k=top_k * 2)
        else:
            filtered["semantic_score"] = 0.0

        ranked = self.ranker.rank(filtered, top_k=top_k)
        return {"results": ranked, "parsed": parsed}

    def run_assistant(
        self,
        user_query: str,
        df: pd.DataFrame,
        top_k: int = 10,
        conditions: Dict[str, Any] | None = None,
        llm_client: Any | None = None,
    ) -> Dict[str, Any]:
        """助手模式：检索→统计→生成分析报告。"""
        result = self.run(
            user_query=user_query,
            df=df,
            top_k=top_k,
            conditions=conditions,
            use_bm25=True,
            use_semantic=True,
        )
        ranked = result["results"]
        if ranked.empty:
            return {"answer": "当前条件下没有找到合适的房源，建议放宽预算/面积/地段后再试。", "results": ranked}

        summary = summarize_listings(ranked, result.get("parsed", {}))
        answer = AnswerGenerator(llm_client=llm_client).generate_report(
            user_query=user_query,
            user_filter=result.get("parsed", {}),
            listings=ranked,
            summary_stats=summary,
        )
        return {"answer": answer, "results": ranked, "summary": summary}
