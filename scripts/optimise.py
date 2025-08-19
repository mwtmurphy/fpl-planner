
from __future__ import annotations
import argparse, json, logging
from pathlib import Path
import pandas as pd
import pulp

from optimiser.utils import load_config, setup_logging
from optimiser.solver import build_squad_lp, extract_solution, pick_starting_xi
from optimiser.expected_points import get_ep_model

def load_json(path: Path) -> dict:
    with open(path, "r") as f:
        return json.load(f)

def main():
    parser = argparse.ArgumentParser(description="Run FPL squad optimiser for a single GW.")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    args = parser.parse_args()

    cfg = load_config(args.config)
    setup_logging(cfg)
    logger = logging.getLogger("optimise")

    data_dir = Path(cfg.get("data_dir", "./data"))
    output_dir = Path(cfg.get("output_dir", "./output"))
    raw_dir = data_dir / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)

    bootstrap_p = raw_dir / "bootstrap-static.json"
    fixtures_p = raw_dir / "fixtures.json"
    if not bootstrap_p.exists():
        raise SystemExit("Missing bootstrap data. Run `make data` first.")
    elements = pd.DataFrame(load_json(bootstrap_p)["elements"])
    teams = pd.DataFrame(load_json(bootstrap_p)["teams"])[["id","name","short_name"]].rename(columns={"id":"team_id"})
    fixtures = pd.DataFrame(load_json(fixtures_p)) if fixtures_p.exists() else pd.DataFrame()

    players = elements[["id","first_name","second_name","team","element_type","now_cost","ep_next","form","points_per_game"]].copy()
    players["name"] = players["first_name"].str.cat(players["second_name"], sep=" ")
    players = players.merge(teams, left_on="team", right_on="team_id", how="left")

    ep_name = cfg.get("expected_points_model", "fpl_ep_next")
    ep_model = get_ep_model(ep_name)
    players["exp_pts"] = ep_model.compute(players, fixtures, cfg.get("horizon", 1), cfg)

    budget = float(cfg.get("budget", 100))
    max_per_team = int(cfg.get("max_per_team", 3))
    model, x = build_squad_lp(players, budget_m=budget, max_per_team=max_per_team)
    status = model.solve(pulp.PULP_CBC_CMD(msg=False))
    logger.info("Solver status: %s", pulp.LpStatus[status])
    if pulp.LpStatus[status] != "Optimal":
        raise SystemExit(f"Optimiser did not find an optimal solution. Status={pulp.LpStatus[status]}")

    squad = extract_solution(players, x).sort_values(["element_type","exp_pts"], ascending=[True, False])
    formations = cfg.get("formations", [[3,4,3],[3,5,2],[4,4,2]])
    xi, formation_used = pick_starting_xi(squad, formations)

    xi = xi.copy()
    xi["is_captain"] = 0
    if not xi.empty:
        cap_idx = xi["exp_pts"].idxmax()
        xi.loc[cap_idx, "is_captain"] = 1

    squad_path = output_dir / "squad.csv"
    xi_path = output_dir / "starting_xi.csv"
    squad[["name","short_name","element_type","now_cost","exp_pts"]].to_csv(squad_path, index=False)
    xi[["name","short_name","element_type","now_cost","exp_pts","is_captain"]].to_csv(xi_path, index=False)

    summary = {
        "formation_used": formation_used,
        "total_expected_points_xi": float(xi["exp_pts"].sum() if not xi.empty else 0.0),
        "captain": (xi[xi["is_captain"]==1]["name"].iloc[0] if (xi["is_captain"]==1).any() else None),
        "ep_model": ep_name,
    }
    with open(output_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
