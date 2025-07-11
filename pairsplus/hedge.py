# pairsplus/hedge.py
import numpy as np
from pykalman import KalmanFilter

def kalman_hedge_ratio(y, x):
    kf = KalmanFilter(
        transition_matrices=np.eye(2),
        observation_matrices=np.vstack([x, np.ones_like(x)]).T[:, None, :],
        transition_covariance=1e-5 * np.eye(2),
        observation_covariance=1e-3
    )
    state_means, _ = kf.filter(np.vstack(y))
    beta, alpha = state_means[-1]
    return alpha, beta

def test_kalman_hedge_ratio():
    x = np.linspace(0, 10, 100) + np.random.normal(0, 0.1, 100)
    y = 2 * x + 5 + np.random.normal(0, 0.1, 100)
    alpha, beta = kalman_hedge_ratio(y, x)
    assert abs(beta - 2) < 0.5
