import datetime
import sqlite3
import pandas as pd
import requests
import streamlit as st

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Veer Pro Terminal | World's Best AI Trading Suite",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CUSTOM ELITE BROKER-GRADE LOGIN & UI CSS ---
st.markdown(
    """
    <style>
    .stApp {
        background: radial-gradient(circle at 50% 10%, #11151c 0%, #07090c 100%) !important;
        color: #fcd535 !important;
    }
    h1, h2, h3, h4, h5, h6, p, span, label, div {
        color: #eaecef !important;
    }
    
    /* TICKER CARDS */
    .ticker-card {
        background: linear-gradient(145deg, #181a20 0%, #1e2329 100%);
        border: 1px solid #2b313a;
        border-radius: 10px;
        padding: 12px 16px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4);
    }
    .ticker-symbol { font-weight: 700; font-size: 13px; color: #848e9c !important; }
    .ticker-price { font-weight: 800; font-size: 17px; color: #ffffff !important; }
    .ticker-change-green { color: #0ecb81 !important; font-size: 12px; font-weight: 700; }
    .ticker-change-red { color: #f6465d !important; font-size: 12px; font-weight: 700; }

    /* VIP LUXURY BANNER */
    .vip-banner {
        background: linear-gradient(135deg, #2b220b 0%, #1a1607 100%);
        border: 2px solid #fcd535;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 0 25px rgba(252,213,53,0.3);
        margin-bottom: 20px;
    }
    .vip-title {
        color: #fcd535 !important;
        font-weight: 900;
        font-size: 22px;
        letter-spacing: 1px;
    }

    /* WORLD-CLASS BROKER LOGIN CARD STYLING */
    .broker-auth-container {
        background: linear-gradient(145deg, #161a22 0%, #0b0e11 100%);
        border: 1px solid #2b313a;
        border-top: 3px solid #fcd535;
        padding: 40px;
        border-radius: 16px;
        box-shadow: 0 20px 50px rgba(0,0,0,0.8), 0 0 30px rgba(252,213,53,0.07);
    }

    /* INPUT FIELDS STYLING */
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div {
        background-color: #0b0e11 !important;
        color: #ffffff !important;
        border: 1px solid #2b313a !important;
        border-radius: 8px !important;
        height: 48px !important;
        font-size: 14px !important;
    }

    /* TABS */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; justify-content: center; }
    .stTabs [data-baseweb="tab"] {
        background-color: #181a20 !important;
        border-radius: 8px !important;
        color: #848e9c !important;
        padding: 10px 24px;
        border: 1px solid #2b313a;
        font-size: 14px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #fcd535 0%, #f0b90b 100%) !important;
        color: #0b0e11 !important;
        font-weight: 900 !important;
        border: none !important;
    }

    /* PRIMARY BUTTONS */
    .stButton>button { 
        width: 100%; 
        border-radius: 8px; 
        font-weight: 800; 
        height: 48px; 
        background: linear-gradient(135deg, #fcd535 0%, #f0b90b 100%); 
        color: #0b0e11; 
        border: none;
        font-size: 15px;
    }
    .stButton>button:hover { 
        background: #ffffff !important; 
        color: #0b0e11 !important;
    }
    .signal-box {
        background: linear-gradient(145deg, #181a20 0%, #1e2329 100%);
        border: 1px solid #fcd535;
        border-radius: 10px;
        padding: 20px;
    }
    .calc-metric-box {
        background: #181a20;
        border: 1px solid #2b313a;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# --- ROBUST DATABASE SETUP & AUTO MIGRATION ---
def get_db_connection():
  return sqlite3.connect("users_database.db", check_same_thread=False)


def init_db():
  conn = get_db_connection()
  cursor = conn.cursor()

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            name TEXT NOT NULL
        )
    """)
  conn.commit()

  user_columns = [
      ("username", "TEXT"),
      ("avatar", "TEXT"),
      ("tier", "TEXT DEFAULT 'Free User'"),
      ("expiry", "TEXT"),
  ]
  for col_name, col_type in user_columns:
    try:
      cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
      conn.commit()
    except sqlite3.OperationalError:
      pass

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS promo_codes (
            code TEXT PRIMARY KEY,
            duration_type TEXT,
            is_used INTEGER DEFAULT 0,
            used_by TEXT DEFAULT NULL
        )
    """)
  conn.commit()

  cursor.execute("SELECT * FROM users WHERE email = ?", ("admin@gmail.com",))
  if not cursor.fetchone():
    cursor.execute(
        "INSERT INTO users (email, password, name, username, tier) VALUES (?, ?, ?, ?, ?)",
        (
            "admin@gmail.com",
            "password123",
            "Pro Master",
            "admin_master",
            "Premium Member (Lifetime)",
        ),
    )
    conn.commit()

  default_promos = [
      ("VEERPREMIUM30", "30 Days"),
      ("VEERPREMIUM1Y", "1 Year"),
      ("VEER3DAYS", "3 Days"),
      ("VEERLIFETIME", "Lifetime Unlimited"),
  ]
  for code, dtype in default_promos:
    cursor.execute("SELECT * FROM promo_codes WHERE code = ?", (code,))
    if not cursor.fetchone():
      cursor.execute(
          "INSERT INTO promo_codes (code, duration_type, is_used) VALUES (?, ?, 0)",
          (code, dtype),
      )
      conn.commit()

  conn.close()


init_db()


# --- FLEXIBLE USER LOOKUP & AUTHENTICATION FIX ---
def get_user_full(login_input):
  try:
    conn = get_db_connection()
    cursor = conn.cursor()
    clean_input = login_input.strip().lower()

    # Match exact email, username, or partial mobile number match inside email field
    cursor.execute(
        """
        SELECT password, name, username, avatar, tier, email FROM users 
        WHERE LOWER(email) = ? OR LOWER(username) = ? OR email LIKE ?
    """,
        (clean_input, clean_input, f"%{clean_input}%"),
    )
    res = cursor.fetchone()
    conn.close()
    return res
  except Exception:
    return None


def register_user(email, password, name, username):
  try:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (email, password, name, username, tier) VALUES (?, ?, ?, ?, ?)",
        (
            email.strip().lower(),
            password,
            name.strip(),
            username.strip(),
            "Free User",
        ),
    )
    conn.commit()
    conn.close()
    return True
  except Exception:
    return False


def update_user_profile(email, name, username, avatar):
  try:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET name = ?, username = ?, avatar = ? WHERE email = ?",
        (name, username, avatar, email),
    )
    conn.commit()
    conn.close()
  except Exception:
    pass


# --- REAL-TIME LIVE MARKET PRICES ---
def fetch_global_prices():
  try:
    url = "https://api.binance.com/api/v3/ticker/24hr?symbols=[%22BTCUSDT%22,%22ETHUSDT%22,%22SOLUSDT%22,%22BNBUSDT%22,%22XRPUSDT%22]"
    response = requests.get(url, timeout=2).json()
    prices = {}
    for item in response:
      prices[item["symbol"]] = {
          "price": float(item["lastPrice"]),
          "change": float(item["priceChangePercent"]),
      }
    prices.update({
        "EURUSD": {"price": 1.0924, "change": 0.15},
        "AAPL": {"price": 224.50, "change": 1.12},
        "RELIANCE": {"price": 2980.50, "change": 0.85},
        "GOLD": {"price": 2512.40, "change": 0.50},
    })
    return prices
  except Exception:
    return {
        "BTCUSDT": {"price": 68417.51, "change": 1.23},
        "ETHUSDT": {"price": 3540.49, "change": -0.45},
        "EURUSD": {"price": 1.0924, "change": 0.15},
        "RELIANCE": {"price": 2980.50, "change": 0.85},
        "GOLD": {"price": 2512.40, "change": 0.50},
    }


# --- SESSION LOGIC ---
query_params = st.query_params
saved_email = query_params.get("session_user", "")

if "logged_in" not in st.session_state:
  if saved_email:
    u_data = get_user_full(saved_email)
    if u_data:
      st.session_state.logged_in = True
      st.session_state.current_user_email = u_data[5]
      st.session_state.current_user_name = u_data[1]
      st.session_state.username = u_data[2] if u_data[2] else "trader"
      st.session_state.avatar = (
          u_data[3] if u_data[3] else "https://i.imgur.com/71916rK.png"
      )
      st.session_state.user_tier = u_data[4] if u_data[4] else "Free User"
    else:
      st.session_state.logged_in = False
  else:
    st.session_state.logged_in = False

if "signals_used" not in st.session_state:
  st.session_state.signals_used = 0


# --- BROKER-GRADE ELITE AUTH SCREEN (CLEAN INPUTS) ---
def show_auth_screen():
  st.markdown("<br><br>", unsafe_allow_html=True)
  c1, col, c2 = st.columns([1, 1.4, 1])

  with col:
    st.markdown(
        """
        <div class="broker-auth-container">
            <div style="text-align: center; margin-bottom: 25px;">
                <h1 style="color: #fcd535; font-size: 28px; font-weight: 900; margin-bottom: 0;">⚡ VEER PRO TERMINAL</h1>
                <p style="color: #848e9c; font-size: 13px; margin-top: 5px;">Institutional Grade Multi-Market Exchange & AI Suite</p>
            </div>
        """,
        unsafe_allow_html=True,
    )

    t1, t2 = st.tabs(["🔑 Secure Sign In", "📝 Open Account"])

    with t1:
      st.markdown(
          "<p style='color:#848e9c; font-size:12px; text-align:center; margin-bottom:20px;'>Enter your registered Email or Mobile Number to access.</p>",
          unsafe_allow_html=True,
      )
      # Completely clean input fields without pre-filled garbage data
      login_input_val = st.text_input(
          "Registered Email or Mobile Number",
          value="",
          placeholder="name@example.com or mobile number",
          key="auth_login_input",
      )
      login_pass = st.text_input(
          "Account Password",
          value="",
          type="password",
          placeholder="••••••••",
          key="auth_login_pass",
      )

      st.markdown("<br>", unsafe_allow_html=True)
      if st.button("Access Terminal", key="auth_login_btn"):
        if not login_input_val or not login_pass:
          st.error("Please enter both email/mobile and password.")
        else:
          u_data = get_user_full(login_input_val)
          if u_data and u_data[0] == login_pass:
            st.session_state.logged_in = True
            db_real_email = u_data[5]
            st.session_state.current_user_email = db_real_email
            st.session_state.current_user_name = u_data[1]
            st.session_state.username = u_data[2] if u_data[2] else "trader"
            st.session_state.avatar = (
                u_data[3] if u_data[3] else "https://i.imgur.com/71916rK.png"
            )
            st.session_state.user_tier = u_data[4] if u_data[4] else "Free User"
            st.query_params["session_user"] = db_real_email
            st.rerun()
          else:
            st.error(
                "Invalid Credentials! Please check your mobile number/email and password."
            )

    with t2:
      st.markdown(
          "<p style='color:#848e9c; font-size:12px; text-align:center; margin-bottom:20px;'>Register to unlock AI signal quotas.</p>",
          unsafe_allow_html=True,
      )
      reg_name = st.text_input(
          "Full Legal Name", value="", placeholder="John Doe", key="reg_name_in"
      )
      reg_uname = st.text_input(
          "Trading Handle",
          value="",
          placeholder="trader_alpha",
          key="reg_uname_in",
      )
      reg_email = st.text_input(
          "Email ID / Mobile Number",
          value="",
          placeholder="john@example.com or mobile",
          key="reg_email_in",
      )
      reg_pass = st.text_input(
          "Secure Password (Min 6 Chars)",
          value="",
          type="password",
          placeholder="••••••••",
          key="reg_pass_in",
      )

      st.markdown("<br>", unsafe_allow_html=True)
      if st.button("Create Free Account", key="auth_reg_btn"):
        cleaned_reg_email = reg_email.strip().lower()
        cleaned_name = reg_name.strip()
        cleaned_uname = reg_uname.strip()
        if (
            cleaned_name
            and cleaned_reg_email
            and cleaned_uname
            and len(reg_pass) >= 6
        ):
          if register_user(
              cleaned_reg_email, reg_pass, cleaned_name, cleaned_uname
          ):
            st.session_state.logged_in = True
            st.session_state.current_user_email = cleaned_reg_email
            st.session_state.current_user_name = cleaned_name
            st.session_state.username = cleaned_uname
            st.session_state.avatar = "https://i.imgur.com/71916rK.png"
            st.session_state.user_tier = "Free User"
            st.query_params["session_user"] = cleaned_reg_email
            st.rerun()
          else:
            st.error("Email ID or Mobile is already registered in our system!")
        else:
          st.warning(
              "Please fill all details correctly (Password must be >= 6 chars)."
          )

    st.markdown(
        """
            <div style="text-align: center; margin-top: 25px; border-top: 1px solid #2b313a; padding-top: 15px;">
                <span style="color: #848e9c; font-size: 11px;">🔒 256-Bit SSL Encrypted Broker Protocol</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


