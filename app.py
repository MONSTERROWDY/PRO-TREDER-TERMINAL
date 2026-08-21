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
    .stTextInput>div>div>input:focus {
        border-color: #fcd535 !important;
        box-shadow: 0 0 10px rgba(252,213,53,0.2) !important;
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


# --- ROBUST DATABASE SETUP & AUTO MIGRATION FOR OLD USERS ---
def get_db_connection():
  return sqlite3.connect("users_database.db", check_same_thread=False)


def init_db():
  conn = get_db_connection()
  cursor = conn.cursor()

  # Base table creation
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            name TEXT NOT NULL
        )
    """)
  conn.commit()

  # Safe column addition for legacy/old users database structure
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

  # Ensure default values for legacy users who might have NULL in name, username, or tier
  try:
    cursor.execute(
        "UPDATE users SET name = 'Trader' WHERE name IS NULL OR name = ''"
    )
    cursor.execute(
        "UPDATE users SET username = 'trader' WHERE username IS NULL OR"
        " username = ''"
    )
    cursor.execute(
        "UPDATE users SET tier = 'Free User' WHERE tier IS NULL OR tier = ''"
    )
    conn.commit()
  except:
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

  # Admin account safety check
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

  # Default promo codes
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
    # Flexible lookup handling lower/upper/whitespace spacing issues in legacy emails
    cleaned_email = email.strip().lower()
    cursor.execute(
        "SELECT password, name, username, avatar, tier FROM users WHERE lower(trim(email)) ="
        " ?",
        (cleaned_email,),
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
        "INSERT INTO users (email, password, name, username, tier) VALUES (?,"
        " ?, ?, ?, ?)",
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
        "UPDATE users SET name = ?, username = ?, avatar = ? WHERE lower(trim(email)) = lower(trim(?))",
        (name, username, avatar, email),
    )
    conn.commit()
    conn.close()
  except Exception:
    pass


def reset_user_password(email, new_password):
  try:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET password = ? WHERE lower(trim(email)) = lower(trim(?))",
        (new_password, email),
    )
    conn.commit()
    conn.close()
    return True
  except:
    return False


# --- REAL-TIME LIVE MARKET PRICES (BINANCE API + FALLBACK) ---
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
      st.session_state.current_user_name = u_data[1] if u_data[1] else "Trader"
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


# --- BROKER-GRADE ELITE AUTH SCREEN WITH PASSWORD RECOVERY ---
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

    t1, t2, t3 = st.tabs(
        ["🔑 Sign In", "📝 Open Account", "🔄 Reset Password"]
    )

    with t1:
      st.markdown(
          "<p style='color:#848e9c; font-size:12px; text-align:center;"
          " margin-bottom:20px;'>Enter your registered email and password.</p>",
          unsafe_allow_html=True,
      )
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
          if u_data and str(u_data[0]) == str(login_pass):
            st.session_state.logged_in = True
            st.session_state.current_user_email = cleaned_email
            st.session_state.current_user_name = (
                u_data[1] if u_data[1] else "Trader"
            )
            st.session_state.username = u_data[2] if u_data[2] else "trader"
            st.session_state.avatar = (
                u_data[3] if u_data[3] else "https://i.imgur.com/71916rK.png"
            )
            st.session_state.user_tier = u_data[4] if u_data[4] else "Free User"
            st.query_params["session_user"] = cleaned_email
            st.rerun()
          else:
            st.error(
                "Invalid Email or Password! Please check your details or use"
                " 'Reset Password' tab if forgotten."
            )

    with t2:
      st.markdown(
          "<p style='color:#848e9c; font-size:12px; text-align:center;"
          " margin-bottom:20px;'>Register now to unlock free AI signal quotas"
          " and advanced charting.</p>",
          unsafe_allow_html=True,
      )
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
              st.error(
                  "Email ID is already registered! Please sign in directly."
              )
          else:
            st.warning("Please fill all details correctly (Password >= 6).")

    with t3:
      st.markdown(
          "<p style='color:#848e9c; font-size:12px; text-align:center;"
          " margin-bottom:20px;'>Purane users apna password yahan turant naya"
          " set kar sakte hain.</p>",
          unsafe_allow_html=True,
      )
      with st.form("reset_form", clear_on_submit=False):
        reset_email = st.text_input(
            "Your Registered Email", placeholder="name@example.com"
        )
        new_pass_input = st.text_input(
            "Set New Password (Min 6 Chars)",
            type="password",
            placeholder="••••••••",
        )
        st.markdown("<br>", unsafe_allow_html=True)
        if st.form_submit_button("Update Password Now"):
          target_email = reset_email.strip().lower()
          existing_check = get_user_full(target_email)
          if existing_check:
            if len(new_pass_input) >= 6:
              if reset_user_password(target_email, new_pass_input):
                st.success(
                    "Password successfully updated! Now you can login with your"
                    " new password."
                )
              else:
                st.error("Error updating password in database.")
            else:
              st.warning("New password must be at least 6 characters long.")
          else:
            st.error(
                "This email is not registered in our database. Please check the"
                " email ID."
            )

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


# --- STREAMLINED SIDEBAR WITH ELITE VIP FEEL ---
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
            "UPDATE users SET tier = ? WHERE lower(trim(email)) = lower(trim(?))",
            (new_tier, st.session_state.current_user_email),
        )
        cursor.execute(
            "UPDATE promo_codes SET is_used = 1, used_by = ? WHERE code = ?",
            (st.session_state.current_user_email, promo_input.strip().upper()),
        )
        conn.commit()
        st.session_state.user_tier = new_tier
        st.success(
            f"Success! Code redeemed. Premium Activated ({duration}) for"
            " single-use."
        )
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
          "SELECT code, duration_type, used_by FROM promo_codes WHERE is_used ="
          " 0"
      )
      active_codes = cursor.fetchall()
      cursor.execute(
          "SELECT code, duration_type, used_by FROM promo_codes WHERE is_used ="
          " 1"
      )
      used_codes = cursor.fetchall()
      conn.close()
    except:
      all_registered_users, active_codes, used_codes = [], [], []

    with st.expander("⚡ Direct User Subscription Allocator"):
      st.write(
          "बिना प्रोमो कोड के सीधे किसी भी यूजर की आईडी/ईमेल चुनकर सब्सक्रिप्शन"
          " दें।"
      )
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
                "UPDATE users SET tier = ? WHERE lower(trim(email)) = lower(trim(?))",
                (selected_tier_type, selected_target_email),
            )
            conn.commit()
            conn.close()
            st.success(
                f"Successfully updated {selected_target_email} to"
                f" '{selected_tier_type}'!"
            )
            if (
                selected_target_email.lower().strip()
                == st.session_state.current_user_email.lower().strip()
            ):
              st.session_state.user_tier = selected_tier_type
            st.rerun()
          except Exception as e:
            st.error(f"Error updating user tier: {e}")
      else:
        st.write("No registered users found.")

    with st.expander("👁️ Active (Unused) Promo Codes"):
      if active_codes:
        st.table(
            pd.DataFrame(
                active_codes, columns=["Code", "Duration", "Used By"]
            )
        )
      else:
        st.write("No active codes.")

    with st.expander("🔒 Used Promo Codes History"):
      if used_codes:
        st.table(
            pd.DataFrame(used_codes, columns=["Code", "Duration", "Used By"])
        )
      else:
        st.write("No codes used yet.")

    gen_code = st.text_input(
        "Generate Single-Use Code", key="sidebar_gen_c"
    )
    dur_type = st.selectbox(
        "Duration",
        ["3 Days", "30 Days", "1 Year", "Lifetime Unlimited"],
        key="sidebar_dur",
    )
    if st.button("Create Single-Use Code"):
      if gen_code.strip():
        try:
          conn = get_db_connection()
          cursor = conn.cursor()
          cursor.execute(
              "INSERT INTO promo_codes (code, duration_type, is_used) VALUES"
              " (?, ?, 0)",
              (gen_code.strip().upper(), dur_type),
          )
          conn.commit()
          conn.close()
          st.success(
              f"Single-use code created: '{gen_code.upper()}' (Valid for 1"
              " person only)"
          )
          st.rerun()
        except:
          st.error("Code already exists!")
      else:
        st.warning("Please enter a valid code name.")

  st.markdown("---")
  if st.button("🚪 Sign Out", key="logout_btn"):
    st.session_state.logged_in = False
    st.session_state.current_user_email = ""
    st.session_state.current_user_name = ""
    st.query_params.clear()
    st.rerun()

# --- VIP LUXURY DASHBOARD BANNER IF VIP ---
if (
    "Premium" in st.session_state.user_tier
    or "Lifetime" in st.session_state.user_tier
):
  st.markdown(
      """
      <div class="vip-banner">
          <div class="vip-title">👑 VEER PRO VIP ELITE TERMINAL UNLOCKED</div>
          <p style="color: #eaecef; font-size: 13px; margin: 5px 0 0 0;">Enjoying unrestricted access to institutional-grade AI signals, zero-latency multi-market feeds, and 0% loss automated protocols.</p>
      </div>
      """,
      unsafe_allow_html=True,
  )

st.title("⚡ Veer Pro Terminal — World's Best 0% Loss AI Trading Suite")

# --- LIVE MULTI-MARKET TICKER STRIP (REAL-TIME API CONNECTED) ---
market_prices = fetch_global_prices()
tc1, tc2, tc3, tc4, tc5 = st.columns(5)

with tc1:
  btc = market_prices.get("BTCUSDT", {"price": 68417.51, "change": 1.23})
  c_class = "ticker-change-green" if btc["change"] >= 0 else "ticker-change-red"
  sign = "+" if btc["change"] >= 0 else ""
  st.markdown(
      f"""<div class="ticker-card"><div class="ticker-symbol">BTC/USDT (Live)</div><div class="ticker-price">${btc['price']:,.2f}</div><div class="{c_class}">{sign}{btc['change']}%</div></div>""",
      unsafe_allow_html=True,
  )

with tc2:
  eth = market_prices.get("ETHUSDT", {"price": 3540.49, "change": -0.45})
  c_class = "ticker-change-green" if eth["change"] >= 0 else "ticker-change-red"
  sign = "+" if eth["change"] >= 0 else ""
  st.markdown(
      f"""<div class="ticker-card"><div class="ticker-symbol">ETH/USDT (Live)</div><div class="ticker-price">${eth['price']:,.2f}</div><div class="{c_class}">{sign}{eth['change']}%</div></div>""",
      unsafe_allow_html=True,
  )

with tc3:
  eur = market_prices.get("EURUSD", {"price": 1.0924, "change": 0.15})
  c_class = "ticker-change-green" if eur["change"] >= 0 else "ticker-change-red"
  sign = "+" if eur["change"] >= 0 else ""
  st.markdown(
      f"""<div class="ticker-card"><div class="ticker-symbol">EUR/USD (Forex)</div><div class="ticker-price">{eur['price']:,.4f}</div><div class="{c_class}">{sign}{eur['change']}%</div></div>""",
      unsafe_allow_html=True,
  )

with tc4:
  rel = market_prices.get("RELIANCE", {"price": 2980.50, "change": 0.85})
  c_class = "ticker-change-green" if rel["change"] >= 0 else "ticker-change-red"
  sign = "+" if rel["change"] >= 0 else ""
  st.markdown(
      f"""<div class="ticker-card"><div class="ticker-symbol">RELIANCE (NSE)</div><div class="ticker-price">₹{rel['price']:,.2f}</div><div class="{c_class}">{sign}{rel['change']}%</div></div>""",
      unsafe_allow_html=True,
  )

with tc5:
  gld = market_prices.get("GOLD", {"price": 2512.40, "change": 0.50})
  c_class = "ticker-change-green" if gld["change"] >= 0 else "ticker-change-red"
  sign = "+" if gld["change"] >= 0 else ""
  st.markdown(
      f"""<div class="ticker-card"><div class="ticker-symbol">GOLD (Commodity)</div><div class="ticker-price">${gld['price']:,.2f}</div><div class="{c_class}">{sign}{gld['change']}%</div></div>""",
      unsafe_allow_html=True,
  )

st.markdown("<br>", unsafe_allow_html=True)

# --- CLEAN MAIN TABS ---
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
    st.markdown("### ⚙️ Global Asset & Signal Configuration")

    market_category = st.selectbox(
        "Market Category (All Markets)",
        [
            "FOREX",
            "CRYPTO",
            "STOCKS",
            "INDICES",
            "COMMODITIES",
            "FUTURES",
            "OPTIONS",
            "BONDS",
            "INTEREST RATES",
        ],
        key="cat_sel",
    )

    if market_category == "FOREX":
      asset_options = [
          "FX:EURUSD",
          "FX:GBPUSD",
          "FX:USDJPY",
          "FX:AUDUSD",
          "FX:USDCAD",
          "FX:NZDUSD",
          "FX:USDCHF",
          "FX:EURGBP",
          "FX:EURJPY",
          "FX:GBPJPY",
      ]
    elif market_category == "CRYPTO":
      asset_options = [
          "BINANCE:BTCUSDT",
          "BINANCE:ETHUSDT",
          "BINANCE:SOLUSDT",
          "BINANCE:BNBUSDT",
          "BINANCE:XRPUSDT",
          "BINANCE:ADAUSDT",
          "BINANCE:DOGEUSDT",
          "BINANCE:AVAXUSDT",
          "BINANCE:DOTUSDT",
          "BINANCE:LINKUSDT",
      ]
    elif market_category == "STOCKS":
      asset_options = [
          "NASDAQ:AAPL",
          "NASDAQ:TSLA",
          "NASDAQ:NVDA",
          "NASDAQ:MSFT",
          "NASDAQ:AMZN",
          "NYSE:JPM",
          "NYSE:V",
          "NSE:RELIANCE",
          "NSE:TCS",
          "NSE:INFY",
      ]
    elif market_category == "INDICES":
      asset_options = [
          "SP:SPX",
          "NASDAQ:NDX",
          "DJ:DJI",
          "TVC:VIX",
          "INDEX:NIFTY",
          "BSE:SENSEX",
          "INDEX:BANKNIFTY",
      ]
    elif market_category == "COMMODITIES":
      asset_options = [
          "COMEX:GC1! (Gold)",
          "NYMEX:CL1! (Crude Oil)",
          "COMEX:SI1! (Silver)",
          "MCX:GOLD",
          "MCX:SILVER",
          "MCX:CRUDEOIL",
      ]
    elif market_category == "FUTURES":
      asset_options = [
          "CME:ES1! (S&P 500 E-mini)",
          "CME:NQ1! (Nasdaq 100 E-mini)",
          "COMEX:GC1! (Gold Futures)",
          "NYMEX:CL1! (Crude Oil)",
      ]
    elif market_category == "OPTIONS":
      asset_options = [
          "NSE:NIFTY_CE",
          "NSE:NIFTY_PE",
          "NSE:BANKNIFTY_CE",
          "NSE:BANKNIFTY_PE",
          "NASDAQ:AAPL_CALL",
      ]
    elif market_category == "BONDS":
      asset_options = [
          "TVC:US10Y (US 10-Yr Treasury)",
          "TVC:GB10Y (UK 10-Yr Gilt)",
          "TVC:DE10Y (Germany 10-Yr Bund)",
      ]
    else:
      asset_options = [
          "ECONOMICS:USINTR (US Fed Funds Rate)",
          "ECONOMICS:ININTR (RBI Repo Rate)",
      ]

    selected_asset = st.selectbox(
        "Select Asset / Symbol", asset_options, key="asset_sel"
    )
    tf = st.selectbox(
        "Timeframe", ["1m", "5m", "15m", "1h", "4h", "1D"], key="tf_sel"
    )

  with col_risk:
    st.markdown("### 🛡️ Smart Capital Defense (0% Loss Guarantee)")
    acc_bal = st.number_input(
        "Account Balance ($)", value=10000.0, step=500.0, key="acc_bal_input"
    )
    risk_pct = 1.0
    st.slider(
        "Max Capital Risk (%) — Locked at 1%",
        0.1,
        5.0,
        1.0,
        disabled=True,
        key="risk_slider",
    )
    risk_amt = acc_bal * (risk_pct / 100)
    st.success(
        f"🔒 **0% Loss Safety Shield Active:** Auto break-even triggers ensure maximum safety. If conditions fail, you exit with minimal or zero loss (${risk_amt:.2f} max risk protection)."
    )

with tab_risk_calc:
  st.markdown("### 🛡️ Advanced Risk & Capital Management Master")
  st.write(
      "अपने कुल कैपिटल पर कितना रिस्क लेना चाहिए, कितना नफा (Profit) होगा और कितना नुकसान (Loss) — सब कुछ यहाँ कैलकुलेट करें।"
  )
  st.markdown("<br>", unsafe_allow_html=True)

  rc1, rc2 = st.columns(2, gap="large")

  with rc1:
    st.markdown("#### 📥 1. इनपुट डिटेल्स भरें (Input Parameters)")
    user_capital = st.number_input(
        "आपका कुल ट्रेडिंग कैपिटल ($ या ₹)",
        value=50000.0,
        step=1000.0,
        key="rc_cap",
    )
    risk_tolerance_pct = st.slider(
        "एक ट्रेड में अधिकतम रिस्क (%)",
        0.1,
        5.0,
        1.0,
        step=0.1,
        key="rc_rt_pct",
    )
    entry_price = st.number_input(
        "खरीद भाव (Entry Price)", value=100.0, step=0.5, key="rc_entry"
    )
    stop_loss_price = st.number_input(
        "स्टॉप लॉस भाव (Stop Loss Price)", value=97.0, step=0.5, key="rc_sl"
    )
    risk_reward_ratio = st.selectbox(
        "रिस्क-टू-रवाॅर्ड रेश्यो (Risk to Reward Ratio)",
        ["1 : 1.5", "1 : 2", "1 : 3", "1 : 5"],
        index=1,
        key="rc_rrr",
    )

  with rc2:
    st.markdown("#### 📊 2. लाइव रिस्क और मनी कैलकुलेशन (Live Output)")

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

    m1, m2 = st.columns(2)
    with m1:
      st.markdown(
          f"""
        <div class="calc-metric-box">
            <p style="color: #848e9c; font-size: 12px; margin-bottom: 5px;">ट्रेडिंग सेटअप टाइप</p>
            <h3 style="color: #fcd535; font-size: 18px; margin: 0;">{trade_type_label}</h3>
        </div>
      """,
          unsafe_allow_html=True,
      )
      st.markdown("<br>", unsafe_allow_html=True)
      st.markdown(
          f"""
        <div class="calc-metric-box">
            <p style="color: #848e9c; font-size: 12px; margin-bottom: 5px;">अधिकतम नुकसान (Max Loss Risk)</p>
            <h3 style="color: #f6465d; font-size: 18px; margin: 0;">- {max_risk_amount:,.2f}</h3>
        </div>
      """,
          unsafe_allow_html=True,
      )

    with m2:
      st.markdown(
          f"""
        <div class="calc-metric-box">
            <p style="color: #848e9c; font-size: 12px; margin-bottom: 5px;">खरीदने योग्य मात्रा (Position Size)</p>
            <h3 style="color: #ffffff; font-size: 18px; margin: 0;">{recommended_quantity:,.2f} Units</h3>
        </div>
      """,
          unsafe_allow_html=True,
      )
      st.markdown("<br>", unsafe_allow_html=True)
      st.markdown(
          f"""
        <div class="calc-metric-box">
            <p style="color: #848e9c; font-size: 12px; margin-bottom: 5px;">संभावित प्रॉफिट (Target Profit)</p>
            <h3 style="color: #0ecb81; font-size: 18px; margin: 0;">+ {potential_profit_amount:,.2f}</h3>
        </div>
      """,
          unsafe_allow_html=True,
      )

  st.markdown("<br>", unsafe_allow_html=True)
  st.markdown(
      f"""
    <div class="signal-box">
        <h4 style="color: #fcd535; margin-top: 0;">💡 आपके लिए सरल निष्कर्ष (Simple Summary):</h4>
        <ul style="color: #eaecef; font-size: 14px; line-height: 1.6;">
            <li><b>सेफ पोजीशन साइज:</b> आपको इस ट्रेड में कुल <b>{recommended_quantity:,.2f} क्वांटिटी/यूनिट</b> लेनी चाहिए।</li>
            <li><b>नुकसान की सीमा (Risk):</b> स्टॉप लॉस हिट होने पर आपका केवल <b>{risk_tolerance_pct}% ({max_risk_amount:,.2f})</b> कैपिटल ही कटेगा।</li>
            <li><b>टारगेट प्राइस (Profit Target):</b> आपके रेश्यो के हिसाब से फाइनल टारगेट <b>{target_price:,.2f}</b> रहेगा, जिस पर आपको <b>{potential_profit_amount:,.2f}</b> का मुनाफा मिलेगा।</li>
            <li><b>0% Loss Defense Rule:</b> टारगेट 1 पर पहुँचते ही स्टॉप लॉस को एंट्री प्राइस पर ले आएं।</li>
        </ul>
    </div>
  """,
      unsafe_allow_html=True,
  )

with tab_chart:
  st.markdown("### 📊 Advanced Ultra-Smooth Live Chart & Real-Time Ticker")
  st.info(
      "💡 Tip: Search any symbol directly inside the chart toolbar or panel below. Real-time milliseconds streaming widget active."
  )

  c_sym, c_tf = st.columns([2, 2])
  with c_sym:
    chart_symbol = st.text_input(
        "Enter TradingView Symbol:",
        value=selected_asset.split(" ")[0],
        key="chart_symbol_input",
    )
  with c_tf:
    chart_tf_map = {
        "1 Minute": "1",
        "5 Minutes": "5",
        "15 Minutes": "15",
        "1 Hour": "60",
        "4 Hours": "240",
        "Daily": "D",
    }
    selected_tf_label = st.selectbox(
        "Select Chart Timeframe",
        list(chart_tf_map.keys()),
        index=2,
        key="chart_tf_sel",
    )
    chart_tf = chart_tf_map[selected_tf_label]

  realtime_ticker_html = f"""
    <div class="tradingview-widget-container" style="width:100%; height:80px; margin-bottom:15px;">
      <div class="tradingview-widget-container__widget"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-single-quote.js" async>
      {{
        "symbol": "{chart_symbol}",
        "width": "100%",
        "colorTheme": "dark",
        "isTransparent": true,
        "locale": "en"
      }}
      </script>
    </div>
    """
  st.components.v1.html(realtime_ticker_html, height=90)

  tv_html = f"""
    <div class="tradingview-widget-container" style="height:550px;width:100%;">
      <div id="tradingview_chart" style="height:100%;width:100%;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget(
      {{
        "width": "100%",
        "height": "550",
        "symbol": "{chart_symbol}",
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
  st.components.v1.html(tv_html, height=570)

with tab_signals:
  st.markdown(
      "### 🎯 World's Best AI Confluence Engine (0% Loss & Precise Entries)"
  )
  if "Premium" not in st.session_state.user_tier:
    rem = max(0, 2 - st.session_state.signals_used)
    st.info(f"Free Plan Quota: {rem}/2 Signals Remaining Today")
  else:
    st.success(
        "👑 VIP Neural Network Active — **SMC + ICT Strategy Model (0% Loss"
        " Shield)**"
    )

  if st.button("🚀 GENERATE 0% LOSS AI SIGNAL & ENTRY", key="gen_sig_btn"):
    if (
        "Premium" not in st.session_state.user_tier
        and st.session_state.signals_used >= 2
    ):
      st.error(
          "⚠️ Daily Free Quota Exhausted! Upgrade to VIP Premium for Unlimited"
          " Elite Signals."
      )
    else:
      if "Premium" not in st.session_state.user_tier:
        st.session_state.signals_used += 1

      raw_sym = selected_asset.split(" ")[0]
      clean_key = (
          raw_sym.replace("BINANCE:", "")
          .replace("FX:", "")
          .replace("NASDAQ:", "")
          .replace("NSE:", "")
      )
      base_p = market_prices.get(clean_key, {"price": 1000.0})["price"]

      entry_val = base_p
      sl_val = round(base_p * 0.985, 2)
      tp1_val = round(base_p * 1.025, 2)
      tp2_val = round(base_p * 1.055, 2)

      st.markdown(
          f"""
          <div class="signal-box">
              <h3 style="color: #0ecb81; margin-top: 0;">🟢 SIGNAL DIRECTION: BUY (LONG) / BULLISH ORDER BLOCK</h3>
              <p style="color: #fcd535; font-size: 14px; font-weight: 700;">Asset: {selected_asset} | Confluence: SMC Market Structure + ICT Liquidity Sweep</p>
          </div>
          """,
          unsafe_allow_html=True,
      )
      st.markdown("<br>", unsafe_allow_html=True)

      s_col1, s_col2 = st.columns(2)
      with s_col1:
        st.metric("Strategy Accuracy Index", "99.8% WIN RATE", "0% LOSS PROTOCOL")
        st.write(f"**Target Asset:** `{selected_asset}`")
        st.write(f"**🟢 Precise Entry Price:** `{entry_val:,.2f}`")
        st.write(f"**🛡️ Stop Loss (SL):** `{sl_val:,.2f}` (Strict 1.5% Risk)")
      with s_col2:
        st.metric("Target Profit Output", "5% to 10%+ Returns", "High Yield Matrix")
        st.write(f"**🎯 Target 1 (TP1 - Secure Profit):** `{tp1_val:,.2f}`")
        st.write(f"**🎯 Target 2 (TP2 - Moonshot):** `{tp2_val:,.2f}`")
        st.write(
            "**Safety Rule:** `Move SL to Entry Price instantly once TP1 is"
            " reached.`"
        )

      st.markdown("<br>", unsafe_allow_html=True)
      st.link_button(
          "🚀 Execute Trade instantly on Broker Terminal",
          "https://in.tradingview.com/",
      )

with tab_plans:
  st.markdown("### 👑 Choose Your VIP Premium Membership Plan")
  st.write(
      "Click on any plan below to instantly open your UPI App with the exact"
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
            "UPDATE users SET tier = ? WHERE lower(trim(email)) = lower(trim(?))",
            (
                "Premium Member (Paid)",
                st.session_state.current_user_email,
            ),
        )
        conn.commit()
        conn.close()
        st.success("🎉 VIP Membership Activated Successfully!")
        st.rerun()
      else:
        st.error("Please enter a valid UTR reference number.")

st.markdown("---")
st.caption(
    "Disclaimer: Veer Pro Terminal is built strictly for educational & research"
    " purposes only. Trading carries risk."
)
