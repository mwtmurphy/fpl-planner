# FPL Project TODO Roadmap

**Status**: Project-specific tracking
**Scope**: Implementation roadmap for all pending TODOs

**Last Updated**: 2025-10-17

---

## Overview

This document tracks all 19 TODOs across the codebase, organized by implementation sprints with clear dependencies and priorities.

## Sprint 1: Foundation (Week 1)

### ✅ Step 1: Complete Model Definitions
**Priority**: CRITICAL - Must complete first

#### `src/fpl/core/models.py`

**1.1 Player Model (Line 41)** - Status: 🔄 In Progress
- Add remaining ~40 fields from `.claude/data_models.md`:
  - Statistics: `minutes`, `goals_scored`, `assists`, `clean_sheets`, `goals_conceded`, `own_goals`, `penalties_saved`, `penalties_missed`, `yellow_cards`, `red_cards`, `saves`, `bonus`, `bps`
  - Advanced metrics: `influence`, `creativity`, `threat`, `ict_index`, `expected_goals`, `expected_assists`, `expected_goal_involvements`, `expected_goals_conceded`
  - Pricing: `cost_change_start`, `cost_change_event`, `selected_by_percent` (already present)
  - Status: `status`, `news`, `news_added`, `chance_of_playing_this_round`, `chance_of_playing_next_round`
  - Transfers: `transfers_in`, `transfers_out`, `transfers_in_event`, `transfers_out_event`
  - Performance: `event_points`, `points_per_game` (already present)
  - Properties: `ownership_percent`, `is_available()`, `is_injured()`
- **Files**: `src/fpl/core/models.py:41`
- **Reference**: `.claude/data_models.md` Player section

**1.2 Team Model (Line 71)** - Status: ⏳ Pending
- Add strength ratings:
  - `strength_overall_home`, `strength_overall_away`
  - `strength_attack_home`, `strength_attack_away`
  - `strength_defence_home`, `strength_defence_away`
- Add performance stats:
  - `position`, `played`, `win`, `draw`, `loss`, `points`
- Add flags: `unavailable`
- Add property: `form_guide`
- **Files**: `src/fpl/core/models.py:71`
- **Reference**: `.claude/data_models.md` Team section

**1.3 Gameweek Model (Line 86)** - Status: ⏳ Pending
- Add statistics:
  - `average_entry_score`, `highest_score`
  - `most_selected`, `most_transferred_in`, `most_captained`, `most_vice_captained`
  - `top_element`, `top_element_info`
  - `transfers_made`
- Add status: `data_checked`
- Add chip usage: `chip_plays`
- Add methods: `is_upcoming()`, `deadline_passed()`
- **Files**: `src/fpl/core/models.py:86`
- **Reference**: `.claude/data_models.md` Gameweek section

**1.4 Fixture Model (Line 106)** - Status: ⏳ Pending
- Add status: `started`, `finished_provisional`
- Add scores: `team_h_score`, `team_a_score`
- Add difficulty: `team_h_difficulty`, `team_a_difficulty`
- Add stats: `stats` list
- Add methods: `home_win()`, `away_win()`, `draw()`, `is_live()`
- **Files**: `src/fpl/core/models.py:106`
- **Reference**: `.claude/data_models.md` Fixture section

**1.5 PlayerHistory Model (Line 122)** - Status: ⏳ Pending
- Add all gameweek performance fields:
  - `kickoff_time`, `round`, `minutes`
  - Statistics: `goals_scored`, `assists`, `clean_sheets`, `goals_conceded`, `own_goals`, `penalties_saved`, `penalties_missed`, `yellow_cards`, `red_cards`, `saves`, `bonus`, `bps`
  - ICT metrics: `influence`, `creativity`, `threat`, `ict_index`
  - Context: `value`, `selected`
- **Files**: `src/fpl/core/models.py:122`
- **Reference**: `.claude/data_models.md` PlayerHistory section

---

### ✅ Step 2: Add Model Tests
**Priority**: HIGH - Test as you build

#### `tests/unit/test_models.py`

**2.1 Player Model Tests (Line 78)** - Status: ⏳ Pending
- Test all new fields parse correctly
- Test `ownership_percent` property
- Test `is_available()` method for all status codes
- Test `is_injured()` method
- Test validation for invalid positions (already exists)
- Test price calculation property (already exists)
- Test position_name property (already exists)
- **Dependency**: 1.1 Player model complete

**2.2 Team Model Tests** - Status: ⏳ Pending
- Test strength rating fields
- Test performance stats
- Test `form_guide` property
- Test ID validation (1-20 range)
- Test short_name validation (3 chars)
- **Dependency**: 1.2 Team model complete

**2.3 Gameweek Model Tests** - Status: ⏳ Pending
- Test `is_active()` method
- Test `is_upcoming()` method
- Test `deadline_passed()` method
- Test gameweek ID validation (1-38)
- Test that only one can be current
- **Dependency**: 1.3 Gameweek model complete

