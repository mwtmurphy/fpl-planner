# 🚀 Fantasy Premier League Multi-GW Optimiser

An advanced FPL squad optimization tool that uses machine learning forecasting and mathematical optimization to maximize points across multiple gameweeks while managing transfers efficiently.

## 🎯 Features

- **Multi-Gameweek Planning**: Optimize across 1-8 gameweek horizons
- **Dynamic Horizon Selection**: Automatically choose optimal planning period
- **Transfer Strategy**: Intelligent transfer planning with hit minimization
- **Chip Strategy**: Optimal timing for Wildcard, Bench Boost, Triple Captain
- **Machine Learning**: XGBoost forecasting for expected points
- **Historical Backtesting**: Validate strategies on past seasons
- **CLI Interface**: Easy-to-use command line application

## 🛠️ Installation

### Prerequisites
- Python 3.9+
- Poetry package manager

### Setup

1. **Install Poetry** (if not already installed):
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. **Clone and setup project**:
```bash
git clone <repository-url>
cd fpl-optimiser
poetry install
poetry shell
```

3. **Initialize project structure**:
```bash
make setup
```

## 🚀 Quick Start

Run the complete optimization pipeline:

```bash
# 1. Fetch latest FPL data
make data

# 2. Engineer features
make features

# 3. Train forecasting model
make forecast

# 4. Optimize for next gameweek
make optimise_gw N=1

# 5. Or optimize over multiple gameweeks
make optimise_horizon H=3

# 6. Find optimal horizon automatically
make select_horizon

# 7. Run CLI application
make run_app
```

## 📊 Usage Examples

### Single Gameweek Optimization
```bash
make optimise_gw N=15  # Optimize for GW15
```

### Multi-Gameweek Optimization
```bash
make optimise_horizon H=5  # Plan over 5 gameweeks
```

### Backtesting
```bash
make backtest  # Test strategy on historical data
make report    # Generate performance report
```

### CLI Application
```bash
python src/app.py --squad current_team.json --budget 1.5 --chips wildcard
```

## 📁 Project Structure

```
fpl-optimiser/
├── src/                    # Source code
│   ├── data_collection.py  # FPL API data fetching
│   ├── feature_engineering.py
│   ├── forecasting.py      # ML predictions
│   ├── single_gw_optimizer.py
│   ├── multi_gw_optimizer.py
│   ├── horizon_selection.py
│   ├── backtesting.py
│   ├── reporting.py
│   └── app.py              # CLI interface
├── data/
│   ├── raw/               # Raw FPL data
│   ├── features/          # Processed features
│   └── forecasts/         # ML predictions
├── output/                # Optimization results
├── tests/                 # Unit tests
├── Makefile              # Build commands
└── pyproject.toml        # Dependencies
```

## 📈 Optimization Model

The optimizer uses Mixed Integer Linear Programming (MILP) with:

**Objective**: Maximize expected points over planning horizon

**Constraints**:
- Squad composition (2 GK, 5 DEF, 5 MID, 3 FWD)
- Budget limit (£100m)
- Max 3 players per team
- Transfer limits (1 free + paid transfers)
- Chip usage restrictions

**Features**:
- Rolling form averages
- Fixture difficulty adjustments  
- Minutes played likelihood
- Price change predictions

## 🎯 Strategy Components

1. **Forecasting**: XGBoost model predicts expected points
2. **Single-GW**: Optimal squad for one gameweek
3. **Multi-GW**: Transfer strategy across multiple gameweeks
4. **Horizon Selection**: Dynamic planning period optimization
5. **Backtesting**: Historical performance validation

## 📊 Performance Metrics

- Total points vs baseline strategies
- Transfer efficiency (points per transfer)
- Chip ROI (return on investment)
- Weekly consistency (variance analysis)

## 🔧 Development

### Code Quality
```bash
make format  # Black + isort formatting
make lint    # Flake8 linting
make test    # Pytest unit tests
```

### Data Pipeline
```bash
make clean   # Clean output files
make data    # Refresh FPL data
make features # Re-engineer features
```

## 📝 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📞 Support

- Open an issue for bugs/feature requests
- Check existing issues before creating new ones
- Provide detailed information for reproducibility

---

**Built with**: Python, Poetry, PuLP, XGBoost, Pandas, NumPy