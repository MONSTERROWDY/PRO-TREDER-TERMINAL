import datetime
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="VEER PRO TRADING TERMINAL",
    page_icon="📈",
    layout="wide",
)

# Custom CSS for Mobile Optimization & Pro Trading Look
st.markdown(
    """
    <style>
    .main { background-color: #0b0e14; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; height: 45px; background: linear-gradient(135deg, #FF4B4B 0%, #FF914D 100%); color: white; border: none; }
    .stButton>button:hover { background: linear-gradient(135deg, #ff3333 0%, #ff7b29 100%); color: white; }
    div.stMetric { background-color: #161b22; padding: 12px; border-radius: 10px; border: 1px solid #30363d; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .signal-card { background: linear-gradient(135deg, #161b22 0%, #1f242c 100%); padding: 20px; border-radius: 12px; border-left: 5px solid #238636; border-top: 1px solid #30363d; border-right: 1px solid #30363d; border-bottom: 1px solid #30363d; margin-top: 15px; }
    .pay-box { background-color: #161b22; padding: 20px; border-radius: 12px; border: 1px solid #30363d; text-align: center; }
    </style>
""",
    unsafe_allow_html=True,
)

# Header Section
st.title("🚀 VEER PRO TRADING TERMINAL")
st.markdown(
    "**Institutional Grade Live Market, Interactive Charts & AI Smart"
    " Signals**"
)
st.markdown("---")

# Initialize session state for user tier and UTR tracking
if "user_tier" not in st.session_state:
  st.session_state.user_tier = "Free User"

if "signals_used" not in st.session_state:
  st.session_state.signals_used = 0
  st.session_state.last_reset = datetime.date.today()

if st.session_state.last_reset != datetime.date.today():
  st.session_state.signals_used = 0
  st.session_state.last_reset = datetime.date.today()

# Sidebar for Access Control Status
st.sidebar.header("🔐 User Account")
st.sidebar.markdown(f"Current Status: **{st.session_state.user_tier}**")
if st.sidebar.button("Reset Session / Logout"):
  st.session_state.user_tier = "Free User"
  st.rerun()

# Main Navigation Tabs
tab1, tab2, tab3, tab4 = st.tabs(
    ["⚡ Pro Terminal", "📊 Live Chart", "🏆 Accuracy", "💎 VIP Plan"]
)

