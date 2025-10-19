"""Update FPL data with latest gameweeks.

This script updates all player histories with the latest N gameweeks from the FPL API.
Updates ALL players (including those who didn't play) to maintain data completeness.

Run with: poetry run python scripts/update_latest_gameweeks.py [--gameweeks N]

Time: ~60-70 minutes (600+ players at 10 req/min rate limit)
"""

import argparse
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
from fpl.core.models import Gameweek, Player
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
            Path("data/logs") / f"update_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        ),
    ],
)

logger = logging.getLogger(__name__)


async def get_current_gameweek(client: FPLClient) -> tuple[int, list[Player]]:
    """Get current gameweek and all players.

    Args:
        client: FPL API client

    Returns:
        Tuple of (current_gameweek_id, players_list)
    """
    logger.info("Fetching bootstrap-static...")
    data = await client.get_bootstrap_static()

    gameweeks = [Gameweek(**gw) for gw in data["events"]]
    players = [Player(**p) for p in data["elements"]]

    # Find current gameweek
    current_gw = next((gw for gw in gameweeks if gw.is_current), None)
    if not current_gw:
        # If no current gameweek, get the latest finished one
        finished_gws = [gw for gw in gameweeks if gw.finished]
        current_gw = max(finished_gws, key=lambda gw: gw.id) if finished_gws else None

    if not current_gw:
        raise ValueError("Could not determine current gameweek")

    logger.info(f"✓ Current gameweek: {current_gw.id}")
    logger.info(f"✓ Found {len(players)} active players")

    return current_gw.id, players


async def update_player_history(
    client: FPLClient,
    player_id: int,
    storage: DataStorage,
    since_gameweek: int,
) -> tuple[int, int, bool]:
    """Update a single player's history with new gameweeks.

    Args:
        client: FPL API client
        player_id: Player ID
        storage: DataStorage instance
        since_gameweek: Only process gameweeks after this number

    Returns:
        Tuple of (player_id, new_gameweeks_count, success)
    """
    try:
        # Fetch latest history from API
        summary = await client.get_player_summary(player_id)
        api_history = summary.get("history", [])

        # Load existing history
        existing_history = storage.load_player_history(player_id) or []

        # Find new gameweeks
        existing_gws = {h["round"] for h in existing_history}
        new_entries = [h for h in api_history if h["round"] > since_gameweek]

        # Merge: keep existing + add new
        merged_history = existing_history.copy()
        new_count = 0

        for entry in new_entries:
            gw = entry["round"]
            if gw not in existing_gws:
                merged_history.append(entry)
                new_count += 1

        # Save updated history
        if new_count > 0 or not existing_history:
            storage.save_player_history(player_id, merged_history)

        return player_id, new_count, True

    except Exception as e:
        logger.error(f"Error updating player {player_id}: {e}")
        return player_id, 0, False


async def update_all_players(
    players: list[Player],
    storage: DataStorage,
    since_gameweek: int,
) -> dict[str, int]:
    """Update all players with new gameweeks.

    Args:
        players: List of all players
        storage: DataStorage instance
        since_gameweek: Only process gameweeks after this number

    Returns:
        Dict with summary statistics
    """
    logger.info(
        f"Updating {len(players)} players with gameweeks since GW{since_gameweek}..."
    )

    stats = {
        "total": len(players),
        "updated": 0,
        "new_gameweeks": 0,
        "played": 0,
        "didnt_play": 0,
        "errors": 0,
    }

    async with FPLClient(rate_limit=10) as client:
        with tqdm(total=len(players), desc="Updating players") as pbar:
            for player in players:
                player_id, new_gw_count, success = await update_player_history(
                    client, player.id, storage, since_gameweek
                )

                if success:
                    stats["updated"] += 1
                    stats["new_gameweeks"] += new_gw_count

                    if new_gw_count > 0:
                        stats["played"] += 1
                    else:
                        stats["didnt_play"] += 1
                else:
                    stats["errors"] += 1

                pbar.update(1)

    return stats


async def main_async(gameweeks: int) -> int:
    """Main async function.

    Args:
        gameweeks: Number of latest gameweeks to update

    Returns:
        Exit code
    """
    logger.info("=" * 70)
    logger.info("FPL Data Update - Latest Gameweeks")
    logger.info(f"Updating latest {gameweeks} gameweek(s)")
    logger.info("=" * 70)

    # Create storage
    storage = DataStorage(data_dir=Path("data"))

    # Create necessary directories
    Path("data/logs").mkdir(parents=True, exist_ok=True)

    start_time = datetime.now()

    # Step 1: Get current gameweek and players
    async with FPLClient() as client:
        current_gw, players = await get_current_gameweek(client)

    # Step 2: Determine which gameweeks to collect
    last_collected = storage.get_last_collected_gameweek()

    if last_collected:
        logger.info(f"Last collected gameweek: {last_collected}")
        since_gameweek = max(last_collected, current_gw - gameweeks)
    else:
        logger.info("No previous collection found, collecting all available gameweeks")
        since_gameweek = 0

    logger.info(f"Will collect gameweeks: {since_gameweek + 1} to {current_gw}")

    if since_gameweek >= current_gw:
        logger.info("No new gameweeks to collect!")
        return 0

    # Step 3: Update all players
    stats = await update_all_players(players, storage, since_gameweek)

    # Step 4: Update metadata
    storage.set_last_collected_gameweek(current_gw)
    storage.set_last_update("current", datetime.now())

    # Summary
    elapsed = datetime.now() - start_time
    logger.info("")
    logger.info("=" * 70)
    logger.info("Update Complete!")
    logger.info(f"Players processed: {stats['total']}")
    logger.info(f"Successfully updated: {stats['updated']}")
    logger.info(
        f"Players who played: {stats['played']} ({stats['played']/stats['total']*100:.1f}%)"
    )
    logger.info(
        f"Players who didn't play: {stats['didnt_play']} ({stats['didnt_play']/stats['total']*100:.1f}%)"
    )
    logger.info(f"Total new gameweek entries: {stats['new_gameweeks']}")
    logger.info(f"Errors: {stats['errors']}")
    logger.info(f"Latest gameweek: {current_gw}")
    logger.info(
        f"Total time: {int(elapsed.total_seconds() // 60)} min {int(elapsed.total_seconds() % 60)} sec"
    )
    logger.info("=" * 70)

    # Determine exit code
    if stats["errors"] > stats["total"] * 0.1:  # > 10% errors
        logger.warning("High error rate!")
        return 1
    elif stats["errors"] > 0:
        logger.warning(f"{stats['errors']} errors occurred")
        return 1
    else:
        return 0


def main() -> int:
    """Main entry point.

    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(
        description="Update FPL data with latest gameweeks"
    )
    parser.add_argument(
        "--gameweeks",
        "-n",
        type=int,
        default=1,
        help="Number of latest gameweeks to update (default: 1)",
    )

    args = parser.parse_args()

    if args.gameweeks < 1:
        logger.error("--gameweeks must be >= 1")
        return 1

    return asyncio.run(main_async(args.gameweeks))


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
