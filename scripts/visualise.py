
from __future__ import annotations
import argparse, json, logging
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

from optimiser.utils import load_config, setup_logging

def main():
    parser = argparse.ArgumentParser(description="Visualise chosen squad and starting XI.")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    args = parser.parse_args()

    cfg = load_config(args.config)
    setup_logging(cfg)
    logger = logging.getLogger("visualise")

    output_dir = Path(cfg.get("output_dir", "./output"))
    output_dir.mkdir(parents=True, exist_ok=True)

    squad_path = output_dir / "squad.csv"
    xi_path = output_dir / "starting_xi.csv"
    summary_path = output_dir / "summary.json"

    if not squad_path.exists() or not xi_path.exists():
        raise SystemExit("Missing outputs. Run `make optimise` first.")

    squad = pd.read_csv(squad_path)
    xi = pd.read_csv(xi_path)
    summary = json.load(open(summary_path)) if summary_path.exists() else {}

    plt.figure()
    ax = plt.gca()
    xi_sorted = xi.sort_values("exp_pts", ascending=True)
    ax.barh(xi_sorted["name"], xi_sorted["exp_pts"])
    ax.set_xlabel("Expected Points")
    ax.set_ylabel("Starting XI (sorted)")
    ax.set_title("Expected Points - Starting XI")
    fig_path = output_dir / "starting_xi_points.png"
    plt.tight_layout()
    plt.savefig(fig_path, dpi=180)
    plt.close()

    html = f"""
    <html><head><meta charset='utf-8'><title>FPL Optimiser Output</title></head>
    <body>
      <h1>FPL Optimiser Output</h1>
      <h2>Summary</h2>
      <pre>{json.dumps(summary, indent=2)}</pre>
      <h2>Starting XI</h2>
      {xi.to_html(index=False)}
      <img src="starting_xi_points.png" alt="Starting XI Points"/>
      <h2>Full Squad</h2>
      {squad.to_html(index=False)}
    </body>
    </html>
    """
    with open(output_dir / "report.html", "w") as f:
        f.write(html)
    print(f"Wrote {fig_path} and {output_dir/'report.html'}")

if __name__ == "__main__":
    main()
