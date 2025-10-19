"""Data loading utilities for Streamlit app."""

import asyncio
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from fpl.api.client import FPLClient
from fpl.core.models import Team
from fpl.data.collectors import PlayerCollector
from fpl.data.storage import DataStorage
from fpl.utils.helpers import (
    calculate_form_fixtures,
    calculate_form_games,
    calculate_form_rating,
    calculate_value,
    format_price,
    get_player_status_circle,
    get_player_status_emoji,
    get_position_name,
    get_team_name,
)


@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_all_data(
    use_local_data: bool = True,
) -> tuple[pd.DataFrame, dict[int, str], str]:
    """Load all player and team data with caching.

    Args:
        use_local_data: If True, load from local storage. If False or local data
                       not available, fetch from FPL API.

    Returns:
        Tuple of (DataFrame with player data, teams dict, last update timestamp)
    """
    # Try to load from local data first
    if use_local_data:
        data_dir = Path("data")
        storage = DataStorage(data_dir=data_dir)

        # Check if we have local data
        player_histories_dir = data_dir / "current" / "player_histories"
        has_local_data = player_histories_dir.exists() and any(
            player_histories_dir.glob("*.json")
        )

        if has_local_data:
            # Load from local storage
            return _load_from_local_storage(storage)

    # Fallback to API
    return _load_from_api()


def _load_from_local_storage(
    storage: DataStorage,
) -> tuple[pd.DataFrame, dict[int, str], str]:
    """Load data from local storage.

    Args:
        storage: DataStorage instance

    Returns:
        Tuple of (DataFrame with player data, teams dict, last update timestamp)
    """
    # Load current players (from bootstrap-static)
    players_data = storage.load_players(filename="current/players.json")

    # Load teams
    teams_cached = storage.get_cached("current_teams")
    if teams_cached:
        teams = [Team(**t) for t in teams_cached]
    else:
        # Fallback: fetch teams from API if cache is missing
        async def fetch_teams():
            async with FPLClient() as client:
                bootstrap = await client.get_bootstrap_static()
                return [Team(**t) for t in bootstrap["teams"]]

        teams = asyncio.run(fetch_teams())
        # Cache for next time
        storage.set_cached("current_teams", [t.model_dump() for t in teams])

    teams_dict = {t.id: t.name for t in teams}

    # Convert players to DataFrame with all metrics
    data = []
    for player_data in players_data:
        # Handle both dict and Player model
        p: dict[str, Any]
        if hasattr(player_data, "model_dump"):
            p = player_data.model_dump()
        else:
            # Type ignore: storage can return raw dicts from JSON in some cases
            p = player_data  # type: ignore[assignment]

        player_id = p.get("id")
        price = float(p.get("now_cost", 0)) / 10.0
        total_points = p.get("total_points", 0)

        # Load player history for form calculations
        history = storage.load_player_history(player_id) if player_id else []

        # Calculate form metrics
        form_fixtures_val = calculate_form_fixtures(history, n=5) if history else 0.0
        form_games_val = (
            calculate_form_games(history, n=5) if history else float(p.get("form", 0))
        )  # Fallback to API form

        # Calculate value metrics
        value_fixtures = (
            float(calculate_value(Decimal(price), total_points)) if price > 0 else 0.0
        )
        value_games = (
            (form_games_val * 38 / price) if price > 0 and form_games_val > 0 else 0.0
        )

        data.append(
            {
                "name": p.get("web_name", ""),
                "team_name": teams_dict.get(p.get("team") or 0, "Unknown"),
                "team_id": p.get("team"),
                "position": get_position_name(p.get("element_type") or 0),
                "price": price,
                "price_formatted": format_price(p.get("now_cost", 0)),
                "total_points": total_points,
                "form_fixtures": form_fixtures_val,
                "value_fixtures": value_fixtures,
                "form_games": form_games_val,
                "value_games": value_games,
                "form": form_games_val,  # Keep for backward compatibility
                "form_rating": calculate_form_rating(str(form_games_val)),
                "value": value_fixtures,  # Keep for backward compatibility
                "ownership": float(p.get("selected_by_percent", 0)),
                "status": p.get("status", "a"),
                "status_emoji": get_player_status_emoji(p.get("status", "a")),
                "status_circle": get_player_status_circle(p.get("status", "a")),
                "minutes": p.get("minutes", 0),
            }
        )

    df = pd.DataFrame(data)

    # Get last update info
    last_gw = storage.get_last_collected_gameweek()
    last_update_meta = storage.get_last_update("current")

    if last_update_meta:
        last_update = last_update_meta.strftime("%Y-%m-%d %H:%M")
    else:
        last_update = "Unknown"

    if last_gw:
        last_update = f"{last_update} (GW{last_gw})"

    return df, teams_dict, last_update