**2.4 Fixture Model Tests** - Status: ⏳ Pending
- Test `home_win()`, `away_win()`, `draw()` methods
- Test `is_live()` method
- Test `is_completed()` method (already exists)
- Test score calculations
- **Dependency**: 1.4 Fixture model complete

**2.5 PlayerHistory Model Tests** - Status: ⏳ Pending
- Test all fields parse correctly
- Test validation of required fields
- **Dependency**: 1.5 PlayerHistory model complete

---

### ✅ Step 3: Add Remaining API Endpoints
**Priority**: HIGH - Enable full data access

#### `src/fpl/api/client.py`

**3.1 League Endpoints (Line 225)** - Status: ⏳ Pending
- `get_classic_league(league_id: int, page: int = 1)` → dict
- `get_h2h_league(league_id: int)` → dict
- **Reference**: `.claude/fpl_api_reference.md` sections 9-10

**3.2 Other Endpoints (Line 225)** - Status: ⏳ Pending
- `get_dream_team(event_id: int)` → dict
- `get_set_piece_notes()` → list[dict]
- `get_event_status()` → dict
- **Reference**: `.claude/fpl_api_reference.md` sections 10-11

**3.3 Endpoint Tests** - Status: ⏳ Pending
- Add tests for each new endpoint using httpx_mock
- Test parameter passing and URL building
- **Dependency**: 3.1, 3.2 complete

---

## Sprint 2: Data Collection (Week 2) ✅

### ✅ Step 4: Test Infrastructure
**Priority**: MEDIUM - Enables better testing

#### `tests/conftest.py`

**4.1 Mock API Client Fixture (Line 51)** - Status: ✅ Complete
```python
@pytest.fixture
def mock_fpl_client(httpx_mock):
    """Pre-configured mock FPL client for testing."""
    # Setup common mock responses
    return FPLClient()
```
- **Dependencies**: Sprint 1 complete

**4.2 Async Test Helpers (Line 52)** - Status: ✅ Complete
```python
def async_return(value):
    """Helper to return async values in tests."""

async def async_raise(exception):
    """Helper to raise exceptions in async tests."""
```
- **Dependencies**: None

---

### ✅ Step 5: Enhanced Client Tests
**Priority**: MEDIUM - Ensure reliability

#### `tests/unit/test_client.py`

**5.1 Rate Limiter Tests (Line 53)** - Status: ✅ Complete
- Test requests are properly spaced
- Test concurrent request limiting
- Test that rate limiter respects window
- Test multiple clients have separate rate limits
- **Dependencies**: 4.2 (async helpers)

**5.2 Error Handling Tests (Line 54)** - Status: ✅ Complete
- Test 500 server errors raise ServerError
- Test timeout handling
- Test network errors
- Test retry logic with exponential backoff
- Test all custom exceptions
- **Dependencies**: 4.2 (async helpers)

---

### ✅ Step 6: Player Collector Enhancements
**Priority**: MEDIUM - Core data collection

#### `src/fpl/data/collectors.py`

**6.1 Player History Collection (Line 67)** - Status: ✅ Complete
```python
async def collect_player_history(
    self,
    player_id: int,
    force_refresh: bool = False
) -> list[PlayerHistory]:
    """Collect player's gameweek-by-gameweek history."""
```
- **Dependencies**: 1.5 (PlayerHistory model), Sprint 1 complete
- **Reference**: `.claude/collection_patterns.md` Player History Collection

**6.2 Incremental Update Logic (Line 68)** - Status: ✅ Complete
```python
async def collect_updated_players(
    self,
    since: datetime
) -> list[Player]:
    """Collect only players updated since timestamp."""
```
- Requires timestamp tracking in storage
- **Dependencies**: 6.1, 8.2 (timestamp tracking)
- **Reference**: `.claude/collection_patterns.md` Incremental Updates

---

### ✅ Step 7: Fixture Collector Enhancements
**Priority**: LOW - Nice to have filters

#### `src/fpl/data/collectors.py`

**7.1 Fixture Filters (Line 115)** - Status: ✅ Complete
```python
async def collect_completed(self) -> list[Fixture]:
    """Collect only completed fixtures."""

async def collect_upcoming(self) -> list[Fixture]:
    """Collect only upcoming fixtures."""

async def collect_by_team(self, team_id: int) -> list[Fixture]:
    """Collect fixtures for specific team."""
```
- **Dependencies**: 1.4 (Fixture model complete)

---

## Sprint 3: Storage & Optimization (Week 3) ✅

### ✅ Step 8: Cache Management
**Priority**: MEDIUM - Performance optimization

#### `src/fpl/data/storage.py`

**8.1 Cache Management (Line 89)** - Status: ✅ Complete
```python
def get_cached(
    self,
    key: str,
    ttl_seconds: Optional[int] = 3600
) -> Optional[Any]:
    """Get cached data if not expired."""

def set_cached(
    self,
    key: str,
    data: Any,
    ttl_seconds: Optional[int] = 3600
) -> None:
    """Cache data with TTL."""

def invalidate_cache(self, key: str) -> None:
    """Invalidate specific cache entry."""
```
- **Dependencies**: Sprint 1 complete
- **Reference**: `.claude/collection_patterns.md` Cache Implementation

