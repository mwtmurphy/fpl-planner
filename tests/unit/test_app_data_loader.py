"""Tests for Streamlit app data loader."""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pandas as pd
import pytest

from app.utils.data_loader import load_all_data


@pytest.fixture
def mock_player_data():
    """Mock player data from API."""
    return {
        "id": 1,
        "code": 12345,
        "first_name": "Mohamed",
        "second_name": "Salah",
        "web_name": "Salah",
        "team": 10,
        "element_type": 3,
        "now_cost": 130,
        "cost_change_start": 5,
        "cost_change_event": 0,
        "selected_by_percent": "45.2",
        "total_points": 186,
        "event_points": 12,
        "form": "8.5",
        "points_per_game": "7.2",
        "minutes": 2340,
        "goals_scored": 15,
        "assists": 10,
        "clean_sheets": 8,
        "goals_conceded": 25,
        "own_goals": 0,
        "penalties_saved": 0,
        "penalties_missed": 0,
        "yellow_cards": 2,
        "red_cards": 0,
        "saves": 0,
        "bonus": 15,
        "bps": 550,
        "influence": "850.5",
        "creativity": "720.2",
        "threat": "1200.5",
        "ict_index": "270.1",
        "expected_goals": "12.5",
        "expected_assists": "8.2",
        "expected_goal_involvements": "20.7",
        "expected_goals_conceded": "28.5",
        "status": "a",
        "news": "",
        "news_added": None,
        "chance_of_playing_this_round": None,
        "chance_of_playing_next_round": None,
        "transfers_in": 150000,
        "transfers_out": 80000,
        "transfers_in_event": 5000,
        "transfers_out_event": 2000,
    }


@pytest.fixture
def mock_team_data():
    """Mock team data from API."""
    return {
        "id": 10,
        "name": "Liverpool",
        "short_name": "LIV",
        "code": 14,
        "strength": 5,
        "strength_overall_home": 1320,
        "strength_overall_away": 1300,
        "strength_attack_home": 1350,
        "strength_attack_away": 1330,
        "strength_defence_home": 1290,
        "strength_defence_away": 1270,
        "position": 1,
        "played": 26,
        "win": 18,
        "draw": 5,
        "loss": 3,
        "points": 59,
        "unavailable": False,
    }


@pytest.fixture
def mock_bootstrap_data(mock_player_data, mock_team_data):
    """Mock bootstrap-static API response."""
    return {"elements": [mock_player_data], "teams": [mock_team_data]}


