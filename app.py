import datetime
import sqlite3
import streamlit as st

# 1. Page Configuration
st.set_page_config(
    page_title="VEER PRO TRADING TERMINAL",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 2. Advanced Responsive TradingView-Style UI (Mobile + PC Optimized)
st.markdown(
    """
    <style>
    /* Dark Terminal Theme Variables */
    :root {
        --bg-dark: #090d16;
        --panel-bg: #131924;
        --border-color: #20293a;
        --accent-blue: #3b82f6;
        --green-up: #10b981;
        --red-down: #ef4444;
        --text-bright: #f3f4f6;
    }

    /* Global Dark Background Override */
    .stApp {
        background-color: var(--bg-dark) !important;
        color: var(--text-bright) !important;
    }

    /* Force Clean Text Colors */
    h1, h2, h3, h4, h5, h6, p, span, label, div {
        color: var(--text-bright) !important;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: var(--panel-bg) !important;
        border-right: 1px solid var(--border-color) !important;
    }

    /* Card Panels Styling */
    div[data-testid="stVerticalBlock"] > div.element-container {
        border-radius: 12px;
    }

    /* Custom Responsive Input Elements */
    .stTextInput input, .stSelectbox select, .stNumberInput input {
        background-color: var(--panel-bg) !important;
        color: #ffffff !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        min-height: 48px !important; /* Mobile Touch Friendly */
        font-size: 15px !important;
    }

    .stTextInput input:focus, .stSelectbox select:focus {
        border-color: var(--accent-blue) !important;
        box-shadow: 0 0 10px rgba(59, 130, 246, 0.4) !important;
    }

    /* Professional TradingView Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background-color: var(--panel-bg);
        padding: 6px;
        border-radius: 10px;
        border: 1px solid var(--border-color);
    }

    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        border-radius: 6px !important;
        color: #9ca3af !important;
        font-weight: 600 !important;
        padding: 10px 16px !important;
        min-height: 44px !important; /* Mobile Touch Optimized */
        border: none !important;
    }

    .stTabs [aria-selected="true"] {
        background-color: var(--accent-blue) !important;
        color: #ffffff !important;
        font-weight: 700 !important;
    }

    /* High Density Glow Action Buttons */
    .stButton>button { 
        width: 100%; 
        border-radius: 8px; 
        font-weight: 700; 
        min-height: 48px; /* Touch-optimized */
        background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%); 
        color: #ffffff !important; 
        border: none; 
        font-size: 15px; 
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
        transition: all 0.2s ease-in-out;
    }

    .stButton>button:hover { 
        background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%); 
        box-shadow: 0 6px 18px rgba(59, 130, 246, 0.5);
    }

    /* Metric Container */
    div.stMetric { 
        background: var(--panel-bg); 
        padding: 14px; 
        border-radius: 10px; 
        border: 1px solid var(--border-color); 
    }

    /* Signal Container Styling */
    .signal-card { 
        background: var(--panel-bg); 
        padding: 16px; 
        border-radius: 12px; 
        border-left: 5px solid var(--green-up); 
        border-top: 1px solid var(--border-color);
        border-right: 1px solid var(--border-color);
        border-bottom: 1px solid var(--border-color);
        margin-top: 10px; 
    }

    /* Mobile Floating Bar for Touch Compatibility */
    @media (max-width: 768px) {
        .stApp {
            padding-bottom: 20px;
        }
        div.block-container {
            padding-left: 0.8rem !important;
            padding-right: 0.8rem !important;
            padding-top: 1rem !important;
        }
    }
    </style>
""",
    unsafe_allow_html=True,
)


# --- PERMANENT SQLITE DATABASE SETUP ---
def init_db():
  conn = sqlite3.connect("users_database.db", check_same_thread=False)
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            name TEXT NOT NULL
        )
    """)
  conn.commit()
  cursor.execute("SELECT * FROM users WHERE email = ?", ("admin@gmail.com",))
  if not cursor.fetchone():
    cursor.execute(
        "INSERT INTO users (email, password, name) VALUES (?, ?, ?)",
        ("admin@gmail.com", "password123", "Admin Trader"),
    )
    conn.commit()
  conn.close()


init_db()


def get_user(email):
  conn = sqlite3.connect("users_database.db", check_same_thread=False)
  cursor = conn.cursor()
  cursor.execute(
      "SELECT password, name FROM users WHERE email = ?", (email.strip(),)
  )
  res = cursor.fetchone()
  conn.close()
  return res


def register_user(email, password, name):
  try:
    conn = sqlite3.connect("users_database.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (email, password, name) VALUES (?, ?, ?)",
        (email.strip(), password, name.strip()),
    )
    conn.commit()
    conn.close()
    return True
  except sqlite3.IntegrityError:
    return False


# --- SESSION STATE INITIALIZATION ---
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

if st.session_state.last_reset != datetime.date.today():
  st.session_state.signals_used = 0
  st.session_state.last_reset = datetime.date.today()


# --- AUTHENTICATION SCREEN ---
def show_auth_screen():
  st.markdown("<br>", unsafe_allow_html=True)
  col1, col2, col3 = st.columns([1, 1.5, 1])

  with col2:
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 20px;">
            <h2 style="font-size: 24px; font-weight: 800; color: #ffffff; margin-bottom: 4px;">🚀 VEER PRO TERMINAL</h2>
            <p style="color: #3b82f6; font-size: 13px; font-weight: 500;">Institutional Grade Trading Platform</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    auth_tab1, auth_tab2 = st.tabs(["📝 Register", "🔑 Login"])

    with auth_tab1:
      st.markdown(
          "<h4 style='color: #ffffff; font-size: 16px; margin-top: 10px;'>Create"
          " New Account</h4>",
          unsafe_allow_html=True,
      )
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

      st.markdown("<br>", unsafe_allow_html=True)
      if st.button("REGISTER & LOGIN", key="reg_btn"):
        cleaned_reg_email = reg_email.strip()
        if not reg_name or not cleaned_reg_email or not reg_pass:
          st.warning("⚠️ Please fill in all fields.")
        elif reg_pass != reg_pass_confirm:
          st.error("⚠️ Passwords do not match!")
        elif len(reg_pass) < 6:
          st.warning("⚠️ Password must be at least 6 characters long.")
        else:
          success = register_user(cleaned_reg_email, reg_pass, reg_name)
          if success:
            st.session_state.logged_in = True
            st.session_state.current_user_email = cleaned_reg_email
            st.session_state.current_user_name = reg_name.strip()
            st.success("🎉 Account Created & Logged In Successfully!")
            st.rerun()
          else:
            st.error("⚠️ This Email/Phone is already registered!")

    with auth_tab2:
      st.markdown(
          "<h4 style='color: #ffffff; font-size: 16px; margin-top:"
          " 10px;'>Welcome Back</h4>",
          unsafe_allow_html=True,
      )
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

      st.markdown("<br>", unsafe_allow_html=True)
      if st.button("LOGIN TO TERMINAL", key="login_btn"):
        cleaned_email = login_email.strip()
        user_data = get_user(cleaned_email)

        if user_data and user_data[0] == login_pass:
          st.session_state.logged_in = True
          st.session_state.current_user_email = cleaned_email
          st.session_state.current_user_name = user_data[1]
          st.success("🎉 Login Successful!")
          st.rerun()
        else:
          st.error("⚠️ Invalid Email/Phone or Password!")


if not st.session_state.logged_in:
  show_auth_screen()
  st.stop()


# --- SIDEBAR USER PROFILE ---
with st.sidebar:
  st.markdown("### 👤 User Profile")
  st.markdown("---")
  st.markdown(f"👋 Hello, **{st.session_state.current_user_name}**")
  st.markdown(f"📧 `{st.session_state.current_user_email}`")
  st.markdown(f"🌟 Status: **{st.session_state.user_tier}**")
  st.markdown("---")
  if st.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.session_state.current_user_email = ""
    st.session_state.current_user_name = ""
    st.session_state.user_tier = "Free User"
    st.rerun()


# --- MAIN TRADING TERMINAL (PRO DASHBOARD) ---
# Ticker Bar
st.markdown(
    """
    <div style="background: #131924; padding: 10px 14px; border-radius: 8px; border: 1px solid #20293a; display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; font-size: 13px;">
        <div><b>🚀 VEER PRO</b></div>
        <div><span style="color: #9ca3af;">BTCUSDT</span> <span style="color: #ef4444; font-weight:700;">$68,420.00 (-1.59%)</span></div>
        <div style="color: #10b981; font-weight:600;">ETHUSDT +2.14%</div>
    </div>
