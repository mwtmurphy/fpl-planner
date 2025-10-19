"""Unit tests for API client."""

import pytest
from httpx import AsyncClient
from pytest_httpx import HTTPXMock

from fpl.api.client import FPLClient
from fpl.api.exceptions import NotFoundError


@pytest.mark.asyncio
async def test_client_context_manager():
    """Test FPLClient can be used as context manager."""
    async with FPLClient() as client:
        assert client.client is not None


@pytest.mark.asyncio
async def test_get_bootstrap_static(httpx_mock: HTTPXMock):
    """Test get_bootstrap_static method."""
    mock_data = {
        "elements": [{"id": 1}],
        "teams": [{"id": 1}],
        "events": [{"id": 1}],
    }

    httpx_mock.add_response(
        url="https://fantasy.premierleague.com/api/bootstrap-static/",
        json=mock_data,
    )

    async with FPLClient() as client:
        data = await client.get_bootstrap_static()

    assert "elements" in data
    assert "teams" in data
    assert "events" in data


@pytest.mark.asyncio
async def test_client_handles_404(httpx_mock: HTTPXMock):
    """Test client raises NotFoundError on 404."""
    httpx_mock.add_response(
        url="https://fantasy.premierleague.com/api/element-summary/999999/",
        status_code=404,
    )

    async with FPLClient() as client:
        with pytest.raises(NotFoundError):
            await client.get_player_summary(999999)


@pytest.mark.asyncio
async def test_get_fixtures(httpx_mock: HTTPXMock):
    """Test get_fixtures method."""
    mock_fixtures = [
        {"id": 1, "team_h": 1, "team_a": 2},
        {"id": 2, "team_h": 3, "team_a": 4},
    ]

    httpx_mock.add_response(
        url="https://fantasy.premierleague.com/api/fixtures/",
        json=mock_fixtures,
    )

    async with FPLClient() as client:
        fixtures = await client.get_fixtures()

    assert len(fixtures) == 2
    assert fixtures[0]["id"] == 1


@pytest.mark.asyncio
async def test_get_fixtures_by_gameweek(httpx_mock: HTTPXMock):
    """Test get_fixtures with event parameter."""
    mock_fixtures = [{"id": 1, "event": 1}]

    httpx_mock.add_response(
        url="https://fantasy.premierleague.com/api/fixtures/?event=1",
        json=mock_fixtures,
    )

    async with FPLClient() as client:
        fixtures = await client.get_fixtures(event=1)

    assert len(fixtures) == 1
    assert fixtures[0]["event"] == 1


@pytest.mark.asyncio
async def test_get_player_summary(httpx_mock: HTTPXMock):
    """Test get_player_summary method."""
    mock_summary = {
        "fixtures": [],
        "history": [{"element": 302, "total_points": 8}],
        "history_past": [],
    }

    httpx_mock.add_response(
        url="https://fantasy.premierleague.com/api/element-summary/302/",
        json=mock_summary,
    )

    async with FPLClient() as client:
        summary = await client.get_player_summary(302)

    assert "fixtures" in summary
    assert "history" in summary
    assert len(summary["history"]) == 1


@pytest.mark.asyncio
async def test_get_live_gameweek(httpx_mock: HTTPXMock):
    """Test get_live_gameweek method."""
    mock_live = {"elements": [{"id": 302, "stats": {"total_points": 8}}]}

    httpx_mock.add_response(
        url="https://fantasy.premierleague.com/api/event/1/live/",
        json=mock_live,
    )

    async with FPLClient() as client:
        live = await client.get_live_gameweek(1)

    assert "elements" in live
    assert len(live["elements"]) == 1


@pytest.mark.asyncio
async def test_get_manager(httpx_mock: HTTPXMock):
    """Test get_manager method."""
    mock_manager = {
        "id": 123456,
        "name": "Test Team",
        "summary_overall_points": 1856,
    }

    httpx_mock.add_response(
        url="https://fantasy.premierleague.com/api/entry/123456/",
        json=mock_manager,
    )

    async with FPLClient() as client:
        manager = await client.get_manager(123456)

    assert manager["id"] == 123456
    assert "name" in manager


