#!/usr/bin/env bash
# One-click setup and run (assumes conda env llm_env already created)
set -e

cd "$(dirname "$0")"
conda activate llm_env
pip install -r requirements.txt
python -m src.pipeline.generate_listings
python -m src.pipeline.preprocess
python -m src.pipeline.build_bm25
python -m src.pipeline.build_vectors
python -m src.app.gradio_app
