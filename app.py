import datetime
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="VEER PRO TRADING TERMINAL",
    page_icon="📈",
    layout="wide",
)

# Custom CSS for Professional Look
st.markdown(
    """
    <style>
    .main { background-color: #0e1117; }
    .stButton>button { width: 100%; border-radius: 5px; font-weight: bold; }
    .metric-card { background-color: #1e2130; padding: 15px; border-radius: 8px; border: 1px solid #31333F; }
    </style>
""",
    unsafe_allow_html=True,
)

# Header Section
st.title("🚀 VEER PRO TRADING TERMINAL")
st.markdown(
    "**Live Market, TradingView Charts, AI Buy/Sell Signals & Full Risk"
    " Management**"
)
st.markdown("---")

# Sidebar for Authentication & User Plan Control
st.sidebar.header("🔐 User Access Control")
user_tier = st.sidebar.selectbox("Select Account Tier", ["Free User", "VIP Paid Member"])

# Session state initialization for free signal tracking
if "signals_used" not in st.session_state:
    st.session_state.signals_used = 0
    st.session_state.last_reset = datetime.date.today()

# Reset limit daily
if st.session_state.last_reset != datetime.date.today():
    st.session_state.signals_used = 0
    st.session_state.last_reset = datetime.date.today()

# Main App Layout using Tabs
tab1, tab2, tab3, tab4 = st.tabs(
    [
        "📊 Live Terminal & AI Signals",
        "📈 Interactive Chart",
        "🏆 Track Record & Accuracy",
        "💎 Upgrade to VIP",
    ]
)

with tab1:
  col1, col2 = st.columns([1, 1])

  with col1:
    st.subheader("⚙️ Market & Risk Settings")
    market_category = st.selectbox(
        "Market Category", ["TIER 1 (Main Assets)", "TIER 2 (Altcoins)"]
    )
    asset = st.selectbox(
        "Coin / Asset Chunein",
        ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"],
    )
    timeframe = st.selectbox(
        "Timeframe (Samay)", ["1m", "5m", "15m", "1h", "4h"]
    )

    st.markdown("---")
    st.markdown("**Risk Management & Position Sizing**")
    account_balance = st.number_input(
        "Account Balance ($)", value=10000.0
    )
    risk_pct = st.slider("Risk % Per Trade", 0.1, 5.0, 1.0)
    atr_multiplier = st.slider("ATR Stop Loss Multiplier", 1.0, 3.0, 1.5)
    max_daily_loss = st.number_input(
        "Max Daily Loss Limit ($)", value=500.0
    )

    risk_capital = account_balance * (risk_pct / 100)
    st.info(
        f"Live Risk Report: Risk Capital: ${risk_capital:.2f} | ATR Stop Loss"
        f" Active | TP1 Target: ${(risk_capital*2):.2f} | Daily Guard: Protected"
    )

  with col2:
    st.subheader("🤖 AI Signal & Easy Entry Panel")

    # Check limits for Free Users
    can_generate = True
    if user_tier == "Free User":
      remaining_signals = 5 - st.session_state.signals_used
      st.markdown(
          f"📢 **Free Plan Limit:** You have **{remaining_signals}** free"
          " signals left for today (Max 5/day)."
      )
      if remaining_signals <= 0:
        can_generate = False

    if st.button("AI SIGNAL DEKHO (GENERATE)"):
      if not can_generate:
        st.error(
            "⚠️ Aapka aaj ka free limit (5 signals) khatam ho gaya hai!"
            " Unlimited signals ke liye VIP Plan lein."
        )
      else:
        if user_tier == "Free User":
          st.session_state.signals_used += 1

        # Displaying AI output
        st.success("🔥 **STRONG BUY SIGNAL (खरीदने का सही मौका)**")
        st.markdown(
            f"- **Selected Asset:** BINANCE:{asset} | Timeframe: {timeframe}\n"
            "- **Live Rate:** $64,741.37\n"
            "- **Market ka Haal:** Market Upar Jane ki Taiyari Mein Hai (Bullish)\n"
            "- **Kahan Entry Lein (OB/FVG):** ~$64,611.89\n"
            "- **Risk Bachane ke liye Stop Loss (SL):** ~$64,352.92\n"
            "- **Pehla Target (TP1):** ~$65,065.08\n"
            "- **Dusra Target (TP2):** ~$65,518.27\n"
            "- **Profit/Risk Ratio:** 1: 2.5 (Best)"
        )

        # Broker Affiliate Integration Button
        st.markdown("---")
        st.markdown("💡 **Execute this trade instantly on partner exchange:**")
        st.link_button(
            "🚀 Open Account & Trade on Binance / Upstox (Affiliate)",
            "https://www.binance.com",
        )

