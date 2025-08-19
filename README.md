# FPL Optimiser

Local, learning-first FPL squad optimisation in Python. Fetches official FPL data, builds an optimal 15-man squad using MILP, then picks a starting XI.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
make all
```

This will:
- Fetch FPL API data and cache it locally.
- Build an optimal 15-man squad under budget and club limits.
- Select the best starting XI according to allowed formations.
- Write outputs to `output/` and an HTML report.

## Configuration

See `config.yaml`. Key options:

```yaml
budget: 100
max_per_team: 3
squad_size: 15
formations:
  - [3,4,3]
  - [3,5,2]
  - [4,4,2]
horizon: 1
transfer_limit: 1
transfer_cost: 4
cache_hours: 6
expected_points_model: fpl_ep_next    # options: fpl_ep_next, form_ppg_blend
data_dir: ./data
output_dir: ./output
logging:
  level: INFO
  file: fpl_optimizer.log
solver:
  backend: pulp
  time_limit: 60
```

## Expected Points Plugins

Choose with `expected_points_model`:

- `fpl_ep_next`: Uses official FPL `ep_next` field.
- `form_ppg_blend`: 0.6 × `form` + 0.4 × `points_per_game`.

Add your own by implementing `BaseEPModel` in `optimiser/expected_points.py` and referencing it in config.

## Make Targets

- `make data` → fetch & cache FPL data
- `make optimise` → solve the MILP and select XI
- `make visualise` → build HTML report + chart
- `make all` → end-to-end
- `make test` → run unit tests
- `make dev` → install dev deps + pre-commit

## CI & Pre-commit

- GitHub Actions workflow runs linting (ruff), formatting checks (black, isort), and tests on each push/PR.
- `pre-commit` hooks configured in `.pre-commit-config.yaml`.

## Learning Notes

- The solver (`optimiser/solver.py`) is annotated and kept minimal for clarity.
- Start by reading `scripts/optimise.py` to see how data flows into the LP.
- A notebook stub exists in `notebooks/explainer.ipynb` for you to add walkthroughs.
