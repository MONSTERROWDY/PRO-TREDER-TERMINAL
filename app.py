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

# --- WORLD-CLASS TRADINGVIEW GRADE UI CSS ---
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
    .vip-box {
        background: linear-gradient(135deg, #1e1e24 0%, #12161c 100%);
        border: 1px solid #fcd535;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 4px 15px rgba(252, 213, 53, 0.1);
    }
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div {
        background-color: #0b0e11 !important;
        color: #ffffff !important;
        border: 1px solid #2b313a !important;
        border-radius: 6px !important;
        height: 40px !important;
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
        height: 40px; 
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
      ("tier", "TEXT DEFAULT 'Standard'"),
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

  cursor.execute("SELECT * FROM users WHERE email = ?", ("admin@gmail.com",))
  if not cursor.fetchone():
    cursor.execute(
        "INSERT INTO users (email, password, name, username, tier,"
        " demo_balance) VALUES (?, ?, ?, ?, ?, ?)",
        (
            "admin@gmail.com",
            "password123",
            "Pro Master",
            "admin_master",
            "VIP Platinum",
            10000.0,
        ),
    )
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
            "Standard",
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
      st.session_state.user_tier = u_data[4] if u_data[4] else "Standard"
      st.session_state.demo_balance = (
          u_data[5] if u_data[5] is not None else 10000.0
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
            st.session_state.user_tier = u_data[4] if u_data[4] else "Standard"
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
            st.session_state.user_tier = "Standard"
            st.session_state.demo_balance = 10000.0
            st.query_params["session_user"] = cleaned_reg_email
            st.rerun()
          else:
            st.error("Email ID already registered!")
    st.markdown("</div>", unsafe_allow_html=True)


if not st.session_state.logged_in:
  show_auth_screen()
  st.stop()


# --- SIDEBAR DASHBOARD ---
with st.sidebar:
  current_tier = st.session_state.get("user_tier", "Standard")
  tier_badge_color = (
      "#fcd535" if "VIP" in current_tier or "Pro" in current_tier else "#848e9c"
  )
  st.markdown(
      f"""
        <div style="background: rgba(252, 213, 53, 0.1); border: 1px solid {tier_badge_color}; padding: 10px; border-radius: 6px; text-align: center; margin-bottom: 15px;">
            <span style="color: {tier_badge_color}; font-weight: 700; font-size: 13px;">👑 {current_tier.upper()}</span>
        </div>
        """,
      unsafe_allow_html=True,
  )

  st.markdown("### 👤 Account Profile")
  st.image(st.session_state.avatar, width=70)
  st.markdown(f"**Name:** {st.session_state.current_user_name}")
  st.markdown(f"**Tier:** `{current_tier}`")

  if "VIP" not in current_tier:
    if st.button("⭐ Upgrade to VIP Access"):
      st.session_state.user_tier = "VIP Platinum"
      try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET tier = 'VIP Platinum' WHERE email = ?",
            (st.session_state.current_user_email,),
        )
        conn.commit()
        conn.close()
      except:
        pass
      st.success("Upgraded to VIP Platinum!")
      st.rerun()

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
                ● OFFICIAL TRADINGVIEW ADVANCED CHARTS ACTIVE
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

# --- REFINED APP TABS (REMOVED SEPARATE DEMO TAB, INTEGRATED EVERYTHING INTO TRADINGVIEW CHART DESK) ---
main_tab1, main_tab2, main_tab3, main_tab4 = st.tabs([
    "📈 TradingView Chart Desk & Paper Broker",
    "🛡️ Risk & Discipline",
    "📊 Market Analytics",
    "⚙️ Settings",
])

# ----------------------------------------------------
# TAB 1: TRADINGVIEW CHART DESK & INTEGRATED PAPER BROKER
# ----------------------------------------------------
with main_tab1:
  st.markdown("### 📈 Professional TradingView Advanced Chart & Integrated Desk")
  st.markdown(
      "<p style='color:#848e9c; font-size:13px;'>Powered by official TradingView"
      " Advanced Charting. Analyze charts with technical indicators, tools,"
      " and execute paper trades directly on the same screen.</p>",
      unsafe_allow_html=True,
  )

  # --- TOP CONTROLS FOR ASSET SELECTION ---
  tc1, tc2 = st.columns([2, 1])
  with tc1:
    chart_symbol = st.selectbox(
        "📈 Select Asset Symbol for TradingView",
        ["BINANCE:BTCUSDT", "BINANCE:ETHUSDT", "BINANCE:SOLUSDT", "FX:EURUSD", "NASDAQ:AAPL", "OANDA:XAUUSD"],
        key="tv_symbol_select",
    )
  with tc2:
    st.markdown(
        "<div style='margin-top: 26px;'><span style='color: #0ecb81; font-size: 12px; font-weight: 700;'>● Live Feed Synchronized</span></div>",
        unsafe_allow_html=True,
    )

  clean_symbol_key = chart_symbol.split(":")[-1]
  current_pair_price = prices_data.get(clean_symbol_key, {"price": 100.0})[
      "price"
  ]

  # --- LAYOUT: OFFICIAL TRADINGVIEW EMBED (LEFT) + INTEGRATED PAPER BROKER (RIGHT) ---
  chart_col, broker_col = st.columns([2.2, 1.1])

  with chart_col:
    # --- OFFICIAL TRADINGVIEW ADVANCED EMBED WIDGET (HTML/JS) ---
    tv_widget_html = f"""
        <div class="tradingview-widget-container" style="height:520px;width:100%">
          <div id="tradingview_advanced_chart" style="height:520px;width:100%"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          new TradingView.widget(
          {{
            "width": "100%",
            "height": 520,
            "symbol": "{chart_symbol}",
            "interval": "60",
            "timezone": "Etc/UTC",
            "theme": "dark",
            "style": "1",
            "locale": "in",
            "toolbar_bg": "#181a20",
            "enable_publishing": false,
            "hide_side_toolbar": false,
            "allow_symbol_change": true,
            "details": true,
            "hotlist": true,
            "calendar": false,
            "studies": [
              "RSI@tv-basicstudies",
              "MACD@tv-basicstudies"
            ],
            "container_id": "tradingview_advanced_chart"
          }}
          );
          </script>
        </div>
        """
    st.components.v1.html(tv_widget_html, height=530, scrolling=False)

  with broker_col:
    # --- INTEGRATED PAPER TRADING WIDGET RIGHT INSIDE THE CHART SECTION ---
    st.markdown(
        """
        <div style="background: #181a20; border: 1px solid #23272e; border-top: 3px solid #fcd535; padding: 16px; border-radius: 10px;">
            <h4 style="margin: 0 0 5px 0; color: #fcd535; font-size: 15px;">⚡ Integrated Paper Broker</h4>
            <p style="margin: 0 0 10px 0; font-size: 11px; color: #848e9c;">Execute orders instantly while viewing the chart.</p>
        """,
        unsafe_allow_html=True,
    )

    demo_wallet = st.session_state.get("demo_balance", 10000.0)
    st.markdown(
        f"<div style='font-size: 12px; color: #848e9c; margin-bottom: 8px;'>Demo Balance: <b style='color: #0ecb81;'>${demo_wallet:,.2f}</b></div>",
        unsafe_allow_html=True,
    )

    chart_trade_action = st.radio(
        "Order Direction",
        ["🟢 BUY / LONG", "🔴 SELL / SHORT"],
        horizontal=True,
        key="tv_chart_trade_action",
    )
    chart_trade_amt = st.number_input(
        "Trade Amount ($)", value=300.0, step=50.0, key="tv_chart_trade_amt"
    )
    chart_trade_lev = st.selectbox(
        "Leverage", [1, 5, 10, 20, 50], index=1, key="tv_chart_trade_lev"
    )

    if st.button(
        f"🚀 Place Order ({clean_symbol_key})", key="tv_place_chart_order"
    ):
      if demo_wallet >= chart_trade_amt:
        new_bal = demo_wallet - chart_trade_amt
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
                  clean_symbol_key,
                  chart_trade_action,
                  current_pair_price,
                  chart_trade_amt,
                  chart_trade_lev,
                  datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
              ),
          )
          conn.commit()
          conn.close()
        except:
          pass
        st.success(f"Order Placed for {clean_symbol_key}!")
        st.rerun()
      else:
        st.error("Insufficient Balance!")

    st.markdown("<hr style='border-color: #23272e; margin: 12px 0;'>", unsafe_allow_html=True)
    st.markdown(
        "<b style='font-size: 12px; color: #eaecef;'>Active Open Positions:</b>",
        unsafe_allow_html=True,
    )

    try:
      conn = get_db_connection()
      cursor = conn.cursor()
      cursor.execute(
          "SELECT id, symbol, action, entry_price, amount, leverage FROM"
          " paper_trades WHERE email = ? AND status = 'OPEN'",
          (st.session_state.current_user_email,),
      )
      chart_open_pos = cursor.fetchall()
      conn.close()
    except:
      chart_open_pos = []

    if chart_open_pos:
      for pos in chart_open_pos:
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
                <div style="background: #12161c; padding: 8px; border-radius: 6px; margin-bottom: 6px; font-size: 11px; border-left: 2px solid {pnl_color};">
                    <b>{p_sym}</b> | PnL: <span style="color: {pnl_color};">${pnl:,.2f}</span>
                </div>
                """,
            unsafe_allow_html=True,
        )
        if st.button(f"Close #{p_id}", key=f"tv_close_{p_id}"):
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
          "<p style='color:#848e9c; font-size:11px; text-align:center;'>No open positions.</p>",
          unsafe_allow_html=True,
      )

    st.markdown("</div>", unsafe_allow_html=True)


# ----------------------------------------------------
# TAB 2: RISK & DISCIPLINE
# ----------------------------------------------------
with main_tab2:
  st.markdown("### 🛡️ Risk Management Guidelines")
  st.checkbox("Never risk more than 1-2% of total capital per trade.")
  st.checkbox("Always set strict Stop-Loss prior to executing paper orders.")


# ----------------------------------------------------
# TAB 3: MARKET ANALYTICS
# ----------------------------------------------------
with main_tab3:
  st.markdown("### 📊 Market Analytics Overview")
  st.dataframe(
      pd.DataFrame({
          "Asset": ["BTCUSDT", "ETHUSDT", "SOLUSDT", "GOLD", "AAPL"],
          "24h Change (%)": [1.23, -0.45, 2.45, 0.72, 1.35],
      }),
      use_container_width=True,
  )


# ----------------------------------------------------
# TAB 4: SETTINGS
# ----------------------------------------------------
with main_tab4:
  st.markdown("### ⚙️ Terminal Settings")
  st.markdown(f"Email: **{st.session_state.current_user_email}**")
  st.markdown(f"Tier: **{st.session_state.get('user_tier', 'Standard')}**")

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown(
    """
    <div style="text-align: center; border-top: 1px solid #23272e; padding-top: 15px;">
        <span style="color: #848e9c; font-size: 11px;">© 2026 Veer Pro Terminal. All Rights Reserved.</span>
    </div>
    """,
    unsafe_allow_html=True,
)
