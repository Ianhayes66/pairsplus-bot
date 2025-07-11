# pairsplus/cluster.py

import numpy as np
from sklearn.cluster import KMeans

def compute_returns(price_df):
    """
    Compute log returns from prices.
    """
    return np.log(price_df / price_df.shift(1)).dropna()

def cluster_tickers(price_df, n_clusters=3):
    """
    Cluster tickers based on correlation of returns.
    
    Returns a dictionary of cluster assignments.
    """
    # 1. Compute returns
    returns = compute_returns(price_df)

    # 2. Correlation matrix
    corr_matrix = returns.corr()

    # 3. Convert correlation to distance
    distance_matrix = 1 - corr_matrix

    # 4. Flatten upper triangle for KMeans
    features = distance_matrix.values

    # 5. Fit KMeans
    model = KMeans(n_clusters=n_clusters, random_state=42)
    model.fit(features)

    # 6. Assign clusters
    labels = model.labels_
    assignments = dict(zip(price_df.columns, labels))

    return assignments
