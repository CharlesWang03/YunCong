"""Build BM25 index with jieba tokenization."""
from __future__ import annotations

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline

from src.config import settings
from src.utils.text_utils import tokenize, join_tokens


def _build_corpus(df: pd.DataFrame) -> list[str]:
    """将多字段文本+标签拼接并分词，生成语料列表。"""
    text_cols = ["description", "community_intro", "surrounding"]
    corpus = []
    for _, row in df.iterrows():
        parts = []
        for col in text_cols:
            val = row.get(col, "") if isinstance(row, dict) else row[col] if col in row else ""
            parts.append(str(val) if pd.notna(val) else "")
        tags = row.get("tags") if isinstance(row, dict) else row["tags"] if "tags" in row else []
        if isinstance(tags, list):
            parts.extend([str(t) for t in tags])
        tokens = tokenize(" ".join(parts))
        corpus.append(join_tokens(tokens))
    return corpus


def build_bm25_index() -> None:
    """构建基于 TF-IDF+jieba 的 BM25 风格索引并持久化。"""
    df = pd.read_parquet(settings.paths.processed_parquet)
    corpus = _build_corpus(df)
    vectorizer = TfidfVectorizer(
        analyzer="word",
        tokenizer=str.split,  # tokens already space-joined
        preprocessor=None,
        lowercase=False,
        max_features=settings.bm25_max_features,
        ngram_range=settings.bm25_ngram,
    )
    pipeline = Pipeline([("tfidf", vectorizer)])
    matrix = pipeline.fit_transform(corpus)
    joblib.dump({"pipeline": pipeline, "matrix": matrix}, settings.paths.bm25_index)
    print(f"Saved BM25-like index to {settings.paths.bm25_index}")


def main() -> None:
    """入口：构建 BM25 索引。"""
    build_bm25_index()


if __name__ == "__main__":
    main()
