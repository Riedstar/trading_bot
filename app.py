import ccxt
import pandas as pd
import plotly.express as px
import streamlit as st
import yfinance as yf

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Multi-Asset Trading Bot Command Center",
    page_icon="📈",
    layout="wide",
)

# --- 2. ADVANCED GLASSMORPHISM STYLING ---
st.markdown(
    """
    <style>
    /* Global App Background */
    .stApp {
        background: radial-gradient(circle at 10% 20%, #0f172a 0%, #090d16 90%);
        color: #f8fafc;
    }
    
    /* Sidebar Glassmorphism */
    [data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.75);
        backdrop-filter: blur(16px);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }
    
    /* Glass Cards (Metrics, Charts, Expanders) */
    div.stMetric, div[data-testid="stExpander"], div.stPlotlyChart, div.stDataFrame {
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    
    /* Typography Overrides */
    h1, h2, h3, h4, h5, h6, label, .stMarkdown {
        color: #f1f5f9 !important;
    }
    
    /* Inputs & Selectboxes Glass styling */
    .stSelectbox div[data-baseweb="select"] {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("📈 Multi-Asset Trading Bot Command Center")
st.markdown(
    "Monitor 24/7 crypto markets alongside traditional ETFs with automated"
    " Moving Average strategies."
)
st.markdown("---")

# --- 3. SIDEBAR CONTROLS ---
st.sidebar.header("⚙️ Bot Configuration")
asset_class = st.sidebar.selectbox(
    "Select Asset Class", ["Cryptocurrency (24/7)", "ETF / Equities"]
)

if asset_class == "Cryptocurrency (24/7)":
  symbol = st.sidebar.selectbox("Crypto Pair", ["BTC/USDT", "ETH/USDT", "SOL/USDT"])
  limit = st.sidebar.slider("Historical Candles", 30, 200, 90)
else:
  symbol = st.sidebar.selectbox("ETF Ticker", ["SPY", "QQQ", "GLD", "VTI"])
  period = st.sidebar.selectbox(
      "Historical Period", ["1mo", "3mo", "6mo", "1y"], index=1
  )

short_window = st.sidebar.slider("Short SMA Window", 5, 20, 10)
long_window = st.sidebar.slider("Long SMA Window", 21, 100, 50)


# --- 4. DATA FETCHING CACHED ---
@st.cache_data(ttl=300)
def load_crypto_data(sym, lim):
  exchange = ccxt.binance({"enableRateLimit": True})
  ohlcv = exchange.fetch_ohlcv(sym, timeframe="1d", limit=lim)
  df = pd.DataFrame(
      ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"]
  )
  df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
  df = df.set_index("timestamp")
  return df


@st.cache_data(ttl=300)
def load_etf_data(ticker, per):
  df = yf.download(ticker, period=per, interval="1d", progress=False)
  if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.droplevel(1)
  df = df[["Open", "High", "Low", "Close", "Volume"]]
  df.columns = ["open", "high", "low", "close", "volume"]
  return df


# --- 5. EXECUTION & BACKTESTING ENGINE ---
if asset_class == "Cryptocurrency (24/7)":
  data = load_crypto_data(symbol, limit)
  asset_title = f"Crypto — {symbol}"
else:
  data = load_etf_data(symbol, period)
  asset_title = f"ETF — {symbol}"

if data is not None and not data.empty:
  # Calculate Indicators
  data["SMA_Short"] = data["close"].rolling(window=short_window).mean()
  data["SMA_Long"] = data["close"].rolling(window=long_window).mean()

  # Backtest Logic
  data["Signal"] = 0
  data.loc[data["SMA_Short"] > data["SMA_Long"], "Signal"] = 1
  data.loc[data["SMA_Short"] <= data["SMA_Long"], "Signal"] = -1

  data["Market_Returns"] = data["close"].pct_change()
  data["Strategy_Returns"] = data["Market_Returns"] * data["Signal"].shift(1)

  data["Cumulative_Market"] = (1 + data["Market_Returns"].fillna(0)).cumprod()
  data["Cumulative_Strategy"] = (
      1 + data["Strategy_Returns"].fillna(0)
  ).cumprod()

  latest_close = data["close"].iloc[-1]
  prev_close = data["close"].iloc[-2]
  price_change = ((latest_close - prev_close) / prev_close) * 100

  latest_short = data["SMA_Short"].iloc[-1]
  latest_long = data["SMA_Long"].iloc[-1]
  strat_total_return = (data["Cumulative_Strategy"].iloc[-1] - 1) * 100
  market_total_return = (data["Cumulative_Market"].iloc[-1] - 1) * 100

  # Metrics Row 1: Live Status
  col1, col2, col3, col4 = st.columns(4)
  with col1:
    st.metric(
        "Latest Close Price",
        f"${latest_close:,.2f}",
        f"{price_change:+.2f}%",
    )
  with col2:
    st.metric(f"Short SMA ({short_window})", f"${latest_short:,.2f}")
  with col3:
    st.metric(f"Long SMA ({long_window})", f"${latest_long:,.2f}")
  with col4:
    signal = (
        "🟢 BULLISH (BUY)"
        if latest_short > latest_long
        else "🔴 BEARISH (SELL)"
    )
    st.metric("Current Signal Status", signal)

  # Metrics Row 2: Backtest Performance
  st.markdown("<br>", unsafe_allow_html=True)
  bcol1, bcol2 = st.columns(2)
  with bcol1:
    st.metric(
        "🤖 Strategy Backtest Return",
        f"{strat_total_return:+.2f}%",
        help="Cumulative return using Moving Average Crossover signals",
    )
  with bcol2:
    st.metric(
        "📊 Buy & Hold Benchmark Return",
        f"{market_total_return:+.2f}%",
        help="Cumulative return of simply holding the asset",
    )

  st.markdown("---")
  st.subheader(f"📊 Price & Moving Average Action: {asset_title}")

  # Plot 1: Price & MAs
  fig_price = px.line(
      data,
      y=["close", "SMA_Short", "SMA_Long"],
      title=f"{asset_title} — Moving Average Crossover Model",
      template="plotly_dark",
  )
  fig_price.update_layout(
      xaxis_title="Date",
      yaxis_title="Price (USD)",
      legend_title="Indicators",
      hovermode="x unified",
      paper_bgcolor="rgba(0,0,0,0)",
      plot_bgcolor="rgba(0,0,0,0)",
  )
  st.plotly_chart(fig_price, use_container_width=True)

  # Plot 2: Backtest Equity Curve
  st.subheader("📈 Backtest Performance: Strategy vs Market Benchmark")
  fig_pnl = px.line(
      data,
      y=["Cumulative_Strategy", "Cumulative_Market"],
      title=f"{asset_title} — Cumulative Growth (Base = 1.0)",
      template="plotly_dark",
  )
  fig_pnl.update_layout(
      xaxis_title="Date",
      yaxis_title="Growth Multiplier",
      legend_title="Portfolio",
      hovermode="x unified",
      paper_bgcolor="rgba(0,0,0,0)",
      plot_bgcolor="rgba(0,0,0,0)",
  )
  st.plotly_chart(fig_pnl, use_container_width=True)

  # Data Table Expander
  with st.expander("🔍 View Raw Historical Data & Strategy Table"):
    st.dataframe(data.tail(20), use_container_width=True)

else:
  st.error("Failed to load market data. Please check your network or inputs.")

  # ... (your existing charts, metrics, and logic in app.py) ...

# === ADD THIS AT THE VERY BOTTOM OF app.py ===

from execution import execute_trade_signal, get_account_summary

# ... (your existing Streamlit app layout, charts, and strategy logic above) ...

# === ALPACA LIVE PAPER EXECUTION & ACCOUNT STATUS SIDEBAR ===
st.sidebar.markdown("---")
st.sidebar.subheader("⚡ Alpaca Live Paper Execution")

trade_symbol = st.sidebar.text_input("Asset Symbol", value="AAPL")
trade_qty = st.sidebar.number_input("Quantity", min_value=1.0, value=1.0, step=1.0)
trade_action = st.sidebar.selectbox("Order Action", ["BUY", "SELL"])

if st.sidebar.button("🚀 Execute Paper Order"):
  with st.spinner(f"Submitting {trade_action} order for {trade_symbol}..."):
    order = execute_trade_signal(
        symbol=trade_symbol, signal=trade_action, qty=trade_qty
    )
    if order:
      st.sidebar.success(f"Order Placed! ID: {str(order.id)[:8]}...")
      st.balloons()
    else:
      st.sidebar.error("Failed to execute order. Check terminal logs.")

st.sidebar.markdown("---")
st.sidebar.subheader("📊 Alpaca Account Status")

account_info = get_account_summary()
if account_info:
  st.sidebar.metric("Paper Cash", f"${account_info['cash']:,.2f}")
  st.sidebar.metric("Buying Power", f"${account_info['buying_power']:,.2f}")

  st.sidebar.markdown("**Open Positions:**")
  if account_info["positions"]:
    for pos in account_info["positions"]:
      st.sidebar.write(
          f"- **{pos.symbol}**: {pos.qty} shares (P/L: ${float(pos.unrealized_pl):,.2f})"
      )
  else:
    st.sidebar.info("No open positions currently held.")
else:
  st.sidebar.error("Could not fetch account data.")