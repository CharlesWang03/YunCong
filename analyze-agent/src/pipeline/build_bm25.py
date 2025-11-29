"""Build BM25-like TF-IDF index for lexical relevance."""
from __future__ import annotations

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline

from src.config import settings


def _build_corpus(df: pd.DataFrame) -> list[str]:
    text_cols = ["description", "community_intro", "surrounding"]
    corpus = []
    for _, row in df.iterrows():
        parts = []
        for col in text_cols:
            val = row.get(col, "") if isinstance(row, dict) else row[col] if col in row else ""
            if pd.notna(val):
                parts.append(str(val))
        tags = row.get("tags") if isinstance(row, dict) else row["tags"] if "tags" in row else []
        if isinstance(tags, list):
            parts.extend(tags)
        corpus.append(" ".join(parts))
    return corpus


def build_bm25_index() -> None:
    df = pd.read_parquet(settings.paths.processed_parquet)
    corpus = _build_corpus(df)
    vectorizer = TfidfVectorizer(max_features=settings.bm25_max_features, ngram_range=settings.bm25_ngram)
    pipeline = Pipeline([("tfidf", vectorizer)])
    matrix = pipeline.fit_transform(corpus)
    joblib.dump({"pipeline": pipeline, "matrix": matrix}, settings.paths.bm25_index)
    print(f"Saved BM25-like index to {settings.paths.bm25_index}")


def main() -> None:
    build_bm25_index()


if __name__ == "__main__":
    main()
