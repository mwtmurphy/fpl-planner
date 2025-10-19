"""Collect current season FPL data from API.

This script performs the initial collection of current season data by fetching
bootstrap-static and all player histories from the FPL API.

Run with: poetry run python scripts/collect_current_season.py

Time: ~60-70 minutes (600+ players at 10 req/min rate limit)
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from tqdm import tqdm
except ImportError:
    print("Error: tqdm is required. Install with: poetry add tqdm")
    sys.exit(1)

from fpl.api.client import FPLClient
from fpl.core.models import Gameweek, Player, Team
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
            Path("data/logs")
            / f"collect_current_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        ),
    ],
)

logger = logging.getLogger(__name__)


async def collect_bootstrap_data(
    client: FPLClient,
) -> tuple[list[Player], list[Team], list[Gameweek]]:
    """Collect bootstrap-static data.

    Args:
        client: FPL API client

    Returns:
        Tuple of (players, teams, gameweeks)
    """
    logger.info("Fetching bootstrap-static data...")
    data = await client.get_bootstrap_static()

    players = [Player(**p) for p in data["elements"]]
    teams = [Team(**t) for t in data["teams"]]
    gameweeks = [Gameweek(**gw) for gw in data["events"]]

    logger.info(
        f"✓ Found {len(players)} players, {len(teams)} teams, {len(gameweeks)} gameweeks"
    )

    return players, teams, gameweeks


async def collect_player_history(
    client: FPLClient, player_id: int
) -> tuple[int, list[dict] | None]:
    """Collect individual player's history.

    Args:
        client: FPL API client
        player_id: Player ID

    Returns:
        Tuple of (player_id, history list or None if error)
    """
    try:
        summary = await client.get_player_summary(player_id)
        history = summary.get("history", [])
        return player_id, history
    except Exception as e:
        logger.error(f"Error fetching player {player_id}: {e}")
        return player_id, None


async def collect_all_player_histories(
    players: list[Player], storage: DataStorage
) -> dict[int, list[dict]]:
    """Collect histories for all players with progress tracking.

    Args:
        players: List of Player objects
        storage: DataStorage instance

    Returns:
        Dict mapping player_id to history list
    """
    # Filter out players who already have history (for resume capability)
    existing_histories = set()
    player_histories_dir = Path("data/current/player_histories")
    if player_histories_dir.exists():
        existing_histories = {int(f.stem) for f in player_histories_dir.glob("*.json")}

    players_to_fetch = [p for p in players if p.id not in existing_histories]

    if not players_to_fetch:
        logger.info("All player histories already collected!")
        return {}

    logger.info(
        f"Collecting histories for {len(players_to_fetch)}/{len(players)} players "
        f"({len(existing_histories)} already collected)"
    )

    # Collect with progress bar
    async with FPLClient(rate_limit=10) as client:
        histories = {}
        errors = []

        with tqdm(
            total=len(players_to_fetch), desc="Collecting player histories"
        ) as pbar:
            for player in players_to_fetch:
                player_id, history = await collect_player_history(client, player.id)

                if history is not None:
                    histories[player_id] = history
                    storage.save_player_history(player_id, history)
                else:
                    errors.append(player_id)

                pbar.update(1)

    logger.info(f"✓ Successfully collected: {len(histories)} players")
    if errors:
        logger.warning(f"✗ Errors: {len(errors)} players (IDs: {errors[:10]}...)")

    return histories


async def main_async() -> int:
    """Main async function.

    Returns:
        Exit code (0 = success, 1 = partial failure, 2 = total failure)
    """
    logger.info("=" * 70)
    logger.info("FPL Current Season Data Collection")
    logger.info("Source: FPL API (fantasy.premierleague.com)")
    logger.info("=" * 70)

    # Create storage
    storage = DataStorage(data_dir=Path("data"))

    # Create necessary directories
    Path("data/logs").mkdir(parents=True, exist_ok=True)
    Path("data/current").mkdir(parents=True, exist_ok=True)

    start_time = datetime.now()

    # Step 1: Collect bootstrap data
    async with FPLClient() as client:
        players, teams, gameweeks = await collect_bootstrap_data(client)

        # Save bootstrap data
        storage.save_players(players, filename="current/players.json")
        logger.info(f"✓ Saved {len(players)} players to current/players.json")

        storage.set_cached("current_teams", [t.model_dump() for t in teams])
        logger.info(f"✓ Saved {len(teams)} teams")

        storage.set_cached("current_gameweeks", [gw.model_dump() for gw in gameweeks])
        logger.info(f"✓ Saved {len(gameweeks)} gameweeks")

    # Get current gameweek
    current_gw = next((gw for gw in gameweeks if gw.is_current), None)
    if current_gw:
        logger.info(f"Current gameweek: {current_gw.id}")
        storage.set_last_collected_gameweek(current_gw.id)

    # Step 2: Collect player histories
    histories = await collect_all_player_histories(players, storage)

    # Summary
    elapsed = datetime.now() - start_time
    logger.info("")
    logger.info("=" * 70)
    logger.info("Collection Complete!")
    logger.info(f"Players: {len(players)}")
    logger.info(f"Histories collected: {len(histories)}")
    logger.info(f"Current gameweek: {current_gw.id if current_gw else 'Unknown'}")
    logger.info(
        f"Total time: {int(elapsed.total_seconds() // 60)} min {int(elapsed.total_seconds() % 60)} sec"
    )
    logger.info("Saved to: data/current/")
    logger.info("=" * 70)

    # Determine exit code
    if len(histories) == 0 and len(players) > 0:
        logger.error("Failed to collect any player histories!")
        return 2
    elif len(histories) < len(players):
        logger.warning(f"Partial success: {len(histories)}/{len(players)} players")
        return 1
    else:
        return 0


def main() -> int:
    """Main entry point.

    Returns:
        Exit code
    """
    return asyncio.run(main_async())


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
