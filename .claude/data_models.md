# FPL Data Models

**Status**: Project-specific reference
**Scope**: Domain models, business rules, and validation patterns for FPL data

## Overview

This document defines the core domain models for FPL data. All models use Pydantic for type-safe validation and serialization, following workspace Python standards.

**Why Pydantic**: Type-safe, validates data, easy JSON serialization, integrates with FastAPI/httpx

## Core Domain Models

### Player

Represents an FPL player (footballer).

```python
from pydantic import BaseModel, Field, field_validator
from decimal import Decimal
from typing import Optional

class Player(BaseModel):
    """FPL player model."""

    # Identity
    id: int = Field(..., description="Unique player ID")
    code: int = Field(..., description="External player code")
    first_name: str
    second_name: str
    web_name: str = Field(..., description="Display name (e.g., 'Saka')")

    # Team and Position
    team: int = Field(..., description="Team ID (1-20)")
    element_type: int = Field(..., description="Position (1=GK, 2=DEF, 3=MID, 4=FWD)")

    # Pricing and Ownership
    now_cost: int = Field(..., description="Current price in 0.1m units (95 = £9.5m)")
    cost_change_start: int = Field(..., description="Price change since season start")
    cost_change_event: int = Field(..., description="Price change this gameweek")
    selected_by_percent: str = Field(..., description="Ownership percentage as string")

    # Performance Metrics
    total_points: int = Field(ge=0, description="Season total points")
    event_points: int = Field(ge=0, description="Points this gameweek")
    form: str = Field(..., description="Average points last 5 games")
    points_per_game: str = Field(..., description="Season average points")

    # Statistics
    minutes: int = Field(ge=0)
    goals_scored: int = Field(ge=0)
    assists: int = Field(ge=0)
    clean_sheets: int = Field(ge=0)
    goals_conceded: int = Field(ge=0)
    own_goals: int = Field(ge=0)
    penalties_saved: int = Field(ge=0)
    penalties_missed: int = Field(ge=0)
    yellow_cards: int = Field(ge=0)
    red_cards: int = Field(ge=0)
    saves: int = Field(ge=0)
    bonus: int = Field(ge=0)
    bps: int = Field(ge=0, description="Bonus Points System score")

    # Advanced Metrics
    influence: str = Field(..., description="Influence rating")
    creativity: str = Field(..., description="Creativity rating")
    threat: str = Field(..., description="Threat rating")
    ict_index: str = Field(..., description="ICT composite index")

    # Expected Stats (xG, xA)
    expected_goals: str = Field(..., description="Expected goals (xG)")
    expected_assists: str = Field(..., description="Expected assists (xA)")
    expected_goal_involvements: str = Field(..., description="xG + xA")
    expected_goals_conceded: str = Field(..., description="xGC")

    # Status
    status: str = Field(..., description="a=available, d=doubtful, i=injured, u=unavailable, s=suspended")
    news: str = Field(default="", description="Injury/availability news")
    news_added: Optional[str] = Field(None, description="News timestamp")
    chance_of_playing_this_round: Optional[int] = Field(None, ge=0, le=100)
    chance_of_playing_next_round: Optional[int] = Field(None, ge=0, le=100)

    # Transfers
    transfers_in: int = Field(ge=0)
    transfers_out: int = Field(ge=0)
    transfers_in_event: int = Field(ge=0)
    transfers_out_event: int = Field(ge=0)

    @field_validator("element_type")
    @classmethod
    def validate_position(cls, v: int) -> int:
        """Validate position is valid (1-4)."""
        if v not in [1, 2, 3, 4]:
            raise ValueError("Position must be 1 (GK), 2 (DEF), 3 (MID), or 4 (FWD)")
        return v

    @property
    def price(self) -> Decimal:
        """Return price in £m (e.g., 9.5)."""
        return Decimal(self.now_cost) / 10

    @property
    def ownership_percent(self) -> float:
        """Return ownership as float (e.g., 35.2)."""
        return float(self.selected_by_percent)

    @property
    def position_name(self) -> str:
        """Return position name (GK, DEF, MID, FWD)."""
        positions = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}
        return positions[self.element_type]

    def is_available(self) -> bool:
        """Check if player is available for selection."""
        return self.status == "a"

    def is_injured(self) -> bool:
        """Check if player is injured."""
        return self.status in ["d", "i"]

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "id": 302,
                "first_name": "Bukayo",
                "second_name": "Saka",
                "web_name": "Saka",
                "team": 1,
                "element_type": 3,
                "now_cost": 95,
                "total_points": 186
            }
        }
```

### Team

Represents a Premier League team.

