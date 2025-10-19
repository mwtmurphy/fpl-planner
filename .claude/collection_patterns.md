# FPL Data Collection Patterns

**Status**: Project-specific reference
**Scope**: Data collection strategies, caching, incremental updates, and optimization patterns

## Overview

This document defines patterns for collecting FPL data efficiently, respecting API rate limits, and managing local data storage.

**Key Principles**:
- Respect API rate limits (conservative 10 req/min)
- Cache strategically based on data update frequency
- Implement incremental updates to minimize API calls
- Handle errors gracefully with retry logic
- Store data efficiently for analysis

## Collection Strategies

### 1. Bootstrap Collection

**Purpose**: Collect all core FPL data (players, teams, gameweeks)

**Frequency**: Once per day, or when new gameweek starts

**Pattern**:
```python
from fpl.api.client import FPLClient
from fpl.core.models import Player, Team, Gameweek
from fpl.data.storage import DataStorage

async def collect_bootstrap_data() -> dict:
    """Collect bootstrap-static data with caching."""
    storage = DataStorage()

    # Check cache (1 hour TTL)
    cached = storage.get_cached("bootstrap", ttl_seconds=3600)
    if cached:
        return cached

    # Fetch from API
    async with FPLClient() as client:
        data = await client.get_bootstrap_static()

    # Parse into models
    players = [Player(**p) for p in data["elements"]]
    teams = [Team(**t) for t in data["teams"]]
    gameweeks = [Gameweek(**gw) for gw in data["events"]]

    # Cache and return
    result = {
        "players": players,
        "teams": teams,
        "gameweeks": gameweeks,
        "timestamp": datetime.now()
    }
    storage.cache("bootstrap", result)
    return result
```

**Caching**: 1 hour TTL, refresh at gameweek deadline

### 2. Player History Collection

**Purpose**: Collect detailed player performance history

**Frequency**: Once per gameweek after gameweek finishes

**Pattern**:
```python
async def collect_player_history(
    player_ids: list[int],
    force_refresh: bool = False
) -> dict[int, PlayerHistory]:
    """Collect player history with rate limiting."""
    storage = DataStorage()
    client = FPLClient(rate_limit=10)  # 10 req/min

    results = {}
    for player_id in player_ids:
        # Check cache first
        if not force_refresh:
            cached = storage.get_player_history(player_id)
            if cached:
                results[player_id] = cached
                continue

        # Fetch from API with rate limiting
        try:
            async with client:
                summary = await client.get_player_summary(player_id)
                history = [
                    PlayerHistory(**h)
                    for h in summary["history"]
                ]
                results[player_id] = history
                storage.save_player_history(player_id, history)

        except FPLAPIError as e:
            logger.error(f"Failed to fetch player {player_id}: {e}")
            continue

    return results
```

**Caching**: Until next gameweek finishes

**Rate Limiting**: Built into client, max 10 requests per minute

### 3. Live Gameweek Collection

**Purpose**: Collect live scores during active gameweek

**Frequency**: Every 5-10 minutes during matches

**Pattern**:
```python
async def collect_live_gameweek(gameweek_id: int) -> dict:
    """Collect live gameweek data (NO CACHING)."""
    async with FPLClient() as client:
        live_data = await client.get_live_gameweek(gameweek_id)

    # Parse live stats
    player_stats = {}
    for element in live_data["elements"]:
        player_stats[element["id"]] = {
            "points": element["stats"]["total_points"],
            "minutes": element["stats"]["minutes"],
            "goals": element["stats"]["goals_scored"],
            "assists": element["stats"]["assists"],
            "bonus": element["stats"]["bonus"],
            "bps": element["stats"]["bps"]
        }

    return {
        "gameweek": gameweek_id,
        "timestamp": datetime.now(),
        "players": player_stats
    }
```

**Caching**: NEVER - data changes frequently during matches

**Polling**: Max every 5 minutes during active matches

### 4. Fixture Collection

**Purpose**: Collect fixture data with results

**Frequency**: Daily, or after matches complete

**Pattern**:
```python
async def collect_fixtures(
    gameweek_id: Optional[int] = None,
    force_refresh: bool = False
) -> list[Fixture]:
    """Collect fixtures with optional gameweek filter."""
    storage = DataStorage()

    # Check cache for completed fixtures
    cache_key = f"fixtures_gw_{gameweek_id}" if gameweek_id else "fixtures_all"
    if not force_refresh:
        cached = storage.get_cached(cache_key, ttl_seconds=3600)
        if cached:
            return cached

    # Fetch from API
    async with FPLClient() as client:
        if gameweek_id:
            fixtures_data = await client.get_fixtures(event=gameweek_id)
        else:
            fixtures_data = await client.get_fixtures()

    fixtures = [Fixture(**f) for f in fixtures_data]

    # Cache completed fixtures indefinitely
    completed = [f for f in fixtures if f.finished]
    if completed:
        storage.cache(f"{cache_key}_completed", completed, ttl_seconds=None)

    # Cache all fixtures for 1 hour
    storage.cache(cache_key, fixtures, ttl_seconds=3600)

    return fixtures
```

**Caching**:
- Completed fixtures: Indefinite
- Upcoming fixtures: 1 hour

### 5. Manager Team Collection

**Purpose**: Track manager's team selections over time

**Frequency**: Once per gameweek after deadline

**Pattern**:
```python
async def collect_manager_team(
    manager_id: int,
    gameweek_id: int
) -> ManagerTeam:
    """Collect manager's team for specific gameweek."""
    storage = DataStorage()

    # Check if gameweek is finished (cache indefinitely)
    gameweek = storage.get_gameweek(gameweek_id)
    cache_key = f"manager_{manager_id}_gw_{gameweek_id}"

    if gameweek and gameweek.finished:
        cached = storage.get_cached(cache_key, ttl_seconds=None)
        if cached:
            return cached

    # Fetch from API
    async with FPLClient() as client:
        picks_data = await client.get_manager_picks(manager_id, gameweek_id)

    team = ManagerTeam(**picks_data)

    # Cache
    ttl = None if gameweek and gameweek.finished else 3600
    storage.cache(cache_key, team, ttl_seconds=ttl)

    return team
```

**Caching**:
- Finished gameweeks: Indefinite
- Current gameweek: 1 hour

## Incremental Update Patterns

### Player Price Tracking

```python
async def track_price_changes() -> list[dict]:
    """Track player price changes since last check."""
    storage = DataStorage()

    # Get last update timestamp
    last_update = storage.get_last_update("price_tracking")

    # Fetch current data
    async with FPLClient() as client:
        data = await client.get_bootstrap_static()

    current_players = {p["id"]: p["now_cost"] for p in data["elements"]}

    # Load previous prices
    previous_prices = storage.get_player_prices()

    # Detect changes
    changes = []
    for player_id, current_price in current_players.items():
        previous_price = previous_prices.get(player_id)
        if previous_price and previous_price != current_price:
            changes.append({
                "player_id": player_id,
                "old_price": previous_price,
                "new_price": current_price,
                "change": current_price - previous_price,
                "timestamp": datetime.now()
            })

    # Update storage
    storage.save_player_prices(current_players)
    storage.set_last_update("price_tracking", datetime.now())

    return changes
```

### Transfer Tracking

```python
async def track_manager_transfers(
    manager_id: int,
    since: Optional[datetime] = None
) -> list[dict]:
    """Track manager's transfers since specified time."""
    storage = DataStorage()

    # Get all transfers
    async with FPLClient() as client:
        all_transfers = await client.get_manager_transfers(manager_id)

    # Filter by timestamp if provided
    if since:
        new_transfers = [
            t for t in all_transfers
            if datetime.fromisoformat(t["time"].replace("Z", "+00:00")) > since
        ]
    else:
        new_transfers = all_transfers

    # Store new transfers
    storage.save_manager_transfers(manager_id, new_transfers)

    return new_transfers
```

## Caching Strategy

### Cache Tiers

**Tier 1: Indefinite Cache**
- Completed gameweek data
- Completed fixture results
- Historical player performance (past gameweeks)
- Never invalidate

**Tier 2: Long Cache (1 hour)**
- Bootstrap-static data (players, teams, gameweeks)
- Player summaries
- Upcoming fixtures
- Manager information

**Tier 3: Short Cache (5-15 minutes)**
- Transfer activity
- Ownership percentages
- Price change predictions

**Tier 4: No Cache**
- Live gameweek data
- Real-time match stats
- Current bonus point standings

### Cache Implementation

```python
from pathlib import Path
import json
from datetime import datetime, timedelta
from typing import Optional, Any

class CacheManager:
    """Manages cached FPL data."""

    def __init__(self, cache_dir: Path = Path("./data/cache")):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get(
        self,
        key: str,
        ttl_seconds: Optional[int] = 3600
    ) -> Optional[Any]:
        """Get cached data if not expired."""
        cache_file = self.cache_dir / f"{key}.json"

        if not cache_file.exists():
            return None

        # Check expiration
        if ttl_seconds is not None:
            file_age = datetime.now().timestamp() - cache_file.stat().st_mtime
            if file_age > ttl_seconds:
                return None

        # Load data
        with cache_file.open("r") as f:
            return json.load(f)

    def set(
        self,
        key: str,
        data: Any,
        ttl_seconds: Optional[int] = 3600
    ) -> None:
        """Cache data with optional TTL."""
        cache_file = self.cache_dir / f"{key}.json"

        with cache_file.open("w") as f:
            json.dump(data, f, default=str)

    def invalidate(self, key: str) -> None:
        """Invalidate specific cache entry."""
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            cache_file.unlink()

    def clear_all(self) -> None:
        """Clear all cached data."""
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
```

## Rate Limiting

### Client-Side Rate Limiting

```python
import asyncio
from collections import deque
from datetime import datetime, timedelta

class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, requests_per_minute: int = 10):
        self.requests_per_minute = requests_per_minute
        self.window = timedelta(minutes=1)
        self.requests = deque()

    async def acquire(self) -> None:
        """Wait if necessary to respect rate limit."""
        now = datetime.now()

        # Remove old requests outside window
        while self.requests and self.requests[0] < now - self.window:
            self.requests.popleft()

        # Check if we need to wait
        if len(self.requests) >= self.requests_per_minute:
            # Calculate wait time
            oldest = self.requests[0]
            wait_until = oldest + self.window
            wait_seconds = (wait_until - now).total_seconds()

            if wait_seconds > 0:
                await asyncio.sleep(wait_seconds)

        # Record this request
        self.requests.append(datetime.now())
```

### Usage in Client

```python
class FPLClient:
    """HTTP client for FPL API with rate limiting."""

    def __init__(self, rate_limit: int = 10):
        self.base_url = "https://fantasy.premierleague.com/api"
        self.rate_limiter = RateLimiter(requests_per_minute=rate_limit)
        self.client = httpx.AsyncClient()

    async def _request(self, endpoint: str) -> dict:
        """Make rate-limited API request."""
        await self.rate_limiter.acquire()

        url = f"{self.base_url}/{endpoint}"
        response = await self.client.get(url)
        response.raise_for_status()

        return response.json()
```

## Error Handling Patterns

### Retry with Exponential Backoff

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(httpx.HTTPError)
)
async def fetch_with_retry(client: FPLClient, endpoint: str) -> dict:
    """Fetch data with automatic retry on failure."""
    return await client._request(endpoint)
```

### Graceful Degradation

```python
async def collect_player_data_robust(player_id: int) -> Optional[Player]:
    """Collect player data with graceful failure handling."""
    try:
        async with FPLClient() as client:
            summary = await client.get_player_summary(player_id)
            return Player(**summary)

    except NotFoundError:
        logger.warning(f"Player {player_id} not found")
        return None

    except RateLimitError:
        logger.error("Rate limited, waiting 60 seconds")
        await asyncio.sleep(60)
        return await collect_player_data_robust(player_id)

    except FPLAPIError as e:
        logger.error(f"API error for player {player_id}: {e}")
        return None
```

## Batch Collection Patterns

### Concurrent Player Collection

```python
async def collect_multiple_players(
    player_ids: list[int],
    max_concurrent: int = 5
) -> dict[int, Optional[Player]]:
    """Collect multiple players with concurrency limit."""
    semaphore = asyncio.Semaphore(max_concurrent)

    async def fetch_one(player_id: int) -> tuple[int, Optional[Player]]:
        async with semaphore:
            player = await collect_player_data_robust(player_id)
            return player_id, player

    # Collect concurrently
    tasks = [fetch_one(pid) for pid in player_ids]
    results = await asyncio.gather(*tasks)

    return dict(results)
```

### Gameweek Batch Collection

```python
async def collect_gameweek_batch(
    start_gw: int,
    end_gw: int
) -> dict[int, Gameweek]:
    """Collect multiple gameweeks efficiently."""
    # Fetch bootstrap once
    async with FPLClient() as client:
        data = await client.get_bootstrap_static()

    gameweeks = data["events"]

    # Filter to requested range
    result = {}
    for gw_data in gameweeks:
        gw_id = gw_data["id"]
        if start_gw <= gw_id <= end_gw:
            result[gw_id] = Gameweek(**gw_data)

    return result
```

## Data Storage Patterns

### File-Based Storage

```python
from pathlib import Path
import json
import csv

class FileStorage:
    """File-based data storage."""

    def __init__(self, data_dir: Path = Path("./data")):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def save_players_json(self, players: list[Player]) -> None:
        """Save players to JSON file."""
        file_path = self.data_dir / "players.json"
        with file_path.open("w") as f:
            json.dump(
                [p.model_dump() for p in players],
                f,
                indent=2,
                default=str
            )

    def save_players_csv(self, players: list[Player]) -> None:
        """Save players to CSV file."""
        file_path = self.data_dir / "players.csv"
        with file_path.open("w", newline="") as f:
            if players:
                writer = csv.DictWriter(f, fieldnames=players[0].model_dump().keys())
                writer.writeheader()
                for player in players:
                    writer.writerow(player.model_dump())

    def load_players_json(self) -> list[Player]:
        """Load players from JSON file."""
        file_path = self.data_dir / "players.json"
        with file_path.open("r") as f:
            data = json.load(f)
            return [Player(**p) for p in data]
```

### SQLite Storage

```python
import sqlite3
from typing import List

class SQLiteStorage:
    """SQLite database storage."""

    def __init__(self, db_path: Path = Path("./data/fpl.db")):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._create_tables()

    def _create_tables(self) -> None:
        """Create database tables."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY,
                web_name TEXT,
                team INTEGER,
                element_type INTEGER,
                now_cost INTEGER,
                total_points INTEGER,
                updated_at TIMESTAMP
            )
        """)

    def save_players(self, players: list[Player]) -> None:
        """Save players to database."""
        self.conn.executemany(
            """
            INSERT OR REPLACE INTO players
            (id, web_name, team, element_type, now_cost, total_points, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    p.id,
                    p.web_name,
                    p.team,
                    p.element_type,
                    p.now_cost,
                    p.total_points,
                    datetime.now()
                )
                for p in players
            ]
        )
        self.conn.commit()

    def get_players(self) -> list[Player]:
        """Get all players from database."""
        cursor = self.conn.execute("SELECT * FROM players")
        # Convert rows to Player objects
        # (simplified - would need full mapping)
        return []
```

## Performance Optimization

### Minimize API Calls

```python
# Good: Single API call for all players
async with FPLClient() as client:
    data = await client.get_bootstrap_static()
    all_players = [Player(**p) for p in data["elements"]]
    midfielders = [p for p in all_players if p.element_type == 3]

# Bad: Multiple API calls
for player_id in player_ids:
    player = await client.get_player_summary(player_id)  # N API calls!
```

### Batch Processing

```python
# Process in batches to control memory usage
def batch_process_players(
    players: list[Player],
    batch_size: int = 100
) -> None:
    """Process players in batches."""
    for i in range(0, len(players), batch_size):
        batch = players[i:i + batch_size]
        # Process batch
        analyze_players(batch)
```

## References

- See `fpl_api_reference.md` for endpoint details
- See workspace `performance_considerations.md` for optimization patterns
- See workspace `error_handling.md` for error handling best practices

---

**Last Updated**: 2025-10-15
**Scope**: FPL data collection patterns and strategies
