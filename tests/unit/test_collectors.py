"""Unit tests for data collectors."""

import pytest
from datetime import datetime, timedelta
from pytest_httpx import HTTPXMock

from fpl.api.client import FPLClient
from fpl.data.collectors import PlayerCollector, FixtureCollector
from fpl.core.models import Player, PlayerHistory, Fixture


# PlayerCollector tests


@pytest.mark.asyncio
async def test_player_collector_collect_all(
    httpx_mock: HTTPXMock, sample_player_data, sample_team_data
):
    """Test collecting all players."""
    # Build response manually to avoid datetime serialization issues
    response = {
        "elements": [sample_player_data],
        "teams": [sample_team_data],
        "events": [],
    }

    httpx_mock.add_response(
        url="https://fantasy.premierleague.com/api/bootstrap-static/",
        json=response,
    )

    collector = PlayerCollector()
    players = await collector.collect_all()

    assert len(players) == 1
    assert isinstance(players[0], Player)
    assert players[0].id == 302


@pytest.mark.asyncio
async def test_player_collector_with_client(
    httpx_mock: HTTPXMock, sample_player_data, sample_team_data
):
    """Test collector with injected client."""
    response = {
        "elements": [sample_player_data],
        "teams": [sample_team_data],
        "events": [],
    }

    httpx_mock.add_response(
        url="https://fantasy.premierleague.com/api/bootstrap-static/",
        json=response,
    )

    async with FPLClient() as client:
        collector = PlayerCollector(client=client)
        players = await collector.collect_all()

    assert len(players) == 1


@pytest.mark.asyncio
async def test_player_collector_by_team(
    httpx_mock: HTTPXMock, sample_player_data, sample_team_data
):
    """Test collecting players by team."""
    # Add second player for different team
    player2 = sample_player_data.copy()
    player2["id"] = 400
    player2["team"] = 2

    response = {
        "elements": [sample_player_data, player2],
        "teams": [sample_team_data],
        "events": [],
    }

    httpx_mock.add_response(
        url="https://fantasy.premierleague.com/api/bootstrap-static/",
        json=response,
    )

    collector = PlayerCollector()
    team1_players = await collector.collect_by_team(1)

    assert len(team1_players) == 1
    assert team1_players[0].team == 1


@pytest.mark.asyncio
async def test_player_collector_by_position(
    httpx_mock: HTTPXMock, sample_player_data, sample_team_data
):
    """Test collecting players by position."""
    # Add second player for different position
    player2 = sample_player_data.copy()
    player2["id"] = 400
    player2["element_type"] = 4  # Forward

    response = {
        "elements": [sample_player_data, player2],
        "teams": [sample_team_data],
        "events": [],
    }

    httpx_mock.add_response(
        url="https://fantasy.premierleague.com/api/bootstrap-static/",
        json=response,
    )

    collector = PlayerCollector()
    midfielders = await collector.collect_by_position(3)

    assert len(midfielders) == 1
    assert midfielders[0].element_type == 3


@pytest.mark.asyncio
async def test_player_collector_history(httpx_mock: HTTPXMock):
    """Test collecting player history."""
    # Build history data without datetime
    history_data = {
        "element": 302,
        "fixture": 1,
        "opponent_team": 2,
        "total_points": 8,
        "was_home": True,
        "kickoff_time": "2024-08-16T20:00:00",
        "round": 1,
        "minutes": 90,
        "goals_scored": 1,
        "assists": 0,
        "clean_sheets": 0,
        "goals_conceded": 1,
        "own_goals": 0,
        "penalties_saved": 0,
        "penalties_missed": 0,
        "yellow_cards": 0,
        "red_cards": 0,
        "saves": 0,
        "bonus": 2,
        "bps": 32,
        "influence": "65.2",
        "creativity": "42.8",
        "threat": "58.0",
        "ict_index": "16.6",
        "value": 95,
        "selected": 3500000,
    }

    mock_summary = {
        "fixtures": [],
        "history": [history_data],
        "history_past": [],
    }

    httpx_mock.add_response(
        url="https://fantasy.premierleague.com/api/element-summary/302/",
        json=mock_summary,
    )

    collector = PlayerCollector()
    history = await collector.collect_player_history(302)

    assert len(history) == 1
    assert isinstance(history[0], PlayerHistory)
    assert history[0].element == 302
    assert history[0].total_points == 8


@pytest.mark.asyncio
async def test_player_collector_changed_players_all(
    httpx_mock: HTTPXMock, sample_player_data, sample_team_data
):
    """Test collecting changed players with no timestamp returns all."""
    response = {
        "elements": [sample_player_data],
        "teams": [sample_team_data],
        "events": [],
    }

    httpx_mock.add_response(
        url="https://fantasy.premierleague.com/api/bootstrap-static/",
        json=response,
    )

    collector = PlayerCollector()
    changed = await collector.collect_changed_players(last_update=None)

    assert len(changed) == 1