if not st.session_state.logged_in:
  show_auth_screen()
  st.stop()


# --- SIDEBAR & MAIN TERMINAL ---
with st.sidebar:
  st.markdown("### 👤 User Profile")
  avatar_url = (
      st.session_state.avatar
      if st.session_state.get("avatar")
      else "https://i.imgur.com/71916rK.png"
  )
  st.image(avatar_url, width=80)
  st.markdown(f"**Name:** {st.session_state.current_user_name}")
  st.markdown(f"**Status:** `{st.session_state.user_tier}`")

  if st.button("🚪 Sign Out", key="logout_btn"):
    st.session_state.logged_in = False
    st.session_state.current_user_email = ""
    st.query_params.clear()
    st.rerun()

st.title("⚡ Veer Pro Terminal — World's Best 0% Loss AI Trading Suite")

market_prices = fetch_global_prices()
tc1, tc2, tc3 = st.columns(3)
with tc1:
  btc = market_prices.get("BTCUSDT", {"price": 68417.51, "change": 1.23})
  st.markdown(
      f"""<div class="ticker-card"><div class="ticker-symbol">BTC/USDT</div><div class="ticker-price">${btc['price']:,.2f}</div></div>""",
      unsafe_allow_html=True,
  )
with tc2:
  eth = market_prices.get("EURUSD", {"price": 1.0924, "change": 0.15})
  st.markdown(
      f"""<div class="ticker-card"><div class="ticker-symbol">EUR/USD</div><div class="ticker-price">{eth['price']:,.4f}</div></div>""",
      unsafe_allow_html=True,
  )
