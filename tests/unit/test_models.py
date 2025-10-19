"""Unit tests for core models."""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from fpl.core.models import Fixture, Gameweek, Player, PlayerHistory, Team


def test_player_creation(sample_player_data):
    """Test Player model creation."""
    player = Player(**sample_player_data)

    assert player.id == 302
    assert player.web_name == "Saka"
    assert player.element_type == 3
    assert player.now_cost == 95


def test_player_price_property(sample_player_data):
    """Test Player.price property."""
    player = Player(**sample_player_data)

    assert player.price == Decimal("9.5")


def test_player_position_name(sample_player_data):
    """Test Player.position_name property."""
    player = Player(**sample_player_data)

    assert player.position_name == "MID"


def test_player_invalid_position():
    """Test Player validation rejects invalid position."""
    invalid_data = {
        "id": 1,
        "code": 123,
        "first_name": "Test",
        "second_name": "Player",
        "web_name": "Test",
        "team": 1,
        "element_type": 5,  # Invalid
        "now_cost": 50,
        "total_points": 0,
        "form": "0.0",
    }

    with pytest.raises(ValueError, match="Position must be"):
        Player(**invalid_data)


def test_team_creation(sample_team_data):
    """Test Team model creation."""
    team = Team(**sample_team_data)

    assert team.id == 1
    assert team.name == "Arsenal"
    assert team.short_name == "ARS"


def test_fixture_creation(sample_fixture_data):
    """Test Fixture model creation."""
    fixture = Fixture(**sample_fixture_data)

    assert fixture.id == 1
    assert fixture.team_h == 1
    assert fixture.team_a == 2
    assert fixture.finished is True


def test_fixture_is_completed(sample_fixture_data):
    """Test Fixture.is_completed method."""
    fixture = Fixture(**sample_fixture_data)

    assert fixture.is_completed() is True


def test_player_ownership_percent(sample_player_data):
    """Test Player.ownership_percent property."""
    player = Player(**sample_player_data)

    assert player.ownership_percent == 35.2


def test_player_is_available(sample_player_data):
    """Test Player.is_available method."""
    player = Player(**sample_player_data)

    assert player.is_available() is True

    # Test injured player
    sample_player_data["status"] = "i"
    injured_player = Player(**sample_player_data)
    assert injured_player.is_available() is False


def test_player_is_injured(sample_player_data):
    """Test Player.is_injured method."""
    player = Player(**sample_player_data)

    assert player.is_injured() is False

    # Test doubtful player
    sample_player_data["status"] = "d"
    doubtful_player = Player(**sample_player_data)
    assert doubtful_player.is_injured() is True

    # Test injured player
    sample_player_data["status"] = "i"
    injured_player = Player(**sample_player_data)
    assert injured_player.is_injured() is True


def test_player_all_statistics(sample_player_data):
    """Test Player has all statistics fields."""
    player = Player(**sample_player_data)

    assert player.minutes == 3140
    assert player.goals_scored == 12
    assert player.assists == 8
    assert player.clean_sheets == 10
    assert player.bonus == 15
    assert player.bps == 654


def test_player_advanced_metrics(sample_player_data):
    """Test Player has all advanced metrics."""
    player = Player(**sample_player_data)

    assert player.influence == "1215.4"
    assert player.creativity == "1089.6"
    assert player.threat == "1156.0"
    assert player.ict_index == "162.3"


def test_player_expected_stats(sample_player_data):
    """Test Player has expected stats (xG, xA)."""
    player = Player(**sample_player_data)

    assert player.expected_goals == "11.2"
    assert player.expected_assists == "7.8"
    assert player.expected_goal_involvements == "19.0"


# Team Model Tests


def test_team_strength_ratings(sample_team_data):
    """Test Team has all strength ratings."""
    team = Team(**sample_team_data)

    assert team.strength == 5
    assert team.strength_overall_home == 1200
    assert team.strength_overall_away == 1180
    assert team.strength_attack_home == 1220
    assert team.strength_defence_home == 1180


def test_team_performance_stats(sample_team_data):
    """Test Team has performance statistics."""
    team = Team(**sample_team_data)

    assert team.position == 2
    assert team.played == 38
    assert team.win == 26
    assert team.draw == 6
    assert team.loss == 6
    assert team.points == 84


def test_team_form_guide(sample_team_data):
    """Test Team.form_guide property."""
    team = Team(**sample_team_data)

    assert "68.4" in team.form_guide
    assert "wins" in team.form_guide


