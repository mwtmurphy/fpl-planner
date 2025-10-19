"""Unit tests for helper utilities."""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from fpl.core.models import Player, Team, Gameweek
from fpl.utils.helpers import (
    calculate_expected_points,
    calculate_form_rating,
    calculate_points_per_game,
    calculate_value,
    format_deadline,
    format_deadline_countdown,
    format_price,
    get_current_gameweek,
    get_fixture_difficulty_label,
    get_next_gameweek,
    get_player_status_emoji,
    get_position_name,
    get_team_name,
    get_team_short_name,
    is_budget,
    is_differential,
    is_premium,
)


# Format helpers


def test_format_price():
    """Test price formatting."""
    assert format_price(95) == "£9.5m"
    assert format_price(130) == "£13.0m"
    assert format_price(45) == "£4.5m"
    assert format_price(100) == "£10.0m"


def test_get_position_name():
    """Test position name lookup."""
    assert get_position_name(1) == "GK"
    assert get_position_name(2) == "DEF"
    assert get_position_name(3) == "MID"
    assert get_position_name(4) == "FWD"
    assert get_position_name(99) == "UNKNOWN"


# Gameweek helpers


def test_get_current_gameweek(sample_gameweek_data):
    """Test finding current gameweek."""
    gw1 = Gameweek(**sample_gameweek_data)
    gw1.is_current = True

    gw2_data = sample_gameweek_data.copy()
    gw2_data["id"] = 2
    gw2_data["is_current"] = False
    gw2 = Gameweek(**gw2_data)

    gameweeks = [gw1, gw2]

    current = get_current_gameweek(gameweeks)
    assert current is not None
    assert current.id == 1


def test_get_current_gameweek_none():
    """Test when no current gameweek."""
    assert get_current_gameweek([]) is None


def test_get_next_gameweek(sample_gameweek_data):
    """Test finding next gameweek."""
    gw1_data = sample_gameweek_data.copy()
    gw1_data["is_current"] = True
    gw1_data["is_next"] = False
    gw1 = Gameweek(**gw1_data)

    gw2_data = sample_gameweek_data.copy()
    gw2_data["id"] = 2
    gw2_data["is_current"] = False
    gw2_data["is_next"] = True
    gw2 = Gameweek(**gw2_data)

    gameweeks = [gw1, gw2]

    next_gw = get_next_gameweek(gameweeks)
    assert next_gw is not None
    assert next_gw.id == 2


def test_get_next_gameweek_none():
    """Test when no next gameweek."""
    assert get_next_gameweek([]) is None


# Value calculations


def test_calculate_value():
    """Test points per million calculation."""
    value = calculate_value(Decimal("9.5"), 186)
    assert value == Decimal(186) / Decimal("9.5")

    # Test zero price
    assert calculate_value(Decimal("0"), 100) == Decimal(0)


def test_is_differential():
    """Test differential detection."""
    assert is_differential(3.2) is True
    assert is_differential(4.9) is True
    assert is_differential(5.0) is False
    assert is_differential(10.5) is False

    # Custom threshold
    assert is_differential(7.0, threshold=10.0) is True
    assert is_differential(12.0, threshold=10.0) is False


# Team lookups


def test_get_team_name(sample_team_data):
    """Test team name lookup."""
    team = Team(**sample_team_data)
    teams = [team]

    assert get_team_name(1, teams) == "Arsenal"
    assert get_team_name(99, teams) == "Unknown"


def test_get_team_short_name(sample_team_data):
    """Test team short name lookup."""
    team = Team(**sample_team_data)
    teams = [team]

    assert get_team_short_name(1, teams) == "ARS"
    assert get_team_short_name(99, teams) == "UNK"


# Deadline formatting


def test_format_deadline():
    """Test deadline formatting."""
    deadline = datetime(2024, 8, 17, 11, 0)
    formatted = format_deadline(deadline)
    assert "Aug" in formatted
    assert "11:00" in formatted


def test_format_deadline_countdown_days():
    """Test deadline countdown with days."""
    deadline = datetime.now() + timedelta(days=2, hours=5)
    countdown = format_deadline_countdown(deadline)
    assert "2 days" in countdown
    assert "hour" in countdown


def test_format_deadline_countdown_hours():
    """Test deadline countdown with hours."""
    deadline = datetime.now() + timedelta(hours=5, minutes=30)
    countdown = format_deadline_countdown(deadline)
    assert "5 hours" in countdown
    # Minutes could be 29 or 30 due to timing
    assert "minutes" in countdown


def test_format_deadline_countdown_minutes():
    """Test deadline countdown with minutes."""
    deadline = datetime.now() + timedelta(minutes=45)
    countdown = format_deadline_countdown(deadline)
    # Minutes could be 44 or 45 due to timing
    assert "44 minutes" in countdown or "45 minutes" in countdown


def test_format_deadline_countdown_passed():
    """Test deadline countdown when passed."""
    deadline = datetime.now() - timedelta(hours=1)
    countdown = format_deadline_countdown(deadline)
    assert countdown == "Deadline passed"


# Form rating


def test_calculate_form_rating():
    """Test form rating categorization."""
    assert calculate_form_rating("8.5") == "Excellent"
    assert calculate_form_rating("7.0") == "Excellent"
    assert calculate_form_rating("6.5") == "Good"
    assert calculate_form_rating("5.0") == "Good"
    assert calculate_form_rating("4.0") == "Average"
    assert calculate_form_rating("3.0") == "Average"
    assert calculate_form_rating("2.5") == "Poor"
    assert calculate_form_rating("invalid") == "Unknown"
    assert calculate_form_rating("") == "Unknown"


# Points per game


def test_calculate_points_per_game():
    """Test points per 90 calculation."""
    # 3140 minutes = 34.89 games
    ppg = calculate_points_per_game(186, 3140)
    assert 5.0 < ppg < 6.0  # Should be around 5.33

    # Zero minutes
    assert calculate_points_per_game(100, 0) == 0.0


# Premium/budget checks


def test_is_premium():
    """Test premium player detection."""
    assert is_premium(Decimal("12.5")) is True
    assert is_premium(Decimal("10.0")) is True
    assert is_premium(Decimal("9.5")) is False

    # Custom threshold
    assert is_premium(Decimal("8.5"), threshold=Decimal("8.0")) is True


def test_is_budget():
    """Test budget player detection."""
    assert is_budget(Decimal("4.5")) is True
    assert is_budget(Decimal("5.0")) is True
    assert is_budget(Decimal("5.5")) is False

    # Custom threshold
    assert is_budget(Decimal("6.0"), threshold=Decimal("6.5")) is True


# Fixture difficulty


def test_get_fixture_difficulty_label():
    """Test fixture difficulty labels."""
    assert get_fixture_difficulty_label(1) == "Very Easy"
    assert get_fixture_difficulty_label(2) == "Easy"
    assert get_fixture_difficulty_label(3) == "Medium"
    assert get_fixture_difficulty_label(4) == "Hard"
    assert get_fixture_difficulty_label(5) == "Very Hard"
    assert get_fixture_difficulty_label(99) == "Unknown"


# Expected points


def test_calculate_expected_points_forward():
    """Test expected points calculation for forward."""
    # Forward with 0.8 xG, 0.4 xA, 1.2 xGC
    xP = calculate_expected_points("0.8", "0.4", "1.2", 4)

    # xG * 4 = 3.2
    # xA * 3 = 1.2
    # CS = 0 (forwards don't get CS)
    # Total ≈ 4.4
    assert 4.0 < xP < 5.0


def test_calculate_expected_points_defender():
    """Test expected points calculation for defender."""
    # Defender with 0.1 xG, 0.2 xA, 0.5 xGC
    xP = calculate_expected_points("0.1", "0.2", "0.5", 2)

    # xG * 6 = 0.6
    # xA * 3 = 0.6
    # CS prob = max(0, min(1, 1-0.5)) = 0.5
    # CS * 4 = 2.0
    # Total ≈ 3.2
    assert 2.5 < xP < 4.0


def test_calculate_expected_points_invalid():
    """Test expected points with invalid data."""
    xP = calculate_expected_points("invalid", "0.5", "1.0", 3)
    assert xP == 0.0


# Player status


def test_get_player_status_emoji():
    """Test player status emoji."""
    assert get_player_status_emoji("a") == "✅"
    assert get_player_status_emoji("d") == "❓"
    assert get_player_status_emoji("i") == "🤕"
    assert get_player_status_emoji("u") == "❌"
    assert get_player_status_emoji("s") == "🚫"
    assert get_player_status_emoji("x") == "❔"


# Integration tests


def test_helper_workflow(sample_player_data, sample_team_data):
    """Test complete helper workflow."""
    player = Player(**sample_player_data)
    team = Team(**sample_team_data)

    # Format price
    price_str = format_price(player.now_cost)
    assert price_str == "£9.5m"

    # Get position
    position = get_position_name(player.element_type)
    assert position == "MID"

    # Get team name
    team_name = get_team_name(player.team, [team])
    assert team_name == "Arsenal"

    # Calculate value
    value = calculate_value(player.price, player.total_points)
    assert value > 0

    # Check if premium
    premium = is_premium(player.price)
    assert premium is False  # 9.5m not premium

    # Check form
    form_rating = calculate_form_rating(player.form)
    assert form_rating in ["Excellent", "Good", "Average", "Poor"]

    # Get status emoji
    emoji = get_player_status_emoji(player.status)
    assert emoji == "✅"
