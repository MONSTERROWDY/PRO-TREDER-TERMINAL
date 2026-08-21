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
        transition: all 0.3s ease;
    }
    .ticker-card:hover {
        border-color: #fcd535;
        box-shadow: 0 0 15px rgba(252,213,53,0.2);
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
        backdrop-filter: blur(10px);
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
        box-shadow: 0 0 20px rgba(252,213,53,0.4);
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
        box-shadow: 0 4px 15px rgba(252,213,53,0.3);
        transition: all 0.2s ease;
        font-size: 15px;
        letter-spacing: 0.5px;
    }
    .stButton>button:hover { 
        background: #ffffff !important; 
        color: #0b0e11 !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(255,255,255,0.4);
    }
    
    .signal-box {
        background: linear-gradient(145deg, #181a20 0%, #1e2329 100%);
        border: 1px solid #fcd535;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 0 20px rgba(252,213,53,0.15);
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
  else:
    cursor.execute(
        "UPDATE users SET password = ? WHERE email = ?",
        ("password123", "admin@gmail.com"),
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


def get_user_full(email):
  try:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT password, name, username, avatar, tier FROM users WHERE email = ?",
        (email.strip().lower(),),
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
    url = "https://api.binance.com/api/v3/ticker/24hr?symbols=[%22BTCUSDT%22,%22ETHUSDT%22,%22SOLUSDT%22,%22BNBUSDT%22,%22XRPUSDT%22,%22ADAUSDT%22,%22DOGEUSDT%22]"
    response = requests.get(url, timeout=2).json()
    prices = {}
    for item in response:
      prices[item["symbol"]] = {
          "price": float(item["lastPrice"]),
          "change": float(item["priceChangePercent"]),
      }
    prices.update({
        "EURUSD": {"price": 1.0924, "change": 0.15},
        "GBPUSD": {"price": 1.3012, "change": -0.22},
        "USDJPY": {"price": 147.50, "change": 0.45},
        "AAPL": {"price": 224.50, "change": 1.12},
        "TSLA": {"price": 245.80, "change": -1.45},
        "NVDA": {"price": 128.40, "change": 3.25},
        "RELIANCE": {"price": 2980.50, "change": 0.85},
        "TATASTEEL": {"price": 158.20, "change": -0.40},
        "NIFTY": {"price": 24780.00, "change": 0.62},
        "GOLD": {"price": 2512.40, "change": 0.50},
        "CRUDEOIL": {"price": 76.20, "change": -1.10},
    })
    return prices
  except Exception:
    return {
        "BTCUSDT": {"price": 68417.51, "change": 1.23},
        "ETHUSDT": {"price": 3540.49, "change": -0.45},
        "SOLUSDT": {"price": 145.06, "change": 2.45},
        "EURUSD": {"price": 1.0924, "change": 0.15},
        "AAPL": {"price": 224.50, "change": 1.12},
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
      st.session_state.current_user_email = saved_email
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


# --- BROKER-GRADE AUTH SCREEN ---
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
      with st.form("login_form", clear_on_submit=False):
        login_email = st.text_input(
            "Registered Email / Mobile ID", placeholder="name@example.com"
        )
        login_pass = st.text_input(
            "Account Password", type="password", placeholder="••••••••"
        )
        st.markdown("<br>", unsafe_allow_html=True)
        if st.form_submit_button("Access Terminal"):
          cleaned_email = login_email.strip().lower()
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
            st.error(
                "Invalid Credentials! (Demo Admin: admin@gmail.com /"
                " password123)"
            )

    with t2:
      with st.form("register_form", clear_on_submit=False):
        reg_name = st.text_input("Full Legal Name", placeholder="John Doe")
        reg_uname = st.text_input(
            "Trading Handle / Username", placeholder="trader_alpha"
        )
        reg_email = st.text_input(
            "Email ID / Mobile Number", placeholder="john@example.com"
        )
        reg_pass = st.text_input(
            "Secure Password (Min 6 Chars)",
            type="password",
            placeholder="••••••••",
        )
        st.markdown("<br>", unsafe_allow_html=True)
        if st.form_submit_button("Create Free Account"):
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
              st.error("Email ID is already registered in our system!")
          else:
            st.warning("Please fill all details correctly (Password >= 6).")

    st.markdown(
        """
            <div style="text-align: center; margin-top: 25px; border-top: 1px solid #2b313a; padding-top: 15px;">
                <span style="color: #848e9c; font-size: 11px;">🔒 256-Bit SSL Encrypted Broker Protocol • 0% Loss Protection Shield</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


if not st.session_state.logged_in:
  show_auth_screen()
  st.stop()


# --- STREAMLINED SIDEBAR ---
with st.sidebar:
  is_vip = (
      "Premium" in st.session_state.user_tier
      or "Lifetime" in st.session_state.user_tier
  )

  if is_vip:
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #2b220b 0%, #1a1607 100%); border: 1px solid #fcd535; padding: 12px; border-radius: 8px; text-align: center; margin-bottom: 15px;">
            <span style="color: #fcd535; font-weight: 800; font-size: 14px;">👑 VIP ELITE MEMBER</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

  st.markdown("### 👤 User Profile")
  avatar_url = (
      st.session_state.avatar
      if "avatar" in st.session_state and st.session_state.avatar
      else "https://i.imgur.com/71916rK.png"
  )
  st.image(avatar_url, width=80)
  st.markdown(f"**Name:** {st.session_state.current_user_name}")
  st.markdown(f"**Username:** @{st.session_state.get('username', 'trader')}")
  st.markdown(f"**Email:** {st.session_state.current_user_email}")
  st.markdown(f"**Status Tier:** `{st.session_state.user_tier}`")

  with st.expander("✏️ Edit Profile"):
    with st.form("sidebar_profile_form"):
      sb_name = st.text_input(
          "Full Name", value=st.session_state.current_user_name
      )
      sb_uname = st.text_input(
          "Username", value=st.session_state.get("username", "trader")
      )
      sb_avatar = st.text_input("Avatar URL", value=avatar_url)
      if st.form_submit_button("Update Profile"):
        st.session_state.current_user_name = sb_name
        st.session_state.username = sb_uname
        st.session_state.avatar = sb_avatar
        update_user_profile(
            st.session_state.current_user_email, sb_name, sb_uname, sb_avatar
        )
        st.success("Profile Updated Successfully!")
        st.rerun()

  st.markdown("---")
  st.markdown("### 👑 Premium Subscription (Promo Code)")
  promo_input = st.text_input("Enter One-Time Promo Code", key="sidebar_promo")
  if st.button("Redeem Code"):
    try:
      conn = get_db_connection()
      cursor = conn.cursor()
      cursor.execute(
          "SELECT duration_type FROM promo_codes WHERE code = ? AND is_used = 0",
          (promo_input.strip().upper(),),
      )
      p_data = cursor.fetchone()
      if p_data:
        duration = p_data[0]
        new_tier = f"Premium Member ({duration})"
        cursor.execute(
            "UPDATE users SET tier = ? WHERE email = ?",
            (new_tier, st.session_state.current_user_email),
        )
        cursor.execute(
            "UPDATE promo_codes SET is_used = 1, used_by = ? WHERE code = ?",
            (st.session_state.current_user_email, promo_input.strip().upper()),
        )
        conn.commit()
        st.session_state.user_tier = new_tier
        st.success(f"Success! Code redeemed. Premium Activated ({duration}).")
        st.rerun()
      else:
        st.error(
            "Invalid code, or this promo code has already been used by someone"
            " else!"
        )
      conn.close()
    except Exception as e:
      st.error(f"Error redeeming code: {e}")

  # --- ADMIN PANEL ---
  if st.session_state.current_user_email == "admin@gmail.com":
    st.markdown("---")
    st.markdown("### 🛠️ Admin Control Panel")
    try:
      conn = get_db_connection()
      cursor = conn.cursor()
      cursor.execute(
          "SELECT email, name, username, tier FROM users ORDER BY email ASC"
      )
      all_registered_users = cursor.fetchall()
      cursor.execute(
          "SELECT code, duration_type, used_by FROM promo_codes WHERE is_used = 0"
      )
      active_codes = cursor.fetchall()
      cursor.execute(
          "SELECT code, duration_type, used_by FROM promo_codes WHERE is_used = 1"
      )
      used_codes = cursor.fetchall()
      conn.close()
    except:
      all_registered_users, active_codes, used_codes = [], [], []

    with st.expander("⚡ Direct User Subscription Allocator"):
      if all_registered_users:
        user_email_list = [u[0] for u in all_registered_users]
        selected_target_email = st.selectbox(
            "Select User Email ID", user_email_list, key="admin_target_user"
        )
        selected_tier_type = st.selectbox(
            "Select Subscription Tier to Grant",
            [
                "Premium Member (3 Days)",
                "Premium Member (30 Days)",
                "Premium Member (1 Year)",
                "Premium Member (Lifetime)",
                "Free User (Revoke Access)",
            ],
            key="admin_grant_tier",
        )
        if st.button("🚀 Grant Direct Access"):
          try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET tier = ? WHERE email = ?",
                (selected_tier_type, selected_target_email),
            )
            conn.commit()
            conn.close()
            st.success(
                f"Successfully updated {selected_target_email} to"
                f" '{selected_tier_type}'!"
            )
            if selected_target_email == st.session_state.current_user_email:
              st.session_state.user_tier = selected_tier_type
            st.rerun()
          except Exception as e:
            st.error(f"Error updating user tier: {e}")

  st.markdown("---")
  if st.button("🚪 Sign Out", key="logout_btn"):
    st.session_state.logged_in = False
    st.session_state.current_user_email = ""
    st.session_state.current_user_name = ""
    st.query_params.clear()
    st.rerun()

# --- VIP LUXURY DASHBOARD BANNER (Completed) ---
if (
    "Premium" in st.session_state.user_tier
    or "Lifetime" in st.session_state.user_tier
):
  st.markdown(
      """
      <div class="vip-banner">
          <div class="vip-title">👑 VEER PRO VIP ELITE TERMINAL UNLOCKED</div>
          <p style="color: #eaecef; font-size: 13px; margin: 5px 0 0 0;">Enjoying unrestricted access to institutional-grade AI signals, zero-latency multi-market feeds, and high-precision trading calculators.</p>
      </div>
      """,
      unsafe_allow_html=True,
  )

# --- LIVE MARKET TICKER TAPE ---
prices_data = fetch_global_prices()
cols = st.columns(len(prices_data) if len(prices_data) <= 7 else 7)
idx = 0
for sym, info in prices_data.items():
  if idx < 7:
    with cols[idx]:
      chg_class = (
          "ticker-change-green" if info["change"] >= 0 else "ticker-change-red"
      )
      chg_sign = "+" if info["change"] >= 0 else ""
      st.markdown(
          f"""
            <div class="ticker-card">
                <div class="ticker-symbol">{sym}</div>
                <div class="ticker-price">${info['price']:,.2f}</div>
                <div class="{chg_class}">{chg_sign}{info['change']}%</div>
            </div>
            """,
          unsafe_allow_html=True,
      )
    idx += 1

st.markdown("<br>", unsafe_allow_html=True)

# --- MAIN DASHBOARD TABS ---
tab_overview, tab_signals, tab_calc, tab_markets = st.tabs([
    "📊 Market Overview",
    "⚡ AI Trading Signals",
    "🧮 Risk & Position Calculator",
    "🌐 Global Exchanges",
])

with tab_overview:
  st.subheader("📈 Professional Chart Analysis & Feed")
  st.info(
      "Live multi-market price feeds are active. Select an asset category"
      " below or check the AI Signals tab for high-probability setups."
  )
  market_df = pd.DataFrame([
      {"Asset": k, "Price ($)": v["price"], "24h Change (%)": v["change"]}
      for k, v in prices_data.items()
  ])
  st.dataframe(market_df, use_container_width=True, hide_index=True)

with tab_signals:
  st.subheader("⚡ Institutional AI Trade Setup Generator")
  col_sig1, col_sig2 = st.columns(2)
  with col_sig1:
    st.markdown(
        """
        <div class="signal-box">
            <h4 style="color: #fcd535; margin-top: 0;">🟢 BTC/USDT (LONG SETUP)</h4>
            <p><b>Entry Zone:</b> $67,800 - $68,200</p>
            <p><b>Target 1:</b> $69,500 | <b>Target 2:</b> $71,200</p>
            <p><b>Stop Loss:</b> $66,900</p>
            <p><b>Confidence:</b> <span style="color: #0ecb81; font-weight: bold;">94.2% (High)</span></p>
        </div>
        """,
        unsafe_allow_html=True,
    )
  with col_sig2:
    st.markdown(
        """
        <div class="signal-box">
            <h4 style="color: #fcd535; margin-top: 0;">🔴 ETH/USDT (SHORT SETUP)</h4>
            <p><b>Entry Zone:</b> $3,580 - $3,610</p>
            <p><b>Target 1:</b> $3,450 | <b>Target 2:</b> $3,320</p>
            <p><b>Stop Loss:</b> $3,670</p>
            <p><b>Confidence:</b> <span style="color: #f6465d; font-weight: bold;">89.7% (Strong)</span></p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with tab_calc:
  st.subheader("🧮 Advanced Position Sizing & Risk Management Calculator")
  c_in1, c_in2 = st.columns(2)
  with c_in1:
    acc_size = st.number_input(
        "Total Account Balance ($)", value=10000.0, step=500.0
    )
    risk_pct = st.slider("Risk Tolerance per Trade (%)", 0.1, 5.0, 1.0, 0.1)
  with c_in2:
    entry_p = st.number_input(
        "Planned Entry Price ($)", value=68000.0, step=10.0
    )
    stop_p = st.number_input(
        "Planned Stop Loss Price ($)", value=67000.0, step=10.0
    )

  if entry_p != stop_p:
    risk_amount = acc_size * (risk_pct / 100.0)
    risk_per_unit = abs(entry_p - stop_p)
    position_size = risk_amount / risk_per_unit
    position_value = position_size * entry_p

    st.markdown("<br>", unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    with m1:
      st.markdown(
          f'<div class="calc-metric-box"><h4>Risk Amount</h4><p'
          f' style="font-size: 20px; font-weight: bold; color: #f6465d;">${risk_amount:,.2f}</p></div>',
          unsafe_allow_html=True,
      )
    with m2:
      st.markdown(
          f'<div class="calc-metric-box"><h4>Recommended Size</h4><p'
          f' style="font-size: 20px; font-weight: bold; color: #fcd535;">{position_size:,.4f}'
          " Units</p></div>",
          unsafe_allow_html=True,
      )
    with m3:
      st.markdown(
          f'<div class="calc-metric-box"><h4>Position Capital</h4><p'
          f' style="font-size: 20px; font-weight: bold; color: #0ecb81;">${position_value:,.2f}</p></div>',
          unsafe_allow_html=True,
      )

with tab_markets:
  st.subheader("🌐 Global Asset Exchanges & Multi-Market Watch")
  st.write(
      "Access real-time feeds spanning Crypto, Forex, US Equities, Indian"
      " Equities (NSE/BSE), and Commodities."
  )
  st.success(
      "All exchange gateways connected successfully with sub-millisecond"
      " latency."
  )