def test_team_form_guide_no_matches():
    """Test Team.form_guide with no matches played."""
    team_data = {
        "id": 1,
        "name": "Test Team",
        "short_name": "TST",
        "code": 999,
        "strength": 3,
        "strength_overall_home": 1000,
        "strength_overall_away": 1000,
        "strength_attack_home": 1000,
        "strength_attack_away": 1000,
        "strength_defence_home": 1000,
        "strength_defence_away": 1000,
        "position": 10,
        "played": 0,
        "win": 0,
        "draw": 0,
        "loss": 0,
        "points": 0,
    }
    team = Team(**team_data)

    assert team.form_guide == "No matches"


def test_team_id_validation():
    """Test Team ID must be between 1 and 20."""
    invalid_data = {
        "id": 21,  # Invalid
        "name": "Test",
        "short_name": "TST",
        "code": 999,
        "strength": 3,
        "strength_overall_home": 1000,
        "strength_overall_away": 1000,
        "strength_attack_home": 1000,
        "strength_attack_away": 1000,
        "strength_defence_home": 1000,
        "strength_defence_away": 1000,
        "position": 10,
        "played": 0,
        "win": 0,
        "draw": 0,
        "loss": 0,
        "points": 0,
    }

    with pytest.raises(ValueError):
        Team(**invalid_data)


# Gameweek Model Tests


def test_gameweek_creation(sample_gameweek_data):
    """Test Gameweek model creation."""
    gameweek = Gameweek(**sample_gameweek_data)

    assert gameweek.id == 1
    assert gameweek.name == "Gameweek 1"
    assert gameweek.is_current is True
    assert gameweek.finished is False


def test_gameweek_is_active(sample_gameweek_data):
    """Test Gameweek.is_active method."""
    gameweek = Gameweek(**sample_gameweek_data)

    assert gameweek.is_active() is True

    # Test finished gameweek
    sample_gameweek_data["finished"] = True
    finished_gw = Gameweek(**sample_gameweek_data)
    assert finished_gw.is_active() is False


def test_gameweek_is_upcoming(sample_gameweek_data):
    """Test Gameweek.is_upcoming method."""
    sample_gameweek_data["is_previous"] = False
    sample_gameweek_data["is_current"] = False
    sample_gameweek_data["is_next"] = True
    sample_gameweek_data["finished"] = False

    gameweek = Gameweek(**sample_gameweek_data)

    assert gameweek.is_upcoming() is True


def test_gameweek_deadline_passed(sample_gameweek_data):
    """Test Gameweek.deadline_passed method."""
    # Future deadline
    sample_gameweek_data["deadline_time"] = datetime.now() + timedelta(days=1)
    future_gw = Gameweek(**sample_gameweek_data)
    assert future_gw.deadline_passed() is False

    # Past deadline
    sample_gameweek_data["deadline_time"] = datetime.now() - timedelta(days=1)
    past_gw = Gameweek(**sample_gameweek_data)
    assert past_gw.deadline_passed() is True


def test_gameweek_statistics(sample_gameweek_data):
    """Test Gameweek has all statistics."""
    gameweek = Gameweek(**sample_gameweek_data)

    assert gameweek.average_entry_score == 45
    assert gameweek.highest_score == 78
    assert gameweek.most_captained == 354
    assert gameweek.transfers_made == 1500000


# Fixture Model Tests


def test_fixture_score_methods(sample_fixture_data):
    """Test Fixture score check methods."""
    fixture = Fixture(**sample_fixture_data)

    assert fixture.home_win() is True
    assert fixture.away_win() is False
    assert fixture.draw() is False


def test_fixture_draw(sample_fixture_data):
    """Test Fixture draw detection."""
    sample_fixture_data["team_h_score"] = 1
    sample_fixture_data["team_a_score"] = 1

    fixture = Fixture(**sample_fixture_data)

    assert fixture.draw() is True
    assert fixture.home_win() is False
    assert fixture.away_win() is False


def test_fixture_is_live():
    """Test Fixture.is_live method."""
    live_fixture_data = {
        "id": 1,
        "code": 12345,
        "team_h": 1,
        "team_a": 2,
        "team_h_difficulty": 3,
        "team_a_difficulty": 4,
        "started": True,
        "finished": False,
    }

    fixture = Fixture(**live_fixture_data)

    assert fixture.is_live() is True
    assert fixture.is_completed() is False


