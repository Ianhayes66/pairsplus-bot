"""
pairsplus/config.py

Loads environment variables and defines global configuration constants
for the trading bot.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# --- Project directory ---
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Load .env variables early ---
load_dotenv(BASE_DIR / ".env")

# --- Alpaca Credentials ---
ALPACA_KEY = os.getenv("ALPACA_KEY")
ALPACA_SECRET = os.getenv("ALPACA_SECRET")
BASE_URL = "https://paper-api.alpaca.markets"

# --- Data Directory ---
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# --- Universe of Stocks ---
UNIVERSE = [
    "AAPL", "MSFT", "AMZN", "GOOGL", "META",
    "TSLA", "NVDA", "JPM", "V", "BAC"
]

# --- Backtesting Settings ---
LOOKBACK_DAYS = 180
ROLLING_WINDOW = 60
Z_THRESHOLD = 1.5

# --- Execution Settings from .env ---
ORDER_TYPE = os.getenv("ORDER_TYPE", "MARKET").strip().upper()
PEG_DISTANCE = float(os.getenv("PEG_DISTANCE", "0.05"))
SPLIT_NOTIONAL = os.getenv("SPLIT_NOTIONAL", "False").strip().lower() in ["true", "1", "yes"]
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "").strip()

