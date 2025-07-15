#!/usr/bin/env python

"""
pairsplus/backtest.py

CLI tool to run a single backtest simulation
using historical bar data and the chosen hyperparameters.
"""

import argparse
from pairsplus import data_io, pairs, signals, portfolio
from pairsplus.tune_config import DEFAULT_HYPERPARAMS
from pairsplus.hyperparams import load_best_hyperparameters
from pairsplus.config import UNIVERSE

def run_backtest(
    z_threshold: float = None,
    lookback_days: int = None,
    rolling_window: int = None,
    kalman_cov: float = None,
    universe: list[str] = None,
    interval: str = "1h"
) -> float:
    """
    Run a single backtest with specified or default hyperparameters.
    """
    z_threshold = z_threshold or DEFAULT_HYPERPARAMS["z_threshold"]
    lookback_days = lookback_days or DEFAULT_HYPERPARAMS["lookback_days"]
    rolling_window = rolling_window or DEFAULT_HYPERPARAMS["rolling_window"]
    kalman_cov = kalman_cov or DEFAULT_HYPERPARAMS["kalman_cov"]
    universe = universe or UNIVERSE

    print("\n📈 Running backtest with hyperparameters:")
    print(f"   - z_threshold: {z_threshold}")
    print(f"   - lookback_days: {lookback_days}")
    print(f"   - rolling_window: {rolling_window}")
    print(f"   - kalman_cov: {kalman_cov}")
    print(f"   - universe: {universe}")
    print(f"   - interval: {interval}\n")

    try:
        df = data_io.fetch_bars(tickers=universe, interval=interval, lookback=lookback_days)
    except Exception as e:
        print(f"❌ Error fetching bars: {e}")
        return 0.0

    best_pairs = pairs.find_cointegrated(df)
    total_pnl = 0.0

    for _, row in best_pairs.iterrows():
        a, b = row["a"], row["b"]
        sig = signals.signal_from_spread(
            df[[a, b]],
            a, b,
            z_threshold=z_threshold,
            rolling_window=rolling_window,
            kalman_cov=kalman_cov
        )
        if sig:
            pnl = portfolio.sim_backtest(df[[a, b]], sig)
            total_pnl += pnl

    return total_pnl


def main():
    parser = argparse.ArgumentParser(
        description="Run backtest with best or custom hyperparameters."
    )
    parser.add_argument("--z_threshold", type=float, help="Z-score entry threshold")
    parser.add_argument("--lookback_days", type=int, help="Lookback window in days")
    parser.add_argument("--rolling_window", type=int, help="Rolling window size")
    parser.add_argument("--kalman_cov", type=float, help="Kalman covariance value")
    parser.add_argument("--no-best", action="store_true", help="Ignore best_hyperparams.json")

    args = parser.parse_args()

    if args.no_best:
        print("⚠️ Ignoring best_hyperparams.json; using defaults or CLI values only.")
        best_params = {}
    else:
        try:
            best_params = load_best_hyperparameters()
            print(f"✅ Loaded best_hyperparameters.json: {best_params}")
        except FileNotFoundError:
            print("⚠️ best_hyperparams.json not found. Falling back to defaults.")
            best_params = {}

    z_threshold = args.z_threshold or best_params.get("z_threshold")
    lookback_days = args.lookback_days or best_params.get("lookback_days")
    rolling_window = args.rolling_window or best_params.get("rolling_window")
    kalman_cov = args.kalman_cov or best_params.get("kalman_cov")

    score = run_backtest(
        z_threshold=z_threshold,
        lookback_days=lookback_days,
        rolling_window=rolling_window,
        kalman_cov=kalman_cov,
    )

    print("\n" + "=" * 50)
    print(f"✅ Backtest completed. PnL: {score:.2f}")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()