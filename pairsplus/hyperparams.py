import json
from pathlib import Path

BEST_PARAMS_FILE = Path(__file__).parent.parent / "best_hyperparams.json"

def load_best_hyperparameters():
    if not BEST_PARAMS_FILE.exists():
        raise FileNotFoundError(f"Best hyperparameters file not found: {BEST_PARAMS_FILE}")
    with open(BEST_PARAMS_FILE) as f:
        return json.load(f)
