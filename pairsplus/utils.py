"""
pairsplus/utils.py

Utility functions for risk management, sizing, and trading calendar awareness.
"""

import numpy as np
import pandas as pd
import datetime


# ===============================
# 1️⃣ Kelly Fraction Sizing
# ===============================

def kelly_fraction(winrate, payoff_ratio, max_fraction=0.01):
    """
    Compute the Kelly fraction given winrate and payoff ratio.
    Caps the fraction at max_fraction of NAV.
    """
    kelly = (winrate * (payoff_ratio + 1) - 1) / payoff_ratio
    kelly = max(0, kelly)
    return min(kelly, max_fraction)


def test_kelly_fraction():
    print("Test 1:", kelly_fraction(0.6, 1.5))  # Expected: capped at 0.01
    print("Test 2:", kelly_fraction(0.5, 1.0))  # Expected: 0
    print("Test 3:", kelly_fraction(0.4, 2.0))  # Expected: 0)


# ===============================
# 2️⃣ Portfolio VaR Monitor
# ===============================

def compute_var(returns, confidence=0.95):
    """
    Computes historical VaR at given confidence level.
    VaR is the *positive* worst-case loss.
    """
    quantile = 1 - confidence
    var = -np.percentile(returns, quantile * 100)
    return var

def test_var():
    example_returns = pd.Series([-0.02, 0.01, -0.015, 0.02, -0.03])
    var_95 = compute_var(example_returns, 0.95)
    print(f"95% VaR: {var_95:.4f}")


# ===============================
# 3️⃣ Pair-level Stop-outs and Targets
# ===============================

def check_stop_or_target(z_series, entry_side, stop_z=3.0, target_z=1.0):
    """
    Check if a position should stop out or hit target.

    Parameters:
    - z_series: pd.Series of Z-scores after entry
    - entry_side: 'LONG_SPREAD' or 'SHORT_SPREAD'
    - stop_z: Z-score stop threshold
    - target_z: Z-score target threshold

    Returns:
    - 'STOP' if stop-out triggered
    - 'TARGET' if target hit
    - None if neither triggered yet
    """
    for z in z_series:
        if entry_side == "LONG_SPREAD":
            if z > stop_z:
                return "STOP"
            if z < target_z:
                return "TARGET"
        elif entry_side == "SHORT_SPREAD":
            if z < -stop_z:
                return "STOP"
            if z > -target_z:
                return "TARGET"
    return None

def test_check_stop_or_target():
    z_long = pd.Series([2.1, 2.5, 3.2])  # should hit STOP
    z_short = pd.Series([-2.1, -1.8, -0.8])  # should hit TARGET
    z_none = pd.Series([2.1, 2.2, 2.3])  # no trigger

    print("LONG result:", check_stop_or_target(z_long, "LONG_SPREAD"))
    print("SHORT result:", check_stop_or_target(z_short, "SHORT_SPREAD"))
    print("No trigger result:", check_stop_or_target(z_none, "LONG_SPREAD"))


# ===============================
# 4️⃣ Trading Calendar Awareness
# ===============================

# Example static event dates
EVENT_DATES = [
    datetime.date(2025, 7, 10),
    datetime.date(2025, 9, 17),
    datetime.date(2025, 12, 12)
]

def is_event_day(today=None):
    """
    Returns True if today is in the list of known event dates.
    """
    if today is None:
        today = datetime.date.today()
    return today in EVENT_DATES

def should_flatten_for_event(now=None, cutoff_hour=15):
    """
    Returns True if today is an event day and it's past cutoff_hour ET.
    """
    if now is None:
        now = datetime.datetime.now()

    if not is_event_day(now.date()):
        return False

    if now.hour >= cutoff_hour:
        return True

    return False

def test_event_flatten_check():
    test_dt = datetime.datetime(2025, 7, 10, 15, 5)
    print("Test 1 (should flatten):", should_flatten_for_event(test_dt))  # Expected: True

    test_dt2 = datetime.datetime(2025, 7, 10, 14, 59)
    print("Test 2 (should NOT flatten):", should_flatten_for_event(test_dt2))  # Expected: False

    test_dt3 = datetime.datetime(2025, 8, 1, 16, 0)
    print("Test 3 (should NOT flatten):", should_flatten_for_event(test_dt3))  # Expected: False


# ===============================
# Main Test Runner
# ===============================

if __name__ == "__main__":
    test_kelly_fraction()
    test_var()
    test_check_stop_or_target()
    test_event_flatten_check()
