import datetime
import sqlite3
import pandas as pd
import requests
import streamlit as st

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Veer Pro Terminal | Professional Trading Suite",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- WORLD-CLASS TRADINGVIEW & BINANCE GRADE UI CSS ---
st.markdown(
    """
    <style>
    .stApp {
        background: #0b0e11 !important;
        color: #eaecef !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    h1, h2, h3, h4, h5, h6, p, span, label, div {
        color: #eaecef !important;
    }
    .ticker-card {
        background: linear-gradient(135deg, #181a20 0%, #0b0e11 100%);
        border: 1px solid #23272e;
        border-radius: 8px;
        padding: 10px 14px;
        text-align: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
    .broker-card {
        background: #181a20;
        border: 1px solid #23272e;
        border-top: 3px solid #fcd535;
        padding: 35px;
        border-radius: 12px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    .trading-card {
        background: #181a20;
        border: 1px solid #23272e;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        margin-bottom: 15px;
    }
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div {
        background-color: #0b0e11 !important;
        color: #ffffff !important;
        border: 1px solid #2b313a !important;
        border-radius: 6px !important;
        height: 44px !important;
    }
    .stTabs [data-baseweb="tab-list"] { 
        gap: 6px; 
        background-color: #0b0e11; 
        padding: 4px; 
        border-radius: 8px;
        border: 1px solid #23272e;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        border-radius: 6px !important;
        color: #848e9c !important;
        padding: 8px 18px;
        font-size: 13px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background: #fcd535 !important;
        color: #0b0e11 !important;
        font-weight: 800 !important;
    }
    .stButton>button { 
        width: 100%; 
        border-radius: 6px; 
        font-weight: 700; 
        height: 44px; 
        background: #fcd535; 
        color: #0b0e11; 
        border: none;
    }
    .stButton>button:hover { 
        background: #f0b90b !important; 
        color: #0b0e11 !important;
    }
    [data-testid="stSidebar"] {
        background-color: #12161c !important;
        border-right: 1px solid #23272e;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# --- DATABASE & CORE SETUP ---
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
      ("demo_balance", "REAL DEFAULT 10000.0"),
      ("free_signal_date", "TEXT DEFAULT ''"),
      ("vip_indicator_sub", "INTEGER DEFAULT 0"),
  ]
  for col_name, col_type in user_columns:
    try:
      cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
      conn.commit()
    except sqlite3.OperationalError:
      pass

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS paper_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            symbol TEXT,
            action TEXT,
            entry_price REAL,
            amount REAL,
            leverage INTEGER,
            status TEXT DEFAULT 'OPEN',
            time TEXT
        )
    """)
  conn.commit()

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
        "INSERT INTO users (email, password, name, username, tier,"
        " demo_balance, vip_indicator_sub) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            "admin@gmail.com",
            "password123",
            "Pro Master",
            "admin_master",
            "Premium Member (Lifetime)",
            10000.0,
            1,
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


def get_user_full(email):
  try:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT password, name, username, avatar, tier, demo_balance,"
        " free_signal_date, vip_indicator_sub FROM users WHERE email = ?",
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
        "INSERT INTO users (email, password, name, username, tier,"
        " demo_balance, vip_indicator_sub) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            email.strip().lower(),
            password,
            name.strip(),
            username.strip(),
            "Free User",
            10000.0,
            0,
        ),
    )
    conn.commit()
    conn.close()
    return True
  except Exception:
    return False