def test_fixture_unfinished_scores():
    """Test Fixture methods return False when scores are None."""
    unfinished_data = {
        "id": 1,
        "code": 12345,
        "team_h": 1,
        "team_a": 2,
        "team_h_difficulty": 3,
        "team_a_difficulty": 4,
        "finished": False,
        "team_h_score": None,
        "team_a_score": None,
    }

    fixture = Fixture(**unfinished_data)

    assert fixture.home_win() is False
    assert fixture.away_win() is False
    assert fixture.draw() is False


# PlayerHistory Model Tests


def test_player_history_creation(sample_player_history_data):
    """Test PlayerHistory model creation."""
    history = PlayerHistory(**sample_player_history_data)

    assert history.element == 302
    assert history.fixture == 1
    assert history.total_points == 8
    assert history.was_home is True


def test_player_history_statistics(sample_player_history_data):
    """Test PlayerHistory has all statistics."""
    history = PlayerHistory(**sample_player_history_data)

    assert history.minutes == 90
    assert history.goals_scored == 1
    assert history.assists == 0
    assert history.bonus == 2
    assert history.bps == 32


def test_player_history_ict_metrics(sample_player_history_data):
    """Test PlayerHistory has ICT metrics."""
    history = PlayerHistory(**sample_player_history_data)

    assert history.influence == "65.2"
    assert history.creativity == "42.8"
    assert history.threat == "58.0"
    assert history.ict_index == "16.6"


def test_player_history_context(sample_player_history_data):
    """Test PlayerHistory has context fields."""
    history = PlayerHistory(**sample_player_history_data)

    assert history.value == 95
    assert history.selected == 3500000
    assert history.round == 1


# Edge Case Tests for Negative Values


def test_player_negative_bps(sample_player_data):
    """Test Player accepts negative BPS values.

    BPS can be negative when a player has a very poor performance
    (red card, own goals, missed penalties, etc.).
    """
    sample_player_data["bps"] = -5
    player = Player(**sample_player_data)

    assert player.bps == -5


def test_player_negative_total_points(sample_player_data):
    """Test Player accepts negative total points.

    Total points can be negative early in season if first games
    result in negative points (red cards, own goals, etc.).
    """
    sample_player_data["total_points"] = -3
    player = Player(**sample_player_data)

    assert player.total_points == -3


def test_player_negative_event_points(sample_player_data):
    """Test Player accepts negative event points.

    Event points can definitely be negative in a single gameweek
    (e.g., red card = -3, own goal = -2, etc.).
    """
    sample_player_data["event_points"] = -5
    player = Player(**sample_player_data)

    assert player.event_points == -5


def test_player_history_negative_total_points(sample_player_history_data):
    """Test PlayerHistory accepts negative total points for a gameweek.

    A player can score negative points in a single gameweek.
    """
    sample_player_history_data["total_points"] = -3
    history = PlayerHistory(**sample_player_history_data)

    assert history.total_points == -3


def test_player_history_negative_bps(sample_player_history_data):
    """Test PlayerHistory accepts negative BPS for a gameweek."""
    sample_player_history_data["bps"] = -10
    history = PlayerHistory(**sample_player_history_data)

    assert history.bps == -10


def test_player_extreme_negative_points():
    """Test Player with extremely negative values (worst case scenario)."""
    extreme_data = {
        "id": 1,
        "code": 123,
        "first_name": "Test",
        "second_name": "Player",
        "web_name": "Test",
        "team": 1,
        "element_type": 2,
        "now_cost": 40,
        "cost_change_start": 0,
        "cost_change_event": 0,
        "selected_by_percent": "0.1",
        "total_points": -10,  # Very bad start to season
        "event_points": -5,  # Red card + own goal
        "form": "-2.0",
        "points_per_game": "-1.0",
        "minutes": 90,
        "goals_scored": 0,
        "assists": 0,
        "clean_sheets": 0,
        "goals_conceded": 3,
        "own_goals": 1,
        "penalties_saved": 0,
        "penalties_missed": 0,
        "yellow_cards": 0,
        "red_cards": 1,
        "saves": 0,
        "bonus": 0,
        "bps": -15,  # Negative BPS from poor performance
        "influence": "10.0",
        "creativity": "5.0",
        "threat": "2.0",
        "ict_index": "1.7",
        "expected_goals": "0.0",
        "expected_assists": "0.0",
        "expected_goal_involvements": "0.0",
        "expected_goals_conceded": "3.0",
        "status": "a",
        "news": "",
        "transfers_in": 0,
        "transfers_out": 100,
        "transfers_in_event": 0,
        "transfers_out_event": 50,
    }

    # Should not raise validation error
    player = Player(**extreme_data)
    assert player.total_points == -10
    assert player.event_points == -5
    assert player.bps == -15
