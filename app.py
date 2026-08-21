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
            