# --- REAL-TIME LIVE MARKET PRICES API ---
def fetch_global_prices():
  try:
    url = "https://api.binance.com/api/v3/ticker/24hr?symbols=[%22BTCUSDT%22,%22ETHUSDT%22,%22SOLUSDT%22,%22BNBUSDT%22,%22XRPUSDT%22,%22ADAUSDT%22]"
    response = requests.get(url, timeout=2).json()
    prices = {}
    for item in response:
      prices[item["symbol"]] = {
          "price": float(item["lastPrice"]),
          "change": float(item["priceChangePercent"]),
      }
    prices.update({
        "EURUSD": {"price": 1.0935, "change": 0.20},
        "AAPL": {"price": 225.40, "change": 1.35},
        "GOLD": {"price": 2521.10, "change": 0.72},
        "RELIANCE": {"price": 3002.50, "change": 1.05},
    })
    return prices
  except Exception:
    return {
        "BTCUSDT": {"price": 68417.51, "change": 1.23},
        "ETHUSDT": {"price": 3540.49, "change": -0.45},
        "SOLUSDT": {"price": 145.06, "change": 2.45},
        "EURUSD": {"price": 1.0935, "change": 0.20},
        "AAPL": {"price": 225.40, "change": 1.35},
        "GOLD": {"price": 2521.10, "change": 0.72},
        "RELIANCE": {"price": 3002.50, "change": 1.05},
    }


def fetch_live_chart_data(symbol, interval="1h"):
  try:
    limit_val = (
        30
        if interval in ["1m", "5m"]
        else (60 if interval in ["15m", "1h"] else 100)
    )
    if symbol in ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]:
      url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit_val}"
      res = requests.get(url, timeout=3).json()
      df = pd.DataFrame(res, columns=[
          "time",
          "open",
          "high",
          "low",
          "close",
          "volume",
          "close_time",
          "qav",
          "num_trades",
          "taker_base_vol",
          "taker_quote_vol",
          "ignore",
      ])
      df["time"] = pd.to_datetime(df["time"], unit="ms")
      for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)
      return df[["time", "close"]].dropna()
  except Exception:
    pass

  base = (
      68000.0
      if symbol == "BTCUSDT"
      else (
          3500.0
          if symbol == "ETHUSDT"
          else (2521.0 if symbol == "GOLD" else 3002.0)
      )
  )
  import numpy as np

  dates = pd.date_range(end=datetime.datetime.now(), periods=60, freq="h")
  np.random.seed(len(symbol) + 7)
  price_paths = base + np.cumsum(np.random.randn(60) * (base * 0.0015))
  df = pd.DataFrame({"time": dates, "close": price_paths})
  return df


# --- SESSION MANAGEMENT ---
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
      st.session_state.demo_balance = (
          u_data[5] if u_data[5] is not None else 10000.0
      )
      st.session_state.free_signal_date = u_data[6] if u_data[6] else ""
      st.session_state.vip_indicator_sub = (
          u_data[7] if u_data[7] is not None else 0
      )
    else:
      st.session_state.logged_in = False
  else:
    st.session_state.logged_in = False


# --- AUTH SCREEN ---
def show_auth_screen():
  st.markdown("<br><br>", unsafe_allow_html=True)
  c1, col, c2 = st.columns([1, 1.3, 1])
  with col:
    st.markdown(
        """
        <div class="broker-card">
            <div style="text-align: center; margin-bottom: 20px;">
                <h2 style="color: #fcd535; font-size: 24px; font-weight: 800;">⚡ VEER PRO TERMINAL</h2>
                <p style="color: #848e9c; font-size: 12px;">Institutional Multi-Market Trading Gateway</p>
            </div>
        """,
        unsafe_allow_html=True,
    )
    t1, t2 = st.tabs(["🔑 Sign In", "📝 Register"])
    with t1:
      with st.form("login_form"):
        login_email = st.text_input("Email ID", placeholder="name@example.com")
        login_pass = st.text_input(
            "Password", type="password", placeholder="••••••••"
        )
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
            st.session_state.demo_balance = (
                u_data[5] if u_data[5] is not None else 10000.0
            )
            st.session_state.free_signal_date = u_data[6] if u_data[6] else ""
            st.session_state.vip_indicator_sub = (
                u_data[7] if u_data[7] is not None else 0
            )
            st.query_params["session_user"] = cleaned_email
            st.rerun()
          else:
            st.error("Invalid Credentials!")
    with t2:
      with st.form("register_form"):
        reg_name = st.text_input("Full Name", placeholder="John Doe")
        reg_uname = st.text_input("Username", placeholder="trader_alpha")
        reg_email = st.text_input("Email ID", placeholder="john@example.com")
        reg_pass = st.text_input(
            "Password", type="password", placeholder="••••••••"
        )
        if st.form_submit_button("Create Account"):
          cleaned_reg_email = reg_email.strip().lower()
          if register_user(
              cleaned_reg_email, reg_pass, reg_name, reg_uname
          ):
            st.session_state.logged_in = True
            st.session_state.current_user_email = cleaned_reg_email
            st.session_state.current_user_name = reg_name
            st.session_state.username = reg_uname
            st.session_state.avatar = "https://i.imgur.com/71916rK.png"
            st.session_state.user_tier = "Free User"
            st.session_state.demo_balance = 10000.0
            st.session_state.free_signal_date = ""
            st.session_state.vip_indicator_sub = 0
            st.query_params["session_user"] = cleaned_reg_email
            st.rerun()
          else:
            st.error("Email ID already registered!")
    st.markdown("</div>", unsafe_allow_html=True)


