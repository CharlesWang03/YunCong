"""Project configuration for analyze-agent."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict


@dataclass
class Paths:
    base_dir: Path = Path(__file__).resolve().parent.parent
    data_dir: Path = base_dir / "data"
    raw_dir: Path = data_dir / "raw"
    processed_dir: Path = data_dir / "processed"
    raw_excel: Path = raw_dir / "listings.xlsx"
    processed_parquet: Path = processed_dir / "listings.parquet"
    bm25_index: Path = processed_dir / "bm25_index.joblib"
    vector_index: Path = processed_dir / "vector_index.joblib"


@dataclass
class RetrievalWeights:
    quality: float = 0.5
    bm25: float = 0.25
    semantic: float = 0.25
    promotion: float = 0.1  # multiplier for promotion_weight if present


@dataclass
class Settings:
    paths: Paths = Paths()
    weights: RetrievalWeights = RetrievalWeights()
    bm25_max_features: int = 8000
    bm25_ngram: tuple[int, int] = (1, 2)
    semantic_model: str = "tfidf"  # placeholder; swap to sentence-transformers name if needed


settings = Settings()
