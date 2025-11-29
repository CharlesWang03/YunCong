# Design Overview

A minimal pipeline for synthetic real-estate listings:

1. `generator.py`: create randomized residential listings to Excel for experimentation.
2. `preprocess.py`: clean types, normalize columns, and persist Parquet for fast querying.
3. `repository.py`: load processed data and expose typed DataFrame access.
4. `filter_engine.py`: apply structured filters with Pandas masking.
5. `ranking.py`: optional scoring layer to reorder matches.
6. `gradio_app.py`: UI wiring to accept user input, parse filters, and render results.

Key decisions
- Keep configuration centralized in `config.py` to ease path changes and seeding.
- Use dataclasses/pydantic models for clarity of schema and validation.
- Favor simple, synchronous pandas operations for ease of understanding.
- Rule-based NLP keeps parsing transparent and debuggable; can be swapped later.
