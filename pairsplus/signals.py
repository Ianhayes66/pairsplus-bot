"""
pairsplus/signals.py

Generates trading signals based on spread z-scores and Kalman filtering.
"""

import pandas as pd
import numpy as np
from .tune_config import DEFAULT_HYPERPARAMS

def zscore(series: pd.Series, rolling_window: int) -> pd.Series:
    return (series - series.rolling(rolling_window).mean()) / series.rolling(rolling_window).std()

def kalman_filter(spread: pd.Series, kalman_cov: float) -> pd.Series:
    state_mean = 0.0
    state_var = 1.0
    result = []

    for obs in spread:
        pred_mean = state_mean
        pred_var = state_var + kalman_cov

        kalman_gain = pred_var / (pred_var + kalman_cov)
        state_mean = pred_mean + kalman_gain * (obs - pred_mean)
        state_var = (1 - kalman_gain) * pred_var

        result.append(state_mean)

    return pd.Series(result, index=spread.index)

def signal_from_spread(
    df: pd.DataFrame,
    a: str,
    b: str,
    z_threshold: float = None,
    rolling_window: int = None,
    kalman_cov: float = None
) -> dict:
    z_threshold = z_threshold or DEFAULT_HYPERPARAMS["z_threshold"]
    rolling_window = rolling_window or DEFAULT_HYPERPARAMS["rolling_window"]
    kalman_cov = kalman_cov or DEFAULT_HYPERPARAMS["kalman_cov"]

    spread = df[a] - df[b]
    spread_smoothed = kalman_filter(spread, kalman_cov)

    z = zscore(spread_smoothed, rolling_window)
    latest = z.iloc[-1]

    if latest > z_threshold:
        return {"action": "SHORT_SPREAD", "pair": (a, b), "z": latest}
    if latest < -z_threshold:
        return {"action": "LONG_SPREAD", "pair": (a, b), "z": latest}
    return None

# --------------- TESTS BELOW ---------------

def test_zscore():
    series = pd.Series(range(1, 101))
    result = zscore(series, rolling_window=20)
    assert result[:19].isna().all()
    assert np.isfinite(result[19:]).all()

def test_kalman_filter():
    series = pd.Series([10]*50 + [20]*50)
    smoothed = kalman_filter(series, kalman_cov=0.001)
    assert len(smoothed) == len(series)
    assert np.all(np.isfinite(smoothed))

def test_signal_from_spread_short(monkeypatch):
    df = pd.DataFrame({
        "A": [i * 2 for i in range(100)],
        "B": list(range(100))
    })
    signal = signal_from_spread(
        df, "A", "B",
        z_threshold=0.5,
        rolling_window=20,
        kalman_cov=0.001
    )
    assert signal is not None
    assert signal["action"] in {"SHORT_SPREAD", "LONG_SPREAD"}
    assert isinstance(signal["z"], float)

def test_signal_from_spread_none():
    df = pd.DataFrame({
        "A": [10]*100,
        "B": [10]*100
    })
    signal = signal_from_spread(
        df, "A", "B",
        z_threshold=1.5,
        rolling_window=20,
        kalman_cov=0.001
    )
    assert signal is None