# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Fantasy Premier League (FPL) multi-gameweek optimization tool that uses machine learning forecasting and mathematical optimization to maximize points across multiple gameweeks while managing transfers efficiently.

## Key Technologies

- **Python 3.9+** with Poetry for dependency management
- **Machine Learning**: XGBoost for expected points forecasting
- **Optimization**: PuLP for Mixed Integer Linear Programming (MILP)
- **Data Processing**: Pandas, NumPy for data manipulation
- **API Integration**: Requests for FPL API data collection
- **Testing**: Pytest for unit tests
- **Code Quality**: Black, isort, flake8

## Development Commands

### Setup and Installation
```bash
# Initialize project structure
make setup

# Install dependencies (requires Poetry)
poetry install
poetry shell
```

### Data Pipeline
```bash
# Complete data pipeline
make data          # Fetch FPL API data
make features      # Engineer features from raw data
make forecast      # Train ML model and generate predictions

# Data validation
make validate      # Validate data quality
```

### Optimization
```bash
# Single gameweek optimization
make optimise_gw N=15

# Multi-gameweek optimization
make optimise_horizon H=5

# Automatic horizon selection
make select_horizon
```

### Code Quality
```bash
make format        # Black + isort formatting
make lint          # Flake8 linting
make test          # Pytest unit tests
```

### Analysis and Reporting
```bash
make backtest      # Historical performance evaluation
make report        # Generate performance reports
make run_app       # Launch CLI application
```

### Utility
```bash
make clean         # Clean output files
make help          # Show available commands
```

## Architecture Overview

### Core Components

1. **Data Collection** (`src/data_collection.py`)
   - Fetches data from FPL API endpoints (bootstrap-static, fixtures, live gameweek data)
   - Handles rate limiting and retry logic
   - Saves structured CSV files to `data/raw/`

2. **Data Validation** (`src/data_validation.py`)
   - Comprehensive data quality checks
   - Validates player data, fixtures, and historical results
   - Ensures data integrity before processing

3. **Feature Engineering** (`src/feature_engineering.py`)
   - Processes raw data into ML-ready features
   - Creates rolling averages, fixture difficulty adjustments
   - Outputs to `data/features/`

4. **Forecasting** (`src/forecasting.py`)
   - XGBoost model for expected points prediction
   - Handles player form, fixture difficulty, minutes likelihood
   - Saves predictions to `data/forecasts/`

5. **Optimization Modules**
   - `single_gw_optimizer.py`: Single gameweek squad optimization
   - `multi_gw_optimizer.py`: Multi-gameweek transfer planning
   - `horizon_selection.py`: Dynamic planning period selection

6. **Analysis Tools**
   - `backtesting.py`: Historical strategy validation
   - `reporting.py`: Performance metrics and visualization
   - `app.py`: CLI interface for user interaction

### Data Flow

1. **Raw Data**: FPL API → `data/raw/*.csv`
2. **Features**: Raw data → `data/features/features.csv`
3. **Forecasts**: Features → `data/forecasts/expected_points.csv`
4. **Optimization**: Forecasts → `output/team_gw*.csv` or `output/plan_h*.csv`

### Key Constraints in Optimization Model

- Squad composition: 2 GK, 5 DEF, 5 MID, 3 FWD
- Budget limit: £100m total squad value
- Max 3 players per team
- Transfer limits: 1 free transfer + paid transfers (-4 points each)
- Chip usage restrictions (Wildcard, Bench Boost, Triple Captain)

## File Structure

```
src/
├── data_collection.py     # FPL API data fetching
├── data_validation.py     # Data quality validation
├── feature_engineering.py # Feature creation for ML
├── forecasting.py         # XGBoost predictions
├── single_gw_optimizer.py # Single gameweek optimization
├── multi_gw_optimizer.py  # Multi-gameweek planning
├── horizon_selection.py   # Dynamic horizon selection
├── backtesting.py         # Historical validation
├── reporting.py           # Performance analysis
└── app.py                 # CLI interface

data/
├── raw/                   # Raw FPL API data
├── features/              # Processed ML features
└── forecasts/             # Model predictions

output/                    # Optimization results
tests/                     # Unit tests
examples/                  # Usage examples
```

## Development Notes

- The project uses Poetry for dependency management - ensure `poetry shell` is active
- All data processing is pipeline-based - run steps sequentially (data → features → forecast → optimize)
- The optimization uses MILP with PuLP - solutions may take several minutes for multi-gameweek horizons
- FPL API has rate limits - data collection includes automatic retry logic and delays
- Code follows Black formatting with 88-character line length
- Use `make validate` to ensure data quality before proceeding to feature engineering

## Testing Strategy

- Unit tests focus on data validation, feature engineering logic, and optimization constraints
- Use `pytest tests/ -v` for detailed test output
- Mock FPL API responses for reliable testing
- Validate optimization solutions meet all FPL constraints