```python
class Team(BaseModel):
    """Premier League team model."""

    id: int = Field(..., ge=1, le=20, description="Team ID (1-20)")
    name: str = Field(..., description="Full team name")
    short_name: str = Field(..., max_length=3, description="3-letter code (e.g., ARS)")
    code: int = Field(..., description="External team code")

    # Strength Ratings
    strength: int = Field(..., ge=1, le=5, description="Overall strength (1-5)")
    strength_overall_home: int = Field(..., description="Home strength rating")
    strength_overall_away: int = Field(..., description="Away strength rating")
    strength_attack_home: int = Field(..., description="Home attack strength")
    strength_attack_away: int = Field(..., description="Away attack strength")
    strength_defence_home: int = Field(..., description="Home defense strength")
    strength_defence_away: int = Field(..., description="Away defense strength")

    # Performance
    position: int = Field(..., ge=1, le=20, description="League position")
    played: int = Field(ge=0, description="Matches played")
    win: int = Field(ge=0)
    draw: int = Field(ge=0)
    loss: int = Field(ge=0)
    points: int = Field(ge=0, description="League points")

    # Flags
    unavailable: bool = Field(default=False)

    @property
    def form_guide(self) -> str:
        """Return basic form guide."""
        total = self.win + self.draw + self.loss
        if total == 0:
            return "No matches"
        win_pct = (self.win / total) * 100
        return f"{win_pct:.1f}% wins"

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Arsenal",
                "short_name": "ARS",
                "strength": 5,
                "position": 2
            }
        }
```

### Gameweek

Represents an FPL gameweek (event).

```python
from datetime import datetime

class Gameweek(BaseModel):
    """FPL gameweek (event) model."""

    id: int = Field(..., ge=1, le=38, description="Gameweek number (1-38)")
    name: str = Field(..., description="Display name (e.g., 'Gameweek 1')")
    deadline_time: datetime = Field(..., description="Team deadline")

    # Status
    is_previous: bool
    is_current: bool
    is_next: bool
    finished: bool
    data_checked: bool

    # Statistics
    average_entry_score: int = Field(ge=0, description="Average manager score")
    highest_score: Optional[int] = Field(None, ge=0, description="Highest manager score")
    most_selected: Optional[int] = Field(None, description="Most selected player ID")
    most_transferred_in: Optional[int] = Field(None, description="Most transferred in player ID")
    most_captained: Optional[int] = Field(None, description="Most captained player ID")
    most_vice_captained: Optional[int] = Field(None, description="Most vice-captained player ID")
    top_element: Optional[int] = Field(None, description="Top scoring player ID")
    top_element_info: Optional[dict] = Field(None, description="Top player details")

    # Transfers
    transfers_made: int = Field(ge=0, description="Total transfers made")

    # Chip usage
    chip_plays: list[dict] = Field(default_factory=list)

    def is_active(self) -> bool:
        """Check if gameweek is currently active."""
        return self.is_current and not self.finished

    def is_upcoming(self) -> bool:
        """Check if gameweek is upcoming."""
        return not self.is_previous and not self.is_current and not self.finished

    def deadline_passed(self) -> bool:
        """Check if deadline has passed."""
        return datetime.now() > self.deadline_time

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Gameweek 1",
                "is_current": True,
                "finished": False,
                "average_entry_score": 45
            }
        }
```

### Fixture

Represents a Premier League match.

```python
class Fixture(BaseModel):
    """Premier League fixture model."""

    id: int = Field(..., description="Fixture ID")
    code: int = Field(..., description="External fixture code")
    event: Optional[int] = Field(None, ge=1, le=38, description="Gameweek number")
    kickoff_time: Optional[datetime] = Field(None, description="Match kickoff time")

    # Teams
    team_h: int = Field(..., description="Home team ID")
    team_a: int = Field(..., description="Away team ID")
    team_h_difficulty: int = Field(..., ge=1, le=5, description="Home team difficulty (1-5)")
    team_a_difficulty: int = Field(..., ge=1, le=5, description="Away team difficulty (1-5)")

    # Status
    started: bool = Field(default=False)
    finished: bool = Field(default=False)
    finished_provisional: bool = Field(default=False)

    # Score
    team_h_score: Optional[int] = Field(None, ge=0)
    team_a_score: Optional[int] = Field(None, ge=0)

    # Statistics
    stats: list[dict] = Field(default_factory=list, description="Match statistics")

    def is_completed(self) -> bool:
        """Check if fixture is completed."""
        return self.finished

    def is_live(self) -> bool:
        """Check if fixture is currently live."""
        return self.started and not self.finished

    def home_win(self) -> bool:
        """Check if home team won."""
        if not self.finished or self.team_h_score is None or self.team_a_score is None:
            return False
        return self.team_h_score > self.team_a_score

    def away_win(self) -> bool:
        """Check if away team won."""
        if not self.finished or self.team_h_score is None or self.team_a_score is None:
            return False
        return self.team_a_score > self.team_h_score

    def draw(self) -> bool:
        """Check if match was a draw."""
        if not self.finished or self.team_h_score is None or self.team_a_score is None:
            return False
        return self.team_h_score == self.team_a_score

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "id": 1,
                "event": 1,
                "team_h": 1,
                "team_a": 2,
                "team_h_score": 2,
                "team_a_score": 1,
                "finished": True
            }
        }
```

## Supporting Models

### PlayerHistory

Player's gameweek performance history.

