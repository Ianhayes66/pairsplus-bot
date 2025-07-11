import pandas as pd
import numpy as np

def zscore(series, window=30):
    """Rolling z-score over a moving window."""
    return (series - series.rolling(window).mean()) / series.rolling(window).std()

def spread_volatility(spread, window=30):
    """Rolling standard deviation of the spread."""
    return spread.rolling(window).std()

def rolling_beta(y, x, window=60):
    """Rolling hedge ratio (beta) over time."""
    betas = []
    for i in range(window, len(y)):
        beta = np.polyfit(x[i-window:i], y[i-window:i], 1)[0]
        betas.append(beta)
    return pd.Series([np.nan]*window + betas, index=y.index)

def estimate_half_life(spread):
    """
    Estimate the half-life of mean reversion.
    Uses an AR(1) regression to estimate speed of mean reversion.
    """
    lagged = spread.shift(1).dropna()
    delta = spread.diff().dropna()
    beta = np.polyfit(lagged, delta, 1)[0]
    half_life = -np.log(2) / beta if beta != 0 else np.inf
    return half_life

def spread_momentum(spread, lag=5):
    """Simple momentum feature."""
    return spread - spread.shift(lag)

def volume_imbalance(volume_a, volume_b):
    """
    Volume imbalance between two assets.
    Requires real traded volume data.
    """
    return (volume_a - volume_b) / (volume_a + volume_b)

def add_macro_features(df, vix_series=None, fed_funds_series=None):
    """
    Add macro regime variables to the feature set.
    For now, uses placeholder static values if real series aren't supplied.
    """
    if vix_series is not None:
        df['vix_level'] = vix_series
    else:
        df['vix_level'] = 20  # Placeholder
    if fed_funds_series is not None:
        df['fed_funds_implied'] = fed_funds_series
    else:
        df['fed_funds_implied'] = 0.05  # Placeholder
    return df

def compute_features(spread, y=None, x=None, window=30):
    """
    Compute a DataFrame of features given a spread series.
    Optionally requires y and x for rolling beta.
    """
    features = pd.DataFrame(index=spread.index)

    features['zscore'] = zscore(spread, window)
    features['volatility'] = spread_volatility(spread, window)
    features['momentum'] = spread_momentum(spread, lag=5)

    # Half-life is scalar; broadcast to all rows for compatibility
    half_life = estimate_half_life(spread)
    features['half_life'] = half_life

    if y is not None and x is not None:
        features['rolling_beta'] = rolling_beta(y, x, window=60)

    return features
