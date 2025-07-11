import pandas as pd
from statsmodels.tsa.stattools import coint
from itertools import combinations

def find_cointegrated(
    df: pd.DataFrame,
    max_pairs: int = 10,
    pval_threshold: float = 1.0
) -> pd.DataFrame:
    """
    Finds the top cointegrated pairs in the dataframe.

    Parameters:
    - df: DataFrame of price series (columns = tickers).
    - max_pairs: maximum number of pairs to return.
    - pval_threshold: only include pairs with p-value below this.

    Returns:
    - DataFrame with columns: ['pval', 'a', 'b'].
    """
    scores = []
    for (a, b) in combinations(df.columns, 2):
        score, pval, _ = coint(df[a], df[b])
        if pval <= pval_threshold:
            scores.append((pval, a, b))

    scores.sort()
    top_scores = scores[:max_pairs]

    return pd.DataFrame(top_scores, columns=["pval", "a", "b"])


def find_rolling_cointegrated(
    df: pd.DataFrame,
    window: int = 100,
    max_pairs: int = 10,
    pval_threshold: float = 1.0
) -> pd.DataFrame:
    """
    Applies cointegration test over rolling windows.

    Parameters:
    - df: DataFrame of price series.
    - window: window size in bars.
    - max_pairs: max pairs per window.
    - pval_threshold: filter for p-values below this.

    Returns:
    - DataFrame with columns: ['pval', 'a', 'b', 'start', 'end'].
    """
    results = []
    cols = df.columns
    combs = list(combinations(cols, 2))

    for start in range(len(df) - window + 1):
        end = start + window
        window_df = df.iloc[start:end]
        window_scores = []

        for (a, b) in combs:
            score, pval, _ = coint(window_df[a], window_df[b])
            if pval <= pval_threshold:
                window_scores.append((pval, a, b, start, end))

        window_scores.sort()
        results.extend(window_scores[:max_pairs])

    return pd.DataFrame(
        results,
        columns=["pval", "a", "b", "start", "end"]
    )
