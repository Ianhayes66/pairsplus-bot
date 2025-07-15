"""
pairsplus/data_io.py

Handles fetching historical bar data for tickers,
with optional local caching.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import os

from .config import DATA_DIR, LOOKBACK_DAYS, UNIVERSE

def fetch_bars(tickers=UNIVERSE, lookback=LOOKBACK_DAYS, interval="1d") -> pd.DataFrame:
    end = datetime.utcnow()
    start = end - timedelta(days=lookback)
    df = yf.download(
        tickers,
        start=start,
        end=end,
        interval=interval,
        group_by="ticker",
        auto_adjust=True,
        threads=True
    )
    closes = {t: df[t]["Close"].rename(t) for t in tickers}
    return pd.concat(closes, axis=1)

def get_cache_path(tickers, interval):
    tickers_str = "_".join(sorted(tickers))
    return os.path.join(DATA_DIR, f"bars_{tickers_str}_{interval}.csv")

def fetch_bars_cached(tickers=UNIVERSE, lookback=LOOKBACK_DAYS, interval="1d") -> pd.DataFrame:
    cache_path = get_cache_path(tickers, interval)
    if os.path.exists(cache_path):
        mtime = datetime.fromtimestamp(os.path.getmtime(cache_path))
        if (datetime.utcnow() - mtime).total_seconds() < 86400:
            return pd.read_csv(cache_path, index_col=0, parse_dates=True)
    df = fetch_bars(tickers, lookback, interval)
    df.to_csv(cache_path)
    return df