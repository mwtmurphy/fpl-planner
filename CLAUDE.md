# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**FPL** is a Python toolkit for collecting and analyzing Fantasy Premier League data. Built with modern Python 3.11+ standards, it provides a clean, type-safe interface to the official FPL API for data analysis, team optimization, and custom applications.

### Development Status
- **Current Version**: 0.1.0 (Pre-release)
- **Phase**: Initial project setup complete
- **Next Steps**: Core API client implementation and data models
- **Breaking Changes**: Expected until 1.0.0 release

## Modern Development Stack (2025)

### Core Technologies
- **Python 3.11+**: Modern Python with latest type hint features
- **httpx**: Async HTTP client for API requests
- **Pydantic**: Type-safe data validation and models
- **pandas**: Data analysis and manipulation
- **pytest**: Testing framework with async support

### Key Dependencies
```bash
# Core
httpx pydantic pandas python-dotenv

# Development
pytest pytest-cov pytest-asyncio black ruff mypy pre-commit httpx-mock
```

### Development Tools
- **pyenv**: Python version management
- **poetry**: Dependency management and packaging
- **black**: Code formatting (88 char line length)
- **ruff**: Fast Python linter
- **mypy**: Static type checking

## Directory Structure

```
/fpl
├── pyproject.toml             # Poetry configuration
├── .python-version            # pyenv Python version
├── .editorconfig              # Editor configuration
├── .gitignore
├── README.md
├── CLAUDE.md                  # This file
├── /src/fpl/                  # Source code
│   ├── __init__.py
│   ├── /core/                 # Domain models
│   │   ├── __init__.py
│   │   └── models.py          # Player, Team, Gameweek, Fixture models
│   ├── /api/                  # API layer
│   │   ├── __init__.py
│   │   ├── client.py          # HTTP client
│   │   └── endpoints.py       # API endpoint constants
│   ├── /data/                 # Data access layer
│   │   ├── __init__.py
│   │   ├── collectors.py      # Data collection logic
│   │   └── storage.py         # Local data persistence
│   └── /utils/                # Shared utilities
│       ├── __init__.py
│       └── helpers.py
├── /tests/                    # Tests
│   ├── __init__.py
│   ├── conftest.py            # Pytest fixtures
│   ├── /unit/                 # Unit tests
│   │   ├── test_models.py
│   │   ├── test_client.py
│   │   └── test_collectors.py
│   └── /integration/          # Integration tests
│       └── test_api_integration.py
├── /scripts/                  # Example scripts and utilities
│   ├── example_usage.py
│   └── validate_streamlit_pages.py  # Streamlit validation
├── /app/                      # Streamlit dashboard
│   ├── __init__.py
│   ├── streamlit_app.py       # Main dashboard entry point
│   ├── /pages/                # Multi-page dashboard
│   │   ├── 1_📊_Form_Analysis.py
│   │   └── 2_💰_Value_Analysis.py
│   └── /utils/                # Dashboard utilities
│       ├── __init__.py
│       ├── data_loader.py
│       └── formatters.py
├── /sql/                      # SQL files (optional)
│   ├── /queries/
│   └── /schemas/
└── /.claude/                  # Project-specific standards
    ├── fpl_api_reference.md
    ├── data_models.md
    └── collection_patterns.md
```

## Development Commands

```bash
# Environment Setup
poetry install              # Install all dependencies
poetry shell                # Activate virtual environment

# Code Quality
poetry run black src tests          # Format code
poetry run ruff check src tests     # Lint code
poetry run ruff check --fix src tests  # Fix linting issues
poetry run mypy src                 # Type checking

# Testing
poetry run pytest                           # Run all tests
poetry run pytest tests/unit                # Run unit tests only
poetry run pytest tests/integration         # Run integration tests
poetry run pytest -v                        # Verbose output
poetry run pytest --cov=src                 # Run with coverage
poetry run pytest --cov=src --cov-report=html  # HTML coverage report

# Development Workflow
poetry run pre-commit install       # Install git hooks
poetry run pre-commit run --all-files  # Run all pre-commit hooks

# Streamlit Dashboard
poetry run streamlit run app/streamlit_app.py  # Run dashboard
poetry run python scripts/validate_streamlit_pages.py  # Validate pages
```

## FPL API Architecture

### API Client Design

The FPL API client follows these principles:
- **Async-first**: All API calls use async/await
- **Type-safe**: Full type hints with Pydantic models
- **Error handling**: Graceful handling of rate limits, timeouts, network errors
- **Caching**: Optional response caching to reduce API load
- **Rate limiting**: Respect API rate limits (no official limit documented, use conservative approach)

### Key API Endpoints

```python
# Core endpoints (see .claude/fpl_api_reference.md for full details)
BASE_URL = "https://fantasy.premierleague.com/api"

# Bootstrap-static: All core data
GET /bootstrap-static/
# Returns: players, teams, events (gameweeks), game settings

# Fixtures
GET /fixtures/
GET /fixtures/?event={gameweek_id}

# Player details
GET /element-summary/{player_id}/

# Live gameweek data
GET /event/{gameweek_id}/live/

# Manager data (requires manager ID)
GET /entry/{manager_id}/
GET /entry/{manager_id}/history/
GET /entry/{manager_id}/event/{gameweek_id}/picks/
```

### Data Models

Core domain models (see `.claude/data_models.md`):

```python
# Player: FPL player data
class Player:
    id, name, team, position, price, points, form, etc.

# Team: Premier League team
class Team:
    id, name, short_name, strength, etc.

# Gameweek (Event): FPL gameweek/event
class Gameweek:
    id, name, deadline, finished, highest_score, average_score, etc.

# Fixture: Premier League match
class Fixture:
    id, event, team_home, team_away, kickoff_time, stats, etc.
```

## Layered Architecture

This project follows workspace architecture standards with clear separation of concerns:

```
┌─────────────────────────────────┐
│  Scripts Layer                  │  ← Example usage, CLI tools
├─────────────────────────────────┤
│  Data Layer (Collectors)        │  ← Data collection orchestration
├─────────────────────────────────┤
│  API Layer (Client)             │  ← HTTP requests, response handling
├─────────────────────────────────┤
│  Core Layer (Models)            │  ← Domain models, business logic
└─────────────────────────────────┘
```

### Layer Responsibilities

**Core Layer** (`src/fpl/core/`)
- Pydantic models for type-safe data
- Domain entities: Player, Team, Gameweek, Fixture
- Business logic and validation rules
- No external dependencies (pure Python + Pydantic)

**API Layer** (`src/fpl/api/`)
- HTTP client using httpx
- Endpoint definitions and URL construction
- Response parsing and error handling
- Rate limiting and retry logic
- Depends on: Core layer

**Data Layer** (`src/fpl/data/`)
- Data collection orchestration
- Caching strategies
- Local storage (CSV, JSON, SQLite)
- Incremental updates
- Depends on: Core layer, API layer

**Scripts Layer** (`scripts/`)
- Example usage scripts
- CLI tools
- Data export utilities
- Depends on: All layers

## Async/Await Patterns

All API interactions use async/await:

```python
# Good: Async context manager
async with FPLClient() as client:
    players = await client.get_players()
    teams = await client.get_teams()

# Good: Concurrent requests
async with FPLClient() as client:
    players_task = client.get_players()
    teams_task = client.get_teams()
    players, teams = await asyncio.gather(players_task, teams_task)

# Bad: Blocking synchronous calls
client = FPLClient()
players = client.get_players()  # Don't do this
```

## Error Handling

Follow workspace error handling standards:

```python
from fpl.api.exceptions import FPLAPIError, RateLimitError, NotFoundError

# Good: Specific exception handling
try:
    player = await client.get_player(player_id)
except NotFoundError:
    logger.warning(f"Player {player_id} not found")
    return None
except RateLimitError:
    logger.error("Rate limit exceeded, waiting...")
    await asyncio.sleep(60)
    return await client.get_player(player_id)
except FPLAPIError as e:
    logger.error(f"API error: {e}")
    raise
```

## Testing Strategy

### Unit Tests
- Test individual functions and classes in isolation
- Mock external dependencies (HTTP client, API responses)
- Fast execution (< 1 second total)

```python
# tests/unit/test_client.py
import pytest
from httpx_mock import HTTPXMock
from fpl.api.client import FPLClient

@pytest.mark.asyncio
async def test_get_players(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json={"elements": [...]})
    async with FPLClient() as client:
        players = await client.get_players()
        assert len(players) > 0
```

### Integration Tests
- Test actual API interactions (use sparingly, respect rate limits)
- Test data flow through multiple layers
- Mark with `@pytest.mark.integration` for selective execution

```python
# tests/integration/test_api_integration.py
@pytest.mark.integration
@pytest.mark.asyncio
async def test_fetch_real_players():
    async with FPLClient() as client:
        players = await client.get_players()
        assert len(players) > 500  # FPL typically has 600+ players
```

### Test Coverage
- Minimum 80% coverage required
- Focus on core business logic and API client
- Use `pytest-cov` for coverage reporting

## Data Collection Patterns

See `.claude/collection_patterns.md` for detailed patterns, but key principles:

### Incremental Updates
```python
# Collect only new data since last update
last_update = load_last_update_timestamp()
new_data = await collector.collect_since(last_update)
```

### Caching Strategy
- Cache bootstrap-static data (updates infrequently)
- Cache player summaries (TTL: 1 hour during gameweek)
- Never cache live gameweek data (changes frequently)

### Rate Limiting
```python
# Conservative approach: max 10 requests per minute
from fpl.api.client import FPLClient

client = FPLClient(rate_limit=10)  # 10 req/min
```

## Common Development Tasks

### Adding a New API Endpoint

1. Add endpoint constant to `src/fpl/api/endpoints.py`
2. Add method to `FPLClient` in `src/fpl/api/client.py`
3. Create Pydantic model if needed in `src/fpl/core/models.py`
4. Write unit tests in `tests/unit/test_client.py`
5. Update `.claude/fpl_api_reference.md`

### Adding a New Data Model

1. Define Pydantic model in `src/fpl/core/models.py`
2. Add validation rules and business logic
3. Document fields and relationships in `.claude/data_models.md`
4. Write unit tests in `tests/unit/test_models.py`

### Creating a Data Collector

1. Create collector class in `src/fpl/data/collectors.py`
2. Inject dependencies (API client, storage)
3. Implement collection logic with error handling
4. Add caching and incremental update support
5. Write unit tests with mocked dependencies

## Workspace Standards Reference

This project follows workspace-level standards at `~/projects/.claude/`:
- **Python Style**: `python_style.md` - PEP 8, Black, type hints
- **Architecture**: `architecture_patterns.md` - Layered architecture, SOLID principles
- **Testing**: `testing_standards.md` - pytest, coverage, test patterns
- **Documentation**: `documentation_standards.md` - Docstrings, README format
- **Git Workflow**: `git_workflow.md` - Conventional commits, branching
- **Error Handling**: `error_handling.md` - Exceptions, logging
- **Environment**: `environment_setup.md` - pyenv, poetry setup
- **Streamlit**: `streamlit_standards.md` - Import patterns, validation, page structure

**Important**: Project-specific standards in `.claude/` extend (not duplicate) workspace standards.

## Type Hints

All code must include type hints following workspace standards:

```python
# Good: Full type hints
from typing import Optional
from collections.abc import Callable

async def fetch_player(
    player_id: int,
    include_history: bool = False
) -> Optional[Player]:
    """Fetch player by ID."""
    pass

def process_players(
    players: list[Player],
    filter_fn: Callable[[Player], bool]
) -> list[Player]:
    """Process players with filter function."""
    return [p for p in players if filter_fn(p)]
```

## Logging

Use Python's logging module with structured logging:

```python
import logging

logger = logging.getLogger(__name__)

# Good: Structured logging with context
logger.info("Fetching players", extra={"endpoint": "bootstrap-static"})
logger.error("API request failed", extra={"status_code": 500, "url": url})

# Configure in main/entry points
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```

## Environment Variables

Use `.env` for configuration (never commit to git):

```bash
# .env
FPL_CACHE_DIR=./data/cache
FPL_CACHE_TTL=3600
FPL_RATE_LIMIT=10
LOG_LEVEL=INFO
```

```python
# Load in code
from dotenv import load_dotenv
import os

load_dotenv()
cache_dir = os.getenv("FPL_CACHE_DIR", "./data/cache")
```

## Troubleshooting

### Common Issues

**Poetry not finding Python version**
```bash
pyenv local 3.11.0
poetry env use $(pyenv which python)
```

**Import errors**
```bash
# Ensure package is installed in editable mode
poetry install
```

**Type checking errors with Pydantic**
```bash
# Install pydantic plugin for mypy
poetry add --group dev pydantic[mypy]
```

**Async tests not running**
```bash
# Ensure pytest-asyncio is installed
poetry add --group dev pytest-asyncio
```

**API rate limiting**
- FPL API has no official rate limit documentation
- Use conservative approach: 10 requests per minute
- Implement exponential backoff on failures
- Cache responses where appropriate

## Development Workflow

### Initial Setup
```bash
# 1. Clone repository
cd /path/to/fpl

# 2. Set Python version
pyenv local 3.11.0

# 3. Install dependencies
poetry install

# 4. Install pre-commit hooks
poetry run pre-commit install

# 5. Verify setup
poetry run pytest
```

### Daily Development
```bash
# 1. Activate virtual environment
poetry shell

# 2. Make changes

# 3. Run formatters and linters
poetry run black src tests
poetry run ruff check --fix src tests

# 4. Run tests
poetry run pytest

# 5. Commit (hooks run automatically)
git commit -m "feat: add player comparison functionality"
```

### Streamlit Development Workflow

When working on the Streamlit dashboard:

```bash
# 1. Make changes to Streamlit files
# Edit app/streamlit_app.py or app/pages/*.py

# 2. REQUIRED: Validate pages after EVERY change
poetry run python scripts/validate_streamlit_pages.py

# 3. Fix any validation errors
# - Check import statements
# - Verify sys.path setup
# - Ensure no relative imports

# 4. Test manually
poetry run streamlit run app/streamlit_app.py
# - Click through all pages
# - Verify functionality
# - Check browser console for errors

# 5. Run tests
poetry run pytest tests/unit/test_app*.py

# 6. Commit only after validation passes
git add app/
git commit -m "feat: add new dashboard feature"
```

**CRITICAL**: The validation script (`scripts/validate_streamlit_pages.py`) **MUST** be run after any changes to Streamlit files. This ensures:
- All imports work correctly
- No relative imports are used
- sys.path setup is correct
- All pages can be loaded without errors

See `~/projects/.claude/streamlit_standards.md` for complete Streamlit development guidelines.

## Important Notes

### Development Phase (0.x.y)
- **Breaking changes are expected** and do not require major version bumps
- **Test thoroughly** before each commit
- **Integration tests** should be run sparingly to respect API rate limits
- **Documentation should reflect current capabilities**, not planned features

### General Best Practices
- **Always use type hints** for function signatures
- **Follow workspace Python style standards** (PEP 8, Black formatting)
- **Write tests first** for new features (TDD approach encouraged)
- **Document API changes** in `.claude/fpl_api_reference.md`
- **Use async/await** for all I/O operations
- **Handle errors gracefully** with specific exception types
- **Log important events** for debugging and monitoring
- **Cache API responses** to reduce load and improve performance

### Pre-1.0 Release Checklist
- [ ] Core API client implemented and tested
- [ ] All major FPL endpoints supported
- [ ] Data models complete with validation
- [ ] Comprehensive test suite with >80% coverage
- [ ] Documentation complete and accurate
- [ ] Example scripts demonstrating key features
- [ ] Performance optimization complete
- [ ] Error handling robust and user-friendly
