import datetime
import sqlite3
import streamlit as st
import streamlit.components.v1 as components

# 1. Page Configuration
st.set_page_config(
    page_title="VEER PRO TRADING TERMINAL",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- BROWSER LOCALSTORAGE JAVASCRIPT BRIDGE ---
# यह कोड ब्राउज़र के LocalStorage से लॉगिन डेटा पढ़ेगा और लिखेगा (Page Refresh Proof)
def set_local_storage(key, value):
    js_code = f"""
    <script>
        localStorage.setItem("{key}", "{value}");
    </script>
    """
    components.html(js_code, height=0, width=0)

def clear_local_storage():
    js_code = """
    <script>
        localStorage.removeItem("veer_user_session");
        window.location.href = window.location.pathname;
    </script>
    """
    components.html(js_code, height=0, width=0)

# 2. TradingView Pro UI Theme (Dark Glassmorphism)
st.markdown(
    """
    <style>
    :root {
        --bg-main: #080b11;
        --card-bg: rgba(19, 25, 36, 0.85);
        --card-border: rgba(255, 255, 255, 0.08);
        --accent-blue: #2962ff;
        --neon-cyan: #00f2fe;
        --text-main: #f0f3fa;
        --text-sub: #787b86;
    }

    .stApp {
        background: radial-gradient(circle at top left, #0e1726, #080b11 70%) !important;
        color: var(--text-main) !important;
    }

    h1, h2, h3, h4, h5, h6, p, span, label, div {
        color: var(--text-main) !important;
    }

    div[data-testid="stVerticalBlock"] > div {
        background: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: 12px;
        padding: 10px;
    }

    .stTextInput input, .stSelectbox div[role="combobox"] {
        background-color: #131722 !important;
        color: #ffffff !important;
        border: 1px solid #2a2e39 !important;
        border-radius: 8px !important;
        min-height: 44px !important;
    }

    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: 700;
        min-height: 46px;
        background: linear-gradient(135deg, #2962ff 0%, #00f2fe 100%) !important;
        color: #ffffff !important;
        border: none !important;
        box-shadow: 0 4px 20px rgba(41, 98, 255, 0.4);
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- SQLITE DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect("users_database.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            name TEXT NOT NULL
        )
    """)
    conn.commit()
    cursor.execute("SELECT * FROM users WHERE email = ?", ("admin@gmail.com",))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (email, password, name) VALUES (?, ?, ?)", 
                       ("admin@gmail.com", "password123", "Admin Trader"))
        conn.commit()
    conn.close()

init_db()

def get_user(email):
    conn = sqlite3.connect("users_database.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT password, name FROM users WHERE email = ?", (email.strip(),))
    res = cursor.fetchone()
    conn.close()
    return res

def register_user(email, password, name):
    try:
        conn = sqlite3.connect("users_database.db", check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (email, password, name) VALUES (?, ?, ?)", 
                       (email.strip(), password, name.strip()))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

# --- SESSION INITIALIZATION WITH QUERY PARAM PERSISTENCE ---
# Streamlit query params + LocalStorage fallback logic
if "session_user" in st.query_params:
    saved_email = st.query_params["session_user"]
    user_info = get_user(saved_email)
    if user_info:
        st.session_state.logged_in = True
        st.session_state.current_user_email = saved_email
        st.session_state.current_user_name = user_info[1]

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user_email" not in st.session_state:
    st.session_state.current_user_email = ""
if "current_user_name" not in st.session_state:
    st.session_state.current_user_name = ""