**8.2 Timestamp Tracking (Line 90)** - Status: ✅ Complete
```python
def get_last_update(self, data_type: str) -> Optional[datetime]:
    """Get last update timestamp for data type."""

def set_last_update(self, data_type: str, timestamp: datetime) -> None:
    """Set last update timestamp."""

def get_player_prices(self) -> dict[int, int]:
    """Get stored player prices for comparison."""

def save_player_prices(self, prices: dict[int, int]) -> None:
    """Save player prices for tracking changes."""
```
- **Dependencies**: 8.1 (cache management)
- **Reference**: `.claude/collection_patterns.md` Incremental Updates

**8.3 CSV Export (Line 91)** - Status: ✅ Complete
```python
def save_players_csv(self, players: list[Player]) -> None:
    """Export players to CSV."""

def save_fixtures_csv(self, fixtures: list[Fixture]) -> None:
    """Export fixtures to CSV."""

def export_to_dataframe(self, data: list[BaseModel]) -> pd.DataFrame:
    """Convert models to pandas DataFrame."""
```
- **Dependencies**: 1.1-1.5 (all models complete)

---

## Sprint 4: Polish & Integration (Week 4)

### Step 9: Utility Functions
**Priority**: LOW - Add as needed

#### `src/fpl/utils/helpers.py`

**9.1 Additional Utilities (Line 45)** - Status: ⏳ Pending
```python
def get_current_gameweek(events: list[Gameweek]) -> Optional[Gameweek]:
    """Find current active gameweek."""

def calculate_value(price: Decimal, points: int) -> Decimal:
    """Calculate points per million."""

def is_differential(ownership_pct: float, threshold: float = 5.0) -> bool:
    """Check if player is a differential (low ownership)."""

def get_team_name(team_id: int, teams: list[Team]) -> str:
    """Lookup team name by ID."""

def format_deadline(deadline: datetime) -> str:
    """Format deadline in human-readable form."""
```
- **Dependencies**: All models complete
- Add functions as patterns emerge during development

---

### Step 10: Integration Tests
**Priority**: MEDIUM - Verify end-to-end

#### `tests/integration/test_api_integration.py`

**10.1 More Integration Tests (Line 49)** - Status: ⏳ Pending
- Test all API endpoints with real data
- Test player summary endpoint
- Test manager endpoints
- Test league endpoints
- Test error scenarios (invalid IDs, not found)
- Test rate limiting in practice
- **Dependencies**: All Sprint 1-3 complete
- **Note**: Run sparingly to respect API limits

---

## Dependency Graph

```
Sprint 1 (Models & Basic Tests)
    ├── 1.1-1.5: Model Definitions
    └── 2.1-2.5: Model Tests
         └── 3.1-3.3: API Endpoints
              ├── Sprint 2 (Collections)
              │    ├── 4.1-4.2: Test Infrastructure
              │    ├── 5.1-5.2: Client Tests
              │    ├── 6.1: Player History
              │    └── 7.1: Fixture Filters
              │
              └── Sprint 3 (Storage)
                   ├── 8.1: Cache Management
                   ├── 8.2: Timestamp Tracking
                   │    └── 6.2: Incremental Updates
                   └── 8.3: CSV Export
                        └── Sprint 4 (Polish)
                             ├── 9.1: Utilities
                             └── 10.1: Integration Tests
```

---

## Status Legend

- ⏳ **Pending**: Not yet started
- 🔄 **In Progress**: Currently being implemented
- ✅ **Complete**: Implementation finished and tested
- ⚠️ **Blocked**: Waiting on dependencies

---

## Tracking Progress

### Sprint 1: Foundation ✅
- [x] 1.1 Player model
- [x] 1.2 Team model
- [x] 1.3 Gameweek model
- [x] 1.4 Fixture model
- [x] 1.5 PlayerHistory model
- [x] 2.1-2.5 Model tests
- [x] 3.1-3.3 API endpoints

### Sprint 2: Data Collection ✅
- [x] 4.1-4.2 Test infrastructure
- [x] 5.1-5.2 Client tests
- [x] 6.1-6.2 Player collector
- [x] 7.1 Fixture filters

### Sprint 3: Storage ✅
- [x] 8.1 Cache management
- [x] 8.2 Timestamp tracking
- [x] 8.3 CSV export

### Sprint 4: Polish
- [ ] 9.1 Utilities
- [ ] 10.1 Integration tests

---

## Notes

- **Priority order**: Models → API → Collectors → Storage → Utilities
- **Test as you go**: Write tests immediately after implementing features
- **Reference docs**: Always check `.claude/` docs for specifications
- **Integration tests**: Mark with `@pytest.mark.integration` and run sparingly

---

**Next Action**: Start Sprint 4, Step 9 (Polish & Integration)
