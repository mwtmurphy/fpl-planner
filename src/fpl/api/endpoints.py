"""FPL API endpoint constants.

See .claude/fpl_api_reference.md for full endpoint documentation.
"""

BASE_URL = "https://fantasy.premierleague.com/api"

ENDPOINTS = {
    # Core data
    "bootstrap_static": "bootstrap-static/",
    "fixtures": "fixtures/",
    "fixtures_by_gameweek": "fixtures/?event={event_id}",
    # Player data
    "player_summary": "element-summary/{player_id}/",
    # Live data
    "live_gameweek": "event/{event_id}/live/",
    # Manager data
    "manager": "entry/{manager_id}/",
    "manager_history": "entry/{manager_id}/history/",
    "manager_picks": "entry/{manager_id}/event/{event_id}/picks/",
    "manager_transfers": "entry/{manager_id}/transfers/",
    # League data
    "classic_league": "leagues-classic/{league_id}/standings/",
    "h2h_league": "leagues-h2h/{league_id}/standings/",
    # Other
    "dream_team": "dream-team/{event_id}/",
    "set_pieces": "team/set-piece-notes/",
    "event_status": "event-status/",
}


def build_url(endpoint_key: str, **kwargs: int | str) -> str:
    """Build full API URL with parameters.

    Args:
        endpoint_key: Key from ENDPOINTS dict
        **kwargs: URL parameters (player_id, event_id, etc.)

    Returns:
        Full API URL

    Example:
        >>> build_url("player_summary", player_id=302)
        'https://fantasy.premierleague.com/api/element-summary/302/'
    """
    endpoint = ENDPOINTS[endpoint_key]
    url = f"{BASE_URL}/{endpoint}"

    if kwargs:
        url = url.format(**kwargs)

    return url