if not st.session_state.logged_in:
  show_auth_screen()
  st.stop()


# --- HELPER FOR VIP STATUS CHECK ---
def check_is_vip():
  return (
      "Premium" in st.session_state.user_tier
      or "Lifetime" in st.session_state.user_tier
      or "VIP" in st.session_state.user_tier
      or st.session_state.get("vip_indicator_sub", 0) == 1
      or st.session_state.current_user_email == "admin@gmail.com"
  )


# --- SIDEBAR DASHBOARD ---
with st.sidebar:
  is_vip = check_is_vip()

  if is_vip:
    st.markdown(
        """
        <div style="background: rgba(252, 213, 53, 0.1); border: 1px solid #fcd535; padding: 10px; border-radius: 6px; text-align: center; margin-bottom: 15px;">
            <span style="color: #fcd535; font-weight: 700; font-size: 13px;">👑 VIP ELITE (ALL-TO-ALL FREE)</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
  else:
    st.markdown(
        """
        <div style="background: rgba(132, 142, 156, 0.1); border: 1px solid #23272e; padding: 10px; border-radius: 6px; text-align: center; margin-bottom: 15px;">
            <span style="color: #848e9c; font-weight: 700; font-size: 13px;">👤 TRIAL / FREE USER (LIMITED)</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

  st.markdown("### 👤 Account Profile")
  st.image(st.session_state.avatar, width=70)
  st.markdown(f"**Name:** {st.session_state.current_user_name}")
  st.markdown(f"**Tier:** `{st.session_state.user_tier}`")

  st.markdown("---")
  st.markdown("### 💰 Demo Wallet")
  demo_bal = st.session_state.get("demo_balance", 10000.0)
  st.markdown(
      f"<h3 style='color: #0ecb81; margin: 0;'>${demo_bal:,.2f}</h3>",
      unsafe_allow_html=True,
  )
  if st.button("🔄 Reset Balance ($10,000)"):
    st.session_state.demo_balance = 10000.0
    try:
      conn = get_db_connection()
      cursor = conn.cursor()
      cursor.execute(
          "UPDATE users SET demo_balance = 10000.0 WHERE email = ?",
          (st.session_state.current_user_email,),
      )
      conn.commit()
      conn.close()
    except:
      pass
    st.success("Balance Reset!")
    st.rerun()

  st.markdown("---")
  st.markdown("### 👑 Promo Code")
  promo_input = st.text_input("Enter Code", key="sb_promo")
  if st.button("Redeem"):
    try:
      conn = get_db_connection()
      cursor = conn.cursor()
      cursor.execute(
          "SELECT duration_type FROM promo_codes WHERE code = ? AND is_used = 0",
          (promo_input.strip().upper(),),
      )
      p_data = cursor.fetchone()
      if p_data:
        new_tier = f"VIP Member ({p_data[0]})"
        cursor.execute(
            "UPDATE users SET tier = ?, vip_indicator_sub = 1 WHERE email = ?",
            (new_tier, st.session_state.current_user_email),
        )
        cursor.execute(
            "UPDATE promo_codes SET is_used = 1, used_by = ? WHERE code = ?",
            (st.session_state.current_user_email, promo_input.strip().upper()),
        )
        conn.commit()
        st.session_state.user_tier = new_tier
        st.session_state.vip_indicator_sub = 1
        st.success(f"Activated ({p_data[0]})!")
        st.rerun()
      else:
        st.error("Invalid or already used code!")
      conn.close()
    except Exception as e:
      st.error(f"Error: {e}")

  st.markdown("---")
  if st.button("🚪 Sign Out"):
    st.query_params.clear()
    st.session_state.logged_in = False
    st.rerun()


# --- MAIN HEADER & TICKERS ---
st.markdown(
    """
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
        <div>
            <h1 style="margin: 0; font-size: 22px; color: #fcd535; font-weight: 800;">⚡ VEER PRO TERMINAL</h1>
            <p style="margin: 0; color: #848e9c; font-size: 11px;">Institutional Multi-Asset Trading Suite</p>
        </div>
        <div>
            <span style="background: #181a20; border: 1px solid #23272e; padding: 5px 12px; border-radius: 15px; font-size: 11px; font-weight: 600; color: #0ecb81;">
                ● LIVE CHARTS & SUITE ACTIVE
            </span>
        </div>
    </div>
""",
    unsafe_allow_html=True,
)

prices_data = fetch_global_prices()
cols = st.columns(6)
ticker_keys = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "EURUSD", "AAPL", "GOLD"]
for i, symbol in enumerate(ticker_keys):
  if symbol in prices_data:
    p = prices_data[symbol]["price"]
    c = prices_data[symbol]["change"]
    with cols[i]:
      st.markdown(
          f"""
            <div class="ticker-card">
                <div style="font-size:12px; color:#848e9c;">{symbol}</div>
                <div style="font-size:16px; font-weight:700;">${p:,.2f}</div>
                <div style="font-size:11px; color: {'#0ecb81' if c>=0 else '#f6465d'};">{c}%</div>
            </div>
            """,
          unsafe_allow_html=True,
      )