@pytest.mark.asyncio
async def test_get_manager_history(httpx_mock: HTTPXMock):
    """Test get_manager_history method."""
    mock_history = {"current": [], "past": [], "chips": []}

    httpx_mock.add_response(
        url="https://fantasy.premierleague.com/api/entry/123456/history/",
        json=mock_history,
    )

    async with FPLClient() as client:
        history = await client.get_manager_history(123456)

    assert "current" in history
    assert "past" in history
    assert "chips" in history


@pytest.mark.asyncio
async def test_get_manager_picks(httpx_mock: HTTPXMock):
    """Test get_manager_picks method."""
    mock_picks = {
        "picks": [{"element": 302, "multiplier": 2, "is_captain": True}],
        "entry_history": {"event": 1, "points": 65},
    }

    httpx_mock.add_response(
        url="https://fantasy.premierleague.com/api/entry/123456/event/1/picks/",
        json=mock_picks,
    )

    async with FPLClient() as client:
        picks = await client.get_manager_picks(123456, 1)

    assert "picks" in picks
    assert len(picks["picks"]) == 1


@pytest.mark.asyncio
async def test_get_manager_transfers(httpx_mock: HTTPXMock):
    """Test get_manager_transfers method."""
    mock_transfers = [
        {"element_in": 401, "element_out": 302, "event": 5},
    ]

    httpx_mock.add_response(
        url="https://fantasy.premierleague.com/api/entry/123456/transfers/",
        json=mock_transfers,
    )

    async with FPLClient() as client:
        transfers = await client.get_manager_transfers(123456)

    assert len(transfers) == 1
    assert transfers[0]["event"] == 5


# New endpoint tests


@pytest.mark.asyncio
async def test_get_classic_league(httpx_mock: HTTPXMock):
    """Test get_classic_league method."""
    mock_league = {
        "league": {"id": 123456, "name": "Test League"},
        "standings": {
            "results": [
                {"entry": 111, "rank": 1, "total": 1856},
                {"entry": 222, "rank": 2, "total": 1820},
            ]
        },
    }

    httpx_mock.add_response(
        url="https://fantasy.premierleague.com/api/leagues-classic/123456/standings/",
        json=mock_league,
    )

    async with FPLClient() as client:
        league = await client.get_classic_league(123456)

    assert "league" in league
    assert league["league"]["id"] == 123456
    assert "standings" in league
    assert len(league["standings"]["results"]) == 2


@pytest.mark.asyncio
async def test_get_h2h_league(httpx_mock: HTTPXMock):
    """Test get_h2h_league method."""
    mock_h2h = {
        "league": {"id": 789, "name": "H2H League"},
        "standings": {"results": []},
    }

    httpx_mock.add_response(
        url="https://fantasy.premierleague.com/api/leagues-h2h/789/standings/",
        json=mock_h2h,
    )

    async with FPLClient() as client:
        h2h = await client.get_h2h_league(789)

    assert "league" in h2h
    assert h2h["league"]["id"] == 789


@pytest.mark.asyncio
async def test_get_dream_team(httpx_mock: HTTPXMock):
    """Test get_dream_team method."""
    mock_dream_team = {
        "team": [
            {"element": 302, "points": 15, "position": 1},
            {"element": 354, "points": 14, "position": 2},
        ],
        "top_player": {"id": 302, "points": 15},
    }

    httpx_mock.add_response(
        url="https://fantasy.premierleague.com/api/dream-team/1/",
        json=mock_dream_team,
    )

    async with FPLClient() as client:
        dream_team = await client.get_dream_team(1)

    assert "team" in dream_team
    assert "top_player" in dream_team
    assert len(dream_team["team"]) == 2
    assert dream_team["top_player"]["id"] == 302


@pytest.mark.asyncio
async def test_get_set_piece_notes(httpx_mock: HTTPXMock):
    """Test get_set_piece_notes method."""
    mock_notes = [
        {"team": 1, "info_message": "Penalties and free kicks: Saka"},
        {"team": 2, "info_message": "Penalties: Salah, Free kicks: TAA"},
    ]

    httpx_mock.add_response(
        url="https://fantasy.premierleague.com/api/team/set-piece-notes/",
        json=mock_notes,
    )

    async with FPLClient() as client:
        notes = await client.get_set_piece_notes()

    assert len(notes) == 2
    assert notes[0]["team"] == 1
    assert "Saka" in notes[0]["info_message"]


