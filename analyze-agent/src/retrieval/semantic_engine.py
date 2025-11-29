"""Semantic retrieval using TF-IDF fallback (can swap to embeddings)."""
from __future__ import annotations

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from src.config import settings


class SemanticEngine:
    """Vector similarity search wrapper."""

    def __init__(self) -> None:
        if not settings.paths.vector_index.exists():
            raise FileNotFoundError(f"Vector index not found at {settings.paths.vector_index}, run pipeline/build_vectors.py first")
        bundle = joblib.load(settings.paths.vector_index)
        self.pipeline = bundle["pipeline"]
        self.matrix = bundle["matrix"]

    def search(self, query: str, top_k: int = 50) -> list[tuple[int, float]]:
        query_vec = self.pipeline.transform([query])
        sims = cosine_similarity(query_vec, self.matrix).ravel()
        top_idx = np.argsort(sims)[::-1][:top_k]
        return [(int(i), float(sims[i])) for i in top_idx if sims[i] > 0]

    def attach_scores(self, df: pd.DataFrame, query: str, top_k: int = 50) -> pd.DataFrame:
        matches = self.search(query, top_k=top_k)
        if not matches:
            df["semantic_score"] = 0.0
            return df
        score_map = {idx: score for idx, score in matches}
        df = df.copy()
        df["semantic_score"] = df.index.map(score_map).fillna(0).astype(float)
        return df
