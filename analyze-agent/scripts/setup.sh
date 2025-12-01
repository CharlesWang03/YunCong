#!/usr/bin/env bash
# Prepare demo data and indexes for the analyze-agent app.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[1/5] Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo "[2/5] Generating sample listings Excel (data/raw/listings.xlsx)..."
python -m src.pipeline.generate_listings

echo "[3/5] Cleaning Excel into structured Parquet (data/processed/listings.parquet)..."
python -m src.pipeline.preprocess

echo "[4/5] Building BM25 lexical index..."
python -m src.pipeline.build_bm25

echo "[5/5] Building semantic vector index..."
python -m src.pipeline.build_vectors

echo "Setup complete. You can now launch the Gradio UI via scripts/start_gradio.sh"
