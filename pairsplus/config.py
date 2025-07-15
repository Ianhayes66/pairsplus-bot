"""
pairsplus/config.py

Loads and validates environment variables for the trading bot.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env
load_dotenv(BASE_DIR / ".env")

def get_env_var(name: str) -> str:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        raise EnvironmentError(
            f"⚠️ Missing required environment variable: {name}. "
            f"Check your .env file or environment settings."
        )
    return value

# --- Required Secrets ---
ALPACA_KEY = get_env_var("ALPACA_KEY")
ALPACA_SECRET = get_env_var("ALPACA_SECRET")
DISCORD_WEBHOOK_URL = get_env_var("DISCORD_WEBHOOK_URL")

# --- Execution Config ---
ORDER_TYPE = get_env_var("ORDER_TYPE").upper()
PEG_DISTANCE = float(get_env_var("PEG_DISTANCE"))
SPLIT_NOTIONAL = float(get_env_var("SPLIT_NOTIONAL"))

# --- Strategy / Signal Parameters ---
LOOKBACK_DAYS = int(get_env_var("LOOKBACK_DAYS"))
ROLLING_WINDOW = int(get_env_var("ROLLING_WINDOW"))
Z_THRESHOLD = float(get_env_var("Z_THRESHOLD"))
KALMAN_COV = float(get_env_var("KALMAN_COV"))

# --- Infra / Monitoring ---
METRICS_PORT = int(get_env_var("METRICS_PORT"))
POLLING_INTERVAL_MINUTES = int(get_env_var("POLLING_INTERVAL_MINUTES"))

# --- Static ---
BASE_URL = "https://paper-api.alpaca.markets"
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

UNIVERSE = [
    "AAPL", "MSFT", "AMZN", "GOOGL", "META",
    "TSLA", "NVDA", "JPM", "V", "BAC"
]