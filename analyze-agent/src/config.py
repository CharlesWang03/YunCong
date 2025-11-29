"""Global configuration placeholders."""
from pathlib import Path
from dataclasses import dataclass


@dataclass
class Paths:
    """Project path configuration (TODO: adjust to actual env)."""
    base_dir: Path = Path(__file__).resolve().parent.parent
    data_dir: Path = base_dir / "data"
    raw_dir: Path = data_dir / "raw"
    processed_dir: Path = data_dir / "processed"
    bm25_index: Path = processed_dir / "bm25_index.bin"
    vector_index: Path = processed_dir / "vectors.faiss"


# TODO: add runtime settings (LLM keys, endpoints, weights, etc.)
