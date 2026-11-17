import os
import ccxt
import pandas as pd
import yfinance as yf
from dotenv import load_dotenv

# Load configuration and environment variables
load_dotenv()


class MultiAssetTradingBot:

  def __init__(self):
    print("Initializing Multi-Asset Trading Bot Engine...")
    # Initialize crypto exchange via CCXT (Binance as default 24/7 source)
    self.crypto_exchange = ccxt.binance({"enableRateLimit": True})

  def fetch_crypto_data(self, symbol="BTC/USDT", timeframe="1d", limit=50):
    """Fetches 24/7 crypto market data."""
    try:
      print(f"Fetching crypto data for {symbol}...")
      ohlcv = self.crypto_exchange.fetch_ohlcv(
          symbol, timeframe=timeframe, limit=limit
      )
      df = pd.DataFrame(
          ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"]
      )
      df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
      # Fix the pandas deprecation warning by assigning the index directly
      df = df.set_index("timestamp")
      df["Asset_Type"] = "Crypto"
      return df
    except Exception as e:
      print(f"Error fetching crypto data: {e}")
      return None

  def fetch_etf_data(self, ticker="SPY", period="3mo", interval="1d"):
    """Fetches ETF or equity market data using Yahoo Finance."""
    try:
      print(f"Fetching ETF/Equity data for {ticker}...")
      df = yf.download(ticker, period=period, interval=interval, progress=False)
      if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
      df = df[["Open", "High", "Low", "Close", "Volume"]]
      df.columns = ["open", "high", "low", "close", "volume"]
      df["Asset_Type"] = "ETF"
      return df
    except Exception as e:
      print(f"Error fetching ETF data: {e}")
      return None

  def run_strategy_check(self, df, asset_name):
    """Simple Moving Average Crossover Strategy Check."""
    if df is None or len(df) < 20:
      print(f"Not enough data to analyze {asset_name}.")
      return

    df["SMA_10"] = df["close"].rolling(window=10).mean()
    df["SMA_20"] = df["close"].rolling(window=20).mean()

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    print(f"\n--- Analysis for {asset_name} ({latest['Asset_Type']}) ---")
    print(f"Current Close Price: {latest['close']:.2f}")
    print(f"10-period SMA: {latest['SMA_10']:.2f}")
    print(f"20-period SMA: {latest['SMA_20']:.2f}")

    # Crossover Logic
    if prev["SMA_10"] <= prev["SMA_20"] and latest["SMA_10"] > latest["SMA_20"]:
      print(f"🟢 SIGNAL: Bullish Crossover detected for {asset_name} (BUY)")
    elif (
        prev["SMA_10"] >= prev["SMA_20"] and latest["SMA_10"] < latest["SMA_20"]
    ):
      print(f"🔴 SIGNAL: Bearish Crossover detected for {asset_name} (SELL)")
    else:
      print(f"⚪ SIGNAL: Holding / No crossover for {asset_name}")


if __name__ == "__main__":
  bot = MultiAssetTradingBot()

  # 1. Test 24/7 Crypto Market Fetch
  btc_data = bot.fetch_crypto_data(symbol="BTC/USDT", timeframe="1d", limit=60)
  if btc_data is not None:
    bot.run_strategy_check(btc_data, "Bitcoin (BTC/USDT)")

  # 2. Test ETF Market Fetch (e.g., SPY S&P 500 ETF)
  spy_data = bot.fetch_etf_data(ticker="SPY", period="3mo", interval="1d")
  if spy_data is not None:
    bot.run_strategy_check(spy_data, "SPDR S&P 500 ETF (SPY)")