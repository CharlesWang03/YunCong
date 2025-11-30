"""BM25/Tfidf retrieval with jieba tokenization."""
from __future__ import annotations

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from src.config import settings
from src.utils.text_utils import tokenize, join_tokens


class BM25Engine:
    """Wrap TF-IDF index for lexical relevance."""

    def __init__(self) -> None:
        if not settings.paths.bm25_index.exists():
            raise FileNotFoundError(f"BM25 index not found at {settings.paths.bm25_index}, run pipeline/build_bm25.py first")
        bundle = joblib.load(settings.paths.bm25_index)
        self.pipeline = bundle["pipeline"]
        self.matrix = bundle["matrix"]

    def _prep_query(self, query: str) -> str:
        return join_tokens(tokenize(query))

    def search(self, query: str, top_k: int = 50) -> list[tuple[int, float]]:
        processed = self._prep_query(query)
        query_vec = self.pipeline.transform([processed])
        sims = cosine_similarity(query_vec, self.matrix).ravel()
        top_idx = np.argsort(sims)[::-1][:top_k]
        return [(int(i), float(sims[i])) for i in top_idx if sims[i] > 0]

    def attach_scores(self, df: pd.DataFrame, query: str, top_k: int = 50) -> pd.DataFrame:
        matches = self.search(query, top_k=top_k)
        if not matches:
            df["bm25_score"] = 0.0
            return df
        score_map = {idx: score for idx, score in matches}
        df = df.copy()
        df["bm25_score"] = df.index.map(score_map).fillna(0).astype(float)
        return df
