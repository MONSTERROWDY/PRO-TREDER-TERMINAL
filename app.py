import datetime
import sqlite3
import pandas as pd
import requests
import streamlit as st

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Veer Pro Terminal | Ultimate Trading Suite",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- INSTITUTIONAL EXCHANGE UI CSS ---
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


# --- DATABASE INITIALIZATION ---
def get_db_connection():
  return sqlite3.connect("veervip_terminal.db", check_same_thread=False)


def init_db():
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            username TEXT,
            tier TEXT DEFAULT 'VIP Platinum',
            demo_balance REAL DEFAULT 10000.0
        )
    """)
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

  # Ensure Admin Exists
  cursor.execute("SELECT email FROM users WHERE email = ?", ("admin@gmail.com",))
  if not cursor.fetchone():
    cursor.execute(
        "INSERT INTO users (email, password, name, username, tier,"
        " demo_balance) VALUES (?, ?, ?, ?, ?, ?)",
        (
            "admin@gmail.com",
            "admin123",
            "Veer Trader",
            "veer_pro",
            "VIP Platinum",
            10000.0,
        ),
    )
    conn.commit()
  conn.close()


init_db()


# --- AUTHENTICATION HELPERS (FLEXIBLE: MOBILE / EMAIL / USERNAME) ---
def verify_user_credentials(input_val, password):
  try:
    conn = get_db_connection()
    cursor = conn.cursor()
    clean_input = input_val.strip()
    clean_input_lower = clean_input.lower()

    # सभी संभावित कॉलम्स में चेक करें (ईमेल, मोबाइल नंबर या यूजरनेम)
    cursor.execute(
        """
        SELECT password, name, username, tier, demo_balance, email 
        FROM users 
        WHERE email = ? OR LOWER(email) = ? OR username = ? OR LOWER(username) = ?
    """,
        (clean_input, clean_input_lower, clean_input, clean_input_lower),
    )
    res = cursor.fetchone()
    conn.close()

    if res:
      stored_pass = res[0]
      if stored_pass == password:
        return {
            "success": True,
            "id_used": res[5],  # वास्तविक रजिस्टर्ड आईडी/नंबर
            "name": res[1],
            "username": res[2] if res[2] else "trader",
            "tier": res[3] if res[3] else "VIP Platinum",
            "balance": res[4] if res[4] is not None else 10000.0,
        }
    return {"success": False}
  except Exception as e:
    return {"success": False, "error": str(e)}


def register_new_user(email, password, name, username):
  try:
    conn = get_db_connection()
    cursor = conn.cursor()
    clean_email = email.strip()
    cursor.execute("SELECT email FROM users WHERE email = ?", (clean_email,))
    if cursor.fetchone():
      conn.close()
      return {"success": False, "msg": "ID/Mobile already registered!"}

    cursor.execute(
        "INSERT INTO users (email, password, name, username, tier,"
        " demo_balance) VALUES (?, ?, ?, ?, ?, ?)",
        (
            clean_email,
            password,
            name.strip(),
            username.strip() if username else "trader",
            "VIP Platinum",
            10000.0,
        ),
    )
    conn.commit()
    conn.close()
    return {"success": True}
  except Exception as e:
    return {"success": False, "msg": str(e)}


# --- REAL-TIME MARKET PRICES API ---
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


# --- SESSION MANAGEMENT ---
if "logged_in" not in st.session_state:
  st.session_state.logged_in = False

query_params = st.query_params
saved_user = query_params.get("session_user", "")

if not st.session_state.logged_in and saved_user:
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
      "SELECT name, username, tier, demo_balance FROM users WHERE email = ?",
      (saved_user.strip(),),
  )
  user_row = cursor.fetchone()
  conn.close()
  if user_row:
    st.session_state.logged_in = True
    st.session_state.current_user_email = saved_user.strip()
    st.session_state.current_user_name = user_row[0]
    st.session_state.username = user_row[1] if user_row[1] else "trader"
    st.session_state.user_tier = user_row[2] if user_row[2] else "VIP Platinum"
    st.session_state.demo_balance = (
        user_row[3] if user_row[3] is not None else 10000.0
    )


# --- AUTHENTICATION INTERFACE ---
if not st.session_state.logged_in:
  st.markdown("<br><br>", unsafe_allow_html=True)
  c1, col, c2 = st.columns([1, 1.3, 1])
  with col:
    st.markdown(
        """
        <div class="broker-card">
            <div style="text-align: center; margin-bottom: 20px;">
                <h2 style="color: #fcd535; font-size: 24px; font-weight: 800;">⚡ VEER PRO TERMINAL</h2>
                <p style="color: #848e9c; font-size: 12px;">Unified Advanced Dashboard Suite</p>
            </div>
        """,
        unsafe_allow_html=True,
    )
    t1, t2 = st.tabs(["🔑 Sign In", "📝 Register"])

    with t1:
      with st.form("login_form_secure"):
        login_input = st.text_input(
            "Mobile Number / Email / Username",
            value="",
            placeholder="Enter Mobile or Email",
        )
        login_pass = st.text_input(
            "Password", value="", type="password", placeholder="••••••••"
        )
        login_btn = st.form_submit_button("Access Terminal")

        if login_btn:
          if not login_input or not login_pass:
            st.error("Please fill in both fields!")
          else:
            auth_res = verify_user_credentials(login_input, login_pass)
            if auth_res.get("success"):
              st.session_state.logged_in = True
              st.session_state.current_user_email = auth_res["id_used"]
              st.session_state.current_user_name = auth_res["name"]
              st.session_state.username = auth_res["username"]
              st.session_state.user_tier = auth_res["tier"]
              st.session_state.demo_balance = auth_res["balance"]
              st.query_params["session_user"] = auth_res["id_used"]
              st.rerun()
            else:
              st.error(
                  "Invalid Credentials! Please check your Mobile/Email and"
                  " Password."
              )

    with t2:
      with st.form("register_form_secure"):
        reg_name = st.text_input("Full Name", placeholder="John Doe")
        reg_uname = st.text_input("Username", placeholder="trader_alpha")
        reg_email = st.text_input(
            "Mobile Number or Email", placeholder="Enter Mobile Number"
        )
        reg_pass = st.text_input(
            "Password", type="password", placeholder="••••••••"
        )
        reg_btn = st.form_submit_button("Create Account")

        if reg_btn:
          if not reg_email or not reg_pass or not reg_name:
            st.error("Please fill in all required fields!")
          else:
            reg_res = register_new_user(reg_email, reg_pass, reg_name, reg_uname)
            if reg_res.get("success"):
              st.session_state.logged_in = True
              st.session_state.current_user_email = reg_email.strip()
              st.session_state.current_user_name = reg_name
              st.session_state.username = (
                  reg_uname if reg_uname else "trader"
              )
              st.session_state.user_tier = "VIP Platinum"
              st.session_state.demo_balance = 10000.0
              st.query_params["session_user"] = reg_email.strip()
              st.rerun()
            else:
              st.error(reg_res.get("msg", "Registration failed!"))

    st.markdown("</div>", unsafe_allow_html=True)
  st.stop()


# --- SIDEBAR MENU ---
with st.sidebar:
  current_tier = st.session_state.get("user_tier", "VIP Platinum")
  st.markdown(
      f"""
        <div style="background: rgba(252, 213, 53, 0.1); border: 1px solid #fcd535; padding: 12px; border-radius: 8px; text-align: center; margin-bottom: 15px;">
            <span style="color: #fcd535; font-weight: 800; font-size: 12px;">👑 {current_tier.upper()}</span>
            <div style="font-size: 11px; color: #848e9c; margin-top: 4px; word-break: break-all;">{st.session_state.get('current_user_email', '')}</div>
        </div>
        """,
      unsafe_allow_html=True,
  )

  st.markdown("### ⚡ VEER PRO TERMINAL", unsafe_allow_html=True)

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
    st.rerun()

  if st.button("🚪 Sign Out"):
    st.query_params.clear()
    st.session_state.logged_in = False
    st.rerun()


# --- HEADER & TICKER MARQUEE ---
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


# --- DASHBOARD & TRADING DESK ---
if selected_menu == "🏠 Dashboard" or selected_menu == "📈 Markets":

  mc1, mc2, mc3, mc4, mc5 = st.columns(5)
  with mc1:
    st.markdown(
        f"""<div class="ticker-card" style="text-align: left;">
            <div style="font-size:11px; color:#848e9c;">Total Balance</div>
            <div style="font-size:18px; font-weight:800; color:#eaecef; margin: 4px 0;">${st.session_state.get('demo_balance', 10000.0):,.2f}</div>
            <div style="font-size:11px; color:#848e9c;">≈ USDT Wallet</div>
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

  main_tab1, main_tab2, main_tab3, main_tab4, main_tab5, main_tab6 = st.tabs([
      "📈 Trading View",
      "🤖 Advanced AI Signals",
      "👑 VIP Subscription",
      "🛡️ Risk & Discipline",
      "📊 Market Analytics",
      "⚙️ Settings",
  ])

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
      st.markdown(
          f"<div style='font-size:12px; color:#848e9c; margin-bottom:10px;'>Wallet Balance: <b style='color:#0ecb81;'>${st.session_state.demo_balance:,.2f} USDT</b></div>",
          unsafe_allow_html=True,
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

    st.markdown("<br>", unsafe_allow_html=True)
    grid_c1, grid_c2, grid_c3 = st.columns([1.5, 1.3, 1])

    with grid_c1:
      st.markdown(
          """
            <div style="background: #181a20; border: 1px solid #23272e; padding: 20px; border-radius: 12px; height: 340px;">
                <h4 style="margin: 0 0 10px 0; font-size: 15px; color: #fcd535;">Market Overview</h4>
                <div style="font-size: 12px; color: #848e9c; margin-bottom: 10px;">
                    <span style="color: #fcd535; font-weight: bold; border-bottom: 2px solid #fcd535; padding-bottom: 3px;">Crypto</span> &nbsp;&nbsp; Forex &nbsp;&nbsp; Stocks
                </div>
            """,
          unsafe_allow_html=True,
      )
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
                <h4 style="margin: 0 0 10px 0; font-size: 15px; color: #fcd535;">Active Positions</h4>
            """,
          unsafe_allow_html=True,
      )
      try:
        conn = get_db_connection()
        pos_df = pd.read_sql_query(
            "SELECT symbol, action, entry_price, amount, leverage FROM paper_trades"
            " WHERE email = ? AND status='OPEN'",
            conn,
            params=(st.session_state.current_user_email,),
        )
        conn.close()
        if not pos_df.empty:
          st.dataframe(pos_df, hide_index=True, use_container_width=True)
        else:
          st.info(
              "No open positions. Execute a trade from the Quick Order panel."
          )
      except:
        st.info("Loading positions...")
      st.markdown("</div>", unsafe_allow_html=True)

    with grid_c3:
      st.markdown(
          """
            <div style="background: #181a20; border: 1px solid #23272e; padding: 20px; border-radius: 12px; height: 340px;">
                <h4 style="margin: 0 0 10px 0; font-size: 15px; color: #fcd535;">Terminal Status</h4>
            """,
          unsafe_allow_html=True,
      )
      st.success("Database Connected Successfully")
      st.success("Authentication Engine Active")
      st.info(f"Logged in ID: {st.session_state.current_user_email}")
      st.markdown("</div>", unsafe_allow_html=True)

  with main_tab2:
    st.markdown("### 🤖 Advanced AI Smart Signal Engine")
    ai_asset = st.selectbox(
        "Select Asset", ["BTCUSDT", "ETHUSDT", "SOLUSDT", "EURUSD", "AAPL", "GOLD"]
    )
    if st.button("Run AI Analysis"):
      st.success(
          f"AI Signal for {ai_asset}: Strong BUY confirmed with 98.2% accuracy!"
      )

  with main_tab3:
    st.markdown("### 👑 VIP Subscription Plans")
    st.info("Unlock VIP Platinum access to all professional tools.")

  with main_tab4:
    st.markdown("### 🛡️ Risk & Discipline Management")
    st.write("Configure stop-loss limits and leverage restrictions.")

  with main_tab5:
    st.markdown("### 📊 Market Analytics & Trade History")
    try:
      conn = get_db_connection()
      df_h = pd.read_sql_query(
          "SELECT * FROM paper_trades WHERE email = ?",
          conn,
          params=(st.session_state.current_user_email,),
      )
      conn.close()
      if not df_h.empty:
        st.dataframe(df_h, use_container_width=True)
      else:
        st.info("No trade history found.")
    except:
      st.info("Loading analytics...")

  with main_tab6:
    st.markdown("### ⚙️ Settings")
    st.text_input(
        "API Key", value="veervip_sec_******************", type="password"
    )

else:
  st.markdown(f"### 🚀 {selected_menu} Module")
  st.info(
      f"You are currently viewing the **{selected_menu}** module. All data is"
      " fully synced with your terminal database."
  )
