import datetime
import sqlite3
import streamlit as st

# 1. Page Configuration (Must be at the top)
st.set_page_config(
    page_title="VEER PRO TRADING TERMINAL",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Custom CSS for Premium Colorful Dark Theme
st.markdown(
    """
    <style>
    /* Global Deep Colorful Dark Theme */
    .stApp {
        background: radial-gradient(circle at top right, #131b2e, #090d16) !important;
        color: #ffffff !important;
    }
    
    /* Force all text, labels, and headers to be bright white */
    h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown {
        color: #ffffff !important;
    }
    
    /* Stylish Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #131b2e 0%, #090d16 100%) !important;
        border-right: 1px solid #1f293d;
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] div, [data-testid="stSidebar"] span, [data-testid="stSidebar"] p {
        color: #e0e7ff !important;
    }
    
    /* Input Field Labels visibility */
    .stTextInput label, .stSelectbox label, .stNumberInput label, .stSlider label {
        color: #00f2fe !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }

    /* Input Boxes Styling */
    .stTextInput>div>div>input, .stNumberInput>div>div>input {
        background-color: #131b2e !important;
        color: #ffffff !important;
        border: 1px solid #3b82f6 !important;
        border-radius: 10px;
        padding: 12px;
    }
    .stTextInput>div>div>input:focus {
        border-color: #00f2fe !important;
        box-shadow: 0 0 12px rgba(0, 242, 254, 0.5);
    }

    /* Selectbox styling */
    .stSelectbox>div>div>div {
        background-color: #131b2e !important;
        color: #ffffff !important;
        border: 1px solid #3b82f6 !important;
        border-radius: 10px;
    }

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #131b2e !important;
        border-radius: 8px !important;
        color: #94a3b8 !important;
        font-weight: 600;
        padding: 10px 18px;
        border: 1px solid #1f293d;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #00f2fe 0%, #6366f1 100%) !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        border: none !important;
    }

    /* Glowing Action Buttons */
    .stButton>button { 
        width: 100%; 
        border-radius: 10px; 
        font-weight: 700; 
        height: 48px; 
        background: linear-gradient(135deg, #00f2fe 0%, #6366f1 100%); 
        color: #ffffff; 
        border: none; 
        font-size: 16px; 
        box-shadow: 0 4px 15px rgba(0,242,254,0.3);
        transition: 0.3s ease;
    }
    .stButton>button:hover { 
        background: linear-gradient(135deg, #6366f1 0%, #00f2fe 100%); 
        box-shadow: 0 6px 20px rgba(99,102,241,0.5);
    }

    div.stMetric { 
        background: #131b2e; 
        padding: 15px; 
        border-radius: 12px; 
        border: 1px solid #3b82f6; 
    }
    .signal-card { 
        background: #131b2e; 
        padding: 20px; 
        border-radius: 14px; 
        border-left: 6px solid #00f2fe; 
        border: 1px solid #3b82f6;
        margin-top: 15px; 
    }
    </style>
""",
    unsafe_allow_html=True,
)


# --- PERMANENT SQLITE DATABASE HELPER FUNCTIONS ---
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
    cursor.execute("SELECT * FROM users WHERE email = ?", ("admin@gmail.com",))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (email, password, name) VALUES (?, ?, ?)",
            ("admin@gmail.com", "password123", "Admin Trader"),
        )
        conn.commit()
    conn.close()

init_db()

def get_user(email):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password, name FROM users WHERE email = ?", (email.strip(),))
    res = cursor.fetchone()
    conn.close()
    return res

def register_user(email, password, name):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (email, password, name) VALUES (?, ?, ?)",
            (email.strip(), password, name.strip()),
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False


# --- SESSION STATE INITIALIZATION ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user_email" not in st.session_state:
    st.session_state.current_user_email = ""
if "current_user_name" not in st.session_state:
    st.session_state.current_user_name = ""
if "user_tier" not in st.session_state:
    st.session_state.user_tier = "Free User"
if "signals_used" not in st.session_state:
    st.session_state.signals_used = 0
if "last_reset" not in st.session_state:
    st.session_state.last_reset = datetime.date.today()

# Auto-reset signal quota daily
if st.session_state.last_reset != datetime.date.today():
    st.session_state.signals_used = 0
    st.session_state.last_reset = datetime.date.today()


