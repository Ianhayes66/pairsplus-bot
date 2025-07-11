"""
pairsplus/execution.py

Handles trade execution via Alpaca TradingClient.
Includes price lookups for sizing and robust error handling.
"""

import decimal
import time
import logging
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestTradeRequest
from .config import ALPACA_KEY, ALPACA_SECRET

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Alpaca clients
client = TradingClient(ALPACA_KEY, ALPACA_SECRET, paper=True)
data_client = StockHistoricalDataClient(ALPACA_KEY, ALPACA_SECRET)


def get_latest_price(symbol):
    """
    Fetch the most recent trade price for a given symbol.
    """
    try:
        trades = data_client.get_stock_latest_trade(
            StockLatestTradeRequest(symbol_or_symbols=symbol)
        )
        price = trades[symbol].price
        logger.info(f"Latest price for {symbol}: {price}")
        return price
    except Exception as e:
        logger.error(f"Failed to fetch latest price for {symbol}: {e}")
        return None


def place_order(req):
    """
    Submit an order with up to 3 retry attempts on failure.
    """
    for attempt in range(3):
        try:
            logger.info(f"Submitting order: {req}")
            client.submit_order(order_data=req)
            return True
        except Exception as e:
            logger.warning(f"Order failed (attempt {attempt + 1}): {str(e)}")
            time.sleep(2)
    logger.error("Order failed after 3 attempts.")
    return False

def close_pair_trade(ticker_long, ticker_short, qty=1):
    logger.info(f"Closing pair trade: SELL {ticker_long}, BUY {ticker_short}")

    sell_req = MarketOrderRequest(
        symbol=ticker_long,
        qty=qty,
        side=OrderSide.SELL,
        time_in_force=TimeInForce.DAY,
    )

    buy_req = MarketOrderRequest(
        symbol=ticker_short,
        qty=qty,
        side=OrderSide.BUY,
        time_in_force=TimeInForce.DAY,
    )

    place_order(sell_req)
    place_order(buy_req)


def place_pair_trade(ticker_long, ticker_short, notional=50):
    """
    Places a pairs trade with:
    - Fractional notional BUY on long leg.
    - Integer qty SELL on short leg.
    """
    logger.info(f"Placing pair trade: LONG {ticker_long}, SHORT {ticker_short}, Notional: {notional}")

    # ✅ Long leg: fractional notional buy
    long_req = MarketOrderRequest(
        symbol=ticker_long,
        notional=decimal.Decimal(notional),
        side=OrderSide.BUY,
        time_in_force=TimeInForce.DAY,
    )
    success_long = place_order(long_req)

    if not success_long:
        logger.error("Long leg order failed. Aborting pair trade.")
        return

    # ✅ Short leg: must use integer quantity
    short_price = get_latest_price(ticker_short)
    if short_price is None or short_price <= 0:
        logger.error(f"Cannot place short order: invalid price for {ticker_short}")
        return

    qty = max(1, int(notional / short_price))
    logger.info(f"Calculated short qty for {ticker_short}: {qty} shares")

    short_req = MarketOrderRequest(
        symbol=ticker_short,
        qty=int(qty),
        side=OrderSide.SELL,
        time_in_force=TimeInForce.DAY,
    )
    success_short = place_order(short_req)

    if success_short:
        logger.info("Pair trade executed successfully.")
    else:
        logger.error("Short leg order failed. Pair trade incomplete.")