@pytest.mark.asyncio
async def test_player_collector_changed_players_filtered(
    httpx_mock: HTTPXMock, sample_player_data, sample_team_data
):
    """Test collecting only changed players."""
    # Add multiple players with different change indicators
    player1 = sample_player_data.copy()
    player1["id"] = 302
    player1["event_points"] = 8  # Played recently

    player2 = sample_player_data.copy()
    player2["id"] = 400
    player2["event_points"] = 0
    player2["transfers_in_event"] = 1000  # Transfer activity
    player2["transfers_out_event"] = 0

    player3 = sample_player_data.copy()
    player3["id"] = 500
    player3["event_points"] = 0
    player3["transfers_in_event"] = 0
    player3["transfers_out_event"] = 0  # No transfer activity
    player3["cost_change_event"] = 0
    player3["news"] = ""  # No changes

    response = {
        "elements": [player1, player2, player3],
        "teams": [sample_team_data],
        "events": [],
    }

    httpx_mock.add_response(
        url="https://fantasy.premierleague.com/api/bootstrap-static/",
        json=response,
    )

    collector = PlayerCollector()
    last_update = datetime.now() - timedelta(days=1)
    changed = await collector.collect_changed_players(last_update)

    # Should get player1 (event_points) and player2 (transfers)
    assert len(changed) == 2
    changed_ids = {p.id for p in changed}
    assert 302 in changed_ids
    assert 400 in changed_ids
    assert 500 not in changed_ids


@pytest.mark.asyncio
async def test_player_collector_top_performers(
    httpx_mock: HTTPXMock, sample_player_data, sample_team_data
):
    """Test collecting top performers by metric."""
    # Add multiple players with different points
    player1 = sample_player_data.copy()
    player1["id"] = 302
    player1["total_points"] = 200

    player2 = sample_player_data.copy()
    player2["id"] = 400
    player2["total_points"] = 180

    player3 = sample_player_data.copy()
    player3["id"] = 500
    player3["total_points"] = 220

    response = {
        "elements": [player1, player2, player3],
        "teams": [sample_team_data],
        "events": [],
    }

    httpx_mock.add_response(
        url="https://fantasy.premierleague.com/api/bootstrap-static/",
        json=response,
    )

    collector = PlayerCollector()
    top_2 = await collector.collect_top_performers(limit=2, metric="total_points")

    assert len(top_2) == 2
    assert top_2[0].total_points == 220  # Player 3
    assert top_2[1].total_points == 200  # Player 1


@pytest.mark.asyncio
async def test_player_collector_top_performers_by_form(
    httpx_mock: HTTPXMock, sample_player_data, sample_team_data
):
    """Test collecting top performers by form (string metric)."""
    player1 = sample_player_data.copy()
    player1["id"] = 302
    player1["form"] = "7.3"

    player2 = sample_player_data.copy()
    player2["id"] = 400
    player2["form"] = "8.5"

    response = {
        "elements": [player1, player2],
        "teams": [sample_team_data],
        "events": [],
    }

    httpx_mock.add_response(
        url="https://fantasy.premierleague.com/api/bootstrap-static/",
        json=response,
    )

    collector = PlayerCollector()
    top_form = await collector.collect_top_performers(limit=1, metric="form")

    assert len(top_form) == 1
    assert top_form[0].id == 400
    assert float(top_form[0].form) == 8.5


# FixtureCollector tests


@pytest.mark.asyncio
async def test_fixture_collector_collect_all(
    httpx_mock: HTTPXMock, sample_fixture_data
):
    """Test collecting all fixtures."""
    httpx_mock.add_response(
        url="https://fantasy.premierleague.com/api/fixtures/",
        json=[sample_fixture_data],
    )

    collector = FixtureCollector()
    fixtures = await collector.collect_all()

    assert len(fixtures) == 1
    assert isinstance(fixtures[0], Fixture)
    assert fixtures[0].id == 1


@pytest.mark.asyncio
async def test_fixture_collector_by_gameweek(
    httpx_mock: HTTPXMock, sample_fixture_data
):
    """Test collecting fixtures by gameweek."""
    httpx_mock.add_response(
        url="https://fantasy.premierleague.com/api/fixtures/?event=1",
        json=[sample_fixture_data],
    )

    collector = FixtureCollector()
    fixtures = await collector.collect_by_gameweek(1)

    assert len(fixtures) == 1
    assert fixtures[0].event == 1


@pytest.mark.asyncio
async def test_fixture_collector_completed(httpx_mock: HTTPXMock, sample_fixture_data):
    """Test collecting completed fixtures."""
    fixture1 = sample_fixture_data.copy()
    fixture1["id"] = 1
    fixture1["finished"] = True

    fixture2 = sample_fixture_data.copy()
    fixture2["id"] = 2
    fixture2["finished"] = False

    httpx_mock.add_response(
        url="https://fantasy.premierleague.com/api/fixtures/",
        json=[fixture1, fixture2],
    )

    collector = FixtureCollector()
    completed = await collector.collect_completed()

    assert len(completed) == 1
    assert completed[0].id == 1
    assert completed[0].finished is True


