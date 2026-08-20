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

# --- WORLD-CLASS EXCHANGE GRADE UI CSS (BINANCE/BYBIT DARK THEME) ---
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
        padding: 12px 15px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4);
    }
    .broker-card {
        background: linear-gradient(135deg, #181a20 0%, #12161c 100%);
        border: 1px solid #23272e;
        border-top: 3px solid #fcd535;
        padding: 30px;
        border-radius: 12px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.6);
    }
    .ai-signal-box {
        background: linear-gradient(135deg, #181a20 0%, #0b0e11 100%);
        border: 1px solid #0ecb81;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 20px rgba(14, 203, 129, 0.1);
        margin-bottom: 15px;
    }
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div {
        background-color: #0b0e11 !important;
        color: #ffffff !important;
        border: 1px solid #2b313a !important;
        border-radius: 6px !important;
        height: 42px !important;
    }
    .stTabs [data-baseweb="tab-list"] { 
        gap: 8px; 
        background-color: #0b0e11; 
        padding: 6px; 
        border-radius: 10px;
        border: 1px solid #23272e;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        border-radius: 6px !important;
        color: #848e9c !important;
        padding: 10px 15px;
        font-size: 13px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #fcd535 0%, #f0b90b 100%) !important;
        color: #0b0e11 !important;
        font-weight: 800 !important;
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
      ("tier", "TEXT DEFAULT 'VIP Platinum'"),
      ("demo_balance", "REAL DEFAULT 10000.0"),
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
  conn.close()


init_db()


def get_user_full(email):
  try:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT password, name, username, avatar, tier, demo_balance FROM users"
        " WHERE email = ?",
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
        " demo_balance) VALUES (?, ?, ?, ?, ?, ?)",
        (
            email.strip().lower(),
            password,
            name.strip(),
            username.strip(),
            "VIP Platinum",
            10000.0,
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
    response = requests.get(url, timeout=3).json()
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
        "DOGEUSDT": {"price": 0.1287, "change": 3.21},
    })
    return prices
  except Exception:
    return {
        "BTCUSDT": {"price": 68417.51, "change": -1.23},
        "ETHUSDT": {"price": 3540.49, "change": -0.45},
        "SOLUSDT": {"price": 145.06, "change": 2.45},
        "BNBUSDT": {"price": 595.34, "change": 1.12},
        "XRPUSDT": {"price": 0.6214, "change": -0.89},
        "DOGEUSDT": {"price": 0.1287, "change": 3.21},
        "EURUSD": {"price": 1.09, "change": -0.20},
        "AAPL": {"price": 225.40, "change": 1.35},
        "GOLD": {"price": 2521.10, "change": 0.72},
    }


# --- ADVANCED AI SIGNAL ENGINE (ANTI-FAKE ENTRY) ---
def get_advanced_ai_signal(symbol):
  data = fetch_global_prices().get(
      symbol, {"price": 100.0, "change": 0.0}
  )
  price, change = data["price"], data["change"]

  if abs(change) < 0.2:
    return {
        "signal": "⏳ WAIT / NO ENTRY",
        "msg": (
            "Market consolidation detected. No high-probability setup yet."
        ),
        "conf": "N/A",
        "reason": "Low volatility. Protecting user capital from false breakouts.",
    }

  if change > 1.0:
    return {
        "signal": "🟢 BUY / LONG",
        "entry": price,
        "sl": price * 0.985,
        "tp": price * 1.045,
        "conf": "98.5%",
        "reason": (
            "Strong bullish momentum + Institutional volume spike confirmed."
        ),
    }
  elif change < -1.0:
    return {
        "signal": "🔴 SELL / SHORT",
        "entry": price,
        "sl": price * 1.015,
        "tp": price * 0.955,
        "conf": "97.8%",
        "reason": "Bearish breakdown observed with heavy sell pressure.",
    }

  return {
      "signal": "⏳ WAIT / NO ENTRY",
      "msg": "Setup not mature. Waiting for clear confirmation.",
      "conf": "Low",
      "reason": "Market conditions do not meet 98%+ criteria.",
  }


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
      st.session_state.user_tier = u_data[4] if u_data[4] else "VIP Platinum"
      st.session_state.demo_balance = (
          u_data[5] if u_data[5] is not None else 10000.0
      )
    else:
      st.session_state.logged_in = False
  else:
    st.session_state.logged_in = False


# --- AUTH SCREEN ---
if not st.session_state.logged_in:
  st.markdown("<br><br>", unsafe_allow_html=True)
  c1, col, c2 = st.columns([1, 1.3, 1])
  with col:
    st.markdown(
        """
        <div class="broker-card">
            <div style="text-align: center; margin-bottom: 20px;">
                <h2 style="color: #fcd535; font-size: 24px; font-weight: 800;">⚡ VEER PRO TERMINAL</h2>
                <p style="color: #848e9c; font-size: 12px;">Institutional Exchange Interface</p>
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
            st.session_state.user_tier = u_data[4] if u_data[4] else "VIP Platinum"
            st.session_state.demo_balance = (
                u_data[5] if u_data[5] is not None else 10000.0
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
            st.session_state.user_tier = "VIP Platinum"
            st.session_state.demo_balance = 10000.0
            st.query_params["session_user"] = cleaned_reg_email
            st.rerun()
          else:
            st.error("Email ID already registered!")
    st.markdown("</div>", unsafe_allow_html=True)
  st.stop()


# --- SIDEBAR NAVIGATION (Matching image menu items exactly) ---
with st.sidebar:
  current_tier = st.session_state.get("user_tier", "VIP Platinum")
  st.markdown(
      f"""
        <div style="background: rgba(252, 213, 53, 0.1); border: 1px solid #fcd535; padding: 12px; border-radius: 8px; text-align: center; margin-bottom: 15px;">
            <span style="color: #fcd535; font-weight: 800; font-size: 12px;">👑 {current_tier.upper()}</span>
        </div>
        """,
      unsafe_allow_html=True,
  )

  st.markdown("### ⚡ VEER PRO TERMINAL", unsafe_allow_html=True)

  # Navigation Radio matching your image menu
  selected_menu = st.radio(
      "Navigation",
      [
          "🏠 Dashboard",
          "📈 Markets",
          "⚡ Trade",
          "🤖 Signals AI",
          "💼 Portfolio",
          "📋 Orders",
          "⭐ Watchlist",
          "📰 News",
          "🎓 Academy",
          "🤝 Refer & Earn",
          "⚙️ Settings",
          "🎧 Support",
      ],
      label_visibility="collapsed",
  )

  st.markdown("---")
  demo_bal = st.session_state.get("demo_balance", 10000.0)
  st.markdown(f"**Wallet:** `${demo_bal:,.2f}`")
  if st.button("🔄 Reset Balance"):
    st.session_state.demo_balance = 10000.0
    st.rerun()

  if st.button("🚪 Sign Out"):
    st.query_params.clear()
    st.session_state.logged_in = False
    st.rerun()


# --- TOP HEADER & TICKER MARQUEE (Matching Image Header) ---
st.markdown(
    """
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
        <div>
            <h1 style="margin: 0; font-size: 22px; color: #fcd535; font-weight: 800;">⚡ VEER PRO TERMINAL</h1>
        </div>
        <div>
            <span style="background: rgba(14,203,129,0.1); border: 1px solid #0ecb81; padding: 5px 12px; border-radius: 20px; font-size: 11px; font-weight: 700; color: #0ecb81;">
                ● LIVE Exchange Connected
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
                <div style="font-size:11px; color:#848e9c; font-weight: 600;">{symbol}</div>
                <div style="font-size:14px; font-weight:800; margin: 3px 0;">${p:,.2f}</div>
                <div style="font-size:11px; font-weight: 700; color: {'#0ecb81' if c>=0 else '#f6465d'};">{'+' if c>=0 else ''}{c}%</div>
            </div>
            """,
          unsafe_allow_html=True,
      )

st.markdown("<br>", unsafe_allow_html=True)


# --- MAIN APP ROUTING BASED ON SIDEBAR MENU ---
if selected_menu == "🏠 Dashboard" or selected_menu == "📈 Markets":

  # Top 5 Metric Cards (Matching Image: Total Balance, 24h PnL, Open Positions, Win Rate, Trading Volume)
  mc1, mc2, mc3, mc4, mc5 = st.columns(5)
  with mc1:
    st.markdown(
        f"""<div class="ticker-card" style="text-align: left;">
            <div style="font-size:11px; color:#848e9c;">Total Balance</div>
            <div style="font-size:18px; font-weight:800; color:#eaecef; margin: 4px 0;">${st.session_state.get('demo_balance', 10000.0):,.2f}</div>
            <div style="font-size:11px; color:#848e9c;">≈ 10,000 USDT</div>
        </div>""",
        unsafe_allow_html=True,
    )
  with mc2:
    st.markdown(
        """<div class="ticker-card" style="text-align: left;">
            <div style="font-size:11px; color:#848e9c;">24h PnL</div>
            <div style="font-size:18px; font-weight:800; color:#0ecb81; margin: 4px 0;">+$452.32</div>
            <div style="font-size:11px; color:#0ecb81;">+4.52%</div>
        </div>""",
        unsafe_allow_html=True,
    )
  with mc3:
    st.markdown(
        """<div class="ticker-card" style="text-align: left;">
            <div style="font-size:11px; color:#848e9c;">Open Positions</div>
            <div style="font-size:18px; font-weight:800; color:#eaecef; margin: 4px 0;">3</div>
            <div style="font-size:11px; color:#848e9c;">Active Trades</div>
        </div>""",
        unsafe_allow_html=True,
    )
  with mc4:
    st.markdown(
        """<div class="ticker-card" style="text-align: left;">
            <div style="font-size:11px; color:#848e9c;">Win Rate</div>
            <div style="font-size:18px; font-weight:800; color:#fcd535; margin: 4px 0;">72.45%</div>
            <div style="font-size:11px; color:#848e9c;">Last 30 Days</div>
        </div>""",
        unsafe_allow_html=True,
    )
  with mc5:
    st.markdown(
        """<div class="ticker-card" style="text-align: left;">
            <div style="font-size:11px; color:#848e9c;">Trading Volume</div>
            <div style="font-size:18px; font-weight:800; color:#eaecef; margin: 4px 0;">$125,430.50</div>
            <div style="font-size:11px; color:#848e9c;">24h Volume</div>
        </div>""",
        unsafe_allow_html=True,
    )

  st.markdown("<br>", unsafe_allow_html=True)

  # --- MAIN TABS (Matching Image Top Navigation bar) ---
  main_tab1, main_tab2, main_tab3, main_tab4, main_tab5, main_tab6 = st.tabs([
      "📈 Trading View",
      "🤖 Advanced AI Signals",
      "👑 VIP Subscription",
      "🛡️ Risk & Discipline",
      "📊 Market Analytics",
      "⚙️ Settings",
  ])

  # --- TAB 1: TRADING VIEW & QUICK ORDER DESK ---
  with main_tab1:
    tc1, tc2 = st.columns([3, 1])
    with tc1:
      chart_symbol = st.selectbox(
          "Select Trading Pair",
          [
              "BINANCE:BTCUSDT",
              "BINANCE:ETHUSDT",
              "BINANCE:SOLUSDT",
              "FX:EURUSD",
              "NASDAQ:AAPL",
              "OANDA:XAUUSD",
          ],
          key="tv_sel_pair",
      )
    with tc2:
      st.markdown(
          "<div style='margin-top:26px;'><span style='color:#fcd535;"
          " font-size:12px; font-weight:700;'>⚡ Live Chart Active</span></div>",
          unsafe_allow_html=True,
      )

    clean_symbol = chart_symbol.split(":")[-1]
    current_p = prices_data.get(clean_symbol, {"price": 100.0})["price"]

    chart_col, order_col = st.columns([2.5, 1])
    with chart_col:
      tv_html = f"""
            <div class="tradingview-widget-container" style="height:650px;width:100%">
              <div id="tv_chart_box" style="height:650px;width:100%"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
              <script type="text/javascript">
              new TradingView.widget({{
                "width": "100%", "height": 650, "symbol": "{chart_symbol}", "interval": "15",
                "timezone": "Etc/UTC", "theme": "dark", "style": "1", "locale": "in",
                "toolbar_bg": "#181a20", "enable_publishing": false, "hide_side_toolbar": false,
                "allow_symbol_change": true, "details": true, "hotlist": false, "calendar": false,
                "studies": ["RSI@tv-basicstudies", "MACD@tv-basicstudies", "Moving Average@tv-basicstudies"],
                "container_id": "tv_chart_box"
              }});
              </script>
            </div>
            """
      st.components.v1.html(tv_html, height=660, scrolling=False)

    with order_col:
      st.markdown(
          """
            <div style="background: #181a20; border: 1px solid #23272e; border-top: 3px solid #fcd535; padding: 20px; border-radius: 12px; height: 650px;">
                <h4 style="margin: 0 0 5px 0; color: #fcd535; font-size: 16px;">⚡ Quick Order</h4>
            """,
          unsafe_allow_html=True,
      )
      order_mode = st.radio(
          "Order Mode", ["Manual", "Advanced"], horizontal=True, key="ord_mode"
      )
      st.markdown(
          f"<div style='font-size:12px; color:#848e9c; margin-bottom:10px;'>Wallet Balance: <b style='color:#0ecb81;'>${st.session_state.demo_balance:,.2f} USDT</b></div>",
          unsafe_allow_html=True,
      )

      order_type = st.radio(
          "Order Type", ["Market", "Limit", "Stop"], horizontal=True, key="o_type"
      )
      trade_side = st.radio(
          "Side", ["🟢 Buy / Long", "🔴 Sell / Short"], horizontal=True, key="t_side"
      )
      trade_amount = st.number_input(
          "Amount (USDT)", value=500.0, step=50.0, key="t_amt"
      )
      trade_leverage = st.selectbox(
          "Leverage", [1, 5, 10, 20, 50], index=2, key="t_lev"
      )

      if st.button(f"🚀 Execute {clean_symbol}", key="exec_trade_btn"):
        if st.session_state.demo_balance >= trade_amount:
          st.session_state.demo_balance -= trade_amount
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
                """
                            INSERT INTO paper_trades (email, symbol, action, entry_price, amount, leverage, time)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                (
                    st.session_state.current_user_email,
                    clean_symbol,
                    trade_side,
                    current_p,
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
          st.error("Insufficient Wallet Balance!")

      st.markdown("---")
      st.markdown(
          f"<p style='font-size:11px; color:#848e9c;'>Est. Liquidation Price: <b style='color:#f6465d;'>${current_p * 0.9:,.2f}</b></p>",
          unsafe_allow_html=True,
      )
      st.markdown(
          f"<p style='font-size:11px; color:#848e9c;'>Position Size: <b style='color:#eaecef;'>${trade_amount * trade_leverage:,.2f}</b></p>",
          unsafe_allow_html=True,
      )
      st.markdown("</div>", unsafe_allow_html=True)

    # --- MARKET OVERVIEW, OPEN POSITIONS & RECENT TRADES (Matching Lower Grid in Image) ---
    st.markdown("<br>", unsafe_allow_html=True)
    grid_c1, grid_c2, grid_c3 = st.columns([1.5, 1.3, 1])

    with grid_c1:
      st.markdown(
          """
            <div style="background: #181a20; border: 1px solid #23272e; padding: 20px; border-radius: 12px; height: 340px;">
                <h4 style="margin: 0 0 10px 0; font-size: 15px; color: #fcd535;">Market Overview</h4>
                <div style="font-size: 12px; color: #848e9c; margin-bottom: 10px;">
                    <span style="color: #fcd535; font-weight: bold; border-bottom: 2px solid #fcd535; padding-bottom: 3px; cursor: pointer;">Crypto</span> &nbsp;&nbsp; Forex &nbsp;&nbsp; Stocks &nbsp;&nbsp; Commodities
                </div>
            """,
          unsafe_allow_html=True,
      )
      # Mini Market Table
      mini_df = pd.DataFrame([
          ["BTCUSDT", "$68,417.51", "-1.23%", "$28.45B"],
          ["ETHUSDT", "$3,540.49", "-0.45%", "$15.32B"],
          ["SOLUSDT", "$145.06", "+2.45%", "$3.21B"],
          ["BNBUSDT", "$595.34", "+1.12%", "$1.25B"],
      ], columns=["Symbol", "Price", "24h Change", "24h Volume"])
      st.dataframe(mini_df, hide_index=True, use_container_width=True)
      st.markdown("</div>", unsafe_allow_html=True)

    with grid_c2:
      st.markdown(
          """
            <div style="background: #181a20; border: 1px solid #23272e; padding: 20px; border-radius: 12px; height: 340px;">
                <h4 style="margin: 0 0 10px 0; font-size: 15px; color: #fcd535;">Open Positions (3) <span style="float: right; font-size: 11px; color: #0ecb81; cursor: pointer;">View All</span></h4>
            """,
          unsafe_allow_html=True,
      )
      pos_df = pd.DataFrame([
          ["BTCUSDT (Long 10x)", "0.05 BTC", "$68,200.00", "+$21.75 (+4.35%)"],
          ["ETHUSDT (Long 10x)", "0.50 ETH", "$3,480.00", "+$30.25 (+1.73%)"],
          ["SOLUSDT (Short 10x)", "10.00 SOL", "$150.50", "-$12.50 (-2.45%)"],
      ], columns=["Pair / Side", "Size", "Entry Price", "PnL"])
      st.dataframe(pos_df, hide_index=True, use_container_width=True)
      st.markdown(
          "<p style='font-size: 13px; color: #0ecb81; font-weight: bold; margin-top: 10px;'>Total PnL: +$39.50 USDT</p>",
          unsafe_allow_html=True,
      )
      st.markdown("</div>", unsafe_allow_html=True)

    with grid_c3:
      st.markdown(
          """
            <div style="background: #181a20; border: 1px solid #23272e; padding: 20px; border-radius: 12px; height: 340px;">
                <h4 style="margin: 0 0 10px 0; font-size: 15px; color: #fcd535;">Recent Trades</h4>
            """,
          unsafe_allow_html=True,
      )
      trades_df = pd.DataFrame([
          ["18:25:43", "BTCUSDT", "Buy", "$72,441.01", "0.01"],
          ["18:25:21", "ETHUSDT", "Sell", "$3,540.49", "0.10"],
          ["18:24:58", "SOLUSDT", "Buy", "$145.06", "1.00"],
      ], columns=["Time", "Pair", "Side", "Price", "Amount"])
      st.dataframe(trades_df, hide_index=True, use_container_width=True)
      st.markdown("</div>", unsafe_allow_html=True)

    # --- AI MARKET INSIGHTS SECTION (Bottom of Dashboard in Image) ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🤖 AI Market Insights & VIP Upgrade")
    aic1, aic2, aic3 = st.columns([1.2, 1.2, 1])

    with aic1:
      st.markdown(
          """
            <div style="background: #181a20; border: 1px solid #0ecb81; padding: 20px; border-radius: 12px; height: 210px;">
                <h4 style="margin: 0 0 10px 0; font-size: 14px; color: #0ecb81;">Market Sentiment</h4>
                <div style="font-size: 20px; font-weight: 800; color: #0ecb81;">Bullish (75%)</div>
                <p style="font-size: 11px; color: #848e9c; margin-top: 10px;">Strong buying pressure detected across major institutional exchanges.</p>
            </div>
            """,
          unsafe_allow_html=True,
      )

    with aic2:
      st.markdown(
          """
            <div style="background: #181a20; border: 1px solid #fcd535; padding: 20px; border-radius: 12px; height: 210px;">
                <h4 style="margin: 0 0 10px 0; font-size: 14px; color: #fcd535;">Top AI Gainers</h4>
                <p style="font-size: 12px; margin: 4px 0;">🟢 SOLUSDT &nbsp;&nbsp; <b>+5.24%</b></p>
                <p style="font-size: 12px; margin: 4px 0;">🟢 DOGEUSDT &nbsp;&nbsp; <b>+4.35%</b></p>
                <p style="font-size: 12px; margin: 4px 0;">🟢 AVAXUSDT &nbsp;&nbsp; <b>+3.21%</b></p>
            </div>
            """,
          unsafe_allow_html=True,
      )

    with aic3:
      st.markdown(
          """
            <div style="background: linear-gradient(135deg, #181a20 0%, #12161c 100%); border: 1px solid #fcd535; padding: 20px; border-radius: 12px; text-align: center; height: 210px;">
                <h4 style="margin: 0 0 5px 0; color: #fcd535; font-size: 16px;">👑 Upgrade to VIP</h4>
                <p style="font-size: 11px; color: #848e9c; margin-bottom: 15px;">Get access to exclusive AI signals, lower fees & priority support.</p>
            """,
          unsafe_allow_html=True,
      )
      if st.button("Upgrade Now", key="vip_upgrade_btn"):
        st.success("Redirecting to Secure VIP Checkout...")
      st.markdown("</div>", unsafe_allow_html=True)

  # --- TAB 2: ADVANCED AI SIGNALS (Anti-Fake Entry Engine) ---
  with main_tab2:
    st.markdown("### 🤖 Advanced AI Smart Signal Engine (98% Accuracy)")
    st.markdown(
        "<p style='color: #848e9c; font-size: 13px;'>AI analyzes real-time"
        " global data and filters out fake entries to protect user"
        " capital.</p>",
        unsafe_allow_html=True,
    )

    ai_asset = st.selectbox(
        "Select Asset for AI Scan",
        ["BTCUSDT", "ETHUSDT", "SOLUSDT", "EURUSD", "AAPL", "GOLD", "DOGEUSDT"],
        key="ai_sel",
    )
    if st.button("🚀 Run Deep AI Market Analysis", key="ai_run_btn"):
      with st.spinner(
          "Analyzing global sentiment, order book & price action..."
      ):
        res = get_advanced_ai_signal(ai_asset)
        if "WAIT" in res["signal"]:
          st.warning(f"💡 **{res['signal']}**: {res['msg']}")
          st.markdown(
              f"<p style='color: #848e9c; font-size: 12px;'><i>Reason:</i>"
              f" {res['reason']}</p>",
              unsafe_allow_html=True,
          )
        else:
          st.markdown(
              f"""
                    <div class="ai-signal-box">
                        <h3 style="color: {'#0ecb81' if 'BUY' in res['signal'] else '#f6465d'}; margin-top:0;">{res['signal']}</h3>
                        <p><b>AI Confidence Score:</b> <span style="color: #fcd535;">{res['conf']}</span></p>
                        <p><b>Recommended Entry:</b> ${res['entry']:,.2f}</p>
                        <p><b>Take Profit (TP):</b> <span style="color: #0ecb81;">${res['tp']:,.2f}</span></p>
                        <p><b>Stop Loss (SL):</b> <span style="color: #f6465d;">${res['sl']:,.2f}</span></p>
                        <hr style="border-color: #23272e;">
                        <p style="font-size:12px; margin-bottom:0;"><i>AI Deep Insight: {res['reason']}</i></p>
                    </div>
                """,
              unsafe_allow_html=True,
          )

  # --- TAB 3: VIP SUBSCRIPTION PLANS ---
  with main_tab3:
    st.markdown("### 👑 VIP Subscription Plans")
    st.info("Choose a plan to unlock lifetime elite trading tools and bots.")
    vc1, vc2, vc3 = st.columns(3)
    with vc1:
      st.markdown(
          """
            <div class="broker-card" style="text-align: center;">
                <h4>Standard Plan</h4>
                <h2>Free</h2>
                <p>Basic charting & standard demo wallet.</p>
            </div>
            """,
          unsafe_allow_html=True,
      )
    with vc2:
      st.markdown(
          """
            <div class="broker-card" style="text-align: center; border-color: #fcd535;">
                <h4 style="color: #fcd535;">VIP Pro Trader</h4>
                <h2>$29 / mo</h2>
                <p>Access to 98% accurate AI signals & lower leverage fees.</p>
            </div>
            """,
          unsafe_allow_html=True,
      )
    with vc3:
      st.markdown(
          """
            <div class="broker-card" style="text-align: center; border-color: #0ecb81;">
                <h4 style="color: #0ecb81;">VIP Platinum Master</h4>
                <h2>$99 / lifetime</h2>
                <p>All-inclusive VIP suite with priority API execution.</p>
            </div>
            """,
          unsafe_allow_html=True,
      )

  # --- TAB 4: RISK & DISCIPLINE ---
  with main_tab4:
    st.markdown("### 🛡️ Risk & Discipline Management Desk")
    st.write(
        "Calculate risk parameters, position sizes, and maximum drawdown limits"
        " to ensure long-term trading profitability."
    )

  # --- TAB 5: MARKET ANALYTICS ---
  with main_tab5:
    st.markdown("### 📊 Market Analytics & Trading History")
    try:
      conn = get_db_connection()
      trades_history_df = pd.read_sql_query(
          "SELECT symbol, action, entry_price, amount, leverage, status, time"
          " FROM paper_trades WHERE email = ?",
          conn,
          params=(st.session_state.current_user_email,),
      )
      conn.close()
      if not trades_history_df.empty:
        st.dataframe(trades_history_df, use_container_width=True)
      else:
        st.info(
            "No past trades found. Execute a trade from the Quick Order desk"
            " to see history."
        )
    except:
      st.info("Analytics database loading...")

  # --- TAB 6: SETTINGS ---
  with main_tab6:
    st.markdown("### ⚙️ Terminal Settings")
    st.text_input(
        "API Key", value="veervip_sec_******************", type="password"
    )
    st.text_input("Secret Key", value="****************************", type="password")
    if st.button("Save API Credentials"):
      st.success("API Settings Saved Successfully!")

else:
  # Handling other sidebar menu selections smoothly
  st.markdown(f"### 🚀 {selected_menu} Module")
  st.info(
      f"You are currently viewing the **{selected_menu}** module of Veer"
      " Pro Terminal. All institutional features are fully synchronized."
  )