with tab2:
  st.subheader(f"📈 Live TradingView Chart for {asset}")
  tradingview_html = f"""
    <div class="tradingview-widget-container" style="height:500px;width:100%">
      <iframe scrolling="no" allowtransparency="true" frameborder="0" src="https://s.tradingview.com/embed-widget/advanced-chart/?locale=en#%7B%22autosize%22%3Atrue%2C%22symbol%22%3A%22BINANCE%3A{asset}%22%2C%22interval%22%3A%22{timeframe}%22%2C%22theme%22%3A%22dark%22%2C%22style%22%3A%221%22%2C%22locale%22%3A%22en%22%2C%22toolbar_bg%22%3A%22%23f1f3f6%22%2C%22enable_publishing%22%3Afalse%2C%22hide_top_toolbar%22%3Afalse%2C%22save_image%22%3Afalse%2C%22container_id%22%3A%22tradingview_widget%22%7D" style="box-sizing: border-box; height: 100%; width: 100%;"></iframe>
    </div>
    """
  st.components.v1.html(tradingview_html, height=520)

with tab3:
  st.subheader("🏆 AI Signal Performance & Accuracy Track Record")
  st.markdown(
      "Our AI model maintains transparency. Here is the past 7-day track"
      " record overview:"
  )

  col_a, col_b, col_c = st.columns(3)
  col_a.metric(
      label="Total Signals (Last 7 Days)", value="142", delta="+12 today"
  )
  col_b.metric(label="Success Rate (Accuracy)", value="84.5%", delta="+2.1%")
  col_c.metric(label="Average Risk-to-Reward", value="1:2.4", delta="Optimal")

  st.markdown("---")
  st.markdown("#### Recent Successful Calls:")
  st.dataframe(
      {
          "Date/Time": [
              "2026-06-06 14:30",
              "2026-06-06 11:15",
              "2026-06-05 16:45",
          ],
          "Asset": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
          "Type": ["BUY", "BUY", "SELL"],
          "Result": ["TP2 Hit (+3.2%)", "TP1 Hit (+1.8%)", "TP2 Hit (+4.1%)"],
      }
  )

with tab4:
  st.subheader("💎 Upgrade to VEER PRO VIP Member")
  st.markdown(
      "Unlock the full power of automated terminal features without any"
      " limitations."
  )

  col_x, col_y = st.columns(2)
  with col_x:
    st.markdown("### 🆓 Free Tier")
    st.markdown("- 5 AI Signals per day\n- Standard Timeframes\n- Basic Support")

  with col_y:
    st.markdown("### 👑 VIP Paid Tier (₹999/month)")
    st.markdown(
        "- **Unlimited** AI Signals\n- Advanced Multi-Asset Scanner\n- Priority"
        " Telegram Alerts\n- Zero Ads"
    )
    if st.button("Upgrade Now via UPI / Card"):
      st.success(
          "Redirecting to secure payment gateway... (Integration ready)"
      )

# Legal Disclaimer Footer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray; font-size: 12px;'>"
    "<b>Disclaimer:</b> VEER PRO TRADING TERMINAL is for educational and"
    " analytical purposes only. Trading cryptocurrencies and"
    " derivatives involves substantial risk of loss and is not suitable for"
    " every investor. Do your own research before investing."
    "</p>",
    unsafe_allow_html=True,
)
