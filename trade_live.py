"""
pairsplus/trade_live.py

Advanced trading loop with position management, logging, and Alpaca integration.
"""

import asyncio
import time
import schedule
import os
import json
from pathlib import Path
from pairsplus import data_io, pairs, signals, execution

# --------- POSITION TRACKING ---------
POSITIONS_FILE = Path("positions.json")
positions = {}

def load_positions():
    global positions
    if POSITIONS_FILE.exists():
        with open(POSITIONS_FILE, "r") as f:
            positions = json.load(f)
    else:
        positions = {}

def save_positions():
    with open(POSITIONS_FILE, "w") as f:
        json.dump(positions, f, indent=2)

def open_trade(pair, side):
    positions[f"{pair[0]}_{pair[1]}"] = side
    save_positions()

def close_trade(pair):
    key = f"{pair[0]}_{pair[1]}"
    if key in positions:
        del positions[key]
        save_positions()

def is_open(pair):
    return f"{pair[0]}_{pair[1]}" in positions or f"{pair[1]}_{pair[0]}" in positions

# --------- LOGGING TRADES ----------
TRADE_LOG = Path("trade_log.txt")

def log_trade(event, pair, side, zscore=None):
    with open(TRADE_LOG, "a") as f:
        f.write(
            f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {event} | Pair: {pair} | Side: {side} | Z: {zscore}\n"
        )

# ----------- Alpaca websocket version ------------
try:
    from alpaca.data.live import StockDataStream
except ImportError:
    StockDataStream = None  # if alpaca-py isn't installed yet

ALPACA_KEY = os.getenv("ALPACA_KEY")
ALPACA_SECRET = os.getenv("ALPACA_SECRET")

async def run_websocket_live():
    """
    Use Alpaca's websocket stream to receive live bars in real time.
    """
    if not StockDataStream:
        raise ImportError("alpaca-py package is required for websocket mode.")

    stream = StockDataStream(ALPACA_KEY, ALPACA_SECRET)
    from pairsplus.config import UNIVERSE

    for symbol in UNIVERSE:
        @stream.on_bar(symbol)
        async def handle_bar(bar):
            print(f"[Websocket] Received bar for {bar.symbol}")
            await process_live_bar(bar.symbol)

    print("[Websocket] Starting event loop.")
    await stream.run()

async def process_live_bar(symbol):
    """
    Handle new bar (websocket mode).
    """
    print(f"[Websocket] Processing new bar for {symbol}")
    run_trading_logic()

# ---------- Core Trading Logic ----------
def run_trading_logic():
    """
    This is the shared core logic for polling and websocket modes.
    """
    print("[Trading] Fetching bars and computing signals...")
    df = data_io.fetch_bars(interval="1h", lookback=90)
    best_pairs = pairs.find_cointegrated(df, max_pairs=5)

    for _, row in best_pairs.iterrows():
        a = row["a"]
        b = row["b"]
        spread_df = df[[a, b]]
        sig = signals.signal_from_spread(spread_df, a, b)

        pair_key = (a, b)

        if sig:
            # ENTRY
            if not is_open(pair_key):
                if sig["action"] == "LONG_SPREAD":
                    print(f"🚀 Opening LONG_SPREAD: {a} - {b}")
                    execution.place_pair_trade(a, b)
                    open_trade(pair_key, "LONG_SPREAD")
                    log_trade("ENTRY", pair_key, "LONG_SPREAD", sig["z"])
                elif sig["action"] == "SHORT_SPREAD":
                    print(f"🚀 Opening SHORT_SPREAD: {b} - {a}")
                    execution.place_pair_trade(b, a)
                    open_trade(pair_key, "SHORT_SPREAD")
                    log_trade("ENTRY", pair_key, "SHORT_SPREAD", sig["z"])
            else:
                print(f"✅ Position already open for {pair_key}. Skipping duplicate entry.")
        else:
            # EXIT LOGIC
            if is_open(pair_key):
                print(f"⚡ Spread mean-reverted. Exiting {pair_key}")
                # You would implement execution.close_pair_trade() here
                close_trade(pair_key)
                log_trade("EXIT", pair_key, "CLOSE", None)

# ------------- Old schedule-based polling ------------
def schedule_polling_loop():
    """
    Cron-like polling loop.
    """
    load_positions()

    def job():
        print("[Polling] Running trading job...")
        run_trading_logic()

    polling_interval = int(os.getenv("POLLING_INTERVAL_MINUTES", "60"))
    schedule.every(polling_interval).minutes.do(job)

    print(f"[Polling] Starting schedule loop every {polling_interval} minutes.")
    while True:
        schedule.run_pending()
        time.sleep(30)

# ------------- CLI entrypoint ------------
if __name__ == "__main__":
    mode = os.getenv("LIVE_MODE", "websocket").lower()
    if mode == "polling":
        schedule_polling_loop()
    else:
        asyncio.run(run_websocket_live())
