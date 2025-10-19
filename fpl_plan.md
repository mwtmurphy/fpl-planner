
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
**Objective:** Prepare clean dataset with engineered features.

**Explicit Instructions:**
1. Load raw CSVs from `data/raw/`.
2. Clean and normalize data:
   - Standardize player IDs and team IDs.
   - Replace missing minutes/points with 0.
   - Drop irrelevant columns.
3. Engineer features for modelling:
   - Rolling averages for goals, assists, clean sheets over last 3-5 GWs.
   - Fixture difficulty-adjusted expected points.
   - Estimate minutes likelihood based on historical play.
4. Save processed dataset to `data/features/features.csv`.
5. Validate row count ≥10,000 (players × GWs).

**Command:**

```bash
make features
```

---

## 📍 Checkpoint 3: Forecasting Expected Points
**Objective:** Predict expected FPL points per player per GW.

**Explicit Instructions:**
1. Split dataset into train/validate/test:
   - Train: 2018–21, Validate: 21/22, Test: 22/23.
2. Train a regression model (XGBoost or scikit-learn linear regressor).
3. Input features: rolling form, fixture difficulty, minutes likelihood.
4. Output expected points CSV: `data/forecasts/expected_points.csv`.
5. Validate correlation with actual points >0.5 on validation set.

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

✅ This plan is fully explicit, checkpointed, and uses **Poetry** for environment management. Each Makefile command can be executed in the Poetry environment.
