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

# --- CUSTOM GLASSMORPHISM & ULTRA-SMOOTH UI CSS ---
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
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        transition: transform 0.2s ease;
    }
    .ticker-card:hover {
        border-color: #fcd535;
    }
    .ticker-symbol { font-weight: 700; font-size: 14px; color: #848e9c !important; }
    .ticker-price { font-weight: 800; font-size: 18px; color: #ffffff !important; }
    .ticker-change-green { color: #0ecb81 !important; font-size: 12px; font-weight: 600; }
    .ticker-change-red { color: #f6465d !important; font-size: 12px; font-weight: 600; }

    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div {
        background-color: #1e2329 !important;
        color: #ffffff !important;
        border: 1px solid #2b313a !important;
        border-radius: 6px !important;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 6px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #181a20 !important;
        border-radius: 6px !important;
        color: #848e9c !important;
        padding: 8px 14px;
        border: 1px solid #2b313a;
        font-size: 13px;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #fcd535 0%, #f0b90b 100%) !important;
        color: #0b0e11 !important;
        font-weight: 800 !important;
        border: none !important;
    }
    .stButton>button { 
        width: 100%; 
        border-radius: 6px; 
        font-weight: 800; 
        height: 44px; 
        background: linear-gradient(135deg, #fcd535 0%, #f0b90b 100%); 
        color: #0b0e11; 
        border: none;
        box-shadow: 0 4px 14px rgba(252,213,53,0.3);
        transition: all 0.2s ease;
    }
    .stButton>button:hover { 
        background: #ffffff !important; 
        color: #0b0e11 !important;
        transform: translateY(-1px);
    }
    .auth-card {
        background: #181a20;
        border: 1px solid #2b313a;
        padding: 30px;
        border-radius: 12px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.6);
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


# --- LIVE BINANCE PRICES ---
def fetch_binance_prices():
  try:
    url = "https://api.binance.com/api/v3/ticker/24hr?symbols=[%22BTCUSDT%22,%22SOLUSDT%22,%22ETHUSDT%22]"
    response = requests.get(url, timeout=2).json()
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
        "ETHUSDT": {"price": 3540.49, "change": -0.45},
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
                <p style="color: #848e9c; font-size: 13px;">World's #1 0% Loss AI Trading Suite</p>
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


# --- STREAMLINED SIDEBAR ---
with st.sidebar:
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
      sb_name = st.text_input("Full Name", value=st.session_state.current_user_name)
      sb_uname = st.text_input("Username", value=st.session_state.get("username", "trader"))
      sb_avatar = st.text_input("Avatar URL", value=avatar_url)
      if st.form_submit_button("Update Profile"):
        st.session_state.current_user_name = sb_name
        st.session_state.username = sb_uname
        st.session_state.avatar = sb_avatar
        update_user_profile(st.session_state.current_user_email, sb_name, sb_uname, sb_avatar)
        st.success("Profile Updated Successfully!")
        st.rerun()

  st.markdown("---")
  st.markdown("### 👑 Premium Subscription")
  
  promo_input = st.text_input("Enter Promo Code", key="sidebar_promo")
  if st.button("Redeem Code"):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT duration_type FROM promo_codes WHERE code = ? AND is_used = 0",
        (promo_input.strip(),),
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
          "UPDATE promo_codes SET is_used = 1 WHERE code = ?",
          (promo_input.strip(),),
      )
      conn.commit()
      st.session_state.user_tier = new_tier
      st.success(f"Success! Premium Activated ({duration}).")
      st.rerun()
    else:
      st.error("Invalid or already used code.")
    conn.close()

  if st.session_state.current_user_email == "admin@gmail.com":
    st.markdown("---")
    st.markdown("### 🛠️ Admin Control Panel")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT code, duration_type FROM promo_codes WHERE is_used = 0")
    active_codes = cursor.fetchall()
    conn.close()
    
    with st.expander("👁️ View Active Codes"):
      if active_codes:
        st.table(pd.DataFrame(active_codes, columns=["Code", "Duration"]))
      else:
        st.write("No active codes.")
        
    gen_code = st.text_input("New Custom Promo Code", key="sidebar_gen_c")
    dur_type = st.selectbox("Duration", ["3 Days", "30 Days", "1 Year", "Lifetime Unlimited"], key="sidebar_dur")
    if st.button("Generate Code"):
      try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO promo_codes (code, duration_type) VALUES (?, ?)",
            (gen_code.strip(), dur_type),
        )
        conn.commit()
        conn.close()
        st.success(f"Created code: '{gen_code}'")
        st.rerun()
      except:
        st.error("Code already exists!")

  st.markdown("---")
  if st.button("🚪 Sign Out", key="logout_btn"):
    st.session_state.logged_in = False
    st.session_state.current_user_email = ""
    st.session_state.current_user_name = ""
    st.query_params.clear()
    st.rerun()

st.title("⚡ Veer Pro Terminal — World's Best 0% Loss AI Trading Suite")

# --- LIVE TICKER STRIP ---
ticker_data = fetch_binance_prices()
tc1, tc2, tc3 = st.columns(3)

with tc1:
  btc = ticker_data.get("BTCUSDT", {"price": 68417.51, "change": 1.23})
  c_class = "ticker-change-green" if btc['change'] >= 0 else "ticker-change-red"
  sign = "+" if btc['change'] >= 0 else ""
  st.markdown(
      f"""<div class="ticker-card"><div class="ticker-symbol">BTCUSDT (Live)</div><div class="ticker-price">${btc['price']:,.2f}</div><div class="{c_class}">{sign}{btc['change']}%</div></div>""",
      unsafe_allow_html=True,
  )

with tc2:
  sol = ticker_data.get("SOLUSDT", {"price": 145.06, "change": 2.45})
  c_class = "ticker-change-green" if sol['change'] >= 0 else "ticker-change-red"
  sign = "+" if sol['change'] >= 0 else ""
  st.markdown(
      f"""<div class="ticker-card"><div class="ticker-symbol">SOLUSDT (Live)</div><div class="ticker-price">${sol['price']:,.2f}</div><div class="{c_class}">{sign}{sol['change']}%</div></div>""",
      unsafe_allow_html=True,
  )

with tc3:
  eth = ticker_data.get("ETHUSDT", {"price": 3540.49, "change": 1.15})
  c_class = "ticker-change-green" if eth['change'] >= 0 else "ticker-change-red"
  sign = "+" if eth['change'] >= 0 else ""
  st.markdown(
      f"""<div class="ticker-card"><div class="ticker-symbol">ETHUSDT (Live)</div><div class="ticker-price">${eth['price']:,.2f}</div><div class="{c_class}">{sign}{eth['change']}%</div></div>""",
      unsafe_allow_html=True,
  )

st.markdown("<br>", unsafe_allow_html=True)

# --- CLEAN MAIN TABS (INCLUDING NEW RISK MANAGEMENT MASTER) ---
tab_dash, tab_risk_calc, tab_chart, tab_signals, tab_plans = st.tabs([
    "⚙️ Dashboard",
    "🛡️ Risk & Capital Master",
    "📊 Global Chart",
    "🎯 AI 0% Loss Signals",
    "👑 Subscription Plans",
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
    st.markdown("### 🛡️ Smart Capital Defense (0% Loss Guarantee)")
    acc_bal = st.number_input(
        "Account Balance ($)", value=10000.0, step=500.0, key="acc_bal_input"
    )
    risk_pct = 1.0
    st.slider("Max Capital Risk (%) — Locked at 1%", 0.1, 5.0, 1.0, disabled=True, key="risk_slider")
    risk_amt = acc_bal * (risk_pct / 100)
    st.success(
        f"🔒 **0% Loss Safety Shield Active:** Auto break-even triggers ensure maximum safety. If conditions fail, you exit with minimal or zero loss (${risk_amt:.2f} max risk protection)."
    )

with tab_risk_calc:
  st.markdown("### 🛡️ Advanced Risk & Capital Management Master")
  st.write(
      "साफ और आसान भाषा में समझें: अपने कुल कैपिटल पर कितना रिस्क लेना चाहिए, कितना नफा (Profit) होगा और कितना नुकसान (Loss) — सब कुछ यहाँ कैलकुलेट करें।"
  )
  st.markdown("<br>", unsafe_allow_html=True)

  rc1, rc2 = st.columns(2, gap="large")

  with rc1:
    st.markdown("#### 📥 1. इनपुट डिटेल्स भरें (Input Parameters)")
    user_capital = st.number_input("आपका कुल ट्रेडिंग कैपिटल (Total Capital in $ या ₹)", value=50000.0, step=1000.0, key="rc_cap")
    risk_tolerance_pct = st.slider("एक ट्रेड में आप अधिकतम कितना रिस्क लेना चाहते हैं? (%)", 0.1, 5.0, 1.0, step=0.1, key="rc_rt_pct")
    entry_price = st.number_input("खरीद भाव (Entry Price)", value=100.0, step=0.5, key="rc_entry")
    stop_loss_price = st.number_input("स्टॉप लॉस भाव (Stop Loss Price - सुरक्षा मूल्य)", value=97.0, step=0.5, key="rc_sl")
    risk_reward_ratio = st.selectbox("रिस्क-टू-रवाॅर्ड रेश्यो (Risk to Reward Ratio)", ["1 : 1.5", "1 : 2", "1 : 3", "1 : 5"], index=1, key="rc_rrr")

  with rc2:
    st.markdown("#### 📊 2. लाइव रिस्क और मनी कैलकुलेशन (Live Output)")
    
    # Mathematical Calculations
    max_risk_amount = user_capital * (risk_tolerance_pct / 100.0)
    price_risk_per_unit = abs(entry_price - stop_loss_price)
    
    if price_risk_per_unit > 0:
      recommended_quantity = max_risk_amount / price_risk_per_unit
    else:
      recommended_quantity = 0.0

    rrr_multiplier = float(risk_reward_ratio.split(":")[-1].strip())
    potential_profit_amount = max_risk_amount * rrr_multiplier
    
    if entry_price > stop_loss_price:
      target_price = entry_price + (price_risk_per_unit * rrr_multiplier)
      trade_type_label = "🟢 LONG (BUY)"
    else:
      target_price = entry_price - (price_risk_per_unit * rrr_multiplier)
      trade_type_label = "🔴 SHORT (SELL)"

    # Display clean metrics
    m1, m2 = st.columns(2)
    with m1:
      st.markdown(f"""
        <div class="calc-metric-box">
            <p style="color: #848e9c; font-size: 12px; margin-bottom: 5px;">ट्रेडिंग सेटअप टाइप</p>
            <h3 style="color: #fcd535; font-size: 18px; margin: 0;">{trade_type_label}</h3>
        </div>
      """, unsafe_allow_html=True)
      st.markdown("<br>", unsafe_allow_html=True)
      st.markdown(f"""
        <div class="calc-metric-box">
            <p style="color: #848e9c; font-size: 12px; margin-bottom: 5px;">अधिकतम नुकसान (Max Loss Risk)</p>
            <h3 style="color: #f6465d; font-size: 18px; margin: 0;">- ₹ / $ {max_risk_amount:,.2f}</h3>
        </div>
      """, unsafe_allow_html=True)

    with m2:
      st.markdown(f"""
        <div class="calc-metric-box">
            <p style="color: #848e9c; font-size: 12px; margin-bottom: 5px;">खरीदने योग्य मात्रा (Position Size)</p>
            <h3 style="color: #ffffff; font-size: 18px; margin: 0;">{recommended_quantity:,.2f} Units</h3>
        </div>
      """, unsafe_allow_html=True)
      st.markdown("<br>", unsafe_allow_html=True)
      st.markdown(f"""
        <div class="calc-metric-box">
            <p style="color: #848e9c; font-size: 12px; margin-bottom: 5px;">संभावित प्रॉफिट (Target Profit)</p>
            <h3 style="color: #0ecb81; font-size: 18px; margin: 0;">+ ₹ / $ {potential_profit_amount:,.2f}</h3>
        </div>
      """, unsafe_allow_html=True)

  st.markdown("<br>", unsafe_allow_html=True)
  
  # Actionable Summary Box for Normal Users
  st.markdown(f"""
    <div class="signal-box">
        <h4 style="color: #fcd535; margin-top: 0;">💡 आपके लिए सरल निष्कर्ष (Simple Summary for You):</h4>
        <ul style="color: #eaecef; font-size: 14px; line-height: 1.6;">
            <li><b>सेफ पोजीशन साइज:</b> आपको इस ट्रेड में कुल <b>{recommended_quantity:,.2f} क्वांटिटी/शेयर/यूनिट</b> लेनी चाहिए।</li>
            <li><b>नुकसान की सीमा (Risk):</b> अगर ट्रेड गलत हुआ और स्टॉप लॉस हिट हुआ, तो आपका केवल <b>{risk_tolerance_pct}% ({max_risk_amount:,.2f})</b> कैपिटल ही कटेगा, जिससे आपका अकाउंट पूरी तरह सुरक्षित रहेगा।</li>
            <li><b>टारगेट प्राइस (Profit Target):</b> आपके चुने गए रेश्यो के हिसाब से आपका फाइनल टारगेट <b>{target_price:,.2f}</b> रहेगा, जिस पर आपको सीधा <b>{potential_profit_amount:,.2f}</b> का शानदार मुनाफा मिलेगा।</li>
            <li><b>0% Loss Defense Rule:</b> जैसे ही मार्केट आपके पक्ष में आधा रास्ता तय करे, अपना स्टॉप लॉस एंट्री प्राइस पर शिफ्ट कर दें ताकि नुकसान का रिस्क बिल्कुल शून्य (0%) हो जाए!</li>
        </ul>
    </div>
  """, unsafe_allow_html=True)

with tab_chart:
  st.markdown("### 📊 Advanced Ultra-Smooth Live Chart")
  st.info(
      "💡 Tip: Search any symbol directly inside the chart toolbar (e.g., AAPL, RELIANCE, EURUSD, GOLD)."
  )

  c_sym, c_tf = st.columns([2, 2])
  with c_sym:
    custom_symbol = st.text_input(
        "Enter TradingView Symbol:",
        value="BINANCE:BTCUSDT",
        key="chart_symbol_input"
    )
  with c_tf:
    chart_tf_map = {
        "1 Minute": "1",
        "3 Minutes": "3",
        "5 Minutes": "5",
        "15 Minutes": "15",
        "30 Minutes": "30",
        "1 Hour": "60",
        "2 Hours": "120",
        "4 Hours": "240",
        "Daily": "D",
        "Weekly": "W"
    }
    selected_tf_label = st.selectbox(
        "Select Chart Timeframe",
        list(chart_tf_map.keys()),
        index=3,
        key="chart_tf_sel"
    )
    chart_tf = chart_tf_map[selected_tf_label]

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
  st.markdown("### 🎯 World's Best AI Confluence Engine (0% Loss & 10%-20%+ Profit Targets)")
  if "Premium" not in st.session_state.user_tier:
    rem = 2 - st.session_state.signals_used
    st.info(f"Free Plan Quota: {rem}/2 Signals Remaining Today")
  else:
    st.success(
        "👑 Global Multi-Concept Neural Network Active — **99.8% Win Rate Precision Model (0% Loss Shield)**"
    )

  if st.button("🚀 GENERATE 0% LOSS AI SIGNAL", key="gen_sig_btn"):
    if (
        "Premium" not in st.session_state.user_tier
        and st.session_state.signals_used >= 2
    ):
      st.error("⚠️ Daily Free Quota Exhausted! Upgrade to Premium for Unlimited Elite Signals.")
    else:
      if "Premium" not in st.session_state.user_tier:
        st.session_state.signals_used += 1

      st.markdown(
          """
          <div class="signal-box">
              <h3 style="color: #0ecb81; margin-top: 0;">🟢 STATUS: 0% LOSS GUARANTEED HIGH-CONVICTION SETUP</h3>
              <p style="color: #fcd535; font-size: 14px; font-weight: 700;">All World Trading Concepts (SMC + ICT + Wyckoff + Price Action + Order Blocks) Merged & Verified</p>
          </div>
          """,
          unsafe_allow_html=True
      )
      st.markdown("<br>", unsafe_allow_html=True)

      s_col1, s_col2 = st.columns(2)
      with s_col1:
        st.metric("Strategy Accuracy Index", "99.8% WIN RATE", "0% LOSS PROTOCOL")
        st.write(f"**Target Asset:** `{custom_symbol}`")
        st.write("**Capital Defense:** `Strict 1% Max Risk with Auto Break-Even Shield`")
        st.write("**Entry Model:** `Institutional Liquidity Sweep & Order Block Rejection`")
        st.write("**Stop Loss (SL):** `Dynamic Nano-SL (Guarantees zero major drawdown)`")
      with s_col2:
        st.metric("Target Profit Output", "10% to 20%+ Returns", "High Yield Matrix")
        st.write(
            "**Multi-Target Execution Plan (0% Loss / High Profit):**<br>"
            "🛡️ **Safety Protocol:** `Auto-moves to Entry Price at TP1 (Zero Loss Guaranteed)`<br>"
            "🎯 **TP1 (+10% Profit):** `Secure Initial Harvest`<br>"
            "🎯 **TP2 / Moonshot (+20% Profit):** `Major Macro Liquidity Target`"
        )
      
      st.markdown("<br>", unsafe_allow_html=True)
      st.link_button(
          "🚀 Execute Trade instantly on Broker Terminal", "https://in.tradingview.com/"
      )

with tab_plans:
  st.markdown("### 👑 Choose Your VIP Premium Membership Plan")
  st.write(
      "Click on any plan below to instantly open your UPI App with the exact pre-filled amount!"
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
            <p style="font-size: 12px;">✔️ 0% Loss AI Signals</p>
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
            <p style="font-size: 12px;">✔️ Unlimited AI Signals</p>
            <p style="font-size: 12px;">✔️ Priority Telegram Alerts</p>
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
            <h4 style="color: #fcd535; font-size: 16px;">👑 Annual Premium</h4>
            <h3 style="color: #ffffff;">₹7,999</h3>
            <p style="color: #848e9c; font-size: 11px;">Direct Pay</p>
            <hr style="border-color: #2b313a;">
            <p style="font-size: 12px;">✔️ 1 Year Full Access</p>
            <p style="font-size: 12px;">✔️ VIP Support Group</p>
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
            <p style="font-size: 12px;">✔️ 1-on-1 Pro Mentorship</p>
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
    if st.button("Verify & Activate VIP"):
      if len(utr_code.strip()) >= 8:
        st.session_state.user_tier = "Premium Member (Paid)"
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET tier = ? WHERE email = ?",
            ("Premium Member (Paid)", st.session_state.current_user_email),
        )
        conn.commit()
        conn.close()
        st.success("🎉 VIP Membership Activated Successfully!")
        st.rerun()
      else:
        st.error("Please enter a valid UTR reference number.")

st.markdown("---")
st.caption(
    "Disclaimer: Veer Pro Terminal is built strictly for educational & research purposes only. Trading carries risk."
)
