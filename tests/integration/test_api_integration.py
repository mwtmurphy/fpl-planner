"""Integration tests for FPL API.

These tests make real API calls to the FPL API.
Run sparingly to respect rate limits.

Usage:
    pytest tests/integration/ -v -m integration
"""

import pytest

from fpl.api.client import FPLClient
from fpl.core.models import Player, Team, Fixture, Gameweek
from fpl.data.collectors import PlayerCollector, FixtureCollector
from fpl.data.storage import DataStorage


# Skip all integration tests by default
pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_bootstrap_static_integration():
    """Test fetching bootstrap-static data from real API."""
    async with FPLClient() as client:
        data = await client.get_bootstrap_static()

    # Verify structure
    assert "elements" in data
    assert "teams" in data
    assert "events" in data
    assert "element_types" in data

    # Verify data
    assert len(data["elements"]) > 0  # Should have players
    assert len(data["teams"]) == 20  # Premier League has 20 teams
    assert len(data["events"]) <= 38  # Max 38 gameweeks

    # Test model creation
    players = [Player(**p) for p in data["elements"]]
    assert len(players) > 0

    teams = [Team(**t) for t in data["teams"]]
    assert len(teams) == 20

    gameweeks = [Gameweek(**gw) for gw in data["events"]]
    assert len(gameweeks) > 0


@pytest.mark.asyncio
async def test_fixtures_integration():
    """Test fetching fixtures from real API."""
    async with FPLClient() as client:
        fixtures_data = await client.get_fixtures()

    # Verify we have fixtures
    assert len(fixtures_data) > 0

    # Test model creation
    fixtures = [Fixture(**f) for f in fixtures_data]

    # Verify fixture properties
    for fixture in fixtures[:5]:  # Check first 5
        assert 1 <= fixture.team_h <= 20
        assert 1 <= fixture.team_a <= 20
        assert 1 <= fixture.team_h_difficulty <= 5
        assert 1 <= fixture.team_a_difficulty <= 5


@pytest.mark.asyncio
async def test_fixtures_by_gameweek_integration():
    """Test fetching fixtures for specific gameweek."""
    async with FPLClient() as client:
        fixtures_data = await client.get_fixtures(event=1)

    # Gameweek 1 should have 10 fixtures (20 teams)
    assert len(fixtures_data) == 10

    fixtures = [Fixture(**f) for f in fixtures_data]

    # All should be for gameweek 1
    for fixture in fixtures:
        assert fixture.event == 1


@pytest.mark.asyncio
async def test_player_summary_integration():
    """Test fetching player summary."""
    async with FPLClient() as client:
        # Get bootstrap first to find a valid player ID
        bootstrap = await client.get_bootstrap_static()
        player_id = bootstrap["elements"][0]["id"]

        # Fetch player summary
        summary = await client.get_player_summary(player_id)

    # Verify structure
    assert "fixtures" in summary
    assert "history" in summary
    assert "history_past" in summary


@pytest.mark.asyncio
async def test_live_gameweek_integration():
    """Test fetching live gameweek data."""
    async with FPLClient() as client:
        # Get current gameweek
        bootstrap = await client.get_bootstrap_static()
        gameweeks = [gw for gw in bootstrap["events"] if gw["is_current"]]

        if gameweeks:
            current_gw = gameweeks[0]["id"]

            # Fetch live data
            live_data = await client.get_live_gameweek(current_gw)

            # Verify structure
            assert "elements" in live_data
            assert len(live_data["elements"]) > 0


@pytest.mark.asyncio
async def test_player_collector_integration():
    """Test PlayerCollector with real API."""
    collector = PlayerCollector()

    # Collect all players
    players = await collector.collect_all()

    assert len(players) > 500  # Should have 500+ players
    assert all(isinstance(p, Player) for p in players)

    # Test position filtering
    goalkeepers = await collector.collect_by_position(1)
    assert all(p.element_type == 1 for p in goalkeepers)
    assert (
        60 <= len(goalkeepers) <= 100
    )  # Premier League expanded squads (includes backup/3rd GKs)

    # Test team filtering
    team_players = await collector.collect_by_team(1)
    assert all(p.team == 1 for p in team_players)
    assert (
        15 <= len(team_players) <= 150
    )  # Squad size (includes historical/inactive players in FPL data)


