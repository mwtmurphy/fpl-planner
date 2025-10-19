"""Helper utilities for FPL data."""

from datetime import datetime
from decimal import Decimal
from typing import Optional, Any

from fpl.core.models import Player, Team, Gameweek, Fixture


def format_price(now_cost: int) -> str:
    """Format player price from API format to display format.

    Args:
        now_cost: Price in 0.1m units (e.g., 95)

    Returns:
        Formatted price string (e.g., "£9.5m")

    Example:
        >>> format_price(95)
        '£9.5m'
    """
    price = now_cost / 10
    return f"£{price:.1f}m"


def get_position_name(element_type: int) -> str:
    """Get position name from element_type.

    Args:
        element_type: Position code (1=GK, 2=DEF, 3=MID, 4=FWD)

    Returns:
        Position name

    Example:
        >>> get_position_name(3)
        'MID'
    """
    positions = {
        1: "GK",
        2: "DEF",
        3: "MID",
        4: "FWD",
    }
    return positions.get(element_type, "UNKNOWN")


def get_current_gameweek(gameweeks: list[Gameweek]) -> Optional[Gameweek]:
    """Find current active gameweek.

    Args:
        gameweeks: List of Gameweek objects

    Returns:
        Current gameweek or None if not found

    Example:
        >>> current = get_current_gameweek(gameweeks)
        >>> if current:
        ...     print(f"Gameweek {current.id}: {current.name}")
    """
    for gw in gameweeks:
        if gw.is_current:
            return gw
    return None


def get_next_gameweek(gameweeks: list[Gameweek]) -> Optional[Gameweek]:
    """Find next upcoming gameweek.

    Args:
        gameweeks: List of Gameweek objects

    Returns:
        Next gameweek or None if not found

    Example:
        >>> next_gw = get_next_gameweek(gameweeks)
        >>> if next_gw:
        ...     print(f"Next: {next_gw.name} (deadline: {next_gw.deadline_time})")
    """
    for gw in gameweeks:
        if gw.is_next:
            return gw
    return None


def calculate_value(price: Decimal, points: int) -> Decimal:
    """Calculate points per million.

    Args:
        price: Player price in £m
        points: Total points

    Returns:
        Points per million spent

    Example:
        >>> value = calculate_value(Decimal("9.5"), 186)
        >>> print(f"{value:.2f} points per £m")
    """
    if price == 0:
        return Decimal(0)
    return Decimal(points) / price


def is_differential(ownership_pct: float, threshold: float = 5.0) -> bool:
    """Check if player is a differential (low ownership).

    Args:
        ownership_pct: Ownership percentage
        threshold: Maximum ownership % to be considered differential (default: 5%)

    Returns:
        True if player is a differential

    Example:
        >>> if is_differential(3.2):
        ...     print("This is a differential pick!")
    """
    return ownership_pct < threshold


def get_team_name(team_id: int, teams: list[Team]) -> str:
    """Lookup team name by ID.

    Args:
        team_id: Team ID (1-20)
        teams: List of Team objects

    Returns:
        Team name or "Unknown" if not found

    Example:
        >>> name = get_team_name(1, teams)
        >>> print(name)  # "Arsenal"
    """
    for team in teams:
        if team.id == team_id:
            return team.name
    return "Unknown"


def get_team_short_name(team_id: int, teams: list[Team]) -> str:
    """Lookup team short name by ID.

    Args:
        team_id: Team ID (1-20)
        teams: List of Team objects

    Returns:
        Team short name or "UNK" if not found

    Example:
        >>> short = get_team_short_name(1, teams)
        >>> print(short)  # "ARS"
    """
    for team in teams:
        if team.id == team_id:
            return team.short_name
    return "UNK"


def format_deadline(deadline: datetime) -> str:
    """Format deadline in human-readable form.

    Args:
        deadline: Deadline datetime

    Returns:
        Formatted deadline string

    Example:
        >>> formatted = format_deadline(deadline)
        >>> print(formatted)  # "Sat 17 Aug, 11:00"
    """
    return deadline.strftime("%a %d %b, %H:%M")


def format_deadline_countdown(deadline: datetime) -> str:
    """Format deadline as countdown from now.

    Args:
        deadline: Deadline datetime

    Returns:
        Countdown string

    Example:
        >>> countdown = format_deadline_countdown(deadline)
        >>> print(countdown)  # "2 days, 5 hours"
    """
    now = datetime.now()

    if deadline < now:
        return "Deadline passed"

    delta = deadline - now
    days = delta.days
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60

    if days > 0:
        return f"{days} day{'s' if days != 1 else ''}, {hours} hour{'s' if hours != 1 else ''}"
    elif hours > 0:
        return f"{hours} hour{'s' if hours != 1 else ''}, {minutes} minute{'s' if minutes != 1 else ''}"
    else:
        return f"{minutes} minute{'s' if minutes != 1 else ''}"


