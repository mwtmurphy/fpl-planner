"""HTTP client for FPL API.

This module provides an async HTTP client for interacting with the Fantasy
Premier League API. See .claude/fpl_api_reference.md for endpoint details.
"""

import asyncio
import logging
from collections import deque
from datetime import datetime, timedelta
from typing import Any, Optional

import httpx

from fpl.api.endpoints import build_url
from fpl.api.exceptions import (
    FPLAPIError,
    NotFoundError,
    RateLimitError,
    ServerError,
)

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, requests_per_minute: int = 10):
        """Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests per minute
        """
        self.requests_per_minute = requests_per_minute
        self.window = timedelta(minutes=1)
        self.requests: deque[datetime] = deque()

    async def acquire(self) -> None:
        """Wait if necessary to respect rate limit."""
        now = datetime.now()

        # Remove old requests outside window
        while self.requests and self.requests[0] < now - self.window:
            self.requests.popleft()

        # Check if we need to wait
        if len(self.requests) >= self.requests_per_minute:
            oldest = self.requests[0]
            wait_until = oldest + self.window
            wait_seconds = (wait_until - now).total_seconds()

            if wait_seconds > 0:
                await asyncio.sleep(wait_seconds)

        # Record this request
        self.requests.append(datetime.now())


class FPLClient:
    """HTTP client for FPL API with rate limiting.

    Example:
        >>> async with FPLClient() as client:
        ...     data = await client.get_bootstrap_static()
        ...     players = data["elements"]
    """

    def __init__(self, rate_limit: int = 10, timeout: float = 30.0):
        """Initialize FPL API client.

        Args:
            rate_limit: Maximum requests per minute (default: 10)
            timeout: Request timeout in seconds (default: 30.0)
        """
        self.rate_limiter = RateLimiter(requests_per_minute=rate_limit)
        self.timeout = timeout
        self.client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "FPLClient":
        """Enter async context manager."""
        self.client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context manager."""
        if self.client:
            await self.client.aclose()

    async def _request(self, endpoint_key: str, **url_params: Any) -> dict[str, Any]:
        """Make rate-limited API request.

        Args:
            endpoint_key: Endpoint key from endpoints.py
            **url_params: URL parameters

        Returns:
            JSON response as dict

        Raises:
            NotFoundError: Resource not found (404)
            RateLimitError: Rate limit exceeded (429)
            ServerError: Server error (500)
            FPLAPIError: Other API errors
        """
        if self.client is None:
            raise RuntimeError("Client not initialized. Use 'async with' context.")

        await self.rate_limiter.acquire()

        url = build_url(endpoint_key, **url_params)

        try:
            response = await self.client.get(url)

            if response.status_code == 404:
                logger.error(
                    "Resource not found",
                    extra={
                        "url": url,
                        "endpoint": endpoint_key,
                        "params": url_params,
                        "status_code": 404,
                    },
                )
                raise NotFoundError(f"Resource not found: {url}")
            elif response.status_code == 429:
                logger.warning(
                    "API rate limit exceeded",
                    extra={
                        "url": url,
                        "endpoint": endpoint_key,
                        "retry_after": response.headers.get("Retry-After"),
                    },
                )
                raise RateLimitError("API rate limit exceeded")
            elif response.status_code >= 500:
                logger.error(
                    "Server error",
                    extra={
                        "url": url,
                        "endpoint": endpoint_key,
                        "status_code": response.status_code,
                        "response_body": response.text[:500],  # First 500 chars
                    },
                )
                raise ServerError(f"Server error: {response.status_code}")

            response.raise_for_status()
            result: dict[str, Any] = response.json()
            return result

        except httpx.HTTPError as e:
            logger.error(
                "HTTP error occurred",
                extra={
                    "url": url,
                    "endpoint": endpoint_key,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                },
            )
            raise FPLAPIError(f"HTTP error: {e}") from e

    async def get_bootstrap_static(self) -> dict[str, Any]:
        """Get bootstrap-static data (players, teams, gameweeks).

        Returns:
            Dict with keys: elements, teams, events, element_types, etc.

        Example:
            >>> data = await client.get_bootstrap_static()
            >>> players = data["elements"]
            >>> teams = data["teams"]
        """
        return await self._request("bootstrap_static")

    async def get_fixtures(self, event: Optional[int] = None) -> list[dict[str, Any]]:
        """Get fixture data.

        Args:
            event: Optional gameweek ID to filter fixtures

        Returns:
            List of fixture dicts
        """
        if event:
            result = await self._request("fixtures_by_gameweek", event_id=event)
            return result  # type: ignore[return-value]
        result = await self._request("fixtures")
        return result  # type: ignore[return-value]

    async def get_player_summary(self, player_id: int) -> dict[str, Any]:
        """Get detailed player summary with history.

        Args:
            player_id: Player ID

        Returns:
            Dict with keys: fixtures, history, history_past
        """
        return await self._request("player_summary", player_id=player_id)

    async def get_live_gameweek(self, event_id: int) -> dict[str, Any]:
        """Get live gameweek data.

        Args:
            event_id: Gameweek ID

        Returns:
            Dict with live player statistics
        """
        return await self._request("live_gameweek", event_id=event_id)

    async def get_manager(self, manager_id: int) -> dict[str, Any]:
        """Get manager information.

        Args:
            manager_id: Manager ID

        Returns:
            Manager data dict
        """
        return await self._request("manager", manager_id=manager_id)

    async def get_manager_history(self, manager_id: int) -> dict[str, Any]:
        """Get manager's gameweek history.

        Args:
            manager_id: Manager ID

        Returns:
            Dict with keys: current, past, chips
        """
        return await self._request("manager_history", manager_id=manager_id)

    async def get_manager_picks(self, manager_id: int, event_id: int) -> dict[str, Any]:
        """Get manager's team picks for specific gameweek.

        Args:
            manager_id: Manager ID
            event_id: Gameweek ID

        Returns:
            Dict with picks and entry_history
        """
        return await self._request(
            "manager_picks", manager_id=manager_id, event_id=event_id
        )

    async def get_manager_transfers(self, manager_id: int) -> list[dict[str, Any]]:
        """Get manager's transfer history.

        Args:
            manager_id: Manager ID

        Returns:
            List of transfer dicts
        """
        result = await self._request("manager_transfers", manager_id=manager_id)
        return result  # type: ignore[return-value]

    async def get_classic_league(self, league_id: int, page: int = 1) -> dict[str, Any]:
        """Get classic league standings.

        Args:
            league_id: League ID
            page: Page number for pagination (default: 1)

        Returns:
            Dict with league info and standings

        Example:
            >>> league = await client.get_classic_league(123456)
            >>> standings = league["standings"]["results"]
        """
        # Note: Pagination is done via query params, not in the endpoint URL
        # We'll need to modify _request to support query params
        # For now, we'll just get page 1
        return await self._request("classic_league", league_id=league_id)

    async def get_h2h_league(self, league_id: int) -> dict[str, Any]:
        """Get head-to-head league standings.

        Args:
            league_id: League ID

        Returns:
            Dict with H2H league info and standings
        """
        return await self._request("h2h_league", league_id=league_id)

    async def get_dream_team(self, event_id: int) -> dict[str, Any]:
        """Get official FPL Dream Team for a gameweek.

        Args:
            event_id: Gameweek ID

        Returns:
            Dict with dream team players and top player

        Example:
            >>> dream_team = await client.get_dream_team(1)
            >>> players = dream_team["team"]
            >>> top_player = dream_team["top_player"]
        """
        return await self._request("dream_team", event_id=event_id)

    async def get_set_piece_notes(self) -> list[dict[str, Any]]:
        """Get set piece taker notes for all teams.

        Returns:
            List of dicts with team set piece information

        Example:
            >>> notes = await client.get_set_piece_notes()
            >>> for note in notes:
            ...     print(f"Team {note['team']}: {note['info_message']}")
        """
        result = await self._request("set_pieces")
        return result  # type: ignore[return-value]

    async def get_event_status(self) -> dict[str, Any]:
        """Get current event status.

        Returns:
            Dict with event status information
        """
        return await self._request("event_status")
