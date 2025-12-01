#!/usr/bin/env bash
# Launch the Gradio UI after data/indexes are prepared.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

DATA_PARQUET="data/processed/listings.parquet"
BM25_INDEX="data/processed/bm25_index.joblib"
VECTOR_FAISS="data/processed/vector_index.faiss"
VECTOR_META="data/processed/vector_meta.joblib"

missing=()
[[ -f "$DATA_PARQUET" ]] || missing+=("$DATA_PARQUET")
[[ -f "$BM25_INDEX" ]] || missing+=("$BM25_INDEX")
[[ -f "$VECTOR_FAISS" ]] || missing+=("$VECTOR_FAISS")
[[ -f "$VECTOR_META" ]] || missing+=("$VECTOR_META")

if (( ${#missing[@]} > 0 )); then
  echo "The following artifacts are missing:"
  printf ' - %s\n' "${missing[@]}"
  echo "Please run scripts/setup.sh first to generate data and indexes." >&2
  exit 1
fi

if [[ -z "${OPENAI_API_KEY:-}" ]] && [[ ! -f .env ]]; then
  echo "OPENAI_API_KEY is not set and no .env file found. The assistant mode may fail to call the LLM." >&2
fi

echo "Starting Gradio app on 127.0.0.1:7860..."
python -m src.app.gradio_app
