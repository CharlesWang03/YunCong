"""Project configuration for analyze-agent."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv

# 预加载仓库内 .env（若存在），便于本地读取 OPENAI_API_KEY 等
_BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(_BASE_DIR / ".env")


@dataclass
class Paths:
    base_dir: Path = _BASE_DIR
    data_dir: Path = base_dir / "data"
    raw_dir: Path = data_dir / "raw"
    processed_dir: Path = data_dir / "processed"
    raw_excel: Path = raw_dir / "listings.xlsx"
    processed_parquet: Path = processed_dir / "listings.parquet"
    bm25_index: Path = processed_dir / "bm25_index.joblib"
    vector_faiss: Path = processed_dir / "vector_index.faiss"
    vector_meta: Path = processed_dir / "vector_meta.joblib"


@dataclass
class RetrievalWeights:
    quality: float = 0.6
    bm25: float = 0.2
    semantic: float = 0.2
    promotion: float = 0.2  # max boost factor (as percentage) for promotion multiplier


@dataclass
class Settings:
    paths: Paths = field(default_factory=Paths)
    weights: RetrievalWeights = field(default_factory=RetrievalWeights)
    quality_weights: Dict[str, float] = field(
        default_factory=lambda: {
            "price": 0.25,
            "area": 0.15,
            "age": 0.1,
            "subway": 0.2,
            "school": 0.15,
            "floor": 0.05,
            "orientation": 0.05,
            "renovation": 0.05,
        }
    )
    bm25_max_features: int = 8000
    bm25_ngram: tuple[int, int] = (1, 2)
    semantic_model: str = "BAAI/bge-small-zh"  # embedding model name
    llm_model: str = "gpt-4o-mini"
    llm_api_key_env: str = "OPENAI_API_KEY"
    llm_api_key: str | None = None  # 如需写死本地 key，可在此填入（不推荐提交）


settings = Settings()
