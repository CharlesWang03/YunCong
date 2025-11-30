"""Build vector index using sentence-transformers and FAISS."""
from __future__ import annotations

import joblib
import numpy as np
import pandas as pd
import faiss
from sentence_transformers import SentenceTransformer

from src.config import settings
from src.utils.text_utils import tokenize, join_tokens


def _build_corpus(df: pd.DataFrame) -> list[str]:
    """拼接文本+标签并分词，生成语料列表。"""
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


def build_vector_index() -> None:
    """使用 bge-small-zh 生成向量并构建 FAISS 索引。"""
    df = pd.read_parquet(settings.paths.processed_parquet)
    corpus = _build_corpus(df)

    try:
        model = SentenceTransformer(settings.semantic_model)
    except Exception as exc:  # pragma: no cover - download/env issues
        raise RuntimeError(
            f"Failed to load model {settings.semantic_model}. "
            "Please ensure torch/torchvision/transformers versions match requirements.txt "
            "and network/cache are available for model download. "
            "Error: %s" % exc
        ) from exc

    embeddings = model.encode(corpus, batch_size=64, show_progress_bar=True, normalize_embeddings=True)
    embeddings = np.asarray(embeddings, dtype="float32")

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    settings.paths.processed_dir.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(settings.paths.vector_faiss))
    joblib.dump({"ids": list(range(len(df))), "model_name": settings.semantic_model}, settings.paths.vector_meta)
    print(f"Saved vector index to {settings.paths.vector_faiss} with {len(df)} entries")


def main() -> None:
    """入口：构建语义向量索引。"""
    build_vector_index()


if __name__ == "__main__":
    main()
