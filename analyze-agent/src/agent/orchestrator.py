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
        """End-to-end flow: parse (or use provided conditions) -> retrieve -> rank."""
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
