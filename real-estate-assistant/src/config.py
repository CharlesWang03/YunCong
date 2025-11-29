"""Global configuration for data paths and defaults."""
from pathlib import Path
from typing import Final

BASE_DIR: Final[Path] = Path(__file__).resolve().parent.parent
DATA_DIR: Final[Path] = BASE_DIR / "data"
RAW_DIR: Final[Path] = DATA_DIR / "raw"
PROCESSED_DIR: Final[Path] = DATA_DIR / "processed"
RAW_LISTINGS_PATH: Final[Path] = RAW_DIR / "listings_generated.xlsx"
PROCESSED_LISTINGS_PATH: Final[Path] = PROCESSED_DIR / "listings.parquet"

RANDOM_SEED: Final[int] = 42
DEFAULT_LISTING_COUNT: Final[int] = 200

DATE_FORMAT: Final[str] = "%Y-%m-%d"