# --- AUTHENTICATION SCREEN ---
def show_auth_screen():
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.6, 1])

    with col2:
        st.markdown(
            """
            <div style="text-align: center; margin-bottom: 20px;">
                <h2 style="font-size: 26px; font-weight: 800; color: #ffffff;">🚀 VEER PRO TERMINAL</h2>
                <p style="color: #00f2fe; font-size: 13px;">Institutional Grade Trading Platform</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        auth_tab1, auth_tab2 = st.tabs(["📝 Register", "🔑 Login"])

        with auth_tab1:
            reg_name = st.text_input("Full Name", placeholder="Enter your full name", key="reg_name_input")
            reg_email = st.text_input("Email ID / Phone Number", placeholder="Enter email or phone", key="reg_email_input")
            reg_pass = st.text_input("Create Password", type="password", placeholder="At least 6 characters", key="reg_pass_input")
            reg_pass_confirm = st.text_input("Confirm Password", type="password", placeholder="Re-enter password", key="reg_confirm_input")

            if st.button("REGISTER & LOGIN", key="reg_btn"):
                cleaned_reg_email = reg_email.strip()
                if not reg_name or not cleaned_reg_email or not reg_pass:
                    st.warning("⚠️ Please fill in all fields.")
                elif reg_pass != reg_pass_confirm:
                    st.error("⚠️ Passwords do not match!")
                elif len(reg_pass) < 6:
                    st.warning("⚠️ Password must be at least 6 characters long.")
                else:
                    success = register_user(cleaned_reg_email, reg_pass, reg_name)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.current_user_email = cleaned_reg_email
                        st.session_state.current_user_name = reg_name.strip()
                        st.query_params["session_user"] = cleaned_reg_email
                        set_local_storage("veer_user_session", cleaned_reg_email)
                        st.rerun()
                    else:
                        st.error("⚠️ Account already exists!")

        with auth_tab2:
            login_email = st.text_input("Email ID / Phone Number", placeholder="Enter email/phone", key="login_email_input")
            login_pass = st.text_input("Password", type="password", placeholder="Enter password", key="login_pass_input")

            if st.button("LOGIN TO TERMINAL", key="login_btn"):
                cleaned_email = login_email.strip()
                user_data = get_user(cleaned_email)

                if user_data and user_data[0] == login_pass:
                    st.session_state.logged_in = True
                    st.session_state.current_user_email = cleaned_email
                    st.session_state.current_user_name = user_data[1]
                    
                    # Store Session in URL Query Params AND Browser Local Storage
                    st.query_params["session_user"] = cleaned_email
                    set_local_storage("veer_user_session", cleaned_email)
                    st.success("🎉 Login Successful!")
                    st.rerun()
                else:
                    st.error("⚠️ Invalid Credentials!")

# JS Bridge Script to Restore Session on Browser Hard Refresh
st.markdown("""
    <script>
        const savedSession = localStorage.getItem("veer_user_session");
        const urlParams = new URLSearchParams(window.location.search);
        if (savedSession && !urlParams.has("session_user")) {
            urlParams.set("session_user", savedSession);
            window.location.search = urlParams.toString();
        }
    </script>
""", unsafe_allow_html=True)

if not st.session_state.logged_in:
    show_auth_screen()
    st.stop()

# --- SIDEBAR & DASHBOARD (LOGGED IN STATE) ---
with st.sidebar:
    st.markdown("### 👤 User Profile")
    st.markdown(f"👋 **{st.session_state.current_user_name}**")
    st.markdown(f"📧 `{st.session_state.current_user_email}`")
    st.markdown("---")
    if st.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.current_user_email = ""
        st.session_state.current_user_name = ""
        st.query_params.clear()
        clear_local_storage()
        st.rerun()

# --- TRADING VIEW PRO TERMINAL UI ---
st.markdown(
    """
    <div style="background: #131722; padding: 8px 12px; border-radius: 8px; border: 1px solid #2a2e39; display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; font-size: 12px;">
        <div><b style="color:#00f2fe;">🚀 VEER TERMINAL</b></div>
        <div><span>BTCUSDT</span> <b style="color: #f23645;">$68,420.00 (-1.59%)</b></div>
        <div style="color: #089981; font-weight:600;">ETHUSDT +2.14%</div>
    </div>
""",
    unsafe_allow_html=True,
)

tab1, tab2, tab3, tab4 = st.tabs(["⚡ Terminal Dashboard", "📊 Live Chart", "🏆 Accuracy", "💎 VIP Plan"])

with tab1:
    col_main, col_side = st.columns([2.2, 1], gap="small")
    with col_main:
        st.markdown("##### ⚙️ Signal Configuration")
        c1, c2, c3 = st.columns(3)
        with c1:
            market_category = st.selectbox("Category", ["TIER 1 (Main Assets)", "TIER 2 (Altcoins)"])
        with c2:
            asset = st.selectbox("Asset", ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"])
        with c3:
            timeframe = st.selectbox("Timeframe", ["1m", "5m", "15m", "1h", "4h", "1d"])

        st.markdown("##### 🛡️ Risk Management")
        account_balance = st.number_input("Account Balance ($)", value=10000.0)
        risk_pct = st.slider("Risk Per Trade (%)", 0.1, 5.0, 1.0)

    with col_side:
        st.markdown("##### 🤖 AI Signals Hub")
        if st.button("✨ GENERATE SIGNAL"):
            st.markdown(
                f"""
                <div style="background:#131722; padding:12px; border-radius:8px; border-left:4px solid #089981; margin-top:8px;">
                    <h5 style="color:#089981; margin:0;">🔥 BULLISH SETUP</h5>
                    <p style="font-size:11px; color:#787b86;">Pair: BINANCE:{asset} ({timeframe})</p>
                    <p style="font-size:12px; margin:2px 0;"><b>Entry:</b> ~$64,611.89</p>
                    <p style="font-size:12px; margin:2px 0;"><b>Stop Loss:</b> ~$64,352.92</p>
                    <p style="font-size:12px; margin:2px 0;"><b>Target:</b> ~$65,518.27</p>
                </div>
            """,
                unsafe_allow_html=True,
            )

with tab2:
    tradingview_html = f"""
    <div class="tradingview-widget-container" style="height:500px;width:100%;">
      <div id="tradingview_widget" style="height:100%;width:100%;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({{
        "width": "100%",
        "height": "500",
        "symbol": "BINANCE:{asset}",
        "interval": "D",
        "timezone": "Etc/UTC",
        "theme": "dark",
        "style": "1",
        "locale": "en",
        "toolbar_bg": "#131722",
        "enable_publishing": false,
        "allow_symbol_change": true,
        "container_id": "tradingview_widget"
      }});
      </script>
    </div>
    """
    st.components.v1.html(tradingview_html, height=520)

with tab3:
    m1, m2, m3 = st.columns(3)
    m1.metric("7-Day Signals", "142")
    m2.metric("Accuracy", "84.5%")
    m3.metric("Avg R:R", "1:2.4")

with tab4:
    st.markdown("### 💎 VIP Access")
    st.link_button("📲 Pay via UPI App (GPay/PhonePe)", "upi://pay?pa=7479465676-7@ybl&pn=VEER%20PRO&am=999.00&cu=INR")
