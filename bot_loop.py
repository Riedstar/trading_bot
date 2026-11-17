import time
from execution import (
    get_trading_client,
    fetch_crypto_data,
    calculate_signal,
    execute_trade_signal,
)


def check_and_trade():
  print("\n🔄 [Bot Worker] Fetching live data & evaluating indicators...")

  # 1. Fetch data matching your app.py configuration (e.g., BTC/USDT)
  symbol = "BTC/USDT"
  alpaca_symbol = "BTCUSD"  # Alpaca format typically omits slashes for crypto symbols
  df = fetch_crypto_data(sym=symbol, lim=90)

  # 2. Calculate moving average signals using the exact same window logic
  signal, short_sma, long_sma = calculate_signal(
      df, short_window=10, long_window=50
  )
  print(
      f"📊 {symbol} -> Short SMA (10): {short_sma:,.2f} | Long SMA (50):"
      f" {long_sma:,.2f} | Signal: {signal}"
  )

  # 3. Check current open positions on Alpaca
  client = get_trading_client()
  positions = client.get_all_positions()
  has_position = any(p.symbol == alpaca_symbol for p in positions)

  # 4. Smart Execution Logic (Avoids duplicate stacking)
  if signal == "BUY" and not has_position:
    print(
        f"🚀 Bullish crossover detected and flat on {alpaca_symbol} -> Executing"
        " automated BUY..."
    )
    execute_trade_signal(symbol=alpaca_symbol, signal="BUY", qty=0.01)
  elif signal == "SELL" and has_position:
    print(
        f"📉 Bearish crossover detected and holding {alpaca_symbol} -> Executing"
        " automated SELL..."
    )
    execute_trade_signal(symbol=alpaca_symbol, signal="SELL", qty=0.01)
  else:
    print(
        "💤 Market state matches portfolio position (No trade action"
        " required)."
    )


if __name__ == "__main__":
  print("🤖 Starting Autonomous Strategy Worker...")
  while True:
    try:
      check_and_trade()
    except Exception as e:
      print(f"❌ Error in autonomous loop: {e}")

    # Check markets every 5 minutes (300 seconds)
    print("⏳ Sleeping for 5 minutes until next check...")
    time.sleep(300)