# FPL API Reference

**Status**: Project-specific reference
**Scope**: Fantasy Premier League API endpoints, data structures, and usage patterns

## Overview

The Fantasy Premier League API is an unofficial, publicly accessible API provided by the official FPL website. This reference documents all known endpoints, their parameters, response formats, and usage patterns.

**Base URL**: `https://fantasy.premierleague.com/api`

## Important Notes

### Rate Limiting
- No official rate limit is documented
- Use conservative approach: **max 10 requests per minute**
- Implement exponential backoff on failures
- Cache responses where appropriate

### CORS Policy
- API has CORS restrictions
- Cannot be called directly from browser JavaScript
- Backend/server-side requests work fine

### Data Updates
- **Bootstrap-static**: Updates when new gameweek data is available
- **Fixtures**: Updated with match results
- **Live data**: Updates during matches (every ~30 seconds)
- **Player prices**: Can change between gameweeks

### Season Changes
- API structure may change during off-season (June-August)
- Always verify endpoint responses at season start
- Player IDs reset each season

## Core Endpoints

### 1. Bootstrap-Static

**Endpoint**: `GET /bootstrap-static/`

**Purpose**: Primary endpoint containing all core FPL data

**Response Structure**:
```json
{
  "events": [],        // Gameweeks (38 items)
  "teams": [],         // Premier League teams (20 items)
  "elements": [],      // All players (600+ items)
  "element_types": [], // Player positions (4 items: GK, DEF, MID, FWD)
  "element_stats": [], // Available player stats
  "game_settings": {}, // FPL game rules and settings
  "phases": [],        // Season phases
  "total_players": 0   // Total FPL managers
}
```

**Key Data**:

**Events (Gameweeks)**:
```python
{
    "id": 1,
    "name": "Gameweek 1",
    "deadline_time": "2024-08-16T17:30:00Z",
    "finished": false,
    "is_current": true,
    "is_next": false,
    "average_entry_score": 45,
    "highest_score": 78,
    "most_captained": 354,  // Player ID
    "most_vice_captained": 355,
    "chip_plays": [],
    "transfers_made": 0
}
```

**Teams**:
```python
{
    "id": 1,
    "name": "Arsenal",
    "short_name": "ARS",
    "strength": 4,
    "strength_overall_home": 1200,
    "strength_overall_away": 1180,
    "strength_attack_home": 1220,
    "strength_attack_away": 1200,
    "strength_defence_home": 1180,
    "strength_defence_away": 1160
}
```

**Elements (Players)**:
```python
{
    "id": 302,
    "first_name": "Bukayo",
    "second_name": "Saka",
    "web_name": "Saka",
    "team": 1,  // Team ID
    "element_type": 3,  // Position (3 = MID)
    "now_cost": 95,  // Price in 0.1m (9.5m)
    "selected_by_percent": "35.2",
    "form": "7.3",
    "points_per_game": "6.2",
    "total_points": 186,
    "goals_scored": 12,
    "assists": 8,
    "clean_sheets": 10,
    "bonus": 15,
    "minutes": 3140,
    "ict_index": "162.3",
    "influence": "1215.4",
    "creativity": "1089.6",
    "threat": "1156.0"
}
```

**Element Types (Positions)**:
```python
{
    "id": 1,
    "plural_name": "Goalkeepers",
    "singular_name": "Goalkeeper",
    "squad_select": 2,  // Must select 2 in squad
    "squad_min_play": 1,  // Min 1 in starting 11
    "squad_max_play": 1   // Max 1 in starting 11
}
```

**Caching**: Cache for 1 hour, re-fetch when new gameweek starts

### 2. Fixtures

**Endpoint**: `GET /fixtures/`

**Purpose**: All Premier League fixtures with results and stats

**Optional Parameters**:
- `?event={gameweek_id}` - Filter by gameweek
- `?team={team_id}` - Filter by team

**Response**:
```python
[
    {
        "id": 1,
        "code": 12345,
        "event": 1,  // Gameweek ID
        "finished": true,
        "kickoff_time": "2024-08-16T20:00:00Z",
        "team_h": 1,  // Home team ID
        "team_a": 2,  // Away team ID
        "team_h_score": 2,
        "team_a_score": 1,
        "team_h_difficulty": 3,
        "team_a_difficulty": 4,
        "stats": [
            {
                "identifier": "goals_scored",
                "h": [{"element": 302, "value": 1}],  // Home scorers
                "a": [{"element": 401, "value": 1}]   // Away scorers
            }
        ]
    }
]
```

**Caching**: Cache until fixture is finished, then cache indefinitely

### 3. Element Summary (Player Details)

**Endpoint**: `GET /element-summary/{player_id}/`

**Purpose**: Detailed player history and upcoming fixtures

