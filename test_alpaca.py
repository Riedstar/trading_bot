from alpaca.trading.client import TradingClient

# Direct configuration using your actual keys
API_KEY = "PKTUPOPPWW3DH3XK5GJ246L56K"
SECRET_KEY = "5tvVirLFvcsZkN5ZytFwtK7fqHjFZC12tguDzTq4E94e"

print("Initializing Alpaca Paper Trading Client...")

# Initialize client in sandbox/paper mode
client = TradingClient(API_KEY, SECRET_KEY, paper=True)

try:
  # Fetch account information to test connection
  account = client.get_account()
  print("\n--- Alpaca Connection Successful! ---")
  print(f"Account Status: {account.status}")
  print(f"Cash Balance: ${float(account.cash):,.2f}")
  print(f"Buying Power: ${float(account.buying_power):,.2f}")
  print(f"Currency: {account.currency}")
except Exception as e:
  print(f"\n❌ Error connecting to Alpaca: {e}")