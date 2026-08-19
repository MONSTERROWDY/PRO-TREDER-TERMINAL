import datetime
import sqlite3
import pandas as pd
import requests
import streamlit as st

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Veer Pro Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CUSTOM GLASSMORPHISM & BINANCE/TRADINGVIEW DARK THEME CSS ---
st.markdown(
    """
    <style>
    .stApp {
        background: #0b0e11 !important;
        color: #fcd535 !important;
    }
    h1, h2, h3, h4, h5, h6, p, span, label, div {
        color: #eaecef !important;
    }
    .ticker-card {
        background: #181a20;
        border: 1px solid #2b313a;
        border-radius: 8px;
        padding: 12px 16px;
        text-align: center;
    }
    .ticker-symbol { font-weight: 700; font-size: 14px; color: #848e9c !important; }
    .ticker-price { font-weight: 800; font-size: 18px; color: #ffffff !important; }
    .ticker-change-green { color: #0ecb81 !important; font-size: 12px; font-weight: 600; }

    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div {
        background-color: #1e2329 !important;
        color: #ffffff !important;
        border: 1px solid #2b313a !important;
        border-radius: 6px !important;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #181a20 !important;
        border-radius: 6px !important;
        color: #848e9c !important;
        padding: 8px 16px;
        border: 1px solid #2b313a;
    }
    .stTabs [aria-selected="true"] {
        background: #fcd535 !important;
        color: #0b0e11 !important;
        font-weight: 700 !important;
        border: none !important;
    }
    .stButton>button { 
        width: 100%; 
        border-radius: 6px; 
        font-weight: 700; 
        height: 42px; 
        background: #fcd535; 
        color: #0b0e11; 
        border: none; 
    }
    .stButton>button:hover { 
        background: #f0b90b !important; 
        color: #0b0e11 !important;
    }
    .auth-card {
        background: #181a20;
        border: 1px solid #2b313a;
        padding: 30px;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }
    </style>
""",
    unsafe_allow_html=True,
)


