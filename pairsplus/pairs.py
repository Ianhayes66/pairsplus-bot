import pandas as pd
from statsmodels.tsa.stattools import coint
from itertools import combinations

def find_cointegrated(df: pd.DataFrame, max_pairs=10):
    scores = []
    for (a, b) in combinations(df.columns, 2):
        score, pval, _ = coint(df[a], df[b])
        scores.append((pval, a, b))
    scores.sort()
    return scores[:max_pairs]
    def find_rolling_cointegrated(df: pd.DataFrame, window: int = 100, max_pairs=10):
        results = []
        cols = df.columns
        combs = list(combinations(cols, 2))
        for start in range(len(df) - window + 1):
            end = start + window
            window_scores = []
            window_df = df.iloc[start:end]
            for (a, b) in combs:
                score, pval, _ = coint(window_df[a], window_df[b])
                window_scores.append((pval, a, b, start, end))
            window_scores.sort()
            results.extend(window_scores[:max_pairs])
        return results                                                      