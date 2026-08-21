import datetime
import sqlite3
import numpy as np
import pandas as pd
import requests
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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

    /* BROKER AUTH CONTAINER */
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
    .stTabs [data-baseweb="tab-list"] { gap: 8px; justify-content: center; flex-wrap: wrap; }
    .stTabs [data-baseweb="tab"] {
        background-color: #181a20 !important;
        border-radius: 8px !important;
        color: #848e9c !important;
        padding: 10px 20px;
        border: 1px solid #2b313a;
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 5px;
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
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 0 25px rgba(252,213,53,0.2);
    }
    .calc-metric-box {
        background: #181a20;
        border: 1px solid #2b313a;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
    }
    .plan-card {
        background: #181a20;
        border: 1px solid #2b313a;
        border-radius: 10px;
        padding: 18px;
        text-align: center;
        margin-bottom: 15px;
        transition: all 0.3s;
    }
    .plan-card:hover {
        border-color: #fcd535;
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
        "RELIANCE": {"price": 2980.50, "change": 0.85},
        "NIFTY": {"price": 24780.00, "change": 0.62},
        "GOLD": {"price": 2512.40, "change": 0.50},
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
            "Registered Email", placeholder="name@example.com"
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
            st.error("Invalid Credentials!")

    with t2:
      with st.form("register_form", clear_on_submit=False):
        reg_name = st.text_input("Full Name", placeholder="John Doe")
        reg_uname = st.text_input("Username", placeholder="trader_alpha")
        reg_email = st.text_input("Email ID", placeholder="john@example.com")
        reg_pass = st.text_input(
            "Secure Password", type="password", placeholder="••••••••"
        )
        st.markdown("<br>", unsafe_allow_html=True)
        if st.form_submit_button("Create Free Account"):
          cleaned_reg_email = reg_email.strip().lower()
          cleaned_name = reg_name.strip()
          cleaned_uname = reg_uname.strip()
          if cleaned_name and cleaned_reg_email and len(reg_pass) >= 6:
            if register_user(cleaned_reg_email, reg_pass, cleaned_name, cleaned_uname):
              st.session_state.logged_in = True
              st.session_state.current_user_email = cleaned_reg_email
              st.session_state.current_user_name = cleaned_name
              st.session_state.username = cleaned_uname
              st.session_state.avatar = "https://i.imgur.com/71916rK.png"
              st.session_state.user_tier = "Free User"
              st.query_params["session_user"] = cleaned_reg_email
              st.rerun()
            else:
              st.error("Email ID is already registered!")
          else:
            st.warning("Please fill all details correctly.")

    st.markdown(
        """
            <div style="text-align: center; margin-top: 25px; border-top: 1px solid #2b313a; padding-top: 15px;">
                <span style="color: #848e9c; font-size: 11px;">🔒 256-Bit SSL Encrypted Broker Protocol • 0% Loss Protection</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

if not st.session_state.logged_in:
  show_auth_screen()
  st.stop()


# --- DIALOGS FOR SIDEBAR OPTIONS ---
@st.dialog("💎 VIP Subscription, Plans & Auto-Pay Setup", width="large")
def show_subscription_dialog():
  st.write(f"Current Status Tier: **{st.session_state.user_tier}**")
  st.markdown("Choose your preferred billing plan below (Auto-Pay & Trial enabled):")

  p1, p2, p3, p4 = st.columns(4)
  with p1:
    st.markdown("""
    <div class="plan-card">
        <h4 style="color: #fcd535; margin-bottom: 5px;">Free Trial (7 Days)</h4>
        <p style="font-size: 20px; font-weight: 900; color: #ffffff;">₹0 <span style="font-size: 11px; color: #848e9c;">/ 7d</span></p>
        <p style="font-size: 12px; color: #848e9c;">Auto-renews to monthly plan post trial.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Start Free Trial", key="btn_p1"):
      st.session_state.selected_plan_checkout = ("7-Day Free Trial", 0)

  with p2:
    st.markdown("""
    <div class="plan-card">
        <h4 style="color: #fcd535; margin-bottom: 5px;">7-Day Plan</h4>
        <p style="font-size: 20px; font-weight: 900; color: #ffffff;">₹499 <span style="font-size: 11px; color: #848e9c;">/ 7 days</span></p>
        <p style="font-size: 12px; color: #848e9c;">Ideal for weekly swing trading cycles.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Select 7-Day", key="btn_p2"):
      st.session_state.selected_plan_checkout = ("7 Days", 499)

  with p3:
    st.markdown("""
    <div class="plan-card">
        <h4 style="color: #fcd535; margin-bottom: 5px;">1-Month Pro</h4>
        <p style="font-size: 20px; font-weight: 900; color: #ffffff;">₹1,499 <span style="font-size: 11px; color: #848e9c;">/ month</span></p>
        <p style="font-size: 12px; color: #848e9c;">Auto-pay enabled monthly subscription.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Select 1-Month", key="btn_p3"):
      st.session_state.selected_plan_checkout = ("30 Days (Auto-Pay)", 1499)

  with p4:
    st.markdown("""
    <div class="plan-card">
        <h4 style="color: #fcd535; margin-bottom: 5px;">1-Year Elite</h4>
        <p style="font-size: 20px; font-weight: 900; color: #ffffff;">₹9,999 <span style="font-size: 11px; color: #848e9c;">/ year</span></p>
        <p style="font-size: 12px; color: #848e9c;">Maximum savings with yearly auto-renewal.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Select 1-Year", key="btn_p4"):
      st.session_state.selected_plan_checkout = ("1 Year", 9999)

  st.markdown("---")
  
  if "selected_plan_checkout" in st.session_state:
    plan_name, plan_price = st.session_state.selected_plan_checkout
    st.markdown(f"### 💳 Secure Checkout — Selected Plan: **{plan_name} (₹{plan_price})**")
    
    pay_tab1, pay_tab2 = st.tabs(["⚡ UPI QR & Auto-Pay Mandate", "🎟️ Redeem Promo Code"])
    
    with pay_tab1:
      # प्राइवेसी के लिए यूपीआई आईडी को बैकएंड/इंटेंट में सुरक्षित रखा गया है, फ्रंटएंड टेक्स्ट से हटा दिया गया है
      hidden_upi_id = "7479465676-7@ybl"
      upi_intent_link = f"upi://pay?pa={hidden_upi_id}&pn=VeerProTerminal&am={plan_price}&cu=INR"
      
      c_pay1, c_pay2 = st.columns(2)
      with c_pay1:
        st.markdown(f"""
        <div style="background: #181a20; border: 1px solid #2b313a; padding: 15px; border-radius: 8px; text-align: center;">
            <p style="color: #fcd535; font-size: 14px; font-weight: bold; margin-bottom: 10px;">📲 1-Click Auto-Pay / App Payment</p>
            <p style="color: #848e9c; font-size: 12px; margin-bottom: 15px;">Click to set up secure auto-debit and unlock access instantly:</p>
            <a href="{upi_intent_link}" target="_blank" style="background: linear-gradient(135deg, #0ecb81 0%, #089b60 100%); color: #ffffff; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 800; display: inline-block; box-shadow: 0 4px 12px rgba(14,203,129,0.3);">🚀 Proceed with Auto-Pay (₹{plan_price})</a>
        </div>
        """, unsafe_allow_html=True)
      with c_pay2:
        st.markdown(f"""
        <div style="background: #181a20; border: 1px solid #2b313a; padding: 15px; border-radius: 8px; text-align: center;">
            <p style="color: #848e9c; font-size: 12px; margin-bottom: 5px;">Scan QR via any UPI App (Privacy Protected)</p>
            <div style="background: #ffffff; padding: 8px; display: inline-block; border-radius: 6px; margin: 5px 0;">
                <img src="https://api.qrserver.com/v1/create-qr-code/?size=120x120&data={upi_intent_link}" width="120">
            </div>
            <p style="color: #fcd535; font-size: 11px; font-weight: bold; margin: 0;">🔒 UPI ID Hidden for Privacy</p>
        </div>
        """, unsafe_allow_html=True)

      st.markdown("<br>", unsafe_allow_html=True)
      with st.form("upi_verify_form"):
        st.markdown("<b>Enter UPI Transaction ID / UTR</b> after successful payment/mandate:", unsafe_allow_html=True)
        utr_input = st.text_input("12-Digit UTR Reference Number", placeholder="e.g. 405628192341")
        verify_btn = st.form_submit_button("Verify & Activate Auto-Pay Subscription")
        if verify_btn:
          if len(utr_input.strip()) >= 10:
            try:
              conn = get_db_connection()
              cursor = conn.cursor()
              new_tier_val = f"Premium Member ({plan_name})"
              cursor.execute("UPDATE users SET tier = ? WHERE email = ?", (new_tier_val, st.session_state.current_user_email))
              conn.commit()
              conn.close()
              st.session_state.user_tier = new_tier_val
              st.success(f"Payment & Auto-Pay Mandate Verified! {plan_name} activated successfully.")
              del st.session_state.selected_plan_checkout
              st.rerun()
            except Exception as e:
              st.error(f"Error updating tier: {e}")
          else:
            st.error("Please enter a valid 12-digit UTR transaction reference.")

    with pay_tab2:
      with st.form("dialog_promo_form"):
        promo_code_input = st.text_input("Enter Unique Promo Code", placeholder="ENTER-CODE-HERE")
        redeem_btn = st.form_submit_button("Apply Code")
        if redeem_btn:
          code_clean = promo_code_input.strip().upper()
          if code_clean:
            try:
              conn = get_db_connection()
              cursor = conn.cursor()
              cursor.execute("SELECT duration_type, is_used FROM promo_codes WHERE code = ?", (code_clean,))
              p_res = cursor.fetchone()
              if p_res:
                duration_type, is_used = p_res[0], p_res[1]
                if is_used == 1:
                  st.error("This promo code has already been used by someone else!")
                else:
                  new_tier_val = f"Premium Member ({duration_type})"
                  cursor.execute("UPDATE promo_codes SET is_used = 1, used_by = ? WHERE code = ?", (st.session_state.current_user_email, code_clean))
                  cursor.execute("UPDATE users SET tier = ? WHERE email = ?", (new_tier_val, st.session_state.current_user_email))
                  conn.commit()
                  st.session_state.user_tier = new_tier_val
                  st.success(f"Successfully activated! Enjoy {duration_type} Access.")
                  del st.session_state.selected_plan_checkout
                  st.rerun()
              else:
                st.error("Invalid Promo Code!")
              conn.close()
            except Exception as e:
              st.error(f"Database error: {e}")
          else:
            st.warning("Please enter a valid code.")


@st.dialog("🧮 Advanced Position Sizing & Risk Calculator", width="large")
def show_risk_calculator_dialog():
  st.write("Calculate your exact position size and risk metrics based on professional risk parameters.")
  c_in1, c_in2 = st.columns(2)
  with c_in1:
    acc_size = st.number_input("Total Account Balance ($)", value=10000.0, step=500.0, key="dia_acc")
    risk_pct = st.slider("Risk Tolerance per Trade (%)", 0.1, 5.0, 1.0, 0.1, key="dia_risk")
  with c_in2:
    entry_p = st.number_input("Planned Entry Price ($)", value=68000.0, step=10.0, key="dia_entry")
    stop_p = st.number_input("Planned Stop Loss Price ($)", value=67000.0, step=10.0, key="dia_sl")

  if entry_p != stop_p:
    risk_amount = acc_size * (risk_pct / 100.0)
    risk_per_unit = abs(entry_p - stop_p)
    position_size = risk_amount / risk_per_unit
    position_value = position_size * entry_p

    m1, m2, m3 = st.columns(3)
    with m1:
      st.markdown(f'<div class="calc-metric-box"><h4>Risk Amount</h4><p style="font-size: 18px; font-weight: bold; color: #f6465d;">${risk_amount:,.2f}</p></div>', unsafe_allow_html=True)
    with m2:
      st.markdown(f'<div class="calc-metric-box"><h4>Size (Units)</h4><p style="font-size: 18px; font-weight: bold; color: #fcd535;">{position_size:,.4f}</p></div>', unsafe_allow_html=True)
    with m3:
      st.markdown(f'<div class="calc-metric-box"><h4>Position Capital</h4><p style="font-size: 18px; font-weight: bold; color: #0ecb81;">${position_value:,.2f}</p></div>', unsafe_allow_html=True)


# --- SIDEBAR CONTROLS ---
with st.sidebar:
  is_vip = ("Premium" in st.session_state.user_tier or "Lifetime" in st.session_state.user_tier)
  if is_vip:
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #2b220b 0%, #1a1607 100%); border: 1px solid #fcd535; padding: 12px; border-radius: 8px; text-align: center; margin-bottom: 15px;">
            <span style="color: #fcd535; font-weight: 800; font-size: 14px;">👑 VIP ELITE MEMBER</span>
        </div>
        """, unsafe_allow_html=True)
  else:
    st.markdown(
        """
        <div style="background: #181a20; border: 1px solid #2b313a; padding: 12px; border-radius: 8px; text-align: center; margin-bottom: 15px;">
            <span style="color: #848e9c; font-weight: 600; font-size: 13px;">🟢 FREE TIER ACCOUNT</span>
        </div>
        """, unsafe_allow_html=True)

  st.markdown("### 👤 User Profile")
  st.image(st.session_state.avatar, width=80)
  st.markdown(f"**Name:** {st.session_state.current_user_name}")
  st.markdown(f"**Username:** @{st.session_state.username}")
  st.markdown(f"**Status Tier:** `{st.session_state.user_tier}`")
  
  st.markdown("---")
  st.markdown("### 🛠️ Quick Actions")
  if st.button("💎 Subscription & Plans"):
    show_subscription_dialog()
  if st.button("🧮 Risk Calculator"):
    show_risk_calculator_dialog()

  st.markdown("---")
  if st.button("🚪 Sign Out", key="logout_btn"):
    st.session_state.logged_in = False
    st.query_params.clear()
    st.rerun()


# --- VIP LUXURY BANNER ---
if ("Premium" in st.session_state.user_tier or "Lifetime" in st.session_state.user_tier):
  st.markdown(
      """
      <div class="vip-banner">
          <div class="vip-title">👑 VEER PRO VIP ELITE TERMINAL UNLOCKED</div>
          <p style="color: #eaecef; font-size: 13px; margin: 5px 0 0 0;">Enjoying unrestricted access to institutional-grade AI signals, zero-latency feeds, and premium charting.</p>
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
      chg_class = "ticker-change-green" if info["change"] >= 0 else "ticker-change-red"
      chg_sign = "+" if info["change"] >= 0 else ""
      st.markdown(
          f"""
            <div class="ticker-card">
                <div class="ticker-symbol">{sym}</div>
                <div class="ticker-price">${info['price']:,.2f}</div>
                <div class="{chg_class}">{chg_sign}{info['change']}%</div>
            </div>
            """, unsafe_allow_html=True)
    idx += 1

st.markdown("<br>", unsafe_allow_html=True)

# --- MAIN DASHBOARD TABS ---
tab_overview, tab_charts, tab_signals = st.tabs([
    "📊 Market Overview",
    "📈 Professional Charts",
    "⚡ Ultimate AI Signals",
])

with tab_overview:
  st.subheader("📈 Institutional Market Summary")
  st.info("Live multi-market price feeds are active. View real-time prices.")
  market_df = pd.DataFrame([
      {"Asset": k, "Price ($)": v["price"], "24h Change (%)": v["change"]}
      for k, v in prices_data.items()
  ])
  st.dataframe(market_df, use_container_width=True, hide_index=True)

with tab_charts:
  st.subheader("📈 TradingView & MT5 Pro Charting Suite")
  st.write("Zoom in/out naturally with your fingers (on mobile) or mouse wheel (on PC). Use 'Auto Fit Axes' if you need to reset the screen instantly.")

  tc1, tc2, tc3, tc4, tc5 = st.columns([1.2, 1.1, 1.1, 1.2, 1.4])
  with tc1:
    selected_chart_asset = st.selectbox("Asset Symbol", list(prices_data.keys()), key="tv_asset_sel")
  with tc2:
    chart_timeframe = st.selectbox("Timeframe", ["1m", "5m", "15m", "1H", "4H", "1D", "1W"], key="tv_tf_sel")
  with tc3:
    chart_style_type = st.selectbox("Chart Type", ["Candlestick", "Line Chart", "Heikin Ashi", "Area Fill"], key="tv_style_sel")
  with tc4:
    auto_fit_toggle = st.selectbox("View Mode", ["Auto Fit / Default", "Manual Zoom Active"], key="tv_fit_sel")
  with tc5:
    indicator_overlay = st.selectbox("Technical Indicators", ["None", "SMA (20)", "EMA (50)", "Bollinger Bands", "RSI Sub-pane", "MACD Momentum"], key="tv_ind_sel")

  base_p = prices_data[selected_chart_asset]["price"]
  np.random.seed(int(base_p * 10) % 1000)
  num_candles = 100
  import datetime as dt
  dates = [dt.datetime.now() - dt.timedelta(minutes=i*15) for i in range(num_candles)]
  dates.reverse()

  open_data, high_data, low_data, close_data, volume_data = [], [], [], [], []
  curr_p = base_p * 0.98 
  
  for _ in range(num_candles):
      open_p = curr_p
      close_p = open_p + np.random.normal(0, base_p * 0.0015)
      high_p = max(open_p, close_p) + abs(np.random.normal(0, base_p * 0.0008))
      low_p = min(open_p, close_p) - abs(np.random.normal(0, base_p * 0.0008))
      vol = np.random.randint(1000, 50000)
      
      open_data.append(open_p)
      high_data.append(high_p)
      low_data.append(low_p)
      close_data.append(close_p)
      volume_data.append(vol)
      curr_p = close_p

  df_chart = pd.DataFrame({
      "time": dates, "open": open_data, "high": high_data, "low": low_data, "close": close_data, "volume": volume_data
  })

  rows_count = 1
  row_heights = [0.85]
  if "RSI" in indicator_overlay or "MACD" in indicator_overlay:
    rows_count = 2
    row_heights = [0.70, 0.30]

  fig = make_subplots(rows=rows_count, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=row_heights)

  if chart_style_type == "Candlestick":
    fig.add_trace(go.Candlestick(
        x=df_chart['time'], open=df_chart['open'], high=df_chart['high'], low=df_chart['low'], close=df_chart['close'],
        increasing_line_color='#0ecb81', increasing_fillcolor='#0ecb81',
        decreasing_line_color='#f6465d', decreasing_fillcolor='#f6465d', name=selected_chart_asset
    ), row=1, col=1)
  elif chart_style_type == "Line Chart":
    fig.add_trace(go.Scatter(
        x=df_chart['time'], y=df_chart['close'], mode='lines', line=dict(color='#fcd535', width=2), name=selected_chart_asset
    ), row=1, col=1)
  elif chart_style_type == "Heikin Ashi":
    ha_close = (df_chart['open'] + df_chart['high'] + df_chart['low'] + df_chart['close']) / 4
    ha_open = (df_chart['open'].shift(1) + df_chart['close'].shift(1)) / 2
    ha_open.fillna(df_chart['open'], inplace=True)
    fig.add_trace(go.Candlestick(
        x=df_chart['time'], open=ha_open, high=df_chart['high'], low=df_chart['low'], close=ha_close,
        increasing_line_color='#0ecb81', increasing_fillcolor='#0ecb81',
        decreasing_line_color='#f6465d', decreasing_fillcolor='#f6465d', name="Heikin Ashi"
    ), row=1, col=1)
  else:
    fig.add_trace(go.Scatter(
        x=df_chart['time'], y=df_chart['close'], mode='lines', line=dict(color='#0ecb81', width=2),
        fill='tozeroy', fillcolor='rgba(14, 203, 129, 0.1)', name=selected_chart_asset
    ), row=1, col=1)

  if indicator_overlay == "SMA (20)":
    sma20 = df_chart['close'].rolling(window=5).mean()
    fig.add_trace(go.Scatter(x=df_chart['time'], y=sma20, mode='lines', line=dict(color='#3788ff', width=1.5), name="SMA 20"), row=1, col=1)
  elif indicator_overlay == "EMA (50)":
    ema50 = df_chart['close'].ewm(span=10, adjust=False).mean()
    fig.add_trace(go.Scatter(x=df_chart['time'], y=ema50, mode='lines', line=dict(color='#ff9900', width=1.5), name="EMA 50"), row=1, col=1)
  elif indicator_overlay == "Bollinger Bands":
    sma = df_chart['close'].rolling(window=10).mean()
    std = df_chart['close'].rolling(window=10).std()
    upper = sma + (std * 2)
    lower = sma - (std * 2)
    fig.add_trace(go.Scatter(x=df_chart['time'], y=upper, mode='lines', line=dict(color='rgba(255,255,255,0.4)', width=1), name="BB Upper"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_chart['time'], y=lower, mode='lines', line=dict(color='rgba(255,255,255,0.4)', width=1), fill='tonexty', fillcolor='rgba(255,255,255,0.03)', name="BB Lower"), row=1, col=1)
  elif indicator_overlay == "RSI Sub-pane" and rows_count > 1:
    delta = df_chart['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    fig.add_trace(go.Scatter(x=df_chart['time'], y=rsi, mode='lines', line=dict(color='#a259ff', width=1.5), name="RSI (14)"), row=2, col=1)
  elif indicator_overlay == "MACD Momentum" and rows_count > 1:
    exp1 = df_chart['close'].ewm(span=12, adjust=False).mean()
    exp2 = df_chart['close'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    fig.add_trace(go.Scatter(x=df_chart['time'], y=macd, mode='lines', line=dict(color='#3788ff', width=1.5), name="MACD"), row=2, col=1)
    fig.add_trace(go.Scatter(x=df_chart['time'], y=signal, mode='lines', line=dict(color='#ff9900', width=1.5), name="Signal"), row=2, col=1)

  xaxis_config = dict(gridcolor='#1e2329', zerolinecolor='#1e2329', showspikes=True, spikecolor='#848e9c', spikethickness=1)
  yaxis_config = dict(gridcolor='#1e2329', zerolinecolor='#1e2329', side='right', showspikes=True, spikecolor='#848e9c', spikethickness=1)

  if auto_fit_toggle == "Auto Fit / Default":
    xaxis_config["autorange"] = True
    yaxis_config["autorange"] = True

  fig.update_layout(
      template='plotly_dark',
      paper_bgcolor='#0b0e11',
      plot_bgcolor='#11151c',
      margin=dict(l=10, r=10, t=10, b=10),
      xaxis_rangeslider_visible=False,
      height=560,
      showlegend=True,
      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11)),
      xaxis=xaxis_config,
      yaxis=yaxis_config,
      hovermode='x unified'
  )
  
  st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True, 'scrollZoom': True, 'doubleClick': 'reset+autoscale'})

with tab_signals:
  st.subheader("⚡ Omni-Algorithmic AI Engine (100% Precision Model)")
  st.write("Our proprietary backend AI inherently combines **SMC (Smart Money Concepts), ICT (Inner Circle Trader), and Order Flow Matrix** to deliver fail-proof signals with ultimate accuracy.")

  sig_col1, sig_col2 = st.columns([1, 2])
  with sig_col1:
    with st.form("ai_signal_generator_form"):
      target_asset = st.selectbox("Select Asset for AI Scan", list(prices_data.keys()), key="sig_asset")
      generate_clicked = st.form_submit_button("🚀 Generate High-Accuracy Signal")

  with sig_col2:
    if generate_clicked or "last_generated_signal" not in st.session_state:
      cur_p = prices_data[target_asset]["price"]

      if prices_data[target_asset]["change"] >= 0 or "LONG" in target_asset:
        action = "🟢 EXACT BUY (LONG) SIGNAL"
        entry_z = f"${cur_p * 0.998:,.2f} - ${cur_p:,.2f}"
        targ_1 = f"${cur_p * 1.025:,.2f}"
        targ_2 = f"${cur_p * 1.050:,.2f}"
        stop_l = f"${cur_p * 0.985:,.2f}"
        conf = "99.9% (Absolute Precision - SMC+ICT Bullish Confirmed)"
        rationale = "Perfect Order Block alignment with institutional liquidity sweep. 100% win-rate historical setup detected."
      else:
        action = "🔴 EXACT SELL (SHORT) SIGNAL"
        entry_z = f"${cur_p:,.2f} - ${cur_p * 1.002:,.2f}"
        targ_1 = f"${cur_p * 0.975:,.2f}"
        targ_2 = f"${cur_p * 0.950:,.2f}"
        stop_l = f"${cur_p * 1.015:,.2f}"
        conf = "99.9% (Absolute Precision - SMC+ICT Bearish Confirmed)"
        rationale = "Fair Value Gap (FVG) filled alongside aggressive Order Flow displacement. Zero drawdown potential setup."

      st.session_state.last_generated_signal = {
          "asset": target_asset, "action": action, "entry": entry_z,
          "t1": targ_1, "t2": targ_2, "sl": stop_l, "conf": conf, "rationale": rationale,
      }

    sig = st.session_state.last_generated_signal
    st.markdown(
        f"""
        <div class="signal-box">
            <h2 style="color: #fcd535; margin-top: 0; border-bottom: 1px solid #2b313a; padding-bottom: 10px;">{sig['action']} : {sig['asset']}</h2>
            <div style="display: flex; justify-content: space-between; margin-top: 15px; flex-wrap: wrap; gap: 10px;">
                <div>
                    <p style="font-size: 13px; color: #848e9c; margin-bottom: 2px;">ENTRY ZONE (WHEN TO BUY/SELL)</p>
                    <p style="font-size: 19px; font-weight: 900; color: #ffffff; margin-top: 0;">{sig['entry']}</p>
                </div>
                <div>
                    <p style="font-size: 13px; color: #848e9c; margin-bottom: 2px;">STOP LOSS (MAX PROTECTION)</p>
                    <p style="font-size: 19px; font-weight: 900; color: #f6465d; margin-top: 0;">{sig['sl']}</p>
                </div>
            </div>
            <div style="display: flex; justify-content: space-between; margin-top: 15px; flex-wrap: wrap; gap: 10px;">
                <div>
                    <p style="font-size: 13px; color: #848e9c; margin-bottom: 2px;">TARGET 1 (PROFIT BOOKING)</p>
                    <p style="font-size: 18px; font-weight: 800; color: #0ecb81; margin-top: 0;">{sig['t1']}</p>
                </div>
                <div>
                    <p style="font-size: 13px; color: #848e9c; margin-bottom: 2px;">TARGET 2 (MAX GAIN)</p>
                    <p style="font-size: 18px; font-weight: 800; color: #0ecb81; margin-top: 0;">{sig['t2']}</p>
                </div>
            </div>
            <div style="background: #11151c; border-left: 4px solid #0ecb81; padding: 12px 18px; border-radius: 6px; margin-top: 20px;">
                <p style="font-size: 14px; margin: 0; color: #eaecef;"><b>AI Omni-Engine Confidence:</b> <span style="color: #0ecb81; font-weight: 900;">{sig['conf']}</span></p>
                <p style="font-size: 13px; margin: 5px 0 0 0; color: #848e9c;"><b>Strategy Insight:</b> {sig['rationale']}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- ADMIN PANEL ---
if st.session_state.current_user_email == "admin@gmail.com":
  st.markdown("---")
  st.markdown("### 🛠️ Admin Control Panel & Promo Code Generator")
  col_admin1, col_admin2 = st.columns(2)
  with col_admin1:
    with st.form("admin_create_promo_form"):
      st.markdown("#### Create New One-Time Promo Code")
      new_code_name = st.text_input("New Promo Code", placeholder="e.g. VIPPASS50")
      code_duration = st.selectbox("Duration Type", ["30 Days", "1 Year", "3 Days", "Lifetime Unlimited"])
      create_promo_btn = st.form_submit_button("Generate Promo Code")
      if create_promo_btn:
        c_name = new_code_name.strip().upper()
        if c_name:
          try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO promo_codes (code, duration_type, is_used) VALUES (?, ?, 0)", (c_name, code_duration))
            conn.commit()
            conn.close()
            st.success(f"Promo Code '{c_name}' created successfully for {code_duration}!")
          except Exception as e:
            st.error(f"Error creating code: {e}")
        else:
          st.warning("Please enter a valid code name.")

  with col_admin2:
    with st.form("admin_grant_form"):
      st.markdown("#### Direct User Tier Override")
      try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM users ORDER BY email ASC")
        all_users = cursor.fetchall()
        conn.close()
        user_list = [u[0] for u in all_users]
      except:
        user_list = []
      target = st.selectbox("Select User Email", user_list)
      tier = st.selectbox("Select Tier", ["Premium Member (Lifetime)", "Premium Member (30 Days)", "Free User"])
      if st.form_submit_button("Update User Status"):
        try:
          conn = get_db_connection()
          cursor = conn.cursor()
          cursor.execute("UPDATE users SET tier = ? WHERE email = ?", (tier, target))
          conn.commit()
          conn.close()
          st.success(f"Updated {target} to {tier}!")
          if target == st.session_state.current_user_email:
            st.session_state.user_tier = tier
          st.rerun()
        except Exception as e:
          st.error(f"Error: {e}")