def _load_from_api() -> tuple[pd.DataFrame, dict[int, str], str]:
    """Load data from FPL API.

    Returns:
        Tuple of (DataFrame with player data, teams dict, last update timestamp)
    """

    async def fetch_data():
        """Async function to fetch data from FPL API."""
        collector = PlayerCollector()
        players = await collector.collect_all()

        async with FPLClient() as client:
            bootstrap = await client.get_bootstrap_static()
            teams = [Team(**t) for t in bootstrap["teams"]]

        return players, teams

    # Run async function
    players, teams = asyncio.run(fetch_data())

    # Create teams dictionary for lookups
    teams_dict = {t.id: t.name for t in teams}

    # Convert players to DataFrame with all calculated fields
    # Note: The "form" field from FPL API represents the average points over the
    # last 5 games (fixtures) that the player actually played in. This accounts for
    # double gameweeks and only includes games where the player was in the squad.
    #
    # We do NOT calculate our own "avg_points_5_games" column here because it would
    # require fetching individual player history for all 600+ players via the
    # element-summary endpoint. This would result in:
    # - 600+ API calls (rate limited to 10/min = 60+ minutes load time)
    # - Significant performance degradation
    # - Unnecessary load on the FPL API
    #
    # Future enhancement: Could add this metric for filtered/selected players only,
    # or implement background caching of player histories.
    data = []
    for player in players:
        price = float(player.price)
        form_api = float(player.form)
        total_points = player.total_points

        # For API-loaded data, we don't have history, so use API form for both
        # and approximate fixture form as same as game form
        value_fixtures = float(calculate_value(player.price, total_points))
        value_games = (form_api * 38 / price) if price > 0 else 0.0

        data.append(
            {
                "name": player.web_name,
                "team_name": get_team_name(player.team, teams),
                "team_id": player.team,
                "position": get_position_name(player.element_type),
                "price": price,
                "price_formatted": format_price(player.now_cost),
                "total_points": total_points,
                "form_fixtures": form_api,  # Approximate
                "value_fixtures": value_fixtures,
                "form_games": form_api,
                "value_games": value_games,
                "form": form_api,  # Keep for backward compatibility
                "form_rating": calculate_form_rating(player.form),
                "value": value_fixtures,  # Keep for backward compatibility
                "ownership": player.ownership_percent,
                "status": player.status,
                "status_emoji": get_player_status_emoji(player.status),
                "status_circle": get_player_status_circle(player.status),
                "minutes": player.minutes,
            }
        )

    df = pd.DataFrame(data)
    last_update = datetime.now().strftime("%Y-%m-%d %H:%M")

    return df, teams_dict, last_update


def load_snapshot_data(
    season: str, through_gameweek: int
) -> tuple[pd.DataFrame, dict[int, str], str]:
    """Load player stats snapshot through a specific gameweek.

    Args:
        season: Season identifier (e.g., "2023-24" or "2024-25 (Current)")
        through_gameweek: Show stats through end of this gameweek

    Returns:
        Tuple of (DataFrame with player data, teams dict, last update timestamp)
    """
    storage = DataStorage(data_dir=Path("data"))

    # Determine actual season string
    actual_season = season.replace(" (Current)", "")

    if season == "2024-25 (Current)":
        # Current season snapshot from player histories
        # For now, return current data
        # TODO: Filter histories to only include data through_gameweek
        return load_all_data(use_local_data=True)  # type: ignore[no-any-return]
    else:
        # Historical season from merged_gw.csv
        season_df = storage.load_historical_season(actual_season)

        if season_df is None:
            # Return empty data if season not found
            return pd.DataFrame(), {}, f"{season} (not available)"

        # Filter to gameweeks through selected GW
        if "round" in season_df.columns:
            season_df = season_df[season_df["round"] <= through_gameweek].copy()
        elif "GW" in season_df.columns:
            season_df = season_df[season_df["GW"] <= through_gameweek].copy()

        # Get unique teams
        teams_dict = {}
        if "team" in season_df.columns and "team_name" in season_df.columns:
            teams_dict = dict(zip(season_df["team"], season_df["team_name"]))

        # Group by player and aggregate stats
        if "element" in season_df.columns:
            # Aggregate per player
            player_stats = (
                season_df.groupby("element")
                .agg(
                    {
                        "name": "first",
                        "position": "first",
                        "team": "first",
                        "total_points": "sum",
                        "value": "last",  # Last known price
                        "selected": "last",  # Last known ownership
                    }
                )
                .reset_index()
            )

            # Convert to dataframe format
            data = []
            for _, row in player_stats.iterrows():
                price = float(row.get("value", 0)) / 10.0 if row.get("value") else 0.0
                total_points = int(row.get("total_points", 0))

                data.append(
                    {
                        "name": row.get("name", ""),
                        "team_name": teams_dict.get(row.get("team"), "Unknown"),
                        "team_id": row.get("team"),
                        "position": row.get("position", ""),
                        "price": price,
                        "price_formatted": f"£{price:.1f}m",
                        "total_points": total_points,
                        "form_fixtures": 0.0,  # TODO: Calculate from history
                        "value_fixtures": (total_points / price if price > 0 else 0.0),
                        "form_games": 0.0,  # TODO: Calculate from history
                        "value_games": 0.0,
                        "form": 0.0,
                        "form_rating": "Unknown",
                        "value": total_points / price if price > 0 else 0.0,
                        "ownership": float(row.get("selected", 0)) / 10000.0,
                        "status": "a",
                        "status_emoji": "✅",
                        "status_circle": "🟢",
                        "minutes": 0,
                    }
                )

            df = pd.DataFrame(data)
            return df, teams_dict, f"{season} through GW{through_gameweek}"
        else:
            return pd.DataFrame(), {}, f"{season} (data format error)"
