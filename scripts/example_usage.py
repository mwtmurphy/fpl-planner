"""Example script demonstrating FPL package usage.

Run with: poetry run python scripts/example_usage.py
"""

import asyncio

from fpl.api.client import FPLClient
from fpl.core.models import Player
from fpl.data.collectors import PlayerCollector
from fpl.utils.helpers import format_price


async def main() -> None:
    """Main example function."""
    print("FPL Data Collection Example\n")

    # Example 1: Fetch all players
    print("=== Example 1: Fetch All Players ===")
    async with FPLClient() as client:
        data = await client.get_bootstrap_static()
        players = [Player(**p) for p in data["elements"]]
        print(f"Fetched {len(players)} players\n")

    # Example 2: Use collector
    print("=== Example 2: Use PlayerCollector ===")
    collector = PlayerCollector()
    players = await collector.collect_all()
    print(f"Collected {len(players)} players\n")

    # Example 3: Filter players
    print("=== Example 3: Filter Top Scorers ===")
    top_scorers = sorted(players, key=lambda p: p.total_points, reverse=True)[:5]

    for i, player in enumerate(top_scorers, 1):
        print(
            f"{i}. {player.web_name} ({player.position_name}) - "
            f"{player.total_points} pts, {format_price(player.now_cost)}"
        )

    print("\n=== Example 4: Filter by Team ===")
    arsenal_players = [p for p in players if p.team == 1]
    print(f"Arsenal has {len(arsenal_players)} players\n")

    # Example 5: Get fixtures
    print("=== Example 5: Fetch Fixtures ===")
    async with FPLClient() as client:
        fixtures = await client.get_fixtures(event=1)
        print(f"Gameweek 1 has {len(fixtures)} fixtures\n")

    print("Examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