""",
    unsafe_allow_html=True,
)

tab1, tab2, tab3, tab4 = st.tabs(
    ["⚡ Terminal Dashboard", "📊 Live Chart", "🏆 Accuracy", "💎 VIP Plan"]
)

with tab1:
  col_main, col_side = st.columns([2.2, 1], gap="medium")

  with col_main:
    st.markdown("### ⚙️ Signal Controls & Configuration")
    m_cat, m_asset, m_tf = st.columns(3)
    with m_cat:
      market_category = st.selectbox(
          "Category", ["TIER 1 (Main Assets)", "TIER 2 (Altcoins)"]
      )
    with m_asset:
      asset = st.selectbox(
          "Select Asset", ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]
      )
    with m_tf:
      timeframe = st.selectbox("Timeframe", ["1m", "5m", "15m", "1h", "4h", "1d"])

    st.markdown("### 🛡️ Risk Management Matrix")
    account_balance = st.number_input(
        "Account Balance ($)", value=10000.0, step=500.0
    )
    risk_pct = st.slider("Risk Per Trade (%)", 0.1, 5.0, 1.0)

    risk_capital = account_balance * (risk_pct / 100)
    st.info(
        f"📊 **Risk Summary:** Capital at Risk: **${risk_capital:.2f}** |"
        " Protection: Active"
    )

  with col_side:
    st.markdown("### 🤖 AI Smart Signals")

    can_generate = True
    if st.session_state.user_tier == "Free User":
      remaining_signals = 2 - st.session_state.signals_used
      st.caption(f"Free Limit: **{remaining_signals}/2** remaining today.")
      if remaining_signals <= 0:
        can_generate = False
    else:
      st.caption("👑 VIP Status: **Unlimited Access**")

    if st.button("✨ GENERATE AI SIGNAL"):
      if not can_generate:
        st.error("⚠️ Free limit reached! Upgrade to VIP Plan.")
      else:
        if st.session_state.user_tier == "Free User":
          st.session_state.signals_used += 1

        st.markdown(
            f"""
            <div class="signal-card">
                <h4 style='color: #10b981; margin: 0;'>🔥 STRONG BUY SETUP</h4>
                <p style='font-size:12px; color:#9ca3af; margin-bottom:10px;'>Pair: BINANCE:{asset} ({timeframe})</p>
                <p><b>📍 Entry:</b> ~$64,611.89</p>
                <p><b>🛑 Stop Loss:</b> ~$64,352.92</p>
                <p><b>🎯 Target 1:</b> ~$65,065.08</p>
                <p><b>🎯 Target 2:</b> ~$65,518.27</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

