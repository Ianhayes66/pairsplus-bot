import decimal
import time
import logging
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from .config import ALPACA_KEY, ALPACA_SECRET, BASE_URL

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Alpaca client
client = TradingClient(ALPACA_KEY, ALPACA_SECRET, paper=True, base_url=BASE_URL)

def place_order(req):
    """Submit an order with basic retry on failure."""
    for attempt in range(3):
        try:
            client.submit_order(req)
            return True
        except Exception as e:
            logger.warning(f"Order failed (attempt {attempt+1}): {e}")
            time.sleep(2)
    logger.error("Order failed after 3 attempts.")
    return False

def place_pair_trade(ticker_long, ticker_short, notional=50):
    """
    Places a pair trade: long one ticker, short the other.

    Args:
        ticker_long (str): The ticker to go long.
        ticker_short (str): The ticker to short.
        notional (float): Dollar notional for each leg.
    """
    logger.info(f"Placing pair trade: LONG {ticker_long}, SHORT {ticker_short}, Notional: {notional}")

    long_req = MarketOrderRequest(
        symbol=ticker_long,
        notional=decimal.Decimal(notional),
        side=OrderSide.BUY,
        time_in_force=TimeInForce.DAY,
    )

    short_req = MarketOrderRequest(
        symbol=ticker_short,
        notional=decimal.Decimal(notional),
        side=OrderSide.SELL,
        time_in_force=TimeInForce.DAY,
    )

    success_long = place_order(long_req)
    success_short = place_order(short_req)

    if success_long and success_short:
        logger.info("Pair trade executed successfully.")
    else:
        logger.error("Pair trade failed.")