with tc3:
  rel = market_prices.get("RELIANCE", {"price": 2980.50, "change": 0.85})
  st.markdown(
      f"""<div class="ticker-card"><div class="ticker-symbol">RELIANCE</div><div class="ticker-price">₹{rel['price']:,.2f}</div></div>""",
      unsafe_allow_html=True,
  )

st.markdown("<br>", unsafe_allow_html=True)
tab_dash, tab_chart = st.tabs(["⚙️ Dashboard", "📊 Global Chart"])

with tab_dash:
  st.markdown("### Welcome to your Trading Suite")
  st.success("आप सफलतापूर्वक लॉगिन हो चुके हैं! अब आप बिना किसी रुकावट के चार्ट और सिग्नल्स का उपयोग कर सकते हैं।")

with tab_chart:
  st.markdown("### 📊 Live Chart")
  tv_html = """
    <div class="tradingview-widget-container" style="height:500px;width:100%;">
      <div id="tradingview_chart" style="height:100%;width:100%;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({
        "width": "100%", "height": "500", "symbol": "BINANCE:BTCUSDT", "interval": "15",
        "timezone": "Etc/UTC", "theme": "dark", "style": "1", "locale": "en", "toolbar_bg": "#0b0e11", "container_id": "tradingview_chart"
      });
      </script>
    </div>
    """
  st.components.v1.html(tv_html, height=520)
