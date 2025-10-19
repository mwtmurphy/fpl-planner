# FPL Data Collection & Analysis

A Python toolkit for collecting and analyzing Fantasy Premier League (FPL) data from the official FPL API.

## Overview

This project provides a clean, type-safe interface for accessing FPL data including players, teams, gameweeks, fixtures, and manager information. Built with modern Python standards, it enables data analysis, team optimization, and custom FPL applications.

## Features

- **Comprehensive API Client**: Async HTTP client for all FPL endpoints
- **Type-Safe Models**: Pydantic models for players, teams, gameweeks, and more
- **Data Collection**: Modular collectors for different data sources
- **Analysis Tools**: Utilities for player performance analysis and team optimization
- **Well-Tested**: Unit and integration tests with pytest
- **Modern Python**: Python 3.11+ with full type hints and async/await support

## Installation

### Requirements

- Python 3.11+
- pyenv (for Python version management)
- poetry (for dependency management)

### Setup

```bash
# Clone repository
git clone <repository-url>
cd fpl

# Set Python version (using pyenv)
pyenv local 3.11.0

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

## Usage

### Basic Example

```python
from fpl.api.client import FPLClient
from fpl.core.models import Player, Team

# Initialize client
async with FPLClient() as client:
    # Get all players
    players = await client.get_players()

    # Get gameweek data
    gameweek = await client.get_gameweek(1)

    # Get team information
    teams = await client.get_teams()
```

### Data Collection

```python
from fpl.data.collectors import PlayerCollector

# Collect player data
collector = PlayerCollector()
players = await collector.collect_all()
```

See `scripts/` directory for more examples.

## Interactive Analysis Dashboard

The project includes a **Streamlit web app** for interactive FPL player analysis.

### Running the Dashboard

```bash
# Install Streamlit (if not already installed)
poetry add streamlit

# Run the app
poetry run streamlit run app/streamlit_app.py
```

The app will open in your browser at `http://localhost:8501`

### Dashboard Features

**Form Analysis Page**
- View all players sorted by current form (avg points over last 5 gameweeks)
- Filter by position (GK, DEF, MID, FWD)
- Filter by team
- Export analysis to CSV

**Value Analysis Page**
- View all players sorted by value (points per £m)
- Filter by position
- Filter by price bracket (Budget/Mid/Premium)
- Set minimum points threshold
- Export analysis to CSV

### Dashboard Usage

1. Navigate between pages using the sidebar
2. Apply filters to narrow your analysis
3. Sort tables by clicking column headers
4. Download filtered results as CSV
5. Data refreshes automatically every hour

## Development

### Commands

```bash
# Install dependencies (including dev)
poetry install

# Run tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=src --cov-report=html

# Format code
poetry run black src tests

# Lint code
poetry run ruff check src tests

# Type checking
poetry run mypy src

# Run all checks
poetry run black src tests && poetry run ruff check src tests && poetry run mypy src && poetry run pytest
```

### Project Structure

```
fpl/
├── src/fpl/
│   ├── core/          # Domain models (Player, Team, Gameweek, etc.)
│   ├── api/           # FPL API client and endpoints
│   ├── data/          # Data collection and storage
│   └── utils/         # Shared utilities
├── tests/             # Unit and integration tests
├── scripts/           # Example usage scripts
└── sql/               # SQL files for local database (optional)
```

## FPL API Reference

### Main Endpoints

- `GET /api/bootstrap-static/` - Core data (players, teams, gameweeks)
- `GET /api/fixtures/` - All fixtures
- `GET /api/element-summary/{id}/` - Player details and history
- `GET /api/event/{id}/live/` - Live gameweek data

See `.claude/fpl_api_reference.md` for comprehensive API documentation.

## Standards

This project follows workspace-level development standards:
- **Python Style**: PEP 8 compliant, formatted with Black (88 char line length)
- **Type Hints**: Required for all function signatures
- **Testing**: pytest with minimum 80% coverage
- **Architecture**: Layered architecture with separation of concerns
- **Documentation**: Google-style docstrings

See `~/projects/.claude/` for detailed workspace standards.

## Contributing

1. Follow conventional commits for commit messages
2. Ensure all tests pass before committing
3. Maintain test coverage above 80%
4. Run code formatters and linters

## License

MIT License

## Resources

- [Fantasy Premier League](https://fantasy.premierleague.com/)
- [FPL API Documentation](https://www.oliverlooney.com/blogs/FPL-APIs-Explained)
- [Workspace Standards](~/projects/.claude/)
