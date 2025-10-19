"""Pytest configuration and fixtures.

This module provides shared fixtures for all tests.
"""

import pandas as pd
import pytest


@pytest.fixture
def sample_player_data() -> dict:
    """Sample player data for testing."""
    return {
        "id": 302,
        "code": 123456,
        "first_name": "Bukayo",
        "second_name": "Saka",
        "web_name": "Saka",
        "team": 1,
        "element_type": 3,
        "now_cost": 95,
        "cost_change_start": 5,
        "cost_change_event": 0,
        "selected_by_percent": "35.2",
        "total_points": 186,
        "event_points": 8,
        "form": "7.3",
        "points_per_game": "6.2",
        "minutes": 3140,
        "goals_scored": 12,
        "assists": 8,
        "clean_sheets": 10,
        "goals_conceded": 28,
        "own_goals": 0,
        "penalties_saved": 0,
        "penalties_missed": 0,
        "yellow_cards": 2,
        "red_cards": 0,
        "saves": 0,
        "bonus": 15,
        "bps": 654,
        "influence": "1215.4",
        "creativity": "1089.6",
        "threat": "1156.0",
        "ict_index": "162.3",
        "expected_goals": "11.2",
        "expected_assists": "7.8",
        "expected_goal_involvements": "19.0",
        "expected_goals_conceded": "28.5",
        "status": "a",
        "news": "",
        "news_added": None,
        "chance_of_playing_this_round": None,
        "chance_of_playing_next_round": None,
        "transfers_in": 2500000,
        "transfers_out": 1800000,
        "transfers_in_event": 50000,
        "transfers_out_event": 30000,
    }


@pytest.fixture
def sample_team_data() -> dict:
    """Sample team data for testing."""
    return {
        "id": 1,
        "name": "Arsenal",
        "short_name": "ARS",
        "code": 3,
        "strength": 5,
        "strength_overall_home": 1200,
        "strength_overall_away": 1180,
        "strength_attack_home": 1220,
        "strength_attack_away": 1200,
        "strength_defence_home": 1180,
        "strength_defence_away": 1160,
        "position": 2,
        "played": 38,
        "win": 26,
        "draw": 6,
        "loss": 6,
        "points": 84,
        "unavailable": False,
    }


@pytest.fixture
def sample_fixture_data() -> dict:
    """Sample fixture data for testing."""
    return {
        "id": 1,
        "code": 12345,
        "event": 1,
        "team_h": 1,
        "team_a": 2,
        "team_h_difficulty": 3,
        "team_a_difficulty": 4,
        "started": True,
        "finished": True,
        "finished_provisional": False,
        "team_h_score": 2,
        "team_a_score": 1,
        "stats": [],
    }


@pytest.fixture
def sample_gameweek_data() -> dict:
    """Sample gameweek data for testing."""
    from datetime import datetime, timedelta

    return {
        "id": 1,
        "name": "Gameweek 1",
        "deadline_time": datetime.now() + timedelta(days=1),
        "is_previous": False,
        "is_current": True,
        "is_next": False,
        "finished": False,
        "data_checked": True,
        "average_entry_score": 45,
        "highest_score": 78,
        "most_selected": 302,
        "most_transferred_in": 302,
        "most_captained": 354,
        "most_vice_captained": 355,
        "top_element": 354,
        "top_element_info": None,
        "transfers_made": 1500000,
        "chip_plays": [],
    }