@pytest.mark.asyncio
async def test_get_event_status(httpx_mock: HTTPXMock):
    """Test get_event_status method."""
    mock_status = {
        "status": [{"event": 1, "bonus_added": True}],
        "leagues": "Updated",
    }

    httpx_mock.add_response(
        url="https://fantasy.premierleague.com/api/event-status/",
        json=mock_status,
    )

    async with FPLClient() as client:
        status = await client.get_event_status()

    assert "status" in status
    assert "leagues" in status


# Rate limiter tests


@pytest.mark.asyncio
async def test_rate_limiter_basic():
    """Test rate limiter allows requests within limit."""
    from fpl.api.client import RateLimiter

    limiter = RateLimiter(requests_per_minute=10)

    # Should allow first request immediately
    await limiter.acquire()
    assert len(limiter.requests) == 1


@pytest.mark.asyncio
async def test_rate_limiter_cleans_old_requests():
    """Test rate limiter removes old requests from tracking."""
    from fpl.api.client import RateLimiter
    from datetime import datetime, timedelta

    limiter = RateLimiter(requests_per_minute=10)

    # Add an old request (2 minutes ago)
    old_time = datetime.now() - timedelta(minutes=2)
    limiter.requests.append(old_time)

    # Acquire should clean it up
    await limiter.acquire()

    # Old request should be removed
    assert len(limiter.requests) == 1
    assert limiter.requests[0] > old_time


@pytest.mark.asyncio
async def test_rate_limiter_enforces_limit():
    """Test rate limiter waits when limit is exceeded."""
    from fpl.api.client import RateLimiter
    from datetime import datetime
    import asyncio

    limiter = RateLimiter(requests_per_minute=2)

    # Make 2 requests (at limit)
    await limiter.acquire()
    await limiter.acquire()
    assert len(limiter.requests) == 2

    # Third request should wait, but we'll use a timeout to verify
    # it would wait without actually waiting in the test
    start = datetime.now()

    # Add a very short timeout to avoid long test execution
    # In real usage, it would wait the full duration
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(limiter.acquire(), timeout=0.01)


# Error handling tests


@pytest.mark.asyncio
async def test_client_not_initialized():
    """Test client raises error when used without context manager."""
    from fpl.api.client import FPLClient

    client = FPLClient()

    with pytest.raises(RuntimeError, match="Client not initialized"):
        await client.get_bootstrap_static()


@pytest.mark.asyncio
async def test_client_handles_429_rate_limit(httpx_mock: HTTPXMock):
    """Test client raises RateLimitError on 429."""
    from fpl.api.exceptions import RateLimitError

    httpx_mock.add_response(
        url="https://fantasy.premierleague.com/api/bootstrap-static/",
        status_code=429,
    )

    async with FPLClient() as client:
        with pytest.raises(RateLimitError, match="rate limit exceeded"):
            await client.get_bootstrap_static()


@pytest.mark.asyncio
async def test_client_handles_500_server_error(httpx_mock: HTTPXMock):
    """Test client raises ServerError on 500."""
    from fpl.api.exceptions import ServerError

    httpx_mock.add_response(
        url="https://fantasy.premierleague.com/api/bootstrap-static/",
        status_code=500,
    )

    async with FPLClient() as client:
        with pytest.raises(ServerError, match="Server error"):
            await client.get_bootstrap_static()


@pytest.mark.asyncio
async def test_client_handles_network_error(httpx_mock: HTTPXMock):
    """Test client handles network errors gracefully."""
    from fpl.api.exceptions import FPLAPIError
    import httpx

    # Simulate network error
    httpx_mock.add_exception(
        httpx.ConnectError("Connection failed"),
        url="https://fantasy.premierleague.com/api/bootstrap-static/",
    )

    async with FPLClient() as client:
        with pytest.raises(FPLAPIError, match="HTTP error"):
            await client.get_bootstrap_static()


@pytest.mark.asyncio
async def test_client_timeout_configuration():
    """Test client timeout can be configured."""
    async with FPLClient(timeout=60.0) as client:
        assert client.timeout == 60.0
        assert client.client.timeout.read == 60.0
