
from __future__ import annotations
import argparse, json, logging
from pathlib import Path
from datetime import datetime, timedelta
import requests

from optimiser.utils import load_config, setup_logging

BOOTSTRAP_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"
FIXTURES_URL = "https://fantasy.premierleague.com/api/fixtures/?future=1"

def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def read_json(path: Path) -> dict:
    with open(path, "r") as f:
        return json.load(f)

def is_fresh(path: Path, hours: int) -> bool:
    if not path.exists():
        return False
    mtime = datetime.fromtimestamp(path.stat().st_mtime)
    return datetime.now() - mtime < timedelta(hours=hours)

def fetch(url: str) -> dict:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json()

def main():
    parser = argparse.ArgumentParser(description="Fetch and cache FPL API data.")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    parser.add_argument("--force", action="store_true", help="Ignore cache and refetch")
    args = parser.parse_args()

    cfg = load_config(args.config)
    setup_logging(cfg)
    logger = logging.getLogger("fetch_data")

    data_dir = Path(cfg.get("data_dir", "./data"))
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    cache_hours = int(cfg.get("cache_hours", 6))

    bootstrap_path = raw_dir / "bootstrap-static.json"
    fixtures_path = raw_dir / "fixtures.json"

    try:
        if not args.force and is_fresh(bootstrap_path, cache_hours) and is_fresh(fixtures_path, cache_hours):
            logger.info("Using fresh cached data in %s", raw_dir)
            bootstrap = read_json(bootstrap_path)
            fixtures = read_json(fixtures_path)
        else:
            logger.info("Fetching FPL data...")
            bootstrap = fetch(BOOTSTRAP_URL)
            fixtures = fetch(FIXTURES_URL)
            write_json(bootstrap_path, bootstrap)
            write_json(fixtures_path, fixtures)
            logger.info("Saved raw data to %s", raw_dir)

        meta = {
            "fetched_at": datetime.now().isoformat(timespec="seconds"),
            "counts": {
                "elements": len(bootstrap.get("elements", [])),
                "teams": len(bootstrap.get("teams", [])),
                "fixtures": len(fixtures),
            }
        }
        write_json(processed_dir / "meta.json", meta)
        print(json.dumps(meta, indent=2))

    except requests.RequestException as e:
        logger.exception("Network error fetching FPL data: %s", e)
        if bootstrap_path.exists() and fixtures_path.exists():
            logger.warning("Falling back to cached data.")
            bootstrap = read_json(bootstrap_path)
            fixtures = read_json(fixtures_path)
            meta = {
                "fetched_at": datetime.now().isoformat(timespec="seconds"),
                "counts": {
                    "elements": len(bootstrap.get("elements", [])),
                    "teams": len(bootstrap.get("teams", [])),
                    "fixtures": len(fixtures),
                }
            }
            write_json(processed_dir / "meta.json", meta)
            print(json.dumps(meta, indent=2))
        else:
            raise SystemExit("No cached data available; try again later or use --force")

if __name__ == "__main__":
    main()