@pytest.mark.asyncio
async def test_fixture_collector_integration():
    """Test FixtureCollector with real API."""
    collector = FixtureCollector()

    # Collect all fixtures
    fixtures = await collector.collect_all()

    assert len(fixtures) == 380  # 20 teams * 19 games * 2
    assert all(isinstance(f, Fixture) for f in fixtures)

    # Test gameweek filtering
    gw1_fixtures = await collector.collect_by_gameweek(1)
    assert len(gw1_fixtures) == 10  # 20 teams = 10 matches


@pytest.mark.asyncio
async def test_storage_integration(tmp_path):
    """Test full data pipeline with real API."""
    storage = DataStorage(data_dir=tmp_path)
    collector = PlayerCollector()

    # Collect data
    players = await collector.collect_all()

    # Save in multiple formats
    storage.save_players(players, "players.json")
    storage.save_players_csv(players, "players.csv")

    # Verify files exist
    assert (tmp_path / "players.json").exists()
    assert (tmp_path / "players.csv").exists()

    # Load back
    loaded_players = storage.load_players("players.json")
    assert len(loaded_players) == len(players)

    # Test DataFrame export
    df = storage.export_to_dataframe(players)
    assert len(df) == len(players)

    # Save timestamps
    storage.set_last_update("players")
    last_update = storage.get_last_update("players")
    assert last_update is not None


@pytest.mark.asyncio
async def test_rate_limiter_integration():
    """Test rate limiter with real API calls."""
    import time

    start_time = time.time()

    async with FPLClient(rate_limit=5) as client:  # 5 requests per minute
        # Make 5 requests quickly
        for _ in range(5):
            await client.get_bootstrap_static()

    elapsed = time.time() - start_time

    # Should complete quickly (all within rate limit)
    assert elapsed < 2.0  # Should take less than 2 seconds for 5 requests


@pytest.mark.asyncio
async def test_error_handling_integration():
    """Test error handling with invalid requests."""
    async with FPLClient() as client:
        # Test 404 error
        from fpl.api.exceptions import NotFoundError

        with pytest.raises(NotFoundError):
            await client.get_player_summary(999999)


@pytest.mark.asyncio
async def test_complete_workflow_integration(tmp_path):
    """Test complete end-to-end workflow.

    This test demonstrates a realistic usage pattern:
    1. Fetch data from API
    2. Process with collectors
    3. Analyze with helpers
    4. Store results
    """
    from fpl.utils.helpers import (
        calculate_value,
        format_price,
        get_team_name,
        is_premium,
    )

    storage = DataStorage(data_dir=tmp_path)
    player_collector = PlayerCollector()

    # Fetch data
    bootstrap = await (await FPLClient().__aenter__()).get_bootstrap_static()
    players_data = bootstrap["elements"]
    teams_data = bootstrap["teams"]

    # Create models
    players = [Player(**p) for p in players_data]
    teams = [Team(**t) for t in teams_data]

    # Analyze top scorers
    top_scorers = sorted(players, key=lambda p: p.total_points, reverse=True)[:10]

    analysis_results = []
    for player in top_scorers:
        result = {
            "name": player.web_name,
            "team": get_team_name(player.team, teams),
            "price": format_price(player.now_cost),
            "points": player.total_points,
            "value": float(calculate_value(player.price, player.total_points)),
            "is_premium": is_premium(player.price),
        }
        analysis_results.append(result)

    # Verify analysis
    assert len(analysis_results) == 10
    assert all(r["points"] > 0 for r in analysis_results)
    assert analysis_results[0]["points"] >= analysis_results[9]["points"]

    # Store results
    storage.save_players(players, "all_players.json")
    storage.set_last_update("players")

    # Create DataFrame and export
    df = storage.export_to_dataframe(top_scorers)
    storage.save_dataframe(df, "top_scorers.csv", format="csv")

    # Verify storage
    assert (tmp_path / "all_players.json").exists()
    assert (tmp_path / "top_scorers.csv").exists()
    assert storage.get_last_update("players") is not None
