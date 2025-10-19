"""Import historical FPL data from vaastav/Fantasy-Premier-League repository.

This script downloads merged gameweek data for all available seasons (2016-17 through
2024-25) from the vaastav GitHub repository and stores it locally.

Run with: poetry run python scripts/import_historical_data.py

Note: vaastav repository stopped weekly updates after 2024-25 season.
Only 3 updates per season: start, January transfer window, end of season.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pandas as pd

from fpl.data.storage import DataStorage

# Create logs directory
Path("data/logs").mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            Path("data/logs") / f"import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        ),
    ],
)

logger = logging.getLogger(__name__)

# Constants
VAASTAV_BASE_URL = "https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data"
SEASONS = [
    "2016-17",
    "2017-18",
    "2018-19",
    "2019-20",
    "2020-21",
    "2021-22",
    "2022-23",
    "2023-24",
    "2024-25",
]

# Expected columns in merged_gw.csv (for validation)
EXPECTED_COLUMNS = {
    "name",
    "position",
    "team",
    "assists",
    "bonus",
    "bps",
    "clean_sheets",
    "creativity",
    "element",
    "fixture",
    "goals_conceded",
    "goals_scored",
    "ict_index",
    "influence",
    "kickoff_time",
    "minutes",
    "opponent_team",
    "own_goals",
    "penalties_missed",
    "penalties_saved",
    "red_cards",
    "round",
    "saves",
    "selected",
    "team_a_score",
    "team_h_score",
    "threat",
    "total_points",
    "transfers_balance",
    "transfers_in",
    "transfers_out",
    "value",
    "was_home",
    "yellow_cards",
    "GW",
}


def import_season(season: str, storage: DataStorage) -> tuple[bool, int]:
    """Import a single season's data.

    Args:
        season: Season identifier (e.g., "2023-24")
        storage: DataStorage instance

    Returns:
        Tuple of (success: bool, row_count: int)
    """
    url = f"{VAASTAV_BASE_URL}/{season}/gws/merged_gw.csv"

    try:
        logger.info(f"Downloading {season}...")

        # Try different encodings and error handling
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
        df = None

        for encoding in encodings:
            try:
                df = pd.read_csv(
                    url,
                    encoding=encoding,
                    on_bad_lines='skip',  # Skip problematic lines
                    low_memory=False
                )
                break
            except (UnicodeDecodeError, pd.errors.ParserError):
                continue

        if df is None:
            raise ValueError("Could not read CSV with any encoding")

        # Validate columns
        df_columns = set(df.columns)
        missing = EXPECTED_COLUMNS - df_columns
        if missing:
            logger.warning(
                f"{season}: Missing columns {missing}, but proceeding anyway"
            )

        # Save to storage
        storage.save_historical_season(season, df)

        row_count = len(df)
        logger.info(f"{season}: ✓ ({row_count:,} rows)")

        return True, row_count

    except Exception as e:
        logger.error(f"{season}: ✗ Error: {e}")
        return False, 0


def main() -> int:
    """Import all historical seasons.

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    logger.info("=" * 60)
    logger.info("FPL Historical Data Import")
    logger.info("Source: vaastav/Fantasy-Premier-League GitHub repository")
    logger.info("=" * 60)

    # Create storage
    storage = DataStorage(data_dir=Path("data"))

    # Create logs directory
    logs_dir = Path("data/logs")
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Import each season
    results = {}
    total_rows = 0

    for season in SEASONS:
        success, row_count = import_season(season, storage)
        results[season] = success
        total_rows += row_count

    # Summary
    successful = sum(1 for v in results.values() if v)
    failed = len(results) - successful

    logger.info("")
    logger.info("=" * 60)
    logger.info("Import Complete!")
    logger.info(f"Successful: {successful}/{len(SEASONS)} seasons")
    logger.info(f"Failed: {failed}/{len(SEASONS)} seasons")
    logger.info(f"Total rows imported: {total_rows:,}")
    logger.info(f"Saved to: data/historical/")
    logger.info("=" * 60)

    # List failed seasons if any
    if failed > 0:
        failed_seasons = [s for s, v in results.items() if not v]
        logger.warning(f"Failed seasons: {', '.join(failed_seasons)}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
