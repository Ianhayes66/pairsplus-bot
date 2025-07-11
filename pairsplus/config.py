from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")  # Load .env early!

ALPACA_KEY = os.getenv("ALPACA_KEY")
ALPACA_SECRET = os.getenv("ALPACA_SECRET")

# Alpaca Paper Trading URL
BASE_URL = "https://paper-api.alpaca.markets"

# Where to save data
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Universe of stocks to trade
UNIVERSE = [
    "AAPL", "MSFT", "AMZN", "GOOGL", "META",
    "TSLA", "NVDA", "JPM", "V", "BAC"
]

# Backtest config
LOOKBACK_DAYS = 180
ROLLING_WINDOW = 60
Z_THRESHOLD = 1.5
