from __future__ import annotations
import logging, yaml
from pathlib import Path

def load_config(path: str | Path) -> dict:
    p = Path(path)
    with open(p, 'r') as f:
        return yaml.safe_load(f)

def setup_logging(cfg: dict) -> None:
    level = getattr(logging, str(cfg.get('logging', {}).get('level', 'INFO')).upper(), logging.INFO)
    log_file = cfg.get('logging', {}).get('file', None)
    logging.basicConfig(level=level,
                        filename=log_file,
                        format='%(asctime)s %(levelname)s %(name)s: %(message)s')