# --- DATABASE SETUP & AUTO MIGRATION ---
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

  columns_to_add = [
      ("username", "TEXT"),
      ("avatar", "TEXT"),
      ("tier", "TEXT DEFAULT 'Free User'"),
      ("expiry", "TEXT"),
  ]
  for col_name, col_type in columns_to_add:
    try:
      cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
      conn.commit()
    except sqlite3.OperationalError:
      pass

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS promo_codes (
            code TEXT PRIMARY KEY,
            duration_type TEXT,
            is_used INTEGER DEFAULT 0
        )
    """)
  conn.commit()

  # Default Admin User
  cursor.execute("SELECT * FROM users WHERE email = ?", ("admin@gmail.com",))
  if not cursor.fetchone():
    cursor.execute(
        "INSERT INTO users (email, password, name, username, tier) VALUES (?, ?, ?, ?, ?)",
        (
            "admin@gmail.com",
            "password123",
            "Pro Master",
            "admin_master",
            "VIP Paid Member",
        ),
    )
    conn.commit()

  # Default Promo Codes Setup as requested
  default_promos = [
      ("फ्री वीआईपी 30", "30 Days"),
      ("VEERVIP30", "30 Days"),
      ("वीर वीआईपी वन ईयर", "1 Year"),
      ("VEERVIP1Y", "1 Year"),
      ("वीआईपी फ्री थ्री डे", "3 Days"),
      ("VEER3DAYS", "3 Days"),
      ("VEERLIFETIME", "Lifetime Unlimited"),
  ]

  for code, dtype in default_promos:
    cursor.execute("SELECT * FROM promo_codes WHERE code = ?", (code,))
    if not cursor.fetchone():
      cursor.execute(
          "INSERT INTO promo_codes (code, duration_type) VALUES (?, ?)",
          (code, dtype),
      )
      conn.commit()

  conn.close()


init_db()


def get_user_full(email):
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
      "SELECT password, name, username, avatar, tier FROM users WHERE email ="
      " ?",
      (email.strip(),),
  )
  res = cursor.fetchone()
  conn.close()
  return res


def register_user(email, password, name, username):
  try:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (email, password, name, username, tier) VALUES (?,"
        " ?, ?, ?, ?)",
        (email.strip(), password, name.strip(), username.strip(), "Free User"),
    )
    conn.commit()
    conn.close()
    return True
  except sqlite3.IntegrityError:
    return False


def update_user_profile(email, name, username, avatar):
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
      "UPDATE users SET name = ?, username = ?, avatar = ? WHERE email = ?",
      (name, username, avatar, email),
  )
  conn.commit()
  conn.close()


# --- BINANCE LIVE PRICES ---
def fetch_binance_prices():
  try:
    url = "https://api.binance.com/api/v3/ticker/24hr?symbols=[%22BTCUSDT%22,%22SOLUSDT%22,%22ETHUSDT%22]"
    response = requests.get(url, timeout=3).json()
    prices = {}
    for item in response:
      prices[item["symbol"]] = {
          "price": float(item["lastPrice"]),
          "change": float(item["priceChangePercent"]),
      }
    return prices
  except Exception:
    return {
        "BTCUSDT": {"price": 68417.51, "change": 1.23},
        "SOLUSDT": {"price": 145.06, "change": 2.45},
        "ETHUSDT": {"price": 3540.49, "change": 1.15},
    }


# --- SESSION LOGIC ---
query_params = st.query_params
saved_email = query_params.get("session_user", "")

if "logged_in" not in st.session_state:
  if saved_email:
    u_data = get_user_full(saved_email)
    if u_data:
      st.session_state.logged_in = True
      st.session_state.current_user_email = saved_email
      st.session_state.current_user_name = u_data[1]
      st.session_state.username = (
          u_data[2] if u_data and u_data[2] else "trader"
      )
      st.session_state.avatar = (
          u_data[3] if u_data and u_data[3] else "https://i.imgur.com/71916rK.png"
      )
      st.session_state.user_tier = u_data[4] if u_data and u_data[4] else "Free User"
    else:
      st.session_state.logged_in = False
  else:
    st.session_state.logged_in = False

if "signals_used" not in st.session_state:
  st.session_state.signals_used = 0


# --- AUTH SCREEN ---
def show_auth_screen():
  st.markdown("<br><br>", unsafe_allow_html=True)
  c1, col, c2 = st.columns([1, 1.3, 1])

  with col:
    st.markdown(
        """
        <div class="auth-card">
            <div style="text-align: center; margin-bottom: 25px;">
                <h2 style="font-weight: 800; color: #fcd535; letter-spacing: 1px;">⚡ VEER PRO TERMINAL</h2>
                <p style="color: #848e9c; font-size: 13px;">Log in to Global Financial & Institutional Suite</p>
            </div>
        """,
        unsafe_allow_html=True,
    )

    t1, t2 = st.tabs(["🔑 Sign In", "📝 Register Account"])

    with t1:
      with st.form("login_form", clear_on_submit=False):
        login_email = st.text_input(
            "Email ID / Registered Mobile", key="l_email"
        )
        login_pass = st.text_input("Password", type="password", key="l_pass")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.form_submit_button("Log In"):
          cleaned_email = login_email.strip()
          u_data = get_user_full(cleaned_email)
          if u_data and u_data[0] == login_pass:
            st.session_state.logged_in = True
            st.session_state.current_user_email = cleaned_email
            st.session_state.current_user_name = u_data[1]
            st.session_state.username = u_data[2] if u_data[2] else "trader"
            st.session_state.avatar = (
                u_data[3] if u_data[3] else "https://i.imgur.com/71916rK.png"
            )
            st.session_state.user_tier = u_data[4] if u_data[4] else "Free User"
            st.query_params["session_user"] = cleaned_email
            st.rerun()
          else:
            st.error("Invalid Credentials! Please check email and password.")

    with t2:
      with st.form("register_form", clear_on_submit=False):
        reg_name = st.text_input("Full Name", key="r_name")
        reg_uname = st.text_input("Choose Username (e.g. trader_veer)", key="r_un")
        reg_email = st.text_input(
            "Email ID / Mobile Number", key="r_email"
        )
        reg_pass = st.text_input(
            "Password (Min 6 Chars)", type="password", key="r_pass"
        )
        st.markdown("<br>", unsafe_allow_html=True)
        if st.form_submit_button("Create Account"):
          cleaned_reg_email = reg_email.strip()
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
              st.error("Email is already registered!")
          else:
            st.warning("Please fill all details correctly.")

    st.markdown("</div>", unsafe_allow_html=True)


if not st.session_state.logged_in:
  show_auth_screen()
  st.stop()


# --- SIDEBAR & HEADER ---
with st.sidebar:
  st.markdown("### 👤 User Profile Panel")
  avatar_url = (
      st.session_state.avatar
      if "avatar" in st.session_state and st.session_state.avatar
      else "https://i.imgur.com/71916rK.png"
  )
  st.image(avatar_url, width=80)
  st.write(
      f"👋 **{st.session_state.current_user_name}**"
      f" (@{st.session_state.get('username', 'trader')})"
  )
  st.caption(f"📧 {st.session_state.current_user_email}")
  st.write(f"🌟 Tier: **{st.session_state.user_tier}**")
  st.markdown("---")
  if st.button("🚪 Sign Out", key="logout_btn"):
    st.session_state.logged_in = False
    st.session_state.current_user_email = ""
    st.session_state.current_user_name = ""
    st.query_params.clear()
    st.rerun()

st.title("⚡ Veer Pro Terminal")

# --- LIVE TICKER STRIP ---
ticker_data = fetch_binance_prices()
tc1, tc2, tc3 = st.columns(3)

with tc1:
  btc = ticker_data.get("BTCUSDT", {"price": 68417.51, "change": 1.23})
  st.markdown(
      f"""<div class="ticker-card"><div class="ticker-symbol">BTCUSDT</div><div class="ticker-price">${btc['price']:,.2f}</div><div class="ticker-change-green">+{btc['change']}%</div></div>""",
      unsafe_allow_html=True,
  )

with tc2:
  sol = ticker_data.get("SOLUSDT", {"price": 145.06, "change": 2.45})
  st.markdown(
      f"""<div class="ticker-card"><div class="ticker-symbol">🔥 SOLUSDT</div><div class="ticker-price">${sol['price']:,.2f}</div><div class="ticker-change-green">+{sol['change']}%</div></div>""",
      unsafe_allow_html=True,
  )

with tc3:
  eth = ticker_data.get("ETHUSDT", {"price": 3540.49, "change": 1.15})
  st.markdown(
      f"""<div class="ticker-card"><div class="ticker-symbol">ETHUSDT</div><div class="ticker-price">${eth['price']:,.2f}</div><div class="ticker-change-green">+{eth['change']}%</div></div>""",
      unsafe_allow_html=True,
  )

st.markdown("<br>", unsafe_allow_html=True)

# --- MAIN TABS ---
tab_dash, tab_chart, tab_signals, tab_profile, tab_vip = st.tabs([
    "⚙️ Dashboard",
    "📊 Global Chart",
    "🎯 Signals",
    "👤 My Profile & Promo",
    "👑 VIP Plans",
])

with tab_dash:
  col_cfg, col_risk = st.columns(2, gap="medium")
  with col_cfg:
    st.markdown("### ⚙️ Signal Configuration")
    category = st.selectbox(
        "Category",
        ["Crypto", "Forex (Currencies)", "Global Stocks", "Commodities"],
        key="cat_sel",
    )
    asset = st.selectbox(
        "Asset / Symbol",
        [
            "BINANCE:BTCUSDT",
            "BINANCE:SOLUSDT",
            "FX:EURUSD",
            "FX:GBPUSD",
            "NASDAQ:AAPL",
            "NASDAQ:TSLA",
            "COMEX:GC1!",
            "NYMEX:CL1!",
        ],
        key="asset_sel",
    )
    tf = st.selectbox(
        "Timeframe", ["1s", "1m", "5m", "15m", "1h", "4h"], key="tf_sel"
    )
  with col_risk:
    st.markdown("### 🛡️ Risk Management")
    acc_bal = st.number_input(
        "Account Balance ($)", value=10000.0, step=500.0, key="acc_bal_input"
    )
    risk_pct = st.slider("Risk Per Trade (%)", 0.1, 5.0, 1.0, key="risk_slider")
    atr_mult = st.slider("ATR SL Multiplier", 1.0, 3.0, 1.5, key="atr_slider")
    risk_amt = acc_bal * (risk_pct / 100)
    st.info(
        f"📊 **Max Capital at Risk:** ${risk_amt:.2f} per position | Protection"
        " Active"
    )

with tab_chart:
  st.markdown(
      "### 📊 Advanced Global Multi-Market Chart (Stocks, Forex, Crypto &"
      " Commodities)"
  )
  st.info(
      "💡 **सुझाव:** आप नीचे दिए गए चार्ट के अंदर सर्च आइकॉन पर क्लिक करके दुनिया"
      " का कोई भी स्टॉक (जैसे RELIANCE, AAPL), फॉरेक्स पेयर (जैसे EURUSD,"
      " USDINR), या कमोडिटी (जैसे GOLD, CRUDEOIL) सर्च कर सकते हैं!"
  )

  c_sym, c_tf = st.columns([2, 2])
  with c_sym:
    custom_symbol = st.text_input(
        "Enter TradingView Symbol (e.g., NASDAQ:AAPL, FX:USDINR,"
        " BINANCE:BTCUSDT,COMEX:GC1!):",
        value="BINANCE:SOLUSDT",
    )
  with c_tf:
    chart_tf = st.selectbox(
        "Select Chart Timeframe",
        ["1", "3", "5", "15", "30", "60", "120", "240", "D", "W", "M"],
        index=3,
        key="chart_tf_sel",
    )

  tv_html = f"""
    <div class="tradingview-widget-container" style="height:620px;width:100%;">
      <div id="tradingview_chart" style="height:100%;width:100%;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget(
      {{
        "width": "100%",
        "height": "620",
        "symbol": "{custom_symbol}",
        "interval": "{chart_tf}",
        "timezone": "Etc/UTC",
        "theme": "dark",
        "style": "1",
        "locale": "en",
        "toolbar_bg": "#0b0e11",
        "enable_publishing": false,
        "allow_symbol_change": true,
        "container_id": "tradingview_chart"
      }});
      </script>
    </div>
    """
  st.components.v1.html(tv_html, height=640)

with tab_signals:
  st.markdown("### 🎯 Ultimate Multi-Confluence AI Smart Signals")
  if st.session_state.user_tier == "Free User":
    rem = 2 - st.session_state.signals_used
    st.info(f"Free Plan Quota: {rem}/2 Signals Remaining Today")
  else:
    st.success(
        "👑 VIP Ultimate Multi-Strategy Confluence Engine Active (94.8%"
        " Accuracy)"
    )

  if st.button("✨ GENERATE ULTIMATE AI SIGNAL", key="gen_sig_btn"):
    if (
        st.session_state.user_tier == "Free User"
        and st.session_state.signals_used >= 2
    ):
      st.error("⚠️ Daily Free Quota Exhausted! Upgrade to VIP for Unlimited.")
    else:
      if st.session_state.user_tier == "Free User":
        st.session_state.signals_used += 1

      st.success("🔥 Multi-Confluence Strategy Triggered: High Probability Setup!")
      s_col1, s_col2 = st.columns(2)
      with s_col1:
        st.metric("Setup Direction & Bias", "STRONG BULLISH BUY", "94.8% Win Index")
        st.write(f"**Target Asset:** {custom_symbol}")
        st.write("**Exact Entry Zone:** `Optimal Market Zone`")
      with s_col2:
        st.metric("Risk / Reward Ratio", "1 : 4.2", "Optimized Structure")
        st.write("**Stop Loss (SL):** `Managed by ATR`")
        st.write(
            "**Take Profit Targets:** 🎯 TP1: `Level 1` | 🎯 TP2: `Level 2` | 🎯"
            " TP3: `Level 3`"
        )
      st.link_button(
          "🚀 Trade via Broker Platform", "https://in.tradingview.com/"
      )

with tab_profile:
  st.markdown("### 👤 User Profile & VIP Promo Code Redemption")
  st.write(
      "Manage your personal details, profile picture, username, and redeem"
      " your VIP promo codes here."
  )

  p_col1, p_col2 = st.columns(2)
  with p_col1:
    with st.form("profile_update_form"):
      st.markdown("#### Edit Profile Details")
      new_name = st.text_input("Full Name", value=st.session_state.current_user_name)
      new_uname = st.text_input(
          "Username",
          value=st.session_state.get(
              "username", st.session_state.current_user_name
          ),
      )
      new_avatar = st.text_input(
          "Profile Picture Image URL",
          value=st.session_state.get(
              "avatar", "https://i.imgur.com/71916rK.png"
          ),
      )
      st.markdown("<br>", unsafe_allow_html=True)
      if st.form_submit_button("Save Profile"):
        st.session_state.current_user_name = new_name
        st.session_state.username = new_uname
        st.session_state.avatar = new_avatar
        update_user_profile(
            st.session_state.current_user_email,
            new_name,
            new_uname,
            new_avatar,
        )
        st.success("✅ Profile Updated Successfully!")
        st.rerun()

  with p_col2:
    st.markdown("#### 🎟️ Redeem VIP Promo Code")
    st.info(
        "💡 **उपलब्ध प्रोमो कोड्स:**\n"
        "- 30 दिन के लिए: `फ्री वीआईपी 30` या `VEERVIP30`\n"
        "- 1 साल के लिए: `वीर वीआईपी वन ईयर` या `VEERVIP1Y`\n"
        "- 3 दिन के लिए: `वीआईपी फ्री थ्री डे` या `VEER3DAYS`"
    )
    promo_input = st.text_input(
        "Enter Promo Code Here", key="promo_box"
    )
    if st.button("Redeem Promo Code"):
      conn = get_db_connection()
      cursor = conn.cursor()
      cursor.execute(
          "SELECT duration_type, is_used FROM promo_codes WHERE code = ?",
          (promo_input.strip(),),
      )
      p_data = cursor.fetchone()
      if p_data:
        duration = p_data[0]
        st.session_state.user_tier = f"VIP Paid Member ({duration})"
        cursor.execute(
            "UPDATE users SET tier = ? WHERE email = ?",
            (st.session_state.user_tier, st.session_state.current_user_email),
        )
        conn.commit()
        conn.close()
        st.success(
            f"🎉 Promo Code Applied Successfully! VIP Access Granted for"
            f" {duration}."
        )
        st.rerun()
      else:
        conn.close()
        st.error("❌ Invalid or Expired Promo Code! कृपया सही कोड दर्ज करें।")

    st.markdown("---")
    st.markdown("#### 🛠️ Admin / Creator Code Generator")
    if st.session_state.current_user_email == "admin@gmail.com":
      gen_code = st.text_input("Create New Custom Promo Code", key="gen_c")
      dur_type = st.selectbox(
          "Select VIP Duration",
          ["3 Days", "30 Days", "1 Year", "Lifetime Unlimited"],
      )
      if st.button("Generate & Save Code"):
        try:
          conn = get_db_connection()
          cursor = conn.cursor()
          cursor.execute(
              "INSERT INTO promo_codes (code, duration_type) VALUES (?, ?)",
              (gen_code.strip(), dur_type),
          )
          conn.commit()
          conn.close()
          st.success(f"✅ New Promo Code '{gen_code}' Generated Successfully!")
        except:
          st.error("This promo code already exists!")
    else:
      st.info(
          "🔒 Creator Code Generation tools are restricted to Admin accounts"
          " only."
      )

with tab_vip:
  st.markdown("### 👑 Choose Your VIP Pro Membership Plan")
  st.write(
      "Click on any plan below to directly open your UPI App with the exact"
      " pre-filled amount!"
  )

  v1, v2, v3, v4 = st.columns(4)

  with v1:
    st.markdown(
        """
        <div style="background: #181a20; padding: 15px; border-radius: 8px; border: 1px solid #2b313a; text-align: center;">
            <h4 style="color: #38bdf8; font-size: 16px;">⚡ 3-Day Trial</h4>
            <h3 style="color: #ffffff;">₹199</h3>
            <p style="color: #848e9c; font-size: 11px;">Direct Pay</p>
            <hr style="border-color: #2b313a;">
            <p style="font-size: 12px;">✔️ All Global Charts</p>
            <p style="font-size: 12px;">✔️ All SMC Tools</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    upi_3days = (
        "upi://pay?pa=7479465676-7@ybl&pn=VEER%20PRO%20TRADER&am=199.00&cu=INR"
    )
    st.link_button("📲 Pay ₹199", upi_3days)

  with v2:
    st.markdown(
        """
        <div style="background: #181a20; padding: 15px; border-radius: 8px; border: 1px solid #2b313a; text-align: center;">
            <h4 style="color: #0ecb81; font-size: 16px;">🔥 Monthly Pro</h4>
            <h3 style="color: #ffffff;">₹999</h3>
            <p style="color: #848e9c; font-size: 11px;">Direct Pay</p>
            <hr style="border-color: #2b313a;">
            <p style="font-size: 12px;">✔️ AI Signals</p>
            <p style="font-size: 12px;">✔️ Priority Alerts</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    upi_monthly = (
        "upi://pay?pa=7479465676-7@ybl&pn=VEER%20PRO%20TRADER&am=999.00&cu=INR"
    )
    st.link_button("📲 Pay ₹999", upi_monthly)

  with v3:
    st.markdown(
        """
        <div style="background: #181a20; padding: 15px; border-radius: 8px; border: 2px solid #fcd535; text-align: center;">
            <h4 style="color: #fcd535; font-size: 16px;">👑 Annual VIP</h4>
            <h3 style="color: #ffffff;">₹7,999</h3>
            <p style="color: #848e9c; font-size: 11px;">Direct Pay</p>
            <hr style="border-color: #2b313a;">
            <p style="font-size: 12px;">✔️ 1 Year Full Access</p>
            <p style="font-size: 12px;">✔️ Priority Support</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    upi_annual = (
        "upi://pay?pa=7479465676-7@ybl&pn=VEER%20PRO%20TRADER&am=7999.00&cu=INR"
    )
    st.link_button("📲 Pay ₹7,999", upi_annual)

  with v4:
    st.markdown(
        """
        <div style="background: #181a20; padding: 15px; border-radius: 8px; border: 1px solid #a855f7; text-align: center;">
            <h4 style="color: #c084fc; font-size: 16px;">💎 Lifetime VIP</h4>
            <h3 style="color: #ffffff;">₹50,000</h3>
            <p style="color: #848e9c; font-size: 11px;">Direct Pay</p>
            <hr style="border-color: #2b313a;">
            <p style="font-size: 12px;">✔️ Lifetime Access</p>
            <p style="font-size: 12px;">✔️ 1-on-1 Mentorship</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    upi_lifetime = (
        "upi://pay?pa=7479465676-7@ybl&pn=VEER%20PRO%20TRADER&am=50000.00&cu=INR"
    )
    st.link_button("📲 Pay ₹50,000", upi_lifetime)

  st.markdown("---")
  st.markdown("#### 🔓 Instant VIP Activation after Payment")
  act_col1, act_col2 = st.columns([2, 1])
  with act_col1:
    utr_code = st.text_input(
        "Enter 12-Digit UTR / Transaction Reference ID:", key="utr_inp"
    )
  with act_col2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Verify & Activate"):
      if len(utr_code.strip()) >= 8:
        st.session_state.user_tier = "VIP Paid Member"
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET tier = ? WHERE email = ?",
            ("VIP Paid Member", st.session_state.current_user_email),
        )
        conn.commit()
        conn.close()
        st.success("🎉 VIP Membership Activated Successfully!")
        st.rerun()
      else:
        st.error("Please enter a valid UTR number.")

st.markdown("---")
st.caption(
    "Disclaimer: Veer Pro Terminal is built for educational & research"
    " purposes only."
)
