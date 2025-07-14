from pairsplus import data_io, pairs, signals, portfolio
from pairsplus.tune_config import DEFAULT_HYPERPARAMS
from pairsplus.hyperparams import load_best_hyperparameters

def run_backtest(
    z_threshold=None,
    lookback_days=None,
    rolling_window=None,
    kalman_cov=None
):
    """
    Run a single backtest with specified or default hyperparameters.
    """
    # Use provided hyperparams or defaults
    z_threshold = z_threshold or DEFAULT_HYPERPARAMS["z_threshold"]
    lookback_days = lookback_days or DEFAULT_HYPERPARAMS["lookback_days"]
    rolling_window = rolling_window or DEFAULT_HYPERPARAMS["rolling_window"]
    kalman_cov = kalman_cov or DEFAULT_HYPERPARAMS["kalman_cov"]

    df = data_io.fetch_bars(interval="1h", lookback=lookback_days)
    best_pairs = pairs.find_cointegrated(df)

    total_pnl = 0
    for _, row in best_pairs.iterrows():
        a = row["a"]
        b = row["b"]
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

if __name__ == "__main__":
    print("📌 Running backtest with best hyperparameters...")
    best_params = load_best_hyperparameters()
    print(f"✅ Loaded Hyperparameters: {best_params}")

    score = run_backtest(
        z_threshold=best_params.get("z_threshold"),
        lookback_days=best_params.get("lookback_days"),
        rolling_window=best_params.get("rolling_window"),
        kalman_cov=best_params.get("kalman_cov"),
    )

    print("\n" + "="*40)
    print(f"✅ Backtest PnL: {score:.2f}")
    print("="*40)
