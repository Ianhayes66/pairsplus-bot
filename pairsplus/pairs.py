"""
pairsplus/pairs.py

Cointegration detection between asset price series.
"""

import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import coint
from itertools import combinations

def clean_pair_series(s1, s2, min_length=30):
    s1 = s1.replace([np.inf, -np.inf], np.nan).dropna()
    s2 = s2.replace([np.inf, -np.inf], np.nan).dropna()

    s1, s2 = s1.align(s2, join="inner")

    if s1.isnull().any() or s2.isnull().any():
        return None, None

    if len(s1) < min_length or len(s2) < min_length:
        return None, None

    return s1, s2

def find_cointegrated(df: pd.DataFrame, max_pairs: int = 10, pval_threshold: float = 1.0) -> pd.DataFrame:
    scores = []
    for (a, b) in combinations(df.columns, 2):
        s1, s2 = clean_pair_series(df[a], df[b])
        if s1 is None or s2 is None:
            continue

        try:
            score, pval, _ = coint(s1, s2)
        except Exception:
            continue

        if np.isfinite(pval) and pval <= pval_threshold:
            scores.append((pval, a, b))

    scores.sort()
    top_scores = scores[:max_pairs]

    return pd.DataFrame(top_scores, columns=["pval", "a", "b"])

def find_rolling_cointegrated(df: pd.DataFrame, window: int = 100, max_pairs: int = 10, pval_threshold: float = 1.0) -> pd.DataFrame:
    results = []
    cols = df.columns
    combs = list(combinations(cols, 2))

    for start in range(len(df) - window + 1):
        end = start + window
        window_df = df.iloc[start:end]
        window_scores = []

        for (a, b) in combs:
            s1, s2 = clean_pair_series(window_df[a], window_df[b])
            if s1 is None or s2 is None:
                continue

            try:
                score, pval, _ = coint(s1, s2)
            except Exception:
                continue

            if np.isfinite(pval) and pval <= pval_threshold:
                window_scores.append((pval, a, b, start, end))

        window_scores.sort()
        results.extend(window_scores[:max_pairs])

    return pd.DataFrame(results, columns=["pval", "a", "b", "start", "end"])