class TestLoadAllData:
    """Test suite for load_all_data function."""

    @patch("app.utils.data_loader.PlayerCollector")
    @patch("app.utils.data_loader.FPLClient")
    def test_load_all_data_success(
        self,
        mock_client_class,
        mock_collector_class,
        mock_bootstrap_data,
        mock_player_data,
    ):
        """Test successful data loading."""
        # Setup mock collector
        mock_collector = AsyncMock()
        from fpl.core.models import Player

        mock_player = Player(**mock_player_data)
        mock_collector.collect_all.return_value = [mock_player]
        mock_collector_class.return_value = mock_collector

        # Setup mock client
        mock_client = AsyncMock()
        mock_client.get_bootstrap_static.return_value = mock_bootstrap_data
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = AsyncMock()
        mock_client_class.return_value = mock_client

        # Call function (force API path to use mocks)
        df, teams_dict, last_update = load_all_data(use_local_data=False)

        # Assertions
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert isinstance(teams_dict, dict)
        assert 10 in teams_dict
        assert teams_dict[10] == "Liverpool"
        assert isinstance(last_update, str)

        # Verify DataFrame columns
        expected_columns = [
            "name",
            "team_name",
            "team_id",
            "position",
            "form",
            "form_rating",
            "total_points",
            "price",
            "price_formatted",
            "value",
            "ownership",
            "status",
            "status_emoji",
            "minutes",
        ]
        for col in expected_columns:
            assert col in df.columns

    @patch("app.utils.data_loader.PlayerCollector")
    @patch("app.utils.data_loader.FPLClient")
    def test_load_all_data_player_transformation(
        self,
        mock_client_class,
        mock_collector_class,
        mock_bootstrap_data,
        mock_player_data,
    ):
        """Test player data is correctly transformed to DataFrame."""
        # Setup mocks
        mock_collector = AsyncMock()
        from fpl.core.models import Player

        mock_player = Player(**mock_player_data)
        mock_collector.collect_all.return_value = [mock_player]
        mock_collector_class.return_value = mock_collector

        mock_client = AsyncMock()
        mock_client.get_bootstrap_static.return_value = mock_bootstrap_data
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = AsyncMock()
        mock_client_class.return_value = mock_client

        # Call function (force API path to use mocks)
        df, teams_dict, last_update = load_all_data(use_local_data=False)

        # Check transformed data
        row = df.iloc[0]
        assert row["name"] == "Salah"
        assert row["team_name"] == "Liverpool"
        assert row["team_id"] == 10
        assert row["position"] == "MID"
        assert row["form"] == 8.5
        assert row["form_rating"] == "Excellent"  # form >= 7.0
        assert row["total_points"] == 186
        assert row["price"] == 13.0  # 130 / 10
        assert row["price_formatted"] == "£13.0m"
        assert row["ownership"] == 45.2
        assert row["status"] == "a"
        assert row["status_emoji"] == "✅"
        assert row["minutes"] == 2340

    @patch("app.utils.data_loader.PlayerCollector")
    @patch("app.utils.data_loader.FPLClient")
    def test_load_all_data_multiple_players(
        self, mock_client_class, mock_collector_class, mock_bootstrap_data
    ):
        """Test loading multiple players."""
        # Create multiple players
        from fpl.core.models import Player

        player1_data = mock_bootstrap_data["elements"][0].copy()
        player1_data["id"] = 1
        player1_data["web_name"] = "Salah"

        player2_data = player1_data.copy()
        player2_data["id"] = 2
        player2_data["web_name"] = "Haaland"
        player2_data["element_type"] = 4
        player2_data["form"] = "6.2"

        players = [Player(**player1_data), Player(**player2_data)]

        # Setup mocks
        mock_collector = AsyncMock()
        mock_collector.collect_all.return_value = players
        mock_collector_class.return_value = mock_collector

        mock_client = AsyncMock()
        mock_client.get_bootstrap_static.return_value = mock_bootstrap_data
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = AsyncMock()
        mock_client_class.return_value = mock_client

        # Call function (force API path to use mocks)
        df, teams_dict, last_update = load_all_data(use_local_data=False)

        # Verify
        assert len(df) == 2
        assert df.iloc[0]["name"] == "Salah"
        assert df.iloc[1]["name"] == "Haaland"
        assert df.iloc[0]["position"] == "MID"
        assert df.iloc[1]["position"] == "FWD"
        assert df.iloc[0]["form_rating"] == "Excellent"  # 8.5 is >= 7.0
        assert df.iloc[1]["form_rating"] == "Good"  # 6.2 is >= 5.0 and < 7.0

    @patch("app.utils.data_loader.PlayerCollector")
    @patch("app.utils.data_loader.FPLClient")
    def test_load_all_data_value_calculation(
        self,
        mock_client_class,
        mock_collector_class,
        mock_bootstrap_data,
        mock_player_data,
    ):
        """Test value calculation in loaded data."""
        # Setup mocks
        mock_collector = AsyncMock()
        from fpl.core.models import Player

        mock_player = Player(**mock_player_data)
        mock_collector.collect_all.return_value = [mock_player]
        mock_collector_class.return_value = mock_collector

        mock_client = AsyncMock()
        mock_client.get_bootstrap_static.return_value = mock_bootstrap_data
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = AsyncMock()
        mock_client_class.return_value = mock_client

        # Call function (force API path to use mocks)
        df, teams_dict, last_update = load_all_data(use_local_data=False)

        # Check value calculation (total_points / price)
        row = df.iloc[0]
        expected_value = 186 / 13.0  # total_points / price
        assert abs(row["value"] - expected_value) < 0.01

    @patch("app.utils.data_loader.PlayerCollector")
    @patch("app.utils.data_loader.FPLClient")
    def test_load_all_data_timestamp_format(
        self,
        mock_client_class,
        mock_collector_class,
        mock_bootstrap_data,
        mock_player_data,
    ):
        """Test last_update timestamp format."""
        # Setup mocks
        mock_collector = AsyncMock()
        from fpl.core.models import Player

        mock_player = Player(**mock_player_data)
        mock_collector.collect_all.return_value = [mock_player]
        mock_collector_class.return_value = mock_collector

        mock_client = AsyncMock()
        mock_client.get_bootstrap_static.return_value = mock_bootstrap_data
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = AsyncMock()
        mock_client_class.return_value = mock_client

        # Call function (force API path to use mocks)
        df, teams_dict, last_update = load_all_data(use_local_data=False)

        # Verify timestamp format (YYYY-MM-DD HH:MM)
        try:
            datetime.strptime(last_update, "%Y-%m-%d %H:%M")
            timestamp_valid = True
        except ValueError:
            timestamp_valid = False

        assert timestamp_valid

    @patch("app.utils.data_loader.PlayerCollector")
    @patch("app.utils.data_loader.FPLClient")
    def test_load_all_data_teams_dict(
        self,
        mock_client_class,
        mock_collector_class,
        mock_bootstrap_data,
        mock_player_data,
    ):
        """Test teams dictionary creation."""
        # Add more teams to mock data
        team2 = mock_bootstrap_data["teams"][0].copy()
        team2["id"] = 1
        team2["name"] = "Arsenal"
        mock_bootstrap_data["teams"].append(team2)

        # Setup mocks
        mock_collector = AsyncMock()
        from fpl.core.models import Player

        mock_player = Player(**mock_player_data)
        mock_collector.collect_all.return_value = [mock_player]
        mock_collector_class.return_value = mock_collector

        mock_client = AsyncMock()
        mock_client.get_bootstrap_static.return_value = mock_bootstrap_data
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = AsyncMock()
        mock_client_class.return_value = mock_client

        # Call function (force API path to use mocks)
        df, teams_dict, last_update = load_all_data(use_local_data=False)

        # Verify teams dict
        assert len(teams_dict) == 2
        assert teams_dict[10] == "Liverpool"
        assert teams_dict[1] == "Arsenal"