@pytest.fixture
def sample_player_history_data() -> dict:
    """Sample player history data for testing."""
    from datetime import datetime

    return {
        "element": 302,
        "fixture": 1,
        "opponent_team": 2,
        "total_points": 8,
        "was_home": True,
        "kickoff_time": datetime(2024, 8, 16, 20, 0),
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


@pytest.fixture
async def mock_fpl_client(httpx_mock):
    """Mock FPL client for testing.

    This fixture provides a pre-configured FPLClient with httpx_mock
    for testing without making real API calls.

    Example:
        >>> async def test_something(mock_fpl_client, httpx_mock):
        ...     httpx_mock.add_response(json={"elements": []})
        ...     data = await mock_fpl_client.get_bootstrap_static()
    """
    from fpl.api.client import FPLClient

    async with FPLClient() as client:
        yield client


@pytest.fixture
def bootstrap_static_response(
    sample_player_data, sample_team_data, sample_gameweek_data
) -> dict:
    """Full bootstrap-static response for testing.

    Returns a complete bootstrap-static API response with players,
    teams, and gameweeks.
    """
    return {
        "elements": [sample_player_data],
        "teams": [sample_team_data],
        "events": [sample_gameweek_data],
        "element_types": [
            {"id": 1, "singular_name": "Goalkeeper", "plural_name": "Goalkeepers"},
            {"id": 2, "singular_name": "Defender", "plural_name": "Defenders"},
            {"id": 3, "singular_name": "Midfielder", "plural_name": "Midfielders"},
            {"id": 4, "singular_name": "Forward", "plural_name": "Forwards"},
        ],
    }


# Async test helpers


async def async_return(value):
    """Helper to create an async function that returns a value.

    Useful for mocking async methods in tests.

    Example:
        >>> mock_client.get_bootstrap_static = lambda: async_return({"elements": []})
    """
    return value


class AsyncContextManagerMock:
    """Mock async context manager for testing.

    Useful for mocking async with statements in tests.

    Example:
        >>> mock = AsyncContextManagerMock(return_value=mock_client)
        >>> FPLClient = lambda: mock
    """

    def __init__(self, return_value):
        """Initialize with return value."""
        self.return_value = return_value

    async def __aenter__(self):
        """Enter context."""
        return self.return_value

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit context."""
        pass


# Streamlit-specific fixtures


@pytest.fixture
def sample_dataframe():
    """Provide sample DataFrame for Streamlit testing."""
    return pd.DataFrame(
        {
            "name": ["Salah", "Haaland", "Saka"],
            "team_name": ["Liverpool", "Man City", "Arsenal"],
            "team_id": [10, 11, 1],
            "position": ["MID", "FWD", "MID"],
            "price": [13.0, 15.0, 9.5],
            "price_formatted": ["£13.0m", "£15.0m", "£9.5m"],
            "total_points": [186, 210, 150],
            "form_fixtures": [8.5, 10.2, 7.3],
            "value_fixtures": [14.3, 14.0, 15.8],
            "form_games": [8.5, 10.2, 7.3],
            "value_games": [49.0, 51.5, 46.8],
            "form": [8.5, 10.2, 7.3],
            "form_rating": ["Hot", "Hot", "Good"],
            "value": [14.3, 14.0, 15.8],
            "ownership": [45.2, 62.8, 35.1],
            "status": ["a", "a", "a"],
            "status_emoji": ["✅", "✅", "✅"],
            "status_circle": ["🟢", "🟢", "🟢"],
            "minutes": [2340, 2520, 2100],
        }
    )


@pytest.fixture
def sample_teams_dict():
    """Provide sample teams dictionary for testing."""
    return {
        1: "Arsenal",
        2: "Aston Villa",
        3: "Bournemouth",
        4: "Brentford",
        5: "Brighton",
        10: "Liverpool",
        11: "Man City",
        12: "Man Utd",
    }


@pytest.fixture(autouse=True)
def reset_streamlit_cache():
    """Reset Streamlit cache between tests.

    This fixture automatically runs before each test to ensure
    clean state and prevent cache pollution between tests.
    """
    try:
        import streamlit as st

        # Clear all caches
        st.cache_data.clear()
        st.cache_resource.clear()
    except ImportError:
        # Streamlit not available in this test
        pass
    yield


@pytest.fixture(autouse=True)
def reset_session_state():
    """Reset Streamlit session state between tests.

    This fixture automatically runs before each test to ensure
    clean session state.
    """
    try:
        import streamlit as st

        if hasattr(st, "session_state"):
            # Clear session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
    except ImportError:
        # Streamlit not available in this test
        pass
    yield


@pytest.fixture
def mock_load_all_data(sample_dataframe, sample_teams_dict):
    """Mock load_all_data function for testing.

    Returns a function that can be used to patch load_all_data
    in Streamlit app tests.

    Example:
        >>> def test_something(mock_load_all_data, mocker):
        ...     mocker.patch('app.utils.data_loader.load_all_data', mock_load_all_data)
    """

    def _load_all_data():
        return sample_dataframe, sample_teams_dict, "2025-10-18 12:00"

    return _load_all_data


@pytest.fixture
def mock_empty_data():
    """Mock empty data for testing edge cases.

    Returns empty DataFrame and teams dict for testing
    how app handles no data scenarios.
    """

    def _load_empty_data():
        return pd.DataFrame(), {}, "2025-10-18 12:00"

    return _load_empty_data