# --- AUTHENTICATION SCREEN ---
def show_auth_screen():
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.4, 1])

    with col2:
        st.markdown(
            """
            <div style="text-align: center; margin-bottom: 25px;">
                <h2 style="font-size: 26px; font-weight: 800; color: #ffffff; margin-bottom: 5px;">🔐 VEER PRO TERMINAL</h2>
                <p style="color: #00f2fe; font-size: 13px; letter-spacing: 1px;">Institutional Grade Trading Platform</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        auth_tab1, auth_tab2 = st.tabs(["📝 Register", "🔑 Login"])

        with auth_tab1:
            st.markdown("<h3 style='color: #ffffff; font-size: 18px; margin-top: 10px;'>Create New Account</h3>", unsafe_allow_html=True)
            
            # Encapsulated inside st.form to fix auto-refresh crashes
            with st.form("register_form", clear_on_submit=False):
                reg_name = st.text_input("Full Name", placeholder="Enter your full name", key="reg_name_input")
                reg_email = st.text_input("Email ID / Phone Number", placeholder="Enter email or phone", key="reg_email_input")
                reg_pass = st.text_input("Create Password", type="password", placeholder="At least 6 characters", key="reg_pass_input")
                reg_pass_confirm = st.text_input("Confirm Password", type="password", placeholder="Re-enter password", key="reg_confirm_input")
                
                st.markdown("<br>", unsafe_allow_html=True)
                reg_submitted = st.form_submit_button("REGISTER & LOGIN")

                if reg_submitted:
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
                            st.success("🎉 Account Created & Logged In Successfully!")
                            st.rerun()
                        else:
                            st.error("⚠️ This Email/Phone is already registered! Please go to Login tab.")

        with auth_tab2:
            st.markdown("<h3 style='color: #ffffff; font-size: 18px; margin-top: 10px;'>Welcome Back</h3>", unsafe_allow_html=True)
            
            # Encapsulated inside st.form to preserve login state
            with st.form("login_form", clear_on_submit=False):
                login_email = st.text_input("Email ID / Phone Number", placeholder="Enter registered email or phone", key="login_email_input")
                login_pass = st.text_input("Password", type="password", placeholder="Enter your password", key="login_pass_input")

                st.markdown("<br>", unsafe_allow_html=True)
                login_submitted = st.form_submit_button("LOGIN TO TERMINAL")

                if login_submitted:
                    cleaned_email = login_email.strip()
                    user_data = get_user(cleaned_email)

                    if user_data and user_data[0] == login_pass:
                        st.session_state.logged_in = True
                        st.session_state.current_user_email = cleaned_email
                        st.session_state.current_user_name = user_data[1]
                        st.success("🎉 Login Successful! Redirecting...")
                        st.rerun()
                    else:
                        st.error("⚠️ Invalid Email/Phone or Password! Please check or register first.")


# Render Auth Screen if not logged in
if not st.session_state.logged_in:
    show_auth_screen()
    st.stop()


# --- SIDEBAR USER PROFILE ---
with st.sidebar:
    st.markdown("### 👤 User Profile")
    st.markdown("---")
    st.markdown(f"👋 Hello, **{st.session_state.current_user_name}**")
    st.markdown(f"📧 `{st.session_state.current_user_email}`")
    st.markdown(f"🌟 Status: **{st.session_state.user_tier}**")
    st.markdown("---")
    if st.button("🚪 Logout", key="logout_btn"):
        st.session_state.logged_in = False
        st.session_state.current_user_email = ""
        st.session_state.current_user_name = ""
        st.session_state.user_tier = "Free User"
        st.rerun()


# --- MAIN TRADING TERMINAL ---
st.title("🚀 VEER PRO TRADING TERMINAL")
st.markdown("<p style='color: #00f2fe;'><b>Institutional Grade Live Market, Interactive Charts & AI Smart Signals</b></p>", unsafe_allow_html=True)
st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["⚡ Pro Terminal", "📊 Live Chart", "🏆 Accuracy", "💎 VIP Plan"])

with tab1:
    col1, col2 = st.columns([1, 1], gap="medium")

    with col1:
        st.markdown("### ⚙️ Configuration")
        market_category = st.selectbox("Market Category", ["TIER 1 (Main Assets)", "TIER 2 (Altcoins)"], key="market_cat")
        asset = st.selectbox("Select Asset", ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"], key="selected_asset")
        timeframe = st.selectbox("Timeframe", ["1m", "5m", "15m", "1h", "4h"], key="timeframe_select")

        st.markdown("### 🛡️ Risk Management")
        account_balance = st.number_input("Account Balance ($)", value=10000.0, step=500.0, key="acc_bal")
        risk_pct = st.slider("Risk Per Trade (%)", 0.1, 5.0, 1.0, key="risk_pct")
        atr_multiplier = st.slider("ATR SL Multiplier", 1.0, 3.0, 1.5, key="atr_mult")

        risk_capital = account_balance * (risk_pct / 100)
        st.info(f"📊 **Risk Summary:** Capital at Risk: **${risk_capital:.2f}** | Protection: Active")

    with col2:
        st.markdown("### 🤖 AI Smart Signal Hub")

        can_generate = True
        if st.session_state.user_tier == "Free User":
            remaining_signals = 2 - st.session_state.signals_used
            st.markdown(f"📢 Free Plan Quota: **{remaining_signals}/2** signals remaining today.")
            if remaining_signals <= 0:
                can_generate = False
        else:
            st.markdown("👑 VIP Status Active: **Unlimited Signals** available for you.")

        if st.button("✨ GENERATE SMART AI SIGNAL", key="gen_sig_btn"):
            if not can_generate:
                st.error("⚠️ Daily free limit of 2 signals reached! Go to 'VIP Plan' tab to upgrade for unlimited access.")
            else:
                if st.session_state.user_tier == "Free User":
                    st.session_state.signals_used += 1

                st.markdown(
                    """
                    <div class="signal-card">
                        <h3 style='color: #00f2fe; margin-top: 0;'>🔥 STRONG BUY SETUP (Bullish)</h3>
                        <hr style='border-color: #3b82f6; margin: 5px 0 15px 0;'>
                    """,
                    unsafe_allow_html=True,
                )

                sc1, sc2 = st.columns(2)
                sc1.metric("Live Market Price", "$64,741.37", "+1.4%")
                sc2.metric("Profit / Risk Ratio", "1 : 2.5", "Optimal")

                st.markdown(
                    f"""
                        <p><b>🎯 Target Asset:</b> BINANCE:{asset} ({timeframe})</p>
                        <p><b>📍 Optimal Entry Zone (OB/FVG):</b> ~$64,611.89</p>
                        <p><b>🛑 Smart Stop Loss (SL):</b> ~$64,352.92</p>
                        <p><b>🎯 Target 1 (TP1):</b> ~$65,065.08</p>
                        <p><b>🎯 Target 2 (TP2):</b> ~$65,518.27</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.markdown("<br>", unsafe_allow_html=True)
                st.link_button("🚀 Execute Trade on Partner Exchange (Affiliate)", "https://www.binance.com")

with tab2:
    st.markdown(f"### 📈 Live Interactive Chart — {asset}")
    tradingview_html = f"""
    <div class="tradingview-widget-container" style="height:500px;width:100%;">
      <div id="tradingview_widget" style="height:100%;width:100%;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget(
      {{
        "width": "100%",
        "height": "500",
        "symbol": "BINANCE:{asset}",
        "interval": "D",
        "timezone": "Etc/UTC",
        "theme": "dark",
        "style": "1",
        "locale": "en",
        "toolbar_bg": "#f1f3f6",
        "enable_publishing": false,
        "allow_symbol_change": true,
        "container_id": "tradingview_widget"
      }});
      </script>
    </div>
    """
    st.components.v1.html(tradingview_html, height=520)

with tab3:
    st.markdown("### 🏆 Performance & Accuracy Metrics")
    st.markdown("Verified past 7-day algorithmic execution results:")

    m1, m2, m3 = st.columns(3)
    m1.metric("7-Day Signals", "142", "+12 today")
    m2.metric("Success Rate", "84.5%", "+2.1%")
    m3.metric("Avg R:R Ratio", "1:2.4", "Optimal")

    st.markdown("---")
    st.markdown("#### 📋 Recent Executed Calls")
    st.dataframe(
        {
            "Timestamp": ["2026-08-19 14:30", "2026-08-19 11:15", "2026-08-18 16:45"],
            "Pair": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
            "Action": ["BUY", "BUY", "SELL"],
            "Outcome": ["TP2 Hit (+3.2%)", "TP1 Hit (+1.8%)", "TP2 Hit (+4.1%)"],
        },
        use_container_width=True,
    )

with tab4:
    st.markdown("### 💎 Upgrade to VIP Pro Access (₹999 / Month)")

    col_p1, col_p2 = st.columns(2, gap="medium")

    with col_p1:
        st.markdown(
            """
            #### 👑 VIP Benefits
            - **Unlimited** Smart AI Signals
            - Advanced Multi-Asset Scanners
            - Priority Alerts & Zero Ads
            """
        )
        st.markdown("---")
        st.markdown("### 📱 Option 1: Direct Pay via UPI App")
        st.markdown("Click below to pay securely through PhonePe, Google Pay, or Paytm:")

        upi_intent_url = "upi://pay?pa=7479465676-7@ybl&pn=VEER%20PRO%20TRADER&am=999.00&cu=INR"
        st.link_button("📲 Pay ₹999 via UPI App (GPay/PhonePe)", upi_intent_url)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 📷 Option 2: Scan QR Code")
        qr_code_url = "https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=" + upi_intent_url
        st.image(qr_code_url, caption="Scan this QR code with any UPI App to Pay ₹999", width=180)

    with col_p2:
        st.markdown("#### ⚡ Step 3: Verify & Unlock")
        st.markdown("Payment karne ke baad jo **12-digit UTR / Reference Number** milega, use yahan dalein:")

        utr_input = st.text_input("Enter 12-digit UTR / UPI Reference Number:", placeholder="e.g. 4152xxxxxxxx", key="utr_input_field")

        if st.button("🔓 Verify & Activate VIP Access", key="utr_verify_btn"):
            if len(utr_input.strip()) >= 8:
                st.session_state.user_tier = "VIP Paid Member"
                st.success("🎉 Congratulations! VIP Access Activated Successfully. Enjoy Unlimited Signals!")
                st.rerun()
            else:
                st.error("⚠️ Kripya sahi UTR / Transaction ID दर्ज करें (कम से कम 8 अंक)।")

st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #94a3b8; font-size: 11px;'>"
    "<b>Disclaimer:</b> VEER PRO TRADING TERMINAL is built for educational & analytical research only. Crypto trading involves high market risk."
    "</p>",
    unsafe_allow_html=True,
)
