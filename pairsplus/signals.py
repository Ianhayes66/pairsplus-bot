import pandas as pd
import numpy as np
from .config import Z_THRESHOLD, ROLLING_WINDOW

def zscore(series: pd.Series) -> pd.Series:
    """
    Calculate the rolling z-score of a time series.
    """
    return (series - series.rolling(ROLLING_WINDOW).mean()) / series.rolling(ROLLING_WINDOW).std()

def signal_from_spread(df: pd.DataFrame, a: str, b: str):
    """
    Generate trading signal based on spread z-score.
    """
    spread = df[a] - df[b]
    z = zscore(spread)
    latest = z.iloc[-1]
    
    if latest > Z_THRESHOLD:
        return {"action": "SHORT_SPREAD", "pair": (a, b), "z": latest}
    if latest < -Z_THRESHOLD:
        return {"action": "LONG_SPREAD", "pair": (a, b), "z": latest}
    return None

# --------------- TESTS BELOW ---------------

def test_zscore():
    """
    Unit test for zscore function.
    """
    series = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    result = zscore(series)
    assert result[:ROLLING_WINDOW-1].isna().all()
    assert np.isfinite(result[ROLLING_WINDOW-1:]).all()

def test_signal_from_spread_short(monkeypatch):
    """
    Unit test for signal_from_spread when z-score > Z_THRESHOLD.
    """
    df = pd.DataFrame({"A": [10, 12, 14, 16, 18, 20, 22, 24, 26, 28],
                       "B": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]})
    monkeypatch.setattr("pairsplus.signals.zscore", lambda s: pd.Series([0]*(len(s)-1) + [Z_THRESHOLD+1]))
    signal = signal_from_spread(df, "A", "B")
    assert signal["action"] == "SHORT_SPREAD"
    assert signal["pair"] == ("A", "B")
    assert signal["z"] == Z_THRESHOLD + 1

def test_signal_from_spread_long(monkeypatch):
    """
    Unit test for signal_from_spread when z-score < -Z_THRESHOLD.
    """
    df = pd.DataFrame({"A": [10, 12, 14, 16, 18, 20, 22, 24, 26, 28],
                       "B": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]})
    monkeypatch.setattr("pairsplus.signals.zscore", lambda s: pd.Series([0]*(len(s)-1) + [-Z_THRESHOLD-1]))
    signal = signal_from_spread(df, "A", "B")
    assert signal["action"] == "LONG_SPREAD"
    assert signal["pair"] == ("A", "B")
    assert signal["z"] == -Z_THRESHOLD - 1

def test_signal_from_spread_none(monkeypatch):
    """
    Unit test for signal_from_spread when z-score is within threshold.
    """
    df = pd.DataFrame({"A": [10, 12, 14, 16, 18, 20, 22, 24, 26, 28],
                       "B": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]})
    monkeypatch.setattr("pairsplus.signals.zscore", lambda s: pd.Series([0]*len(s)))
    signal = signal_from_spread(df, "A", "B")
    assert signal is None