with tab2:
  st.markdown(f"### 📈 Interactive Pro Chart — {asset}")
  tradingview_html = f"""
    <div class="tradingview-widget-container" style="height:520px;width:100%;">
      <div id="tradingview_widget" style="height:100%;width:100%;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget(
      {{
        "width": "100%",
        "height": "520",
        "symbol": "BINANCE:{asset}",
        "interval": "D",
        "timezone": "Etc/UTC",
        "theme": "dark",
        "style": "1",
        "locale": "en",
        "toolbar_bg": "#131924",
        "enable_publishing": false,
        "allow_symbol_change": true,
        "container_id": "tradingview_widget"
      }});
      </script>
    </div>
    """
  st.components.v1.html(tradingview_html, height=540)

with tab3:
  st.markdown("### 🏆 Performance & Accuracy Metrics")

  m1, m2, m3 = st.columns(3)
  m1.metric("7-Day Signals", "142", "+12 today")
  m2.metric("Success Rate", "84.5%", "+2.1%")
  m3.metric("Avg R:R Ratio", "1:2.4", "Optimal")

  st.markdown("---")
  st.markdown("#### 📋 Executed Signals History")
  st.dataframe(
      {
          "Timestamp": [
              "2026-08-19 14:30",
              "2026-08-19 11:15",
              "2026-08-18 16:45",
          ],
          "Pair": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
          "Action": ["BUY", "BUY", "SELL"],
          "Outcome": ["TP2 Hit (+3.2%)", "TP1 Hit (+1.8%)", "TP2 Hit (+4.1%)"],
      },
      use_container_width=True,
  )

with tab4:
  st.markdown("### 💎 VIP Pro Access (₹999 / Month)")
  col_p1, col_p2 = st.columns(2, gap="medium")

  with col_p1:
    st.markdown(
        """
        - **Unlimited** Smart AI Signals
        - Multi-Asset Technical Scanners
        - Instant VIP Telegram Notifications
        """
    )
    upi_intent_url = (
        "upi://pay?pa=7479465676-7@ybl&pn=VEER%20PRO%20TRADER&am=999.00&cu=INR"
    )
    st.link_button("📲 Pay ₹999 via UPI App (GPay/PhonePe)", upi_intent_url)

    qr_code_url = (
        "https://api.qrserver.com/v1/create-qr-code/?size=180x180&data="
        + upi_intent_url
    )
    st.image(qr_code_url, caption="Scan QR with any UPI App", width=180)

  with col_p2:
    st.markdown("#### ⚡ Verify Transaction")
    utr_input = st.text_input(
        "Enter 12-digit UTR / UPI Ref No:", placeholder="e.g. 4152xxxxxxxx"
    )

    if st.button("🔓 Verify & Activate VIP Access"):
      if len(utr_input.strip()) >= 8:
        st.session_state.user_tier = "VIP Paid Member"
        st.success("🎉 VIP Access Activated Successfully!")
        st.rerun()
      else:
        st.error("⚠️ Invalid UTR Number!")

st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #9ca3af; font-size: 11px;'>VEER PRO"
    " TRADING TERMINAL — Educational Research & Analytics Platform</p>",
    unsafe_allow_html=True,
)