```python
class PlayerHistory(BaseModel):
    """Player gameweek performance history."""

    element: int = Field(..., description="Player ID")
    fixture: int = Field(..., description="Fixture ID")
    opponent_team: int = Field(..., description="Opponent team ID")
    total_points: int = Field(ge=0)
    was_home: bool
    kickoff_time: datetime
    round: int = Field(..., ge=1, le=38, description="Gameweek number")
    minutes: int = Field(ge=0)
    goals_scored: int = Field(ge=0)
    assists: int = Field(ge=0)
    clean_sheets: int = Field(ge=0)
    goals_conceded: int = Field(ge=0)
    own_goals: int = Field(ge=0)
    penalties_saved: int = Field(ge=0)
    penalties_missed: int = Field(ge=0)
    yellow_cards: int = Field(ge=0)
    red_cards: int = Field(ge=0)
    saves: int = Field(ge=0)
    bonus: int = Field(ge=0)
    bps: int = Field(ge=0)
    influence: str
    creativity: str
    threat: str
    ict_index: str
    value: int = Field(..., description="Player price at time (0.1m units)")
    selected: int = Field(ge=0, description="Ownership at time")
```

### ManagerTeam

Manager's team selection for a gameweek.

```python
class ManagerPick(BaseModel):
    """Single player pick in manager's team."""

    element: int = Field(..., description="Player ID")
    position: int = Field(..., ge=1, le=15, description="Position in team (1-15)")
    multiplier: int = Field(..., ge=0, le=3, description="0=bench, 1=playing, 2=captain, 3=triple captain")
    is_captain: bool
    is_vice_captain: bool

    def is_benched(self) -> bool:
        """Check if player is on bench."""
        return self.multiplier == 0


class ManagerTeam(BaseModel):
    """Manager's team for a gameweek."""

    active_chip: Optional[str] = Field(None, description="wildcard, bboost, 3xc, freehit")
    picks: list[ManagerPick] = Field(..., min_length=15, max_length=15)
    entry_history: dict = Field(..., description="Gameweek history")

    def get_captain(self) -> int:
        """Get captain player ID."""
        captain = next((p for p in self.picks if p.is_captain), None)
        if captain is None:
            raise ValueError("No captain found")
        return captain.element

    def get_starting_11(self) -> list[ManagerPick]:
        """Get starting 11 players."""
        return [p for p in self.picks if p.multiplier > 0]

    def get_bench(self) -> list[ManagerPick]:
        """Get bench players."""
        return [p for p in self.picks if p.multiplier == 0]
```

## Business Rules

### Player Pricing
- Price stored as integer in 0.1m units (95 = £9.5m)
- Minimum price: £4.0m (40 units)
- Maximum price: £15.0m (150 units)
- Price changes occur between gameweeks based on transfers

### Position Constraints
- 1 = Goalkeeper (GK)
- 2 = Defender (DEF)
- 3 = Midfielder (MID)
- 4 = Forward (FWD)

Squad requirements:
- 2 Goalkeepers
- 5 Defenders
- 5 Midfielders
- 3 Forwards
- Total: 15 players

### Team Selection
- Exactly 11 starting players
- Exactly 4 bench players
- 1 captain (2x points)
- 1 vice-captain (backup if captain doesn't play)

### Scoring System
- Minutes: 1 point (1-59 min), 2 points (60+ min)
- Goals: GK/DEF=6, MID=5, FWD=4
- Assists: 3 points
- Clean sheets: GK/DEF=4, MID=1
- Bonus: 1-3 points (top 3 BPS in match)

### Status Codes
- `a`: Available
- `d`: Doubtful (25-75% chance of playing)
- `i`: Injured/unavailable (0% chance)
- `u`: Unavailable
- `s`: Suspended

## Validation Rules

### Player Validation
- `element_type` must be 1-4
- `now_cost` must be >= 40 (£4.0m)
- All point fields must be >= 0
- `selected_by_percent` must parse to valid float

### Team Validation
- `id` must be 1-20 (20 Premier League teams)
- `short_name` must be exactly 3 characters
- `position` must be 1-20
- Strength ratings must be 1-5

### Gameweek Validation
- `id` must be 1-38 (38 gameweeks per season)
- Only one gameweek can have `is_current=True`
- `deadline_time` must be future for upcoming gameweeks

## Usage Examples

### Create Player from API Response
```python
api_response = {
    "id": 302,
    "first_name": "Bukayo",
    "second_name": "Saka",
    # ... other fields
}

player = Player(**api_response)
print(f"{player.web_name}: £{player.price}m, {player.total_points} pts")
```

### Filter Players by Position
```python
players = [Player(**p) for p in api_data["elements"]]
midfielders = [p for p in players if p.element_type == 3]
available_mids = [p for p in midfielders if p.is_available()]
```

### Calculate Team Value
```python
from decimal import Decimal

picks = manager_team.picks
total_value = sum(
    player_map[pick.element].price
    for pick in picks
)
print(f"Team value: £{total_value}m")
```

## References

- See `fpl_api_reference.md` for API endpoint details
- See workspace `architecture_patterns.md` for model design patterns
- See workspace `python_style.md` for coding standards

---

**Last Updated**: 2025-10-15
**Scope**: FPL domain models and business rules
