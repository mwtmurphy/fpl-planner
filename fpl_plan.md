
# 🚀 Fantasy Premier League (FPL) Multi-GW Optimisation Model Build Plan (Poetry Version)

This document provides a **fully explicit step-by-step implementation plan** with checkpoints, instructions, and command-line verification commands (via Makefile) using **Poetry** as the package manager.

---

## 📦 Environment Setup with Poetry
**Objective:** Ensure reproducible environment for all scripts.

**Instructions:**

1. Install Poetry if not already installed:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. Initialize a Poetry project and add dependencies:

```bash
poetry init --name fpl-optimiser --dependency requests --dependency pandas --dependency numpy --dependency scikit-learn --dependency pulp --dependency duckdb --dependency typer --dev-dependency pytest --dev-dependency black --dev-dependency isort
```

3. Install all dependencies:

```bash
poetry install
```

4. Activate the Poetry shell to run all scripts:

```bash
poetry shell
```

All further commands assume the Poetry environment is active.

---

## 📍 Checkpoint 1: Data Collection
**Objective:** Gather official FPL data into structured local files.

**Explicit Instructions:**  
1. Fetch JSON data from FPL API endpoints:  
   - `bootstrap-static` → players, teams, positions.  
   - `fixtures` → fixture dates, teams, difficulty ratings.  
   - `event/{GW}/live` → weekly player scores.  
2. Use `requests` + `pandas` to parse JSON into DataFrames.  
3. Save three CSVs to `data/raw/`: `players.csv`, `fixtures.csv`, `results.csv`.  
4. Ensure columns follow snake_case convention.  
5. Validate: `players.csv` has >500 rows, `fixtures.csv` >380 rows, `results.csv` >10,000 rows.  

**Command:**

```bash
make data
```

---

## 📍 Checkpoint 2: Data Cleaning & Feature Engineering
**Objective:** Prepare clean dataset with anti-leakage engineered features for realistic ML modeling.

**Explicit Instructions:**  
1. **Data Loading & Cleaning:**
   - Load raw CSVs from `data/raw/`
   - Standardize player IDs and team IDs
   - Replace missing minutes/points with 0, ensure non-negative values
   - Drop irrelevant columns and handle data quality issues

2. **Anti-Leakage Feature Engineering:**
   - **Lagged Rolling Features**: Create rolling averages (3, 5 GW windows) that EXCLUDE current gameweek
     - `total_points_rolling_3_lag`, `goals_scored_rolling_3_lag`, etc.
     - Use `.shift(1)` to prevent data leakage in temporal prediction
   - **Current Rolling Features**: Also create current-inclusive versions for comparison/debugging
   - **Minutes Likelihood**: Historical probability of getting minutes based on past performance
   
3. **Temporal & Context Features:**
   - **Fixture Difficulty**: Use upcoming match difficulty, not current match results
   - **Form Metrics**: Points consistency, goal involvement, efficiency ratios
   - **Position & Price**: Static player attributes for model context

4. **Output & Validation:**
   - Save processed dataset to `data/features/features.csv`
   - Validate: sufficient rows for modeling (≥500 for limited data, ≥10,000 ideal)
   - Ensure lagged features have proper null handling for first gameweeks  

**Testing Requirements:**
- Unit tests for data cleaning logic (missing value handling, data type validation)
- Test anti-leakage feature creation (verify lagged features exclude current GW)
- Test rolling feature calculations with edge cases (single GW, insufficient data)
- Test fixture difficulty mapping and feature creation
- Test minutes likelihood probability calculations
- Mock data pipeline integration tests

**Command:**

```bash
make features
```

---

## 📍 Checkpoint 3: Forecasting Expected Points
**Objective:** Predict expected FPL points per player per GW using realistic validation.

**Explicit Instructions:**  
1. **Data Collection & Temporal Validation:**
   - Collect multiple gameweeks of data for proper time-series validation
   - Use time-shifted validation: train on GW 1-(n-1), predict GW n
   - Implement leave-one-gameweek-out cross-validation for robust assessment
   
2. **Feature Engineering (Anti-Leakage):**
   - **Lagged rolling features:** exclude current GW from rolling averages
   - **Forward-only features:** use only past performance to predict future
   - **Temporal features:** fixture difficulty for upcoming matches, not current
   
3. **Model Training:**
   - Train XGBoost or RandomForest regression model
   - Input features: lagged rolling form, upcoming fixture difficulty, minutes likelihood
   - Hyperparameter tuning with time-aware cross-validation
   
4. **Realistic Validation:**
   - **Target correlation: 0.3-0.6** (industry-realistic for FPL prediction)
   - **Expected R²: 0.1-0.4** (typical for sports forecasting)
   - **RMSE target: 2-4 points** (realistic prediction error)
   - Validate on genuinely unseen future gameweeks
   
5. **Output:**
   - Generate predictions for next gameweek using only historical data
   - Save to `data/forecasts/expected_points.csv` with confidence intervals
   - Include model uncertainty and prediction intervals  

**Testing Requirements:**
- Unit tests for data loading and preparation (features.csv validation)
- Test temporal data splitting (time-based vs player-based splits)
- Mock model training with synthetic data (XGBoost and RandomForest fallback)
- Test prediction generation and validation metrics
- Test cross-validation implementation (leave-one-gameweek-out)
- Test feature importance analysis and output validation
- Integration tests for complete forecasting pipeline
- Test error handling for missing data and edge cases

**Command:**

```bash
make forecast
```

---

## 📍 Checkpoint 4: Single-GW Optimisation
**Objective:** Optimise squad selection for one GW using MILP.