def calculate_form_rating(form: str) -> str:
    """Categorize form as Excellent/Good/Average/Poor.

    Args:
        form: Form string from API

    Returns:
        Form rating category

    Example:
        >>> rating = calculate_form_rating("8.5")
        >>> print(rating)  # "Excellent"
    """
    try:
        form_value = float(form)
    except (ValueError, TypeError):
        return "Unknown"

    if form_value >= 7.0:
        return "Excellent"
    elif form_value >= 5.0:
        return "Good"
    elif form_value >= 3.0:
        return "Average"
    else:
        return "Poor"


def calculate_points_per_game(total_points: int, minutes: int) -> float:
    """Calculate points per 90 minutes played.

    Args:
        total_points: Total points scored
        minutes: Total minutes played

    Returns:
        Points per 90 minutes

    Example:
        >>> ppg = calculate_points_per_game(186, 3140)
        >>> print(f"{ppg:.2f} points per 90")
    """
    if minutes == 0:
        return 0.0

    games_played = minutes / 90
    return total_points / games_played if games_played > 0 else 0.0


def is_premium(price: Decimal, threshold: Decimal = Decimal("10.0")) -> bool:
    """Check if player is premium priced.

    Args:
        price: Player price in £m
        threshold: Price threshold for premium (default: £10.0m)

    Returns:
        True if player is premium

    Example:
        >>> if is_premium(Decimal("12.5")):
        ...     print("This is a premium player!")
    """
    return price >= threshold


def is_budget(price: Decimal, threshold: Decimal = Decimal("5.0")) -> bool:
    """Check if player is budget priced.

    Args:
        price: Player price in £m
        threshold: Price threshold for budget (default: £5.0m)

    Returns:
        True if player is budget

    Example:
        >>> if is_budget(Decimal("4.5")):
        ...     print("This is a budget player!")
    """
    return price <= threshold


def get_fixture_difficulty_label(difficulty: int) -> str:
    """Get human-readable difficulty label.

    Args:
        difficulty: Difficulty rating (1-5)

    Returns:
        Difficulty label

    Example:
        >>> label = get_fixture_difficulty_label(5)
        >>> print(label)  # "Very Hard"
    """
    labels = {
        1: "Very Easy",
        2: "Easy",
        3: "Medium",
        4: "Hard",
        5: "Very Hard",
    }
    return labels.get(difficulty, "Unknown")


def calculate_expected_points(
    expected_goals: str,
    expected_assists: str,
    expected_goals_conceded: str,
    position: int,
) -> float:
    """Calculate basic expected points from xG, xA, xGC.

    Simple calculation:
    - xG * 4-6 points (depending on position)
    - xA * 3 points
    - Clean sheet probability * 1-4 points (depending on position)

    Args:
        expected_goals: Expected goals string
        expected_assists: Expected assists string
        expected_goals_conceded: Expected goals conceded string
        position: Player position (1=GK, 2=DEF, 3=MID, 4=FWD)

    Returns:
        Estimated expected points

    Example:
        >>> xP = calculate_expected_points("0.8", "0.4", "1.2", 4)
        >>> print(f"Expected: {xP:.1f} points")
    """
    try:
        xg = float(expected_goals)
        xa = float(expected_assists)
        xgc = float(expected_goals_conceded)
    except (ValueError, TypeError):
        return 0.0

    # Goal points by position
    goal_points = {1: 6, 2: 6, 3: 5, 4: 4}
    # Clean sheet points by position
    cs_points = {1: 4, 2: 4, 3: 1, 4: 0}

    # Expected goal points
    ep_goals = xg * goal_points.get(position, 4)

    # Expected assist points
    ep_assists = xa * 3

    # Clean sheet probability (simple: 1 - xGC capped at 0-1)
    cs_prob = max(0, min(1, 1 - xgc))
    ep_cs = cs_prob * cs_points.get(position, 0)

    return ep_goals + ep_assists + ep_cs


def get_player_status_emoji(status: str) -> str:
    """Get emoji for player status.

    Args:
        status: Player status code (a/d/i/u/s)

    Returns:
        Status emoji

    Example:
        >>> emoji = get_player_status_emoji("i")
        >>> print(emoji)  # "🤕"
    """
    status_map = {
        "a": "✅",  # Available
        "d": "❓",  # Doubtful
        "i": "🤕",  # Injured
        "u": "❌",  # Unavailable
        "s": "🚫",  # Suspended
    }
    return status_map.get(status, "❔")


