# FPL Optimiser Makefile
# Assumes Poetry environment is active

.PHONY: help setup data features forecast optimise_gw optimise_horizon select_horizon backtest report run_app clean

# Default target
help:
	@echo "FPL Multi-GW Optimiser Commands:"
	@echo "  setup           - Initialize project structure"
	@echo "  data            - Fetch and save raw FPL data"
	@echo "  features        - Clean data and engineer features"
	@echo "  forecast        - Generate expected points predictions"
	@echo "  optimise_gw N=X - Optimize squad for gameweek X"
	@echo "  optimise_horizon H=X - Optimize over X gameweeks"
	@echo "  select_horizon  - Find optimal planning horizon"
	@echo "  backtest        - Run historical strategy evaluation"
	@echo "  report          - Generate performance report"
	@echo "  run_app         - Launch CLI application"
	@echo "  clean           - Clean output files"
	@echo ""
	@echo "Usage: make [target] (ensure Poetry shell is active)"

# Setup project structure
setup:
	@echo "Setting up project directories..."
	mkdir -p data/raw data/features data/forecasts output src tests examples
	touch src/__init__.py tests/__init__.py
	@echo "Project structure created successfully!"
	@echo "Next: Run 'make data' to fetch FPL data"

# Phase 1: Data Collection
data:
	@echo "Fetching FPL data from API..."
	python src/data_collection.py
	@echo "✅ Data collection complete! Check data/raw/"
	@echo "Running comprehensive data validation..."
	python src/data_validation.py
	@echo "Next: Run 'make features' to engineer features"

# Phase 2: Feature Engineering
features:
	@echo "Engineering features from raw data..."
	python src/feature_engineering.py
	@echo "✅ Feature engineering complete! Check data/features/"
	@python -c "import pandas as pd; \
		df = pd.read_csv('data/features/features.csv'); \
		print(f'Features dataset: {len(df)} rows, {len(df.columns)} columns'); \
		assert len(df) >= 500, 'Features dataset too small'; \
		print('✅ Feature validation passed!')"

# Phase 3: Forecasting
forecast:
	@echo "Training forecasting model and generating predictions..."
	python src/forecasting.py
	@echo "✅ Forecasting complete! Check data/forecasts/"
	@python -c "import pandas as pd; \
		df = pd.read_csv('data/forecasts/expected_points.csv'); \
		print(f'Expected points: {len(df)} predictions'); \
		print('✅ Forecast validation passed!')"

# Phase 4: Single-GW Optimization
optimise_gw:
ifndef N
	$(error N is undefined. Usage: make optimise_gw N=1)
endif
	@echo "Optimizing squad for gameweek $(N)..."
	python src/single_gw_optimizer.py --gameweek $(N)
	@echo "✅ GW$(N) optimization complete! Check output/team_gw$(N).csv"

# Phase 5: Multi-GW Optimization
optimise_horizon:
ifndef H
	$(error H is undefined. Usage: make optimise_horizon H=3)
endif
	@echo "Optimizing over $(H) gameweeks..."
	python src/multi_gw_optimizer.py --horizon $(H)
	@echo "✅ Multi-GW optimization complete! Check output/plan_h$(H).csv"

# Phase 6: Horizon Selection
select_horizon:
	@echo "Finding optimal planning horizon..."
	python src/horizon_selection.py
	@echo "✅ Horizon selection complete! Check output/horizon_selection.json"

# Phase 7: Backtesting
backtest:
	@echo "Running backtesting evaluation..."
	python src/backtesting.py
	@echo "✅ Backtesting complete! Check output/backtest_results.csv"

# Phase 8: Reporting
report:
	@echo "Generating performance report..."
	python src/reporting.py
	@echo "✅ Report generated! Check output/report.md and output/report.pdf"

# Phase 9: CLI Application
run_app:
	@echo "Launching FPL Optimizer CLI..."
	python src/app.py --help
	@echo "Use: python src/app.py --squad input.json for full optimization"

# Utility commands
clean:
	@echo "Cleaning output files..."
	rm -rf output/*
	rm -rf data/features/*
	rm -rf data/forecasts/*
	@echo "✅ Cleanup complete!"

# Development helpers
validate:
	@echo "Running data validation..."
	python src/data_validation.py

format:
	@echo "Formatting code..."
	black src/ tests/
	isort src/ tests/
	@echo "✅ Code formatted!"

test:
	@echo "Running tests..."
	pytest tests/ -v
	@echo "✅ Tests complete!"

lint:
	@echo "Linting code..."
	flake8 src/ tests/ --max-line-length=88
	@echo "✅ Linting complete!"