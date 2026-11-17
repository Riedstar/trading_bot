import os
import ccxt
import pandas as pd
import yfinance as yf
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce


def get_trading_client():
  """Initializes and returns the Alpaca Trading Client in paper mode."""
  API_KEY = "PKTUPOPPWW3DH3XK5GJ246L56K"
  SECRET_KEY = "5tvVirLFvcsZkN5ZytFwtK7fqHjFZC12tguDzTq4E94e"
  return TradingClient(API_KEY, SECRET_KEY, paper=True)


def get_account_summary():
  """Fetches account balance, buying power, and open positions."""
  client = get_trading_client()
  try:
    account = client.get_account()
    positions = client.get_all_positions()
    return {
        "status": account.status,
        "cash": float(account.cash),
        "buying_power": float(account.buying_power),
        "positions": positions,
    }
  except Exception as e:
    print(f"❌ Error fetching account summary: {e}")
    return None


def fetch_crypto_data(sym="BTC/USDT", lim=90):
  """Matches app.py CCXT data loader."""
  exchange = ccxt.binance({"enableRateLimit": True})
  ohlcv = exchange.fetch_ohlcv(sym, timeframe="1d", limit=lim)
  df = pd.DataFrame(
      ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"]
  )
  df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
  df = df.set_index("timestamp")
  return df


def calculate_signal(df, short_window=10, long_window=50):
  """Calculates moving averages and returns the latest signal status."""
  df["SMA_Short"] = df["close"].rolling(window=short_window).mean()
  df["SMA_Long"] = df["close"].rolling(window=long_window).mean()

  latest = df.iloc[-1]
  short_val = float(latest["SMA_Short"])
  long_val = float(latest["SMA_Long"])

  signal = "BUY" if short_val > long_val else "SELL"
  return signal, short_val, long_val


def execute_trade_signal(symbol: str, signal: str, qty: float = 1.0):
  """Executes a market order on Alpaca paper trading based on strategy signal."""
  client = get_trading_client()

  if signal.upper() == "BUY":
    side = OrderSide.BUY
  elif signal.upper() == "SELL":
    side = OrderSide.SELL
  else:
    print(f"⚠️ Invalid signal '{signal}' received. No trade executed.")
    return None

  try:
    market_order_data = MarketOrderRequest(
        symbol=symbol.upper(),
        qty=qty,
        side=side,
        time_in_force=TimeInForce.GTC,
    )
    order = client.submit_order(order_data=market_order_data)
    print(f"\n🚀 Successfully Placed Paper Order!")
    print(f"ID: {order.id}")
    print(f"Symbol: {order.symbol}")
    print(f"Side: {order.side.value}")
    print(f"Quantity: {order.qty}")
    print(f"Status: {order.status}")
    return order
  except Exception as e:
    print(f"\n❌ Error executing order for {symbol}: {e}")
    return None