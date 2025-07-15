"""
pairsplus/trade_live.py

Advanced trading loop with position management,
Alpaca integration, Discord notifications, and
Prometheus metrics server.
"""

import asyncio
import time
import schedule
import json
from pathlib import Path

from pairsplus import data_io, pairs, signals, execution
from pairsplus.notifier import send_discord_message
from pairsplus.hyperparams import load_best_hyperparameters
from pairsplus.config import (
    ALPACA_KEY,
    ALPACA_SECRET,
    METRICS_PORT,
    POLLING_INTERVAL_MINUTES,
    LIVE_MODE,
    UNIVERSE
)

from prometheus_client import start_http_server, Counter

# ----------------- SSL / Certificates -----------------
import ssl
import certifi

try:
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    ssl._create_default_https_context = ssl.create_default_context
except Exception as e:
    print(f"[SSL Warning] Could not set certifi SSL context: {e}")
    send_discord_message("⚠️ SSL certificates might not be verified correctly.")

# ----------------- Prometheus Metrics -----------------
TRADES_PROCESSED = Counter("trades_processed_total", "Number of trade logic cycles run")
ENTRIES_TOTAL = Counter("trade_entries_total", "Total number of new trades entered")
EXITS_TOTAL = Counter("trade_exits_total", "Total number of trades exited")

# ----------------- Metrics Server ---------------------
try:
    start_http_server(METRICS_PORT)
    print(f"[Metrics] Prometheus available at http://localhost:{METRICS_PORT}/metrics")
    send_discord_message(f"✅ Metrics server running on port {METRICS_PORT}")
except Exception as e:
    print(f"[Metrics] Error starting server: {e}")
    send_discord_message(f"❌ Metrics server error: {e}")

# ----------------- POSITION TRACKING ------------------
POSITIONS_FILE = Path("positions.json")
positions = {}

def load_positions():
    global positions
    if POSITIONS_FILE.exists():
        with open(POSITIONS_FILE, "r") as f:
            positions = json.load(f)
        print(f"[Positions] Loaded {len(positions)} open positions.")
    else:
        positions = {}
        print("[Positions] No positions file found. Starting fresh.")

def save_positions():
    with open(POSITIONS_FILE, "w") as f:
        json.dump(positions, f, indent=2)
    print(f"[Positions] Saved {len(positions)} open positions.")

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

# ----------------- TRADE LOGGING ---------------------
TRADE_LOG = Path("trade_log.txt")

def log_trade(event, pair, side, zscore=None):
    log_line = (
        f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {event} | Pair: {pair} | Side: {side} | Z: {zscore}\n"
    )
    with open(TRADE_LOG, "a") as f:
        f.write(log_line)
    print(f"[Log] {log_line.strip()}")

# ----------------- Alpaca WebSocket -------------------
try:
    from alpaca.data.live import StockDataStream
except ImportError:
    StockDataStream = None

async def run_websocket_live():
    """Run trading loop in WebSocket mode using Alpaca's data stream."""
    if not StockDataStream:
        raise ImportError("alpaca-py package is required for websocket mode.")

    stream = StockDataStream(ALPACA_KEY, ALPACA_SECRET)

    async def handle_bar(bar):
        print(f"[WebSocket] New bar for {bar.symbol}")
        await process_live_bar(bar.symbol)

    try:
        stream.subscribe_bars(handle_bar, *UNIVERSE)
        print(f"[WebSocket] Subscribed to bars for: {UNIVERSE}")
        send_discord_message(f"🟢 WebSocket trading mode started. Watching symbols: {UNIVERSE}")
        await stream._run_forever()
    except ssl.SSLError as ssl_err:
        print(f"[WebSocket Error] SSL verification failed: {ssl_err}")
        send_discord_message("❌ WebSocket SSL verification error. Check your certificates.")
    except Exception as e:
        print(f"[WebSocket Error] Unexpected error: {e}")
        send_discord_message(f"❌ WebSocket error: {e}")

async def process_live_bar(symbol):
    print(f"[WebSocket] Processing new bar for {symbol}")
    run_trading_logic()

# ----------------- Core Trading Logic -----------------
def run_trading_logic():
    print("[Trading] Fetching bars and computing signals...")
    try:
        best_params = load_best_hyperparameters()
        lookback_days = best_params.get("lookback_days", 90)
        rolling_window = best_params.get("rolling_window", 60)
        z_threshold = best_params.get("z_threshold", 1.5)
        kalman_cov = best_params.get("kalman_cov", 0.005)

        df = data_io.fetch_bars(interval="1h", lookback=lookback_days)
    except Exception as e:
        print(f"[Error] Failed to fetch bars: {e}")
        send_discord_message(f"❌ Error fetching bars: {e}")
        return

    best_pairs = pairs.find_cointegrated(df, max_pairs=5)
    TRADES_PROCESSED.inc()

    for _, row in best_pairs.iterrows():
        a, b = row["a"], row["b"]
        spread_df = df[[a, b]]
        sig = signals.signal_from_spread(
            spread_df, a, b,
            z_threshold=z_threshold,
            rolling_window=rolling_window,
            kalman_cov=kalman_cov
        )

        pair_key = (a, b)

        if sig:
            if not is_open(pair_key):
                if sig["action"] == "LONG_SPREAD":
                    print(f"🚀 Opening LONG_SPREAD: {a} - {b}")
                    execution.place_pair_trade(a, b)
                    open_trade(pair_key, "LONG_SPREAD")
                    log_trade("ENTRY", pair_key, "LONG_SPREAD", sig["z"])
                    ENTRIES_TOTAL.inc()
                    send_discord_message(f"🚀 ENTRY: LONG_SPREAD {a} - {b} | Z: {sig['z']:.2f}")
                elif sig["action"] == "SHORT_SPREAD":
                    print(f"🚀 Opening SHORT_SPREAD: {b} - {a}")
                    execution.place_pair_trade(b, a)
                    open_trade(pair_key, "SHORT_SPREAD")
                    log_trade("ENTRY", pair_key, "SHORT_SPREAD", sig["z"])
                    ENTRIES_TOTAL.inc()
                    send_discord_message(f"🚀 ENTRY: SHORT_SPREAD {b} - {a} | Z: {sig['z']:.2f}")
            else:
                print(f"✅ Position already open for {pair_key}. Skipping entry.")
        else:
            if is_open(pair_key):
                print(f"⚡ Spread mean-reverted. Exiting {pair_key}")
                close_trade(pair_key)
                log_trade("EXIT", pair_key, "CLOSE")
                EXITS_TOTAL.inc()
                send_discord_message(f"⚡ EXIT: Closed position for pair {pair_key}")

# ----------------- Polling Mode Loop -----------------
def schedule_polling_loop():
    load_positions()
    send_discord_message("🟢 Polling trading mode started.")

    def job():
        print("[Polling] Running trading job...")
        run_trading_logic()

    schedule.every(POLLING_INTERVAL_MINUTES).minutes.do(job)

    print(f"[Polling] Starting schedule loop every {POLLING_INTERVAL_MINUTES} minutes.")
    while True:
        schedule.run_pending()
        time.sleep(30)

# ----------------- CLI Entrypoint --------------------
if __name__ == "__main__":
    send_discord_message(f"🤖 Bot starting in {LIVE_MODE.upper()} mode.")
    load_positions()
    if LIVE_MODE == "polling":
        schedule_polling_loop()
    else:
        asyncio.run(run_websocket_live())