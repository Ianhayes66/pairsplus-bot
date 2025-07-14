"""
pairsplus/execution.py

Handles trade execution via Alpaca TradingClient.
Features:
- Limit order pegging with rounding
- Notional splitting for liquidity
- CSV trade logging
- Console and file logging
- Discord notifications
- Prometheus metrics
"""

import decimal
import time
import logging
import csv
from datetime import datetime
from .notifier import send_discord_message
from prometheus_client import Counter, Gauge, start_http_server

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestTradeRequest

from .config import (
    ALPACA_KEY,
    ALPACA_SECRET,
    ORDER_TYPE,
    PEG_DISTANCE,
    SPLIT_NOTIONAL,
    BASE_DIR
)

# === Logging Setup ===
LOG_FILE = BASE_DIR / "trade_Log.txt"
TRADE_LOG_CSV = BASE_DIR / "positions.csv"

log_format = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    handlers=[
        logging.FileHandler(LOG_FILE, mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# === Prometheus Metrics ===
trades_opened_total = Counter('trades_opened_total', 'Number of trades opened')
trades_closed_total = Counter('trades_closed_total', 'Number of trades closed')
trade_errors_total = Counter('trade_errors_total', 'Number of trade errors')
orders_attempted_total = Counter('orders_attempted_total', 'Number of orders attempted')
equity_value = Gauge('equity_value', 'Simulated equity curve')

# === Initialize Alpaca Clients ===
client = TradingClient(ALPACA_KEY, ALPACA_SECRET, paper=True)
data_client = StockHistoricalDataClient(ALPACA_KEY, ALPACA_SECRET)


# === Helper: Fetch Latest Price ===
def get_latest_price(symbol):
    """
    Fetch the latest trade price for a stock.
    """
    try:
        trades = data_client.get_stock_latest_trade(
            StockLatestTradeRequest(symbol_or_symbols=symbol)
        )
        price = trades[symbol].price
        if price is None or price <= 0:
            raise ValueError(f"Invalid fetched price for {symbol}: {price}")
        logger.info(f"Latest price for {symbol}: {price}")
        return price
    except Exception as e:
        logger.error(f"Failed to fetch latest price for {symbol}: {e}")
        trade_errors_total.inc()
        return None


# === Helper: CSV Trade Log ===
def log_trade_csv(action, ticker, qty, price=None):
    """
    Append a trade entry to CSV log.
    """
    row = {
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "ticker": ticker,
        "qty": qty,
        "price": price or "N/A"
    }
    TRADE_LOG_CSV.parent.mkdir(parents=True, exist_ok=True)
    exists = TRADE_LOG_CSV.exists()

    with open(TRADE_LOG_CSV, mode='a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not exists:
            writer.writeheader()
        writer.writerow(row)
    logger.info(f"Logged trade to CSV: {row}")


# === Helper: Place Order ===
def place_order(req):
    """
    Submit an order to Alpaca with retries.
    """
    orders_attempted_total.inc()
    for attempt in range(3):
        try:
            logger.info(f"Submitting order: {req}")
            client.submit_order(order_data=req)
            log_trade_csv(
                action=req.side.value,
                ticker=req.symbol,
                qty=req.qty if hasattr(req, 'qty') else "fractional",
                price="MARKET"
            )
            send_discord_message(
                f"✅ Order: {req.side.value.upper()} {req.symbol} "
                f"Qty: {req.qty if hasattr(req, 'qty') else 'fractional'}"
            )
            return True
        except Exception as e:
            logger.warning(f"Order failed (attempt {attempt + 1}): {str(e)}")
            trade_errors_total.inc()
            time.sleep(2)
    logger.error("❌ Order failed after 3 attempts.")
    return False


# === Helper: Build Market or Limit Order ===
def build_order_request(symbol, side, qty=None, notional=None, price=None):
    """
    Build Market or Limit order request.
    """
    if qty is None and notional is None:
        raise ValueError(f"[Execution] ERROR: Both qty and notional are None for {symbol}.")
    if qty is not None and qty <= 0:
        raise ValueError(f"[Execution] ERROR: Invalid qty for {symbol}: {qty}")

    if ORDER_TYPE == "LIMIT":
        if price is None or price <= 0:
            raise ValueError(f"[Execution] ERROR: Missing or invalid price for LIMIT order on {symbol}")
        if qty is None and notional is not None:
            qty = max(1, int(notional / price))
            logger.info(f"Calculated qty for LIMIT order on {symbol}: {qty} shares from notional {notional}")

        # Round limit price to 2 decimals (avoiding sub-penny errors)
        peg_factor = 1 + (PEG_DISTANCE if side == OrderSide.BUY else -PEG_DISTANCE)
        limit_price = round(price * peg_factor, 2)
        logger.info(f"Pegging {side.name} order for {symbol} at limit {limit_price} (peg distance {PEG_DISTANCE})")
        return LimitOrderRequest(
            symbol=symbol,
            qty=int(qty),
            side=side,
            time_in_force=TimeInForce.DAY,
            limit_price=decimal.Decimal(limit_price)
        )
    else:
        return MarketOrderRequest(
            symbol=symbol,
            qty=int(qty) if qty is not None else None,
            notional=decimal.Decimal(notional) if notional else None,
            side=side,
            time_in_force=TimeInForce.DAY,
        )


# === Helper: Split Notional if Configured ===
def maybe_split_notional(notional):
    """
    Split notional into halves if enabled.
    """
    if SPLIT_NOTIONAL and notional > 20:
        half = notional / 2
        logger.info(f"Smart notional split: {notional} -> {half} + {half}")
        return [half, half]
    else:
        return [notional]


# === Close Existing Pair ===
def close_pair_trade(ticker_long, ticker_short, qty=1):
    """
    Close both legs of an existing pair.
    """
    logger.info(f"Closing pair trade: SELL {ticker_long}, BUY {ticker_short}")

    price_long = get_latest_price(ticker_long)
    price_short = get_latest_price(ticker_short)

    if price_long is None or price_short is None:
        logger.error("[Execution] ERROR: Cannot close trade due to missing price data.")
        return

    sell_req = build_order_request(
        symbol=ticker_long,
        side=OrderSide.SELL,
        qty=qty,
        price=price_long
    )
    buy_req = build_order_request(
        symbol=ticker_short,
        side=OrderSide.BUY,
        qty=qty,
        price=price_short
    )

    if place_order(sell_req) and place_order(buy_req):
        trades_closed_total.inc()
        send_discord_message(f"📉 Closed pair trade: SELL {ticker_long}, BUY {ticker_short}")


# === Place New Pair Trade ===
def place_pair_trade(ticker_long, ticker_short, notional=50):
    """
    Place new pair trade with notional split and pegged limit pricing.
    """
    logger.info(f"Placing pair trade: LONG {ticker_long}, SHORT {ticker_short}, Notional: {notional}")

    # --- Long leg ---
    for chunk in maybe_split_notional(notional):
        long_price = get_latest_price(ticker_long)
        if long_price is None or long_price <= 0:
            logger.error(f"[Execution] ERROR: Cannot place long order: invalid price for {ticker_long}")
            return

        long_req = build_order_request(
            symbol=ticker_long,
            side=OrderSide.BUY,
            notional=chunk,
            price=long_price
        )
        success_long = place_order(long_req)
        if not success_long:
            logger.error("[Execution] ERROR: Long leg order failed. Aborting pair trade.")
            return

    # --- Short leg ---
    short_price = get_latest_price(ticker_short)
    if short_price is None or short_price <= 0:
        logger.error(f"[Execution] ERROR: Cannot place short order: invalid price for {ticker_short}")
        return

    qty_short = max(1, int(notional / short_price))
    logger.info(f"Calculated short qty for {ticker_short}: {qty_short} shares")

    short_req = build_order_request(
        symbol=ticker_short,
        side=OrderSide.SELL,
        qty=qty_short,
        price=short_price
    )
    success_short = place_order(short_req)

    if success_short:
        trades_opened_total.inc()
        logger.info("✅ Pair trade executed successfully.")
        send_discord_message(
            f"🚀 Executed pair trade: LONG {ticker_long}, SHORT {ticker_short}, Notional: {notional}"
        )
    else:
        logger.error("[Execution] ERROR: Short leg order failed. Pair trade incomplete.")


# === Prometheus Exporter ===
if __name__ == "__main__":
    try:
        start_http_server(8000)
        logger.info("[Metrics] Prometheus metrics server running at http://localhost:8000/metrics")
        while True:
            time.sleep(60)
    except Exception as e:
        logger.error(f"[Metrics] Failed to start Prometheus server: {e}")