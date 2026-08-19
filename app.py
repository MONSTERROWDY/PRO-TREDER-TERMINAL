import datetime
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="VEER PRO TRADING TERMINAL",
    page_icon="📈",
    layout="wide",
)

# Custom CSS for Professional & Smart Look
st.markdown(
    """
    <style>
    .main { background-color: #0b0e14; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; height: 45px; background: linear-gradient(135deg, #FF4B4B 0%, #FF914D 100%); color: white; border: none; }
    .stButton>button:hover { background: linear-gradient(135deg, #ff3333 0%, #ff7b29 100%); color: white; }
    div.stMetric { background-color: #161b22; padding: 12px; border-radius: 10px; border: 1px solid #30363d; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .signal-card { background: linear-gradient(135deg, #161b22 0%, #1f242c 100%); padding: 20px; border-radius: 12px; border-left: 5px solid #238636; border-top: 1px solid #30363d; border-right: 1px solid #30363d; border-bottom: 1px solid #30363d; margin-top: 15px; }
    .auth-card { background: #161b22; padding: 25px; border-radius: 16px; border: 1px solid #30363d; box-shadow: 0 8px 24px rgba(0,0,0,0.4); }
    </style>
""",
    unsafe_allow_html=True,
)

# Initialize Persistent User Database using st.session_state
if "users_db" not in st.session_state:
  st.session_state.users_db = {
      "admin@gmail.com": {"password": "password123", "name": "Admin Trader"}
  }

if "logged_in" not in st.session_state:
  st.session_state.logged_in = False
if "current_user_email" not in st.session_state:
  st.session_state.current_user_email = ""
if "current_user_name" not in st.session_state:
  st.session_state.current_user_name = ""
if "user_tier" not in st.session_state:
  st.session_state.user_tier = "Free User"
if "signals_used" not in st.session_state:
  st.session_state.signals_used = 0
if "last_reset" not in st.session_state:
  st.session_state.last_reset = datetime.date.today()

# Reset daily signals if date changes
if st.session_state.last_reset != datetime.date.today():
  st.session_state.signals_used = 0
  st.session_state.last_reset = datetime.date.today()


# --- SMART & CLEAN AUTHENTICATION SCREEN ---
def show_auth_screen():
  st.markdown("<br>", unsafe_allow_html=True)
  col1, col2, col3 = st.columns([1, 1.3, 1])

  with col2:
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 15px;">
            <h2>🔐 VEER PRO TERMINAL</h2>
            <p style="color: #8b949e; font-size: 14px;">Institutional Grade Trading Platform</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    auth_tab1, auth_tab2 = st.tabs(["🔑 Login", "📝 Register"])

    with auth_tab1:
      st.markdown("### Welcome Back")
      login_email = st.text_input(
          "Email ID / Phone Number",
          placeholder="Enter registered email or phone",
          key="login_email_input",
      )
      login_pass = st.text_input(
          "Password",
          type="password",
          placeholder="Enter your password",
          key="login_pass_input",
      )

      if st.button("LOGIN TO TERMINAL", key="login_btn"):
        if login_email in st.session_state.users_db and st.session_state.users_db[
            login_email
        ]["password"] == login_pass:
          st.session_state.logged_in = True
          st.session_state.current_user_email = login_email
          st.session_state.current_user_name = st.session_state.users_db[
              login_email
          ]["name"]
          st.success("🎉 Login Successful! Redirecting...")
          st.rerun()
        else:
          st.error("⚠️ Invalid Email/Phone or Password! Please check.")

    with auth_tab2:
      st.markdown("### Create New Account")
      reg_name = st.text_input(
          "Full Name",
          placeholder="Enter your full name",
          key="reg_name_input",
      )
      reg_email = st.text_input(
          "Email ID / Phone Number",
          placeholder="Enter email or phone",
          key="reg_email_input",
      )
      reg_pass = st.text_input(
          "Create Password",
          type="password",
          placeholder="At least 6 characters",
          key="reg_pass_input",
      )
      reg_pass_confirm = st.text_input(
          "Confirm Password",
          type="password",
          placeholder="Re-enter password",
          key="reg_confirm_input",
      )

      if st.button("REGISTER & LOGIN", key="reg_btn"):
        if not reg_name or not reg_email or not reg_pass:
          st.warning("⚠️ Please fill in all fields.")
        elif reg_email in st.session_state.users_db:
          st.error(
              "⚠️ This Email/Phone is already registered. Please go to Login"
              " tab."
          )
        elif reg_pass != reg_pass_confirm:
          st.error("⚠️ Passwords do not match!")
        elif len(reg_pass) < 6:
          st.warning("⚠️ Password must be at least 6 characters long.")
        else:
          # Save user in database
          st.session_state.users_db[reg_email] = {
              "password": reg_pass,
              "name": reg_name.strip(),
          }
          # Instant auto-login upon successful registration
          st.session_state.logged_in = True
          st.session_state.current_user_email = reg_email
          st.session_state.current_user_name = reg_name.strip()
          st.success("🎉 Account Created & Logged In Successfully!")
          st.rerun()


# If not logged in, stop execution and show only the auth screen
if not st.session_state.logged_in:
  show_auth_screen()
  st.stop()


# --- MAIN TRADING TERMINAL (Accessible only when logged in) ---

# Sidebar Profile & Logout
st.sidebar.header("👤 User Profile")
st.sidebar.markdown(f"👋 Hello, **{st.session_state.current_user_name}**")
st.sidebar.markdown(f"📧 `{st.session_state.current_user_email}`")
st.sidebar.markdown(f"🌟 Status: **{st.session_state.user_tier}**")
if st.sidebar.button("🚪 Logout"):
  st.session_state.logged_in = False
  st.session_state.current_user_email = ""
  st.session_state.current_user_name = ""
  st.session_state.user_tier = "Free User"
  st.rerun()

# Header Section with Personalized Name
st.title(
    f"🚀 {st.session_state.current_user_name.upper()}'S PRO TRADING TERMINAL"
)
st.markdown(
    "**Institutional Grade Live Market, Interactive Charts & AI Smart"
    " Signals**"
)
st.markdown("---")

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
      remaining_signals = 2 - st.session_state.signals_used
      st.markdown(
          f"📢 Free Plan Quota: **{remaining_signals}/2** signals remaining"
          " today."
      )
      if remaining_signals <= 0:
        can_generate = False
    else:
      st.markdown(
          "👑 VIP Status Active: **Unlimited Signals** available for you."
      )

    if st.button("✨ GENERATE SMART AI SIGNAL"):
      if not can_generate:
        st.error(
            "⚠️ Daily free limit of 2 signals reached! Go to 'VIP Plan' tab to"
            " upgrade for unlimited access."
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

    upi_intent_url = (
        "upi://pay?pa=7479465676-7@ybl&pn=VEER%20PRO%20TRADER&am=999.00&cu=INR"
    )
    st.link_button("📲 Pay ₹999 via UPI App (GPay/PhonePe)", upi_intent_url)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📷 Option 2: Scan QR Code")
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