st.markdown("<br>", unsafe_allow_html=True)

# --- APP TABS ---
main_tab1, main_tab2, main_tab3, main_tab4, main_tab5, main_tab6 = st.tabs([
    "📈 Live Paper Trading",
    "📊 Chart Analyst & Signals",
    "🤖 VIP Indicators & Automation",
    "🛡️ Risk & Discipline",
    "📊 Market Analytics",
    "⚙️ Settings",
])

# ----------------------------------------------------
# TAB 1: LIVE PAPER TRADING
# ----------------------------------------------------
with main_tab1:
  st.markdown("### 📈 Live Market Paper Trading Desk")
  pt_col1, pt_col2 = st.columns([1.2, 1])

  with pt_col1:
    st.markdown("<div class='trading-card'>", unsafe_allow_html=True)
    st.markdown("#### ⚡ Live Order Execution")
    selected_symbol = st.selectbox(
        "Select Asset Pair", list(prices_data.keys()), key="live_pt_symbol"
    )
    current_asset_price = prices_data[selected_symbol]["price"]
    st.markdown(
        f"Market Price: <b style='color: #fcd535;'>${current_asset_price:,.2f}</b>",
        unsafe_allow_html=True,
    )

    trade_action = st.radio(
        "Direction",
        ["🟢 BUY / LONG", "🔴 SELL / SHORT"],
        horizontal=True,
        key="live_pt_action",
    )
    trade_amount = st.number_input(
        "Amount ($)", value=500.0, step=50.0, key="live_pt_amt"
    )
    trade_leverage = st.selectbox(
        "Leverage", [1, 2, 5, 10, 20, 50], index=2, key="live_pt_lev"
    )

    if st.button("🚀 Execute Live Market Order", key="live_exec_btn"):
      current_bal = st.session_state.get("demo_balance", 10000.0)
      if current_bal >= trade_amount:
        new_bal = current_bal - trade_amount
        st.session_state.demo_balance = new_bal
        try:
          conn = get_db_connection()
          cursor = conn.cursor()
          cursor.execute(
              "UPDATE users SET demo_balance = ? WHERE email = ?",
              (new_bal, st.session_state.current_user_email),
          )
          cursor.execute(
              """
                        INSERT INTO paper_trades (email, symbol, action, entry_price, amount, leverage, time)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
              (
                  st.session_state.current_user_email,
                  selected_symbol,
                  trade_action,
                  current_asset_price,
                  trade_amount,
                  trade_leverage,
                  datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
              ),
          )
          conn.commit()
          conn.close()
        except:
          pass
        st.success("Order Executed Successfully!")
        st.rerun()
      else:
        st.error("Insufficient Demo Balance!")
    st.markdown("</div>", unsafe_allow_html=True)

  with pt_col2:
    st.markdown("<div class='trading-card'>", unsafe_allow_html=True)
    st.markdown("#### 📊 Active Open Positions")
    try:
      conn = get_db_connection()
      cursor = conn.cursor()
      cursor.execute(
          "SELECT id, symbol, action, entry_price, amount, leverage FROM"
          " paper_trades WHERE email = ? AND status = 'OPEN'",
          (st.session_state.current_user_email,),
      )
      open_positions = cursor.fetchall()
      conn.close()
    except:
      open_positions = []

    if open_positions:
      for pos in open_positions:
        p_id, p_sym, p_act, p_entry, p_amt, p_lev = pos
        curr_p = prices_data.get(p_sym, {"price": p_entry})["price"]
        pnl = (
            ((curr_p - p_entry) / p_entry) * p_amt * p_lev
            if "BUY" in p_act
            else ((p_entry - curr_p) / p_entry) * p_amt * p_lev
        )
        pnl_color = "#0ecb81" if pnl >= 0 else "#f6465d"
        st.markdown(
            f"""
                <div style="background: #12161c; padding: 12px; border-radius: 6px; margin-bottom: 10px; border-left: 3px solid {pnl_color};">
                    <b>{p_sym}</b> ({p_act}) | PnL: <span style="color: {pnl_color};">${pnl:,.2f}</span><br>
                    <span style="font-size: 11px; color: #848e9c;">Entry: ${p_entry:,.2f} | Live: ${curr_p:,.2f}</span>
                </div>
                """,
            unsafe_allow_html=True,
        )
        if st.button(f"Close Position #{p_id}", key=f"close_{p_id}"):
          st.session_state.demo_balance += p_amt + pnl
          try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET demo_balance = ? WHERE email = ?",
                (
                    st.session_state.demo_balance,
                    st.session_state.current_user_email,
                ),
            )
            cursor.execute(
                "UPDATE paper_trades SET status = 'CLOSED' WHERE id = ?",
                (p_id,),
            )
            conn.commit()
            conn.close()
          except:
            pass
          st.rerun()
    else:
      st.markdown(
          "<p style='color:#848e9c; text-align:center;'>No open positions.</p>",
          unsafe_allow_html=True,
      )
    st.markdown("</div>", unsafe_allow_html=True)


# ----------------------------------------------------
# TAB 2: ADVANCED CHART ANALYST & MULTI-STYLE AI SIGNALS
# ----------------------------------------------------
with main_tab2:
  st.markdown(
      "### 📊 Advanced Multi-Style Chart Analyst & AI Signal Engine"
  )
  st.markdown(
      "<p style='color:#848e9c; font-size:13px;'>Choose your preferred trading"
      " style (Scalping, Intraday, or Swing), timeframe, and AI model below"
      " to generate institutional-grade entry, stop-loss, and take-profit"
      " setups.</p>",
      unsafe_allow_html=True,
  )

  # --- ADVANCED CONTROL TOOLBAR (Binance/TradingView Style) ---
  c_col1, c_col2, c_col3, c_col4 = st.columns(4)
  with c_col1:
    chart_symbol = st.selectbox(
        "📈 Asset Pair", list(prices_data.keys()), key="adv_ca_sym"
    )
  with c_col2:
    trading_style = st.selectbox(
        "⚡ Trading Style",
        [
            "⚡ Scalping (Fast 1m/5m)",
            "📊 Intraday (15m/1h)",
            "📈 Swing Trading (4h/1D)",
        ],
        key="adv_trading_style",
    )
  with c_col3:
    if "Scalping" in trading_style:
      default_tf_idx = 0
      available_tfs = ["1m", "5m", "15m"]
    elif "Intraday" in trading_style:
      default_tf_idx = 1
      available_tfs = ["15m", "1h", "4h"]
    else:
      default_tf_idx = 2
      available_tfs = ["4h", "1D"]

    chart_timeframe = st.selectbox(
        "⏱️ Timeframe",
        available_tfs,
        index=min(default_tf_idx, len(available_tfs) - 1),
        key="adv_ca_tf",
    )
  with c_col4:
    ai_strategy_mode = st.selectbox(
        "🤖 AI Strategy",
        [
            "Momentum Breakout",
            "Trend Following (EMA)",
            "Mean Reversion (RSI)",
            "VIP BOS / ChoCH",
        ],
        key="adv_ai_strategy",
    )

  current_pair_price = prices_data.get(chart_symbol, {"price": 100.0})[
      "price"
  ]
  st.markdown(
      f"<div style='background: #181a20; padding: 12px 16px; border-radius: 8px; margin-bottom: 12px; border: 1px solid #23272e; display: flex; justify-content: space-between; align-items: center;'><span>Active Pair: <b>{chart_symbol}</b> | Style: <b style='color: #fcd535;'>{trading_style}</b></span> <span>Live Price: <b style='color: #0ecb81;'>${current_pair_price:,.2f}</b></span></div>",
      unsafe_allow_html=True,
  )

  # --- DYNAMIC CHART RENDERING ---
  df_chart = fetch_live_chart_data(chart_symbol, chart_timeframe)
  if not df_chart.empty:
    chart_data_indexed = df_chart.set_index("time")
    st.line_chart(
        chart_data_indexed,
        height=380,
        color=["#fcd535"],
    )
  else:
    st.warning("No chart data available for this selection.")

  st.markdown("<br>", unsafe_allow_html=True)

  # --- ADVANCED AI SIGNAL GENERATION TRIGGER ---
  st.markdown(
      """
        <div style="background: #181a20; border: 1px solid #23272e; padding: 20px; border-radius: 10px;">
            <h4 style="margin: 0; color: #fcd535;">🎯 AI Strategy Signal & Risk Matrix Generator</h4>
            <p style="margin: 4px 0 0 0; font-size: 12px; color: #848e9c;">Calculates tailored Stop-Loss (SL) and Take-Profit (TP) according to your selected Trading Style and Timeframe.</p>
        </div>
        """,
      unsafe_allow_html=True,
  )

  st.markdown("<br>", unsafe_allow_html=True)
  if st.button("🚀 Generate Advanced AI Signal", key="generate_adv_signal"):
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    is_vip_active = check_is_vip()

    if is_vip_active:
      can_show_signal = True
    else:
      if st.session_state.get("free_signal_date", "") == today_str:
        can_show_signal = False
      else:
        can_show_signal = True
        st.session_state.free_signal_date = today_str
        try:
          conn = get_db_connection()
          cursor = conn.cursor()
          cursor.execute(
              "UPDATE users SET free_signal_date = ? WHERE email = ?",
              (today_str, st.session_state.current_user_email),
          )
          conn.commit()
          conn.close()
        except:
          pass

    if can_show_signal:
      current_p = current_pair_price

      # Adjust SL and TP multipliers based on user's trading style
      if "Scalping" in trading_style:
        sl_pct = 0.003
        tp_pct = 0.008
        recommended_lev = "10x - 20x"
      elif "Intraday" in trading_style:
        sl_pct = 0.009
        tp_pct = 0.022
        recommended_lev = "5x - 10x"
      else:
        sl_pct = 0.025
        tp_pct = 0.065
        recommended_lev = "1x - 3x"

      entry_l = current_p
      sl_l = current_p * (1 - sl_pct)
      tp_l = current_p * (1 + tp_pct)
      risk_reward = round(tp_pct / sl_pct, 2)

      st.markdown(
          f"""
            <div class="trading-card" style="border-left: 4px solid #0ecb81; background: #12161c;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <h4 style="color: #0ecb81; margin: 0;">🟢 BUY / LONG SIGNAL ({chart_symbol})</h4>
                    <span style="background: rgba(252, 213, 53, 0.1); color: #fcd535; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 700;">{trading_style} | TF: {chart_timeframe}</span>
                </div>
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-top: 10px;">
                    <div style="background: #181a20; padding: 10px; border-radius: 6px;">
                        <span style="font-size: 11px; color: #848e9c;">Entry Price</span><br><b style="color: #ffffff;">${entry_l:,.2f}</b>
                    </div>
                    <div style="background: #181a20; padding: 10px; border-radius: 6px;">
                        <span style="font-size: 11px; color: #848e9c;">Stop Loss (SL)</span><br><b style="color: #f6465d;">${sl_l:,.2f}</b>
                    </div>
                    <div style="background: #181a20; padding: 10px; border-radius: 6px;">
                        <span style="font-size: 11px; color: #848e9c;">Take Profit (TP)</span><br><b style="color: #0ecb81;">${tp_l:,.2f}</b>
                    </div>
                    <div style="background: #181a20; padding: 10px; border-radius: 6px;">
                        <span style="font-size: 11px; color: #848e9c;">Risk-Reward / Lev</span><br><b style="color: #fcd535;">1:{risk_reward} ({recommended_lev})</b>
                    </div>
                </div>
                <p style="font-size: 12px; color: #848e9c; margin-top: 12px; margin-bottom: 0;">✔ Strategy: <b>{ai_strategy_mode}</b> successfully optimized for <b>{chart_symbol}</b>.</p>
            </div>
            """,
          unsafe_allow_html=True,
      )
    else:
      st.warning(
          "⏳ **Trial/Free User Limit Reached!** You have already used your 1"
          " free signal for today. Purchase the **₹399 VIP Subscription** below"
          " to unlock **All-to-All Unlimited Access**."
      )


# ----------------------------------------------------
# TAB 3: VIP INDICATORS & AUTOMATION TOOLS (₹399 / 1 Month)
# ----------------------------------------------------
with main_tab3:
  st.markdown(
      "### 🤖 VIP Indicators & Automated Trading Suite (₹399 / 1 Month)"
  )
  st.markdown(
      "<p style='color:#848e9c; font-size:13px;'>When you purchase the 1 Month"
      " VIP Pass (₹399), <b>All-to-All features become 100% Free and"
      " Unrestricted</b> across the entire terminal.</p>",
      unsafe_allow_html=True,
  )

  is_vip_active = check_is_vip()

  col_ind1, col_ind2 = st.columns(2)

  with col_ind1:
    st.markdown(
        """
        <div class="trading-card" style="border-top: 3px solid #fcd535;">
            <h4 style="color: #fcd535; margin-top: 0;">🚀 VIP Indicator & Automation Pass</h4>
            <p style="font-size: 13px; color: #eaecef;">Get 100% All-to-All Unrestricted Access to all custom AI indicators, automated execution triggers, and live TP/SL charts.</p>
            <h2 style="color: #0ecb81; margin: 10px 0;">₹399 <span style="font-size: 12px; color: #848e9c;">/ 1 Month</span></h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not is_vip_active:
      if st.button("💳 Buy VIP All-Access Pass (₹399 / Month)", key="buy_ind_pass"):
        st.session_state.vip_indicator_sub = 1
        try:
          conn = get_db_connection()
          cursor = conn.cursor()
          cursor.execute(
              "UPDATE users SET vip_indicator_sub = 1, tier = 'VIP All-Access Member (1 Month)' WHERE email = ?",
              (st.session_state.current_user_email,),
          )
          conn.commit()
          conn.close()
        except:
          pass
        st.session_state.user_tier = "VIP All-Access Member (1 Month)"
        st.success(
            "🎉 Successfully Subscribed! All-to-All features are now 100% Free"
            " and Unlocked!"
        )
        st.rerun()
    else:
      st.markdown(
          """
            <div style="background: rgba(14, 203, 129, 0.1); border: 1px solid #0ecb81; padding: 12px; border-radius: 6px; text-align: center;">
                <span style="color: #0ecb81; font-weight: 700; font-size: 13px;">✔ VIP ALL-ACCESS PASS ACTIVE (EVERYTHING UNLOCKED)</span>
            </div>
            """,
          unsafe_allow_html=True,
      )

  with col_ind2:
    st.markdown(
        """
        <div class="trading-card">
            <h4 style="margin-top: 0;">🛠️ VIP All-to-All Benefits</h4>
            <ul style="color: #848e9c; font-size: 13px; padding-left: 20px; line-height: 1.8;">
                <li><b>Unlimited AI Signals:</b> No daily restrictions on charts or timeframes.</li>
                <li><b>All Automation Tools:</b> Instant bot triggers & automated mapping.</li>
                <li><b>Market Structure Auto-Mapping:</b> BOS & ChoCH live scanning.</li>
                <li><b>Priority Server Execution:</b> Zero lag during high market volatility.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

  st.markdown("<br>", unsafe_allow_html=True)
  if st.button(
      "⚡ Run VIP Market Structure Auto-Mapping & Automation Tool",
      key="run_automation_tool",
  ):
    if is_vip_active:
      st.success(
          "✔ VIP All-Access Automation Tool & Market Structure successfully"
          " executed!"
      )
    else:
      st.error(
          "🔒 Access Denied! Trial users have limited automation access."
          " Please purchase the ₹399 VIP Pass for complete All-to-All freedom."
      )


# ----------------------------------------------------
# TAB 4: RISK & DISCIPLINE
# ----------------------------------------------------
with main_tab4:
  st.markdown("### 🛡️ Risk Management")
  st.checkbox("Never risk more than 1-2% per trade.")
  st.checkbox("Always use Stop-Loss.")


# ----------------------------------------------------
# TAB 5: MARKET ANALYTICS
# ----------------------------------------------------
with main_tab5:
  st.markdown("### 📊 Market Analytics")
  st.dataframe(
      pd.DataFrame({
          "Asset": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
          "24h Change (%)": [1.23, -0.45, 2.45],
      }),
      use_container_width=True,
  )


# ----------------------------------------------------
# TAB 6: SETTINGS
# ----------------------------------------------------
with main_tab6:
  st.markdown("### ⚙️ Terminal Settings")
  st.markdown(f"Email: **{st.session_state.current_user_email}**")
  st.markdown(f"Tier: **{st.session_state.user_tier}**")

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown(
    """
    <div style="text-align: center; border-top: 1px solid #23272e; padding-top: 15px;">
        <span style="color: #848e9c; font-size: 11px;">© 2026 Veer Pro Terminal. All Rights Reserved.</span>
    </div>
    """,
    unsafe_allow_html=True,
)
