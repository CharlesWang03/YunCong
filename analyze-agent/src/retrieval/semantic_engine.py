"""Semantic retrieval using sentence-transformers and FAISS."""
from __future__ import annotations

import joblib
import numpy as np
import pandas as pd
import faiss
from sentence_transformers import SentenceTransformer

from src.config import settings
from src.utils.text_utils import tokenize, join_tokens


class SemanticEngine:
    """Vector similarity search wrapper."""

    def __init__(self) -> None:
        if not settings.paths.vector_faiss.exists() or not settings.paths.vector_meta.exists():
            raise FileNotFoundError(
                f"Vector index/meta not found ({settings.paths.vector_faiss}, {settings.paths.vector_meta}), run pipeline/build_vectors.py first"
            )
        self.index = faiss.read_index(str(settings.paths.vector_faiss))
        meta = joblib.load(settings.paths.vector_meta)
        self.ids = meta.get("ids", [])
        model_name = meta.get("model_name", settings.semantic_model)
        self.model = SentenceTransformer(model_name)

    def _prep_query(self, query: str) -> np.ndarray:
        processed = join_tokens(tokenize(query))
        vec = self.model.encode([processed], normalize_embeddings=True)
        return np.asarray(vec, dtype="float32")

    def search(self, query: str, top_k: int = 50) -> list[tuple[int, float]]:
        query_vec = self._prep_query(query)
        scores, idxs = self.index.search(query_vec, top_k)
        results: list[tuple[int, float]] = []
        for score, idx in zip(scores[0], idxs[0]):
            if idx == -1:
                continue
            results.append((int(idx), float(score)))
        return results

    def attach_scores(self, df: pd.DataFrame, query: str, top_k: int = 50) -> pd.DataFrame:
        matches = self.search(query, top_k=top_k)
        if not matches:
            df["semantic_score"] = 0.0
            return df
        score_map = {idx: score for idx, score in matches}
        df = df.copy()
        df["semantic_score"] = df.index.map(score_map).fillna(0).astype(float)
        return df
