"""Domain models for FPL data.

This module defines Pydantic models for all FPL entities including players,
teams, gameweeks, and fixtures. See .claude/data_models.md for full specifications.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Player(BaseModel):
    """FPL player model.

    Represents a Premier League player with all FPL-relevant statistics,
    pricing, and status information.
    """

    # Identity
    id: int = Field(..., description="Unique player ID")
    code: int = Field(..., description="External player code")
    first_name: str
    second_name: str
    web_name: str = Field(..., description="Display name")

    # Team and Position
    team: int = Field(..., description="Team ID (1-20)")
    element_type: int = Field(..., description="Position (1=GK, 2=DEF, 3=MID, 4=FWD)")

    # Pricing and Ownership
    now_cost: int = Field(..., description="Current price in 0.1m units")
    cost_change_start: int = Field(..., description="Price change since season start")
    cost_change_event: int = Field(..., description="Price change this gameweek")
    selected_by_percent: str = Field(..., description="Ownership percentage as string")

    # Performance Metrics
    total_points: int = Field(..., description="Season total points")
    event_points: int = Field(..., description="Points this gameweek")
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
    bps: int = Field(..., description="Bonus Points System score")

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
    status: str = Field(
        ...,
        description="a=available, d=doubtful, i=injured, u=unavailable, s=suspended",
    )
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
        """Return price in £m."""
        return Decimal(self.now_cost) / 10

    @property
    def ownership_percent(self) -> float:
        """Return ownership as float (e.g., 35.2)."""
        return float(self.selected_by_percent)

    @property
    def position_name(self) -> str:
        """Return position name."""
        positions = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}
        return positions[self.element_type]

    def is_available(self) -> bool:
        """Check if player is available for selection."""
        return self.status == "a"

    def is_injured(self) -> bool:
        """Check if player is injured."""
        return self.status in ["d", "i"]


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
    highest_score: Optional[int] = Field(
        None, ge=0, description="Highest manager score"
    )
    most_selected: Optional[int] = Field(None, description="Most selected player ID")
    most_transferred_in: Optional[int] = Field(
        None, description="Most transferred in player ID"
    )
    most_captained: Optional[int] = Field(None, description="Most captained player ID")
    most_vice_captained: Optional[int] = Field(
        None, description="Most vice-captained player ID"
    )
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


class Fixture(BaseModel):
    """Premier League fixture model."""

    id: int = Field(..., description="Fixture ID")
    code: int = Field(..., description="External fixture code")
    event: Optional[int] = Field(None, ge=1, le=38, description="Gameweek number")
    kickoff_time: Optional[datetime] = Field(None, description="Match kickoff time")

    # Teams
    team_h: int = Field(..., description="Home team ID")
    team_a: int = Field(..., description="Away team ID")
    team_h_difficulty: int = Field(
        ..., ge=1, le=5, description="Home team difficulty (1-5)"
    )
    team_a_difficulty: int = Field(
        ..., ge=1, le=5, description="Away team difficulty (1-5)"
    )

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


class PlayerHistory(BaseModel):
    """Player gameweek performance history."""

    element: int = Field(..., description="Player ID")
    fixture: int = Field(..., description="Fixture ID")
    opponent_team: int = Field(..., description="Opponent team ID")
    total_points: int = Field(..., description="Points scored in this gameweek")
    was_home: bool
    kickoff_time: datetime
    round: int = Field(..., ge=1, le=38, description="Gameweek number")

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
    bps: int = Field(..., description="Bonus Points System score")

    # ICT Metrics
    influence: str
    creativity: str
    threat: str
    ict_index: str

    # Context
    value: int = Field(..., description="Player price at time (0.1m units)")
    selected: int = Field(ge=0, description="Ownership at time")


class ManagerPick(BaseModel):
    """Single player pick in manager's team."""

    element: int = Field(..., description="Player ID")
    position: int = Field(..., ge=1, le=15)
    multiplier: int = Field(..., ge=0, le=3)
    is_captain: bool
    is_vice_captain: bool

    def is_benched(self) -> bool:
        """Check if player is on bench."""
        return self.multiplier == 0


class ManagerTeam(BaseModel):
    """Manager's team for a gameweek."""

    active_chip: Optional[str] = None
    picks: list[ManagerPick] = Field(..., min_length=15, max_length=15)
    entry_history: dict

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