**Response**:
```python
{
    "fixtures": [],  // Upcoming fixtures for player's team
    "history": [],   // Gameweek-by-gameweek performance this season
    "history_past": []  // Season-by-season summary (past seasons)
}
```

**History (This Season)**:
```python
{
    "element": 302,
    "fixture": 1,
    "opponent_team": 2,
    "total_points": 8,
    "was_home": true,
    "minutes": 90,
    "goals_scored": 1,
    "assists": 0,
    "clean_sheets": 0,
    "goals_conceded": 1,
    "bonus": 2,
    "influence": "65.2",
    "creativity": "42.8",
    "threat": "58.0",
    "ict_index": "16.6",
    "value": 95,  // Price at time of gameweek
    "selected": 3500000  // Ownership at time
}
```

**History Past (Previous Seasons)**:
```python
{
    "season_name": "2023/24",
    "element_code": 123456,
    "start_cost": 80,
    "end_cost": 95,
    "total_points": 186,
    "minutes": 3140,
    "goals_scored": 12,
    "assists": 8,
    "clean_sheets": 10,
    "bonus": 15
}
```

**Caching**: Cache for 1 hour, update after each gameweek

### 4. Live Gameweek Data

**Endpoint**: `GET /event/{gameweek_id}/live/`

**Purpose**: Real-time player performance during gameweek

**Response**:
```python
{
    "elements": [
        {
            "id": 302,
            "stats": {
                "minutes": 45,  // Current minutes played
                "goals_scored": 1,
                "assists": 0,
                "total_points": 6,
                "bonus": 0,  // Provisional bonus
                "bps": 32  // Bonus points system score
            },
            "explain": [
                {
                    "fixture": 1,
                    "stats": [
                        {
                            "identifier": "goals_scored",
                            "points": 5,
                            "value": 1
                        }
                    ]
                }
            ]
        }
    ]
}
```

**Caching**: Do NOT cache - updates frequently during matches

### 5. Manager Entry

**Endpoint**: `GET /entry/{manager_id}/`

**Purpose**: Manager's basic information and current season stats

**Response**:
```python
{
    "id": 123456,
    "joined_time": "2020-07-01T10:00:00Z",
    "started_event": 1,
    "player_first_name": "John",
    "player_last_name": "Doe",
    "player_region_name": "England",
    "summary_overall_points": 1856,
    "summary_overall_rank": 123456,
    "summary_event_points": 65,
    "summary_event_rank": 2345678,
    "current_event": 15,
    "name": "Team Name",
    "kit": {},
    "favourite_team": 1
}
```

**Caching**: Cache for 1 hour

### 6. Manager History

**Endpoint**: `GET /entry/{manager_id}/history/`

**Purpose**: Manager's gameweek-by-gameweek history and past seasons

**Response**:
```python
{
    "current": [  // This season, gameweek by gameweek
        {
            "event": 1,
            "points": 65,
            "total_points": 65,
            "rank": 1234567,
            "overall_rank": 1234567,
            "bank": 5,  // Money in bank (0.5m)
            "value": 1000,  // Team value (100.0m)
            "event_transfers": 0,
            "event_transfers_cost": 0,
            "points_on_bench": 12
        }
    ],
    "past": [  // Previous seasons
        {
            "season_name": "2023/24",
            "total_points": 2156,
            "rank": 234567
        }
    ],
    "chips": [  // Chip usage
        {
            "name": "wildcard",
            "time": "2024-09-01T12:00:00Z",
            "event": 5
        }
    ]
}
```

**Caching**: Cache for 1 hour, update after gameweek deadline

### 7. Manager Team Picks

**Endpoint**: `GET /entry/{manager_id}/event/{gameweek_id}/picks/`

**Purpose**: Manager's team selection for specific gameweek

**Response**:
```python
{
    "active_chip": null,  // or "wildcard", "bboost", etc.
    "automatic_subs": [],  // Auto-substitutions made
    "entry_history": {
        "event": 1,
        "points": 65,
        "total_points": 65,
        "rank": 1234567,
        "overall_rank": 1234567,
        "bank": 5,
        "value": 1000,
        "event_transfers": 1,
        "event_transfers_cost": 4
    },
    "picks": [
        {
            "element": 302,  // Player ID
            "position": 1,  // Position in team (1-15)
            "multiplier": 2,  // 2 = captain, 3 = triple captain, 0 = bench
            "is_captain": true,
            "is_vice_captain": false
        }
    ]
}
```

**Caching**: Cache after gameweek is finished, re-fetch for current gameweek

### 8. Manager Transfers

**Endpoint**: `GET /entry/{manager_id}/transfers/`

**Purpose**: All transfers made by manager this season

**Response**:
```python
[
    {
        "element_in": 401,  // Player ID transferred in
        "element_in_cost": 85,
        "element_out": 302,  // Player ID transferred out
        "element_out_cost": 95,
        "entry": 123456,
        "event": 5,
        "time": "2024-09-15T10:30:00Z"
    }
]
```