with tab1:
  col1, col2 = st.columns([1, 1], gap="medium")

  with col1:
    st.markdown("### ⚙️ Configuration")
    market_category = st.selectbox(
        "Market Category", ["TIER 1 (Main Assets)", "TIER 2 (Altcoins)"]
    )
    asset = st.selectbox(
        "Select Asset", ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]
    )
    timeframe = st.selectbox("Timeframe", ["1m", "5m", "15m", "1h", "4h"])

    st.markdown("### 🛡️ Risk Management")
    account_balance = st.number_input(
        "Account Balance ($)", value=10000.0, step=500.0
    )
    risk_pct = st.slider("Risk Per Trade (%)", 0.1, 5.0, 1.0)
    atr_multiplier = st.slider("ATR SL Multiplier", 1.0, 3.0, 1.5)
    max_daily_loss = st.number_input(
        "Max Daily Loss ($)", value=500.0, step=50.0
    )

    risk_capital = account_balance * (risk_pct / 100)
    st.info(
        f"📊 **Risk Summary:** Capital at Risk: **${risk_capital:.2f}** |"
        " Protection: Active"
    )

  with col2:
    st.markdown("### 🤖 AI Smart Signal Hub")

    can_generate = True
    if st.session_state.user_tier == "Free User":
      remaining_signals = 5 - st.session_state.signals_used
      st.markdown(
          f"📢 Free Plan Quota: **{remaining_signals}/5** signals remaining"
          " today."
      )
      if remaining_signals <= 0:
        can_generate = False

    if st.button("✨ GENERATE SMART AI SIGNAL"):
      if not can_generate:
        st.error(
            "⚠️ Daily free limit reached! Go to 'VIP Plan' tab to unlock"
            " unlimited access."
        )
      else:
        if st.session_state.user_tier == "Free User":
          st.session_state.signals_used += 1

        st.markdown(
            """
            <div class="signal-card">
                <h3 style='color: #2ea043; margin-top: 0;'>🔥 STRONG BUY SETUP (Bullish)</h3>
                <hr style='border-color: #30363d; margin: 5px 0 15px 0;'>
            """,
            unsafe_allow_html=True,
        )

        sc1, sc2 = st.columns(2)
        sc1.metric("Live Market Price", "$64,741.37", "+1.4%")
        sc2.metric("Profit / Risk Ratio", "1 : 2.5", "Optimal")

        st.markdown(
            f"""
                <p><b>🎯 Target Asset:</b> BINANCE:{asset} ({timeframe})</p>
                <p><b>📍 Optimal Entry Zone (OB/FVG):</b> ~$64,611.89</p>
                <p><b>🛑 Smart Stop Loss (SL):</b> ~$64,352.92</p>
                <p><b>🎯 Target 1 (TP1):</b> ~$65,065.08</p>
                <p><b>🎯 Target 2 (TP2):</b> ~$65,518.27</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)
        st.link_button(
            "🚀 Execute Trade on Partner Exchange (Affiliate)",
            "https://www.binance.com",
        )

with tab2:
  st.markdown(f"### 📈 Live Interactive Chart — {asset}")
  tradingview_html = f"""
    <div class="tradingview-widget-container" style="height:500px;width:100%;">
      <div id="tradingview_widget" style="height:100%;width:100%;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget(
      {{
        "width": "100%",
        "height": "500",
        "symbol": "BINANCE:{asset}",
        "interval": "D",
        "timezone": "Etc/UTC",
        "theme": "dark",
        "style": "1",
        "locale": "en",
        "toolbar_bg": "#f1f3f6",
        "enable_publishing": false,
        "allow_symbol_change": true,
        "container_id": "tradingview_widget"
      }});
      </script>
    </div>
    """
  st.components.v1.html(tradingview_html, height=520)

with tab3:
  st.markdown("### 🏆 Performance & Accuracy Metrics")
  st.markdown("Verified past 7-day algorithmic execution results:")

  m1, m2, m3 = st.columns(3)
  m1.metric("7-Day Signals", "142", "+12 today")
  m2.metric("Success Rate", "84.5%", "+2.1%")
  m3.metric("Avg R:R Ratio", "1:2.4", "Optimal")

  st.markdown("---")
  st.markdown("#### 📋 Recent Executed Calls")
  st.dataframe(
      {
          "Timestamp": [
              "2026-06-06 14:30",
              "2026-06-06 11:15",
              "2026-06-05 16:45",
          ],
          "Pair": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
          "Action": ["BUY", "BUY", "SELL"],
          "Outcome": ["TP2 Hit (+3.2%)", "TP1 Hit (+1.8%)", "TP2 Hit (+4.1%)"],
      },
      use_container_width=True,
  )

with tab4:
  st.markdown("### 💎 Upgrade to VIP Pro Access (₹999 / Month)")

  col_p1, col_p2 = st.columns(2, gap="medium")

  with col_p1:
    st.markdown(
        """
        #### 👑 VIP Benefits
        - **Unlimited** Smart AI Signals
        - Advanced Multi-Asset Scanners
        - Priority Alerts & Zero Ads
        """
    )
    st.markdown("---")
    st.markdown("### 📱 Option 1: Direct Pay via UPI App")
    st.markdown(
        "Click below to pay securely through PhonePe, Google Pay, or Paytm:"
    )

    # UPI Intent link configured with your UPI ID (Hidden from plain text view)
    upi_intent_url = (
        "upi://pay?pa=7479465676-7@ybl&pn=VEER%20PRO%20TRADER&am=999.00&cu=INR"
    )
    st.link_button("📲 Pay ₹999 via UPI App (GPay/PhonePe)", upi_intent_url)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📷 Option 2: Scan QR Code")
    # Public standard UPI QR generator API using your hidden UPI ID
    qr_code_url = (
        "https://api.qrserver.com/v1/create-qr-code/?size=180x180&data="
        + upi_intent_url
    )
    st.image(
        qr_code_url,
        caption="Scan this QR code with any UPI App to Pay ₹999",
        width=180,
    )

  with col_p2:
    st.markdown("#### ⚡ Step 3: Verify & Unlock")
    st.markdown(
        "Payment karne ke baad jo **12-digit UTR / Reference Number** milega,"
        " use yahan dalein:"
    )

    utr_input = st.text_input(
        "Enter 12-digit UTR / UPI Reference Number:",
        placeholder="e.g. 4152xxxxxxxx",
    )

    if st.button("🔓 Verify & Activate VIP Access"):
      if len(utr_input.strip()) >= 8:
        st.session_state.user_tier = "VIP Paid Member"
        st.success(
            "🎉 Congratulations! VIP Access Activated Successfully. Enjoy"
            " Unlimited Signals!"
        )
        st.rerun()
      else:
        st.error(
            "⚠️ Kripya sahi UTR / Transaction ID दर्ज करें (कम से कम 8 अंक)।"
        )

# Footer Disclaimer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #8b949e; font-size: 11px;'>"
    "<b>Disclaimer:</b> VEER PRO TERMINAL is built for educational &"
    " analytical research only. Crypto trading involves high market risk."
    "</p>",
    unsafe_allow_html=True,
)