**Explicit Instructions:**  
1. Use `PuLP` to define binary decision variables for each player (`x[player]=1 if selected`).  
2. Constraints:  
   - Squad size = 15  
   - Positions: 2 GK, 5 DEF, 5 MID, 3 FWD  
   - ≤3 players per team  
   - Budget ≤ £100m  
3. Objective: Maximise sum(expected_points × x[player]).  
4. Save selected squad: `output/team_gw{N}.csv`.  
5. Validate: Exactly 15 players selected, budget within limit.  

**Testing Requirements:**
- Unit tests for MILP model setup and constraint validation
- Test squad composition constraints (positions, team limits, budget)
- Test optimization objective function and solver integration
- Test solution validation and output formatting
- Test edge cases (no feasible solution, budget constraints)
- Mock data tests with known optimal solutions

**Command:**

```bash
make optimise_gw N=1
```

---

## 📍 Checkpoint 5: Multi-GW Optimisation
**Objective:** Optimise squad across multiple GWs with transfers and chips.

**Explicit Instructions:**  
1. Extend MILP with transfer variables:  
   - Binary `y[player, GW] = 1 if player in squad that GW`.  
   - Transfer constraints: 1 free transfer per GW, extra transfers = -4 points.  
   - Include chips: wildcard, bench boost, triple captain.  
2. Maximise cumulative expected points over horizon H.  
3. Save transfer plan + weekly squads: `output/plan_h{H}.csv`.  
4. Validate: Constraints (budget, positions, transfers) respected.  

**Testing Requirements:**
- Unit tests for multi-GW MILP model setup and transfer constraints
- Test transfer cost calculations and free transfer logic
- Test chip usage constraints and point bonuses
- Test horizon-based optimization objective
- Test squad continuity between gameweeks
- Test output validation for multi-gameweek plans
- Integration tests with forecasting data

**Command:**

```bash
make optimise_horizon H=3
```

---

## 📍 Checkpoint 6: Horizon Selection Meta-Model
**Objective:** Choose optimal horizon dynamically.

**Explicit Instructions:**  
1. Run multi-GW optimisation for H = 1..8.  
2. Score horizons with:  

```
Score(H) = λ * ExpectedPoints - β * TransferHits - δ * Variance - γ * Instability
```

3. Default weights: λ=1, β=1, δ=0.5, γ=0.5.  
4. Select horizon H with highest score.  
5. Save JSON: `output/horizon_selection.json`.  
6. Validate: JSON contains `"best_horizon": <int>`.  

**Command:**

```bash
make select_horizon
```

---

## 📍 Checkpoint 7: Backtesting Loop
**Objective:** Evaluate strategy on past seasons.

**Explicit Instructions:**  
1. Start from template squad.  
2. Week-by-week: apply optimisation + dynamic horizon.  
3. Track: realised points, transfers, chip usage.  
4. Save results: `output/backtest_results.csv`.  
5. Validate: file contains weekly points and cumulative points.  

**Command:**

```bash
make backtest
```

---

## 📍 Checkpoint 8: Evaluation & Reporting
**Objective:** Generate performance report.

**Explicit Instructions:**  
1. Compare dynamic horizon vs fixed horizons (H=3,5) and optimiser vs baseline.  
2. Metrics: total points, average weekly points, transfer efficiency, chip ROI.  
3. Generate tables and plots (Matplotlib).  
4. Save report: `output/report.md` and `output/report.pdf`.  
5. Validate: report includes plots + summary tables.  

**Command:**

```bash
make report
```

---

## 📍 Checkpoint 9: Deployment & UX
**Objective:** Provide user interface for optimisation tool.

**Explicit Instructions:**  
1. CLI using `typer`/`argparse` for input (current squad, budget, chips).  
2. Output: transfer plan, recommended squad, horizon, projected points.  
3. Optionally wrap as Flask API or Streamlit app.  
4. Save outputs as JSON/CSV in `output/`.  
5. Validate CLI runs:  

```bash
poetry run python src/app.py --squad input.json
```

**Command:**

```bash
make run_app
```

---

## 📍 Testing Standards & Best Practices

**Testing Philosophy:**
- **Comprehensive Coverage**: All phases require robust unit tests covering core functionality
- **Anti-Leakage Validation**: Critical tests to ensure temporal data integrity in ML pipeline
- **Edge Case Handling**: Tests for insufficient data, missing files, and constraint violations
- **Integration Testing**: End-to-end pipeline validation with mock data
- **Realistic Expectations**: Test targets aligned with FPL forecasting industry standards

**Test Organization:**
- `tests/test_feature_engineering.py` - Phase 2 feature engineering tests
- `tests/test_forecasting.py` - Phase 3 ML forecasting tests  
- `tests/test_single_gw_optimizer.py` - Phase 4 single GW optimization tests
- `tests/test_multi_gw_optimizer.py` - Phase 5 multi-GW optimization tests
- `tests/test_horizon_selection.py` - Phase 6 horizon selection tests
- `tests/test_integration.py` - End-to-end pipeline integration tests

**Key Testing Commands:**
```bash
make test           # Run all unit tests
make test_coverage  # Generate coverage report
pytest tests/ -v    # Verbose test output
```

**Quality Gates:**
- All phases must have >80% test coverage before implementation
- Tests must pass before any optimization phase begins
- Critical path validation for data pipeline integrity
- Performance benchmarks for optimization solve times

---

✅ This plan is fully explicit, checkpointed, and uses **Poetry** for environment management. Each Makefile command can be executed in the Poetry environment.