**Caching**: Cache for 1 hour

### 9. Classic League Standings

**Endpoint**: `GET /leagues-classic/{league_id}/standings/`

**Optional Parameters**:
- `?page_standings={page}` - Pagination (50 per page)

**Response**:
```python
{
    "league": {
        "id": 123456,
        "name": "League Name",
        "created": "2024-08-01T00:00:00Z",
        "admin_entry": 234567,
        "start_event": 1
    },
    "standings": {
        "has_next": true,
        "page": 1,
        "results": [
            {
                "id": 234567,
                "entry_name": "Team Name",
                "player_name": "John Doe",
                "rank": 1,
                "last_rank": 2,
                "total": 1856,
                "entry": 234567
            }
        ]
    }
}
```

**Caching**: Cache for 1 hour

### 10. Dream Team

**Endpoint**: `GET /dream-team/{gameweek_id}/`

**Purpose**: Official FPL Dream Team for a gameweek

**Response**:
```python
{
    "team": [
        {
            "element": 302,
            "points": 15,
            "position": 1  // Formation position
        }
    ],
    "top_player": {
        "id": 302,
        "points": 15
    }
}
```

**Caching**: Cache after gameweek is finished

### 11. Set Piece Takers

**Endpoint**: `GET /team/set-piece-notes/`

**Purpose**: Official notes on set piece takers for each team

**Response**:
```python
[
    {
        "external_link": false,
        "info_message": "Penalties and free kicks: Saka",
        "team": 1
    }
]
```

**Caching**: Cache for 1 week, update manually when news breaks

## Error Handling

### HTTP Status Codes
- `200 OK` - Success
- `404 Not Found` - Resource doesn't exist (invalid player/manager/league ID)
- `429 Too Many Requests` - Rate limited (unofficial, implement conservative limits)
- `500 Internal Server Error` - FPL server error (retry with exponential backoff)

### Error Response Format
```python
{
    "detail": "Error message"
}
```

## Best Practices

### Request Headers
```python
{
    "User-Agent": "FPL-Data-Collector/0.1.0",
    "Accept": "application/json"
}
```

### Retry Strategy
```python
# Exponential backoff
retries = 3
for attempt in range(retries):
    try:
        response = await client.get(url)
        return response
    except HTTPError:
        if attempt < retries - 1:
            await asyncio.sleep(2 ** attempt)
        else:
            raise
```

### Batch Requests
```python
# Use asyncio.gather for concurrent requests
players_task = client.get_players()
teams_task = client.get_teams()
fixtures_task = client.get_fixtures()

players, teams, fixtures = await asyncio.gather(
    players_task, teams_task, fixtures_task
)
```

## Data Relationships

### ID References
- `element` / `player_id`: References player in bootstrap-static elements
- `team` / `team_id`: References team in bootstrap-static teams
- `event` / `gameweek_id`: References gameweek in bootstrap-static events
- `fixture_id`: References fixture in fixtures endpoint
- `element_type`: References position in bootstrap-static element_types (1=GK, 2=DEF, 3=MID, 4=FWD)

### Derived Fields
- `now_cost`: Price in 0.1m units (95 = £9.5m)
- `selected_by_percent`: String percentage "35.2"
- `ict_index`: Influence + Creativity + Threat composite metric
- `form`: Average points over last 5 games (fixtures) played. Note: This counts actual games the player participated in, not gameweeks. Accounts for double gameweeks and games missed.
- `points_per_game`: Season average points per game played

## Usage Examples

### Fetch All Core Data
```python
async with FPLClient() as client:
    data = await client.get_bootstrap_static()
    players = data["elements"]
    teams = data["teams"]
    gameweeks = data["events"]
```

### Get Player Performance History
```python
player_id = 302
summary = await client.get_player_summary(player_id)
this_season = summary["history"]  # Gameweek by gameweek
past_seasons = summary["history_past"]  # Season totals
```

### Get Live Gameweek Data
```python
gameweek = 1
live_data = await client.get_live_gameweek(gameweek)
for player in live_data["elements"]:
    print(f"Player {player['id']}: {player['stats']['total_points']} pts")
```

### Track Manager Team
```python
manager_id = 123456
gameweek = 1
picks = await client.get_manager_picks(manager_id, gameweek)
captain_id = next(p["element"] for p in picks["picks"] if p["is_captain"])
```

## References

- [Oliver Looney's FPL API Guide](https://www.oliverlooney.com/blogs/FPL-APIs-Explained)
- [Medium: FPL API Endpoints](https://medium.com/@frenzelts/fantasy-premier-league-api-endpoints-a-detailed-guide-acbd5598eb19)
- [FPL ReadTheDocs (Python wrapper)](https://fpl.readthedocs.io/)

---

**Last Updated**: 2025-10-15
**Scope**: FPL API endpoints and data structures