def get_player_status_circle(status: str) -> str:
    """Get colored circle for player status.

    Args:
        status: Player status code (a/d/i/u/s)

    Returns:
        Colored circle emoji

    Example:
        >>> circle = get_player_status_circle("a")
        >>> print(circle)  # "🟢"
    """
    status_map = {
        "a": "🟢",  # Available - Green
        "d": "🟡",  # Doubtful - Yellow
        "i": "🔴",  # Injured - Red
        "u": "🔴",  # Unavailable - Red
        "s": "🔴",  # Suspended - Red
    }
    return status_map.get(status, "⚪")


def calculate_form_fixtures(
    player_history: list[dict[str, Any]], n: int = 5
) -> float:
    """Calculate average points from last N fixtures (including 0s when didn't play).

    This is fixture-based form that includes all gameweeks in the calculation,
    even when the player didn't play (0 points).

    Args:
        player_history: Player's history list from API (element-summary endpoint)
        n: Number of fixtures to include (default: 5)

    Returns:
        Average points from last N fixtures, or 0.0 if no history

    Example:
        >>> history = [
        ...     {"round": 1, "total_points": 6, "minutes": 90},
        ...     {"round": 2, "total_points": 0, "minutes": 0},  # Didn't play
        ...     {"round": 3, "total_points": 8, "minutes": 90},
        ... ]
        >>> form = calculate_form_fixtures(history, n=3)
        >>> print(f"Fixture form: {form:.1f}")  # (6 + 0 + 8) / 3 = 4.7
    """
    if not player_history:
        return 0.0

    # Sort by gameweek (round) in descending order to get most recent first
    sorted_history = sorted(
        player_history, key=lambda x: x.get("round", 0), reverse=True
    )

    # Take last N fixtures
    last_n_fixtures = sorted_history[:n]

    if not last_n_fixtures:
        return 0.0

    # Calculate average (includes 0s)
    total_points = sum(fixture.get("total_points", 0) for fixture in last_n_fixtures)
    fixture_count = len(last_n_fixtures)

    return total_points / fixture_count if fixture_count > 0 else 0.0


def calculate_form_games(player_history: list[dict[str, Any]], n: int = 5) -> float:
    """Calculate average points from last N games actually played.

    This is game-based form that only includes gameweeks where the player
    actually played (minutes > 0).

    Args:
        player_history: Player's history list from API (element-summary endpoint)
        n: Number of games to include (default: 5)

    Returns:
        Average points from last N games played, or 0.0 if no games played

    Example:
        >>> history = [
        ...     {"round": 1, "total_points": 6, "minutes": 90},
        ...     {"round": 2, "total_points": 0, "minutes": 0},  # Didn't play
        ...     {"round": 3, "total_points": 8, "minutes": 90},
        ... ]
        >>> form = calculate_form_games(history, n=2)
        >>> print(f"Game form: {form:.1f}")  # (6 + 8) / 2 = 7.0
    """
    if not player_history:
        return 0.0

    # Filter to only games where player actually played
    games_played = [h for h in player_history if h.get("minutes", 0) > 0]

    if not games_played:
        return 0.0

    # Sort by gameweek (round) in descending order to get most recent first
    sorted_games = sorted(games_played, key=lambda x: x.get("round", 0), reverse=True)

    # Take last N games
    last_n_games = sorted_games[:n]

    if not last_n_games:
        return 0.0

    # Calculate average
    total_points = sum(game.get("total_points", 0) for game in last_n_games)
    games_count = len(last_n_games)

    return total_points / games_count if games_count > 0 else 0.0


def calculate_avg_points_last_5_games(player_history: list[dict[str, Any]]) -> float:
    """Calculate average points from last 5 games (fixtures) played.

    This differs from FPL's "form" metric by being calculated from raw history data,
    accounting for double gameweeks and only looking at actual games played.

    DEPRECATED: Use calculate_form_games() instead.

    Args:
        player_history: Player's history list from API (element-summary endpoint)

    Returns:
        Average points from last 5 games, or 0.0 if no games played

    Example:
        >>> history = [
        ...     {"total_points": 8, "minutes": 90},
        ...     {"total_points": 5, "minutes": 60},
        ...     {"total_points": 0, "minutes": 0},  # Didn't play
        ...     {"total_points": 12, "minutes": 90},
        ... ]
        >>> avg = calculate_avg_points_last_5_games(history)
        >>> print(f"{avg:.1f}")  # Only counts games where minutes > 0
    """
    # Delegate to new function
    return calculate_form_games(player_history, n=5)