@pytest.mark.asyncio
async def test_fixture_collector_upcoming(httpx_mock: HTTPXMock, sample_fixture_data):
    """Test collecting upcoming fixtures."""
    fixture1 = sample_fixture_data.copy()
    fixture1["id"] = 1
    fixture1["started"] = False
    fixture1["finished"] = False

    fixture2 = sample_fixture_data.copy()
    fixture2["id"] = 2
    fixture2["started"] = True
    fixture2["finished"] = False

    httpx_mock.add_response(
        url="https://fantasy.premierleague.com/api/fixtures/",
        json=[fixture1, fixture2],
    )

    collector = FixtureCollector()
    upcoming = await collector.collect_upcoming()

    assert len(upcoming) == 1
    assert upcoming[0].id == 1
    assert upcoming[0].started is False


@pytest.mark.asyncio
async def test_fixture_collector_live(httpx_mock: HTTPXMock, sample_fixture_data):
    """Test collecting live fixtures."""
    fixture1 = sample_fixture_data.copy()
    fixture1["id"] = 1
    fixture1["started"] = True
    fixture1["finished"] = False

    fixture2 = sample_fixture_data.copy()
    fixture2["id"] = 2
    fixture2["started"] = False
    fixture2["finished"] = False

    fixture3 = sample_fixture_data.copy()
    fixture3["id"] = 3
    fixture3["started"] = True
    fixture3["finished"] = True

    httpx_mock.add_response(
        url="https://fantasy.premierleague.com/api/fixtures/",
        json=[fixture1, fixture2, fixture3],
    )

    collector = FixtureCollector()
    live = await collector.collect_live()

    assert len(live) == 1
    assert live[0].id == 1
    assert live[0].started is True
    assert live[0].finished is False


@pytest.mark.asyncio
async def test_fixture_collector_by_team(httpx_mock: HTTPXMock, sample_fixture_data):
    """Test collecting fixtures by team."""
    fixture1 = sample_fixture_data.copy()
    fixture1["id"] = 1
    fixture1["team_h"] = 1
    fixture1["team_a"] = 2

    fixture2 = sample_fixture_data.copy()
    fixture2["id"] = 2
    fixture2["team_h"] = 3
    fixture2["team_a"] = 1  # Arsenal away

    fixture3 = sample_fixture_data.copy()
    fixture3["id"] = 3
    fixture3["team_h"] = 4
    fixture3["team_a"] = 5

    httpx_mock.add_response(
        url="https://fantasy.premierleague.com/api/fixtures/",
        json=[fixture1, fixture2, fixture3],
    )

    collector = FixtureCollector()
    arsenal_fixtures = await collector.collect_by_team(1)

    assert len(arsenal_fixtures) == 2
    fixture_ids = {f.id for f in arsenal_fixtures}
    assert 1 in fixture_ids
    assert 2 in fixture_ids


@pytest.mark.asyncio
async def test_fixture_collector_by_difficulty(
    httpx_mock: HTTPXMock, sample_fixture_data
):
    """Test collecting fixtures by difficulty."""
    fixture1 = sample_fixture_data.copy()
    fixture1["id"] = 1
    fixture1["team_h"] = 1
    fixture1["team_h_difficulty"] = 2  # Easy

    fixture2 = sample_fixture_data.copy()
    fixture2["id"] = 2
    fixture2["team_h"] = 2
    fixture2["team_h_difficulty"] = 5  # Hard

    httpx_mock.add_response(
        url="https://fantasy.premierleague.com/api/fixtures/",
        json=[fixture1, fixture2],
    )

    collector = FixtureCollector()
    easy_fixtures = await collector.collect_by_difficulty(
        min_difficulty=1, max_difficulty=2
    )

    assert len(easy_fixtures) == 1
    assert easy_fixtures[0].team_h_difficulty == 2


@pytest.mark.asyncio
async def test_fixture_collector_by_difficulty_for_team(
    httpx_mock: HTTPXMock, sample_fixture_data
):
    """Test collecting fixtures by difficulty for specific team."""
    fixture1 = sample_fixture_data.copy()
    fixture1["id"] = 1
    fixture1["team_h"] = 1  # Arsenal home
    fixture1["team_a"] = 2
    fixture1["team_h_difficulty"] = 2  # Easy for Arsenal

    fixture2 = sample_fixture_data.copy()
    fixture2["id"] = 2
    fixture2["team_h"] = 3
    fixture2["team_a"] = 1  # Arsenal away
    fixture2["team_a_difficulty"] = 5  # Hard for Arsenal

    fixture3 = sample_fixture_data.copy()
    fixture3["id"] = 3
    fixture3["team_h"] = 4
    fixture3["team_a"] = 5
    fixture3["team_h_difficulty"] = 1

    httpx_mock.add_response(
        url="https://fantasy.premierleague.com/api/fixtures/",
        json=[fixture1, fixture2, fixture3],
    )

    collector = FixtureCollector()
    # Get easy fixtures for Arsenal (difficulty <= 3)
    easy_for_arsenal = await collector.collect_by_difficulty(
        min_difficulty=1, max_difficulty=3, team_id=1
    )

    assert len(easy_for_arsenal) == 1
    assert easy_for_arsenal[0].id == 1
