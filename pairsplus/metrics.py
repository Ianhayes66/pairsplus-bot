"""
pairsplus/metrics.py

Prometheus metrics for monitoring trades, errors, and performance.
"""

from prometheus_client import Counter, Gauge, start_http_server
import threading

# === METRICS ===

TRADES_OPENED = Counter('trades_opened_total', 'Number of trades opened')
TRADES_CLOSED = Counter('trades_closed_total', 'Number of trades closed')
ERRORS = Counter('errors_total', 'Number of errors encountered')
WIN_TRADES = Counter('trades_win_total', 'Number of winning trades')
LOSS_TRADES = Counter('trades_loss_total', 'Number of losing trades')
EQUITY = Gauge('equity_value', 'Current simulated equity curve')

# === HELPERS ===

def inc_trade_open():
    TRADES_OPENED.inc()

def inc_trade_close():
    TRADES_CLOSED.inc()

def inc_error():
    ERRORS.inc()

def inc_win():
    WIN_TRADES.inc()

def inc_loss():
    LOSS_TRADES.inc()

def set_equity(value):
    EQUITY.set(value)

# === START SERVER ===

def start_metrics_server(port=8000):
    """
    Start Prometheus /metrics server on separate thread.
    """
    def server_thread():
        print(f"[Metrics] Prometheus /metrics endpoint on http://localhost:{port}/metrics")
        start_http_server(port)

    thread = threading.Thread(target=server_thread, daemon=True)
    thread.start()
