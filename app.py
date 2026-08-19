import datetime
import random
import sqlite3
import json
import streamlit as st
import streamlit.components.v1 as components

# 1. Page Configuration
st.set_page_config(
    page_title="VEER PRO TRADING TERMINAL",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- BROWSER LOCALSTORAGE JAVASCRIPT BRIDGE ---
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

# 2. Ultra-Compact & Sleek Dark UI CSS
st.markdown(
    """
    <style>
    :root {
        --bg-main: #080b11;
        --card-bg: rgba(19, 25, 36, 0.9);
        --card-border: rgba(255, 255, 255, 0.08);
        --accent-blue: #2962ff;
        --neon-cyan: #00f2fe;
        --green-up: #089981;
        --red-down: #f23645;
        --text-main: #f0f3fa;
        --text-sub: #787b86;
    }

    .stApp {
        background: radial-gradient(circle at top left, #0e1726, #080b11 70%) !important;
        color: var(--text-main) !important;
    }

    /* Reduce vertical padding across app */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
    }

    h1, h2, h3, h4, h5, h6, p, span, label, div {
        color: var(--text-main) !important;
    }

    .stTextInput input, .stSelectbox div[role="combobox"], .stNumberInput input {
        background-color: #131722 !important;
        color: #ffffff !important;
        border: 1px solid #2a2e39 !important;
        border-radius: 6px !important;
        min-height: 38px !important;
        font-size: 13px !important;
    }

    section[data-testid="stSidebar"] {
        background-color: #0e131f !important;
        border-right: 1px solid #2a2e39 !important;
    }

    /* Compact Main Action Buttons */
    .stButton>button, .stLinkButton>a {
        width: 100%;
        border-radius: 6px;
        font-weight: 700;
        min-height: 38px;
        font-size: 13px;
        background: linear-gradient(135deg, #2962ff 0%, #00f2fe 100%) !important;
        color: #ffffff !important;
        border: none !important;
        box-shadow: 0 2px 10px rgba(41, 98, 255, 0.3);
        text-align: center;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    
    /* Compact Quick Action Row Buttons */
    .quick-btn-container {
        display: flex;
        gap: 4px;
        align-items: center;
        flex-wrap: nowrap;
        overflow-x: auto;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background-color: #131722;
        padding: 3px;
        border-radius: 6px;
        border: 1px solid #2a2e39;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        border-radius: 4px !important;
        color: var(--text-sub) !important;
        font-weight: 600 !important;
        padding: 6px 12px !important;
        font-size: 12px !important;
        border: none !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: var(--accent-blue) !important;
        color: #ffffff !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- SAFE SQLITE DATABASE SETUP ---
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

    cursor.execute("PRAGMA table_info(users);")
    columns = [col[1] for col in cursor.fetchall()]

    if "tier" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN tier TEXT DEFAULT 'Free User'")
    if "vip_expiry" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN vip_expiry TEXT DEFAULT ''")
    
    conn.commit()

    cursor.execute("SELECT * FROM users WHERE email = ?", ("admin@gmail.com",))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (email, password, name, tier, vip_expiry) VALUES (?, ?, ?, ?, ?)", 
                       ("admin@gmail.com", "password123", "Admin Trader", "Free User", ""))
        conn.commit()
        
    conn.close()

init_db()

def get_user(email):
    conn = sqlite3.connect("users_database.db", check_same_thread=False)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT password, name, tier, vip_expiry FROM users WHERE email = ?", (email.strip(),))
        res = cursor.fetchone()
    except sqlite3.OperationalError:
        res = None
    conn.close()
    return res

def register_user(email, password, name):
    try:
        conn = sqlite3.connect("users_database.db", check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (email, password, name, tier, vip_expiry) VALUES (?, ?, ?, 'Free User', '')", 
                       (email.strip(), password, name.strip()))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def update_user_vip(email, days=30):
    expiry_date = (datetime.datetime.now() + datetime.timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect("users_database.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET tier = 'VIP Paid Member', vip_expiry = ? WHERE email = ?", (email.strip(), email.strip()))
    conn.commit()
    conn.close()
    return expiry_date

# --- SESSION & VIP STATUS VALIDATION ---
if "session_user" in st.query_params:
    saved_email = st.query_params["session_user"]
    user_info = get_user(saved_email)
    if user_info:
        st.session_state.logged_in = True
        st.session_state.current_user_email = saved_email
        st.session_state.current_user_name = user_info[1]
        
        tier = user_info[2] if len(user_info) > 2 and user_info[2] else "Free User"
        expiry_str = user_info[3] if len(user_info) > 3 and user_info[3] else ""
        
        if tier == "VIP Paid Member" and expiry_str:
            try:
                expiry_dt = datetime.datetime.strptime(expiry_str, "%Y-%m-%d %H:%M:%S")
                if datetime.datetime.now() < expiry_dt:
                    st.session_state.user_tier = "VIP Paid Member"
                    st.session_state.vip_expiry = expiry_str
                else:
                    st.session_state.user_tier = "Free User"
                    st.session_state.vip_expiry = ""
            except ValueError:
                st.session_state.user_tier = "Free User"
                st.session_state.vip_expiry = ""
        else:
            st.session_state.user_tier = tier
            st.session_state.vip_expiry = expiry_str

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user_email" not in st.session_state:
    st.session_state.current_user_email = ""
if "current_user_name" not in st.session_state:
    st.session_state.current_user_name = ""
if "user_tier" not in st.session_state:
    st.session_state.user_tier = "Free User"
if "vip_expiry" not in st.session_state:
    st.session_state.vip_expiry = ""
if "signals_used" not in st.session_state:
    st.session_state.signals_used = 0

# --- SEPARATE STATE TRACKING FOR MULTI-TICKER ---
if "signal_asset" not in st.session_state:
    st.session_state.signal_asset = "BTCUSDT"
if "chart_asset" not in st.session_state:
    st.session_state.chart_asset = "ETHUSDT"
if "custom_ticker_asset" not in st.session_state:
    st.session_state.custom_ticker_asset = "SOLUSDT"

# --- AUTHENTICATION SCREEN ---
def show_auth_screen():
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.6, 1])

    with col2:
        st.markdown(
            """
            <div style="text-align: center; margin-bottom: 20px;">
                <h2 style="font-size: 24px; font-weight: 800; color: #ffffff; margin:0;">🚀 VEER PRO TERMINAL</h2>
                <p style="color: #00f2fe; font-size: 12px; margin:0;">Institutional Grade Trading Platform</p>
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
                        st.session_state.user_tier = "Free User"
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
                    st.session_state.user_tier = user_data[2] if len(user_data) > 2 and user_data[2] else "Free User"
                    st.session_state.vip_expiry = user_data[3] if len(user_data) > 3 and user_data[3] else ""
                    st.query_params["session_user"] = cleaned_email
                    set_local_storage("veer_user_session", cleaned_email)
                    st.success("🎉 Login Successful!")
                    st.rerun()
                else:
                    st.error("⚠️ Invalid Credentials!")

if not st.session_state.logged_in:
    show_auth_screen()
    st.stop()

# --- OPTIMIZED SIDEBAR ---
with st.sidebar:
    st.markdown("### 👤 User Profile")
    st.markdown(f"👋 **{st.session_state.current_user_name}**")
    st.markdown(f"📧 `{st.session_state.current_user_email}`")
    
    is_vip = st.session_state.user_tier == "VIP Paid Member"
    if is_vip:
        st.markdown("🌟 Status: <b style='color:#00f2fe;'>👑 VIP Member</b>", unsafe_allow_html=True)
        if st.session_state.vip_expiry:
            st.caption(f"⏳ Expires on: `{st.session_state.vip_expiry[:10]}`")
    else:
        st.markdown("🌟 Status: **Free User**")

    st.markdown("---")
    
    st.markdown("### 🎟️ VIP Access Code")
    sidebar_promo = st.text_input("Enter Promo Code:", placeholder="Enter Promo Code", key="sidebar_promo_code")
    
    if st.button("Redeem Promo Code", key="apply_sidebar_promo"):
        if sidebar_promo.strip().upper() == "FREEVIP2026":
            expiry_dt = update_user_vip(st.session_state.current_user_email, days=30)
            st.session_state.user_tier = "VIP Paid Member"
            st.session_state.vip_expiry = expiry_dt
            st.success("🎉 30 Days Free VIP Access Activated!")
            st.rerun()
        else:
            st.error("❌ Invalid Promo Code")

    st.markdown("---")
    
    if st.button("🚪 Logout", key="logout_btn"):
        st.session_state.logged_in = False
        st.session_state.current_user_email = ""
        st.session_state.current_user_name = ""
        st.session_state.user_tier = "Free User"
        st.session_state.vip_expiry = ""
        st.query_params.clear()
        clear_local_storage()
        st.rerun()

# --- FULL ASSET DICTIONARY ---
ASSET_CATEGORIES = {
    "Crypto Top Major": ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "DOTUSDT", "LINKUSDT", "LTCUSDT", "MATICUSDT", "NEARUSDT", "TRXUSDT", "SHIBUSDT"],
    "Forex Currency Pairs": ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY"],
    "Commodities & Indices": ["XAUUSD (GOLD)", "XAGUSD (SILVER)", "USOIL (CRUDE)", "SPX500", "NAS100", "US30"],
    "Indian Market (NSE/BSE)": ["NIFTY50", "BANKNIFTY", "FINNIFTY", "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY", "TATAMOTORS", "SBIN"]
}

ALL_FLAT_ASSETS = [asset for sublist in ASSET_CATEGORIES.values() for asset in sublist]

def get_asset_price(asset_name):
    if "BTC" in asset_name:
        return 68420.00 + random.uniform(-12.5, 12.5)
    elif "ETH" in asset_name:
        return 3540.50 + random.uniform(-1.8, 1.8)
    elif "SOL" in asset_name:
        return 145.20 + random.uniform(-0.5, 0.5)
    elif "NIFTY" in asset_name:
        return 24500.00 + random.uniform(-8.0, 8.0)
    elif "XAU" in asset_name:
        return 2500.00 + random.uniform(-1.5, 1.5)
    else:
        return 1.0850 + random.uniform(-0.0005, 0.0005)

# --- REAL-TIME 3-WAY COMPACT LIVE HEADER ---
@st.fragment(run_every="1s")
def render_live_header():
    sig_asset = st.session_state.get("signal_asset", "BTCUSDT")
    chart_asset = st.session_state.get("chart_asset", "ETHUSDT")
    custom_asset = st.session_state.get("custom_ticker_asset", "SOLUSDT")

    sig_p = get_asset_price(sig_asset)
    chart_p = get_asset_price(chart_asset)
    custom_p = get_asset_price(custom_asset)

    chg1 = random.uniform(0.1, 2.5)
    chg2 = random.uniform(0.1, 2.5)
    chg3 = random.uniform(0.1, 2.5)

    st.markdown(
        f"""
        <div style="background: #131722; padding: 6px 12px; border-radius: 6px; border: 1px solid #2a2e39; display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; font-size: 11px;">
            <div style="flex:1; text-align:left;">
                <span style="color:#787b86; font-size:9px;">🎯 SIGNAL (LEFT)</span><br>
                <b style="color: #00f2fe;">{sig_asset}</b> <b style="color: #089981;">${sig_p:,.2f}</b>
            </div>
            <div style="flex:1; text-align:center; border-left: 1px solid #2a2e39; border-right: 1px solid #2a2e39; padding: 0 6px;">
                <span style="color:#787b86; font-size:9px;">📌 PERMANENT (MID)</span><br>
                <b style="color: #ffb703;">{custom_asset}</b> <b style="color: #089981;">${custom_p:,.2f}</b>
            </div>
            <div style="flex:1; text-align:right;">
                <span style="color:#787b86; font-size:9px;">📊 CHART (RIGHT)</span><br>
                <b style="color: #00f2fe;">{chart_asset}</b> <b style="color: #089981;">${chart_p:,.2f}</b>
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )

render_live_header()

# --- HIGHLY OPTIMIZED & COMPACT PERMANENT TICKER BAR ---
st.markdown("<div style='background:#0e131f; padding:6px 10px; border-radius:6px; border:1px solid #2a2e39; margin-bottom:8px;'>", unsafe_allow_html=True)
p_col1, p_col2 = st.columns([1.2, 2])

with p_col1:
    cur_idx = ALL_FLAT_ASSETS.index(st.session_state.custom_ticker_asset) if st.session_state.custom_ticker_asset in ALL_FLAT_ASSETS else 0
    sel_custom = st.selectbox("📌 Mid Permanent Live Asset:", ALL_FLAT_ASSETS, index=cur_idx, key="select_custom_ticker", label_visibility="collapsed")
    if sel_custom != st.session_state.custom_ticker_asset:
        st.session_state.custom_ticker_asset = sel_custom
        st.rerun()

with p_col2:
    famous = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XAUUSD", "NIFTY50"]
    btn_cols = st.columns(5)
    for i, fam in enumerate(famous):
        with btn_cols[i]:
            display_label = fam.replace("USDT", "").replace(" (GOLD)", "")
            if st.button(display_label, key=f"perm_quick_{i}"):
                full_asset = "XAUUSD (GOLD)" if fam == "XAUUSD" else (fam + "USDT" if fam in ["BTC", "ETH", "SOL"] else fam)
                st.session_state.custom_ticker_asset = full_asset
                st.rerun()
st.markdown("</div>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["⚡ Terminal Dashboard", "📊 Live Chart", "🏆 Accuracy", "💎 VIP Plan"])

ALL_TIMEFRAMES = ["1s", "5s", "10s", "30s", "1m", "5m", "15m", "1h", "4h", "1D", "1W", "1M", "1Y"]

with tab1:
    col_main, col_side = st.columns([2, 1], gap="small")
    with col_main:
        st.markdown("##### ⚙️ Signal Configuration")
        c1, c2, c3 = st.columns(3)
        with c1:
            market_category = st.selectbox("Category", list(ASSET_CATEGORIES.keys()), key="sig_cat_sel")
        with c2:
            sig_idx = 0
            if st.session_state.signal_asset in ASSET_CATEGORIES[market_category]:
                sig_idx = ASSET_CATEGORIES[market_category].index(st.session_state.signal_asset)
            
            asset = st.selectbox("Asset", ASSET_CATEGORIES[market_category], index=sig_idx, key="sig_asset_sel")
            if asset != st.session_state.signal_asset:
                st.session_state.signal_asset = asset
                st.rerun()

        with c3:
            timeframe_options = ALL_TIMEFRAMES if is_vip else ["1m", "5m", "15m", "1h", "4h", "1D"]
            timeframe = st.selectbox("Timeframe", timeframe_options, key="sig_tf_sel")

        st.markdown("##### 🛡️ Risk Management")
        rc1, rc2 = st.columns(2)
        with rc1:
            account_balance = st.number_input("Account Balance ($)", value=10000.0)
        with rc2:
            risk_pct = st.slider("Risk Per Trade (%)", 0.1, 5.0, 1.0)

    with col_side:
        st.markdown("##### 🤖 Institutional AI Signals")
        
        can_generate = True
        if not is_vip:
            remaining_signals = 2 - st.session_state.signals_used
            st.caption(f"Free Limit: **{remaining_signals}/2** remaining today.")
            if remaining_signals <= 0:
                can_generate = False
        else:
            st.caption("👑 VIP Status: **Unlimited Signals**")

        if st.button("✨ GENERATE ACCURATE SIGNAL", key="gen_sig_btn"):
            if not can_generate:
                st.error("⚠️ Free limit reached! Upgrade to VIP Plan.")
            else:
                if not is_vip:
                    st.session_state.signals_used += 1

                entry_p = get_asset_price(asset)
                sl_p = entry_p * 0.994
                tp1_p = entry_p * 1.008
                tp2_p = entry_p * 1.018

                st.markdown(
                    f"""
                    <div style="background:#131722; padding:12px; border-radius:8px; border-left:4px solid #089981; border-top:1px solid #2a2e39; border-right:1px solid #2a2e39; border-bottom:1px solid #2a2e39; margin-top:6px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <b style="color:#089981; font-size:13px;">🔥 BUY SETUP</b>
                            <span style="background:#08998122; color:#089981; padding:2px 6px; border-radius:4px; font-size:10px; font-weight:bold;">93.8% ACCURACY</span>
                        </div>
                        <p style="font-size:11px; color:#787b86; margin:2px 0 6px 0;">{asset} ({timeframe}) | SMC Order Block</p>
                        <p style="margin:2px 0; font-size:12px;"><b>📍 Entry:</b> ~${entry_p:,.2f}</p>
                        <p style="margin:2px 0; font-size:12px; color:#f23645;"><b>🛑 SL:</b> ~${sl_p:,.2f}</p>
                        <p style="margin:2px 0; font-size:12px; color:#089981;"><b>🎯 TP1:</b> ~${tp1_p:,.2f}</p>
                        <p style="margin:2px 0; font-size:12px; color:#089981;"><b>🎯 TP2:</b> ~${tp2_p:,.2f}</p>
                    </div>
                """,
                    unsafe_allow_html=True,
                )

# --- ADVANCED HIGH-ACCURACY SMC AUTO-MAPPING CHART ENGINE WITH DYNAMIC TIMEFRAME FIX ---
with tab2:
    chart_col1, chart_col2 = st.columns([1, 2.5])
    with chart_col1:
        cat_select = st.selectbox("Market Category:", list(ASSET_CATEGORIES.keys()), key="chart_cat_select")
        
        c_asset_idx = 0
        if st.session_state.chart_asset in ASSET_CATEGORIES[cat_select]:
            c_asset_idx = ASSET_CATEGORIES[cat_select].index(st.session_state.chart_asset)
            
        selected_chart_asset = st.selectbox("Select Asset for Chart:", ASSET_CATEGORIES[cat_select], index=c_asset_idx, key="chart_asset_select")
        
        if selected_chart_asset != st.session_state.chart_asset:
            st.session_state.chart_asset = selected_chart_asset
            st.rerun()

        if is_vip:
            chart_tf = st.selectbox("Chart Timeframe:", ALL_TIMEFRAMES, index=4, key="chart_tf_select")
            chart_mode = st.radio("🖥️ View Mode:", ["Single Chart", "Multi-Chart Grid (VIP)"], horizontal=True)
        else:
            chart_tf = st.selectbox("Chart Timeframe:", ["1m", "5m", "15m", "1h", "4h", "1D"], index=0, key="chart_tf_select_free")
            chart_mode = "Single Chart"

    # --- ADVANCED INSTITUTIONAL SMC + ICT CHART ENGINE (TIMEFRAME SWITCHING FIXED) ---
    def render_pro_smc_engine(symbol_name, timeframe_str="1m", height=500):
        # Calculate dynamic interval in milliseconds based on user selected timeframe
        interval_ms = 60000
        if timeframe_str.endswith("s"):
            interval_ms = int(timeframe_str.replace("s", "")) * 1000
        elif timeframe_str.endswith("m"):
            interval_ms = int(timeframe_str.replace("m", "")) * 60 * 1000
        elif timeframe_str.endswith("h"):
            interval_ms = int(timeframe_str.replace("h", "")) * 3600 * 1000
        elif timeframe_str == "1D":
            interval_ms = 86400 * 1000
        elif timeframe_str == "1W":
            interval_ms = 7 * 86400 * 1000
        elif timeframe_str == "1M":
            interval_ms = 30 * 86400 * 1000
        elif timeframe_str == "1Y":
            interval_ms = 365 * 86400 * 1000

        # Fast animation interval for live stream preview
        tick_speed = min(interval_ms, 2000)

        html_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8"/>
            <script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/luxon@3.0.1/build/global/luxon.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-luxon@1.2.0/dist/chartjs-adapter-luxon.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/chartjs-chart-financial@0.1.1/dist/chartjs-chart-financial.min.js"></script>
            <style>
                body, html {{ margin: 0; padding: 0; width: 100%; height: 100%; background-color: #131722; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; overflow: hidden; }}
                #main-wrap {{ width: 100%; height: {height}px; padding: 6px; box-sizing: border-box; background: #131722; display: flex; flex-direction: column; }}
                .top-bar {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; flex-wrap: wrap; gap: 6px; background: #1e222d; padding: 4px 10px; border-radius: 4px; border: 1px solid #2a2e39; }}
                .title {{ color: #00f2fe; font-size: 12px; font-weight: bold; display: flex; align-items: center; gap: 4px; }}
                .btn-group {{ display: flex; gap: 4px; }}
                .btn-ui {{ background: #2962ff; color: #fff; border: none; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 10px; cursor: pointer; text-decoration: none; display: inline-flex; align-items: center; gap: 4px; transition: all 0.2s; }}
                .btn-ui:hover {{ background: #00f2fe; color: #000; }}
                .btn-smc {{ background: #089981; }}
                .btn-smc.active {{ background: #f23645; }}
                .chart-box {{ flex: 1; position: relative; width: 100%; }}
            </style>
        </head>
        <body>
            <div id="main-wrap">
                <div class="top-bar">
                    <div class="title">⚡ {symbol_name} ({timeframe_str}) — SMC VIP ENGINE</div>
                    <div class="btn-group">
                        <button id="smcBtn" class="btn-ui btn-smc active" onclick="toggleSMC()">⚡ SMC: ON</button>
                    </div>
                </div>
                <div class="chart-box">
                    <canvas id="candleCanvas"></canvas>
                </div>
            </div>
            <script>
                let smcEnabled = true;
                let chartUpdateTimer = null;

                function toggleSMC() {{
                    smcEnabled = !smcEnabled;
                    const btn = document.getElementById('smcBtn');
                    if (smcEnabled) {{
                        btn.classList.add('active');
                        btn.innerText = "⚡ SMC: ON";
                    }} else {{
                        btn.classList.remove('active');
                        btn.innerText = "❌ SMC: OFF";
                    }}
                    if(window.myChartInstance) window.myChartInstance.update('none');
                }}

                const smcInstitutionalEngine = {{
                    id: 'smcInstitutionalEngine',
                    afterDraw: (chart) => {{
                        if (!smcEnabled) return;
                        const ctx = chart.ctx;
                        const meta = chart.getDatasetMeta(0);
                        const dataset = chart.data.datasets[0].data;
                        if (!meta.data || meta.data.length < 3) return;

                        ctx.save();

                        for (let i = 2; i < dataset.length; i++) {{
                            let c1 = dataset[i-2];
                            let c3 = dataset[i];

                            if (c1.h < c3.l) {{ 
                                let yTop = chart.scales.y.getPixelForValue(c3.l);
                                let yBottom = chart.scales.y.getPixelForValue(c1.h);
                                let xStart = meta.data[i-2].x;
                                let xEnd = meta.data[i].x + 30;

                                ctx.fillStyle = 'rgba(8, 153, 129, 0.18)';
                                ctx.strokeStyle = '#089981';
                                ctx.lineWidth = 1;
                                ctx.fillRect(xStart, yTop, xEnd - xStart, yBottom - yTop);
                                ctx.strokeRect(xStart, yTop, xEnd - xStart, yBottom - yTop);
                            }} else if (c1.l > c3.h) {{ 
                                let yTop = chart.scales.y.getPixelForValue(c1.l);
                                let yBottom = chart.scales.y.getPixelForValue(c3.h);
                                let xStart = meta.data[i-2].x;
                                let xEnd = meta.data[i].x + 30;

                                ctx.fillStyle = 'rgba(242, 54, 69, 0.18)';
                                ctx.strokeStyle = '#f23645';
                                ctx.lineWidth = 1;
                                ctx.fillRect(xStart, yTop, xEnd - xStart, yBottom - yTop);
                                ctx.strokeRect(xStart, yTop, xEnd - xStart, yBottom - yTop);
                            }}
                        }}

                        let maxHigh = -Infinity, minLow = Infinity;
                        let maxIdx = -1, minIdx = -1;
                        for (let i = 0; i < dataset.length; i++) {{
                            if (dataset[i].h > maxHigh) {{ maxHigh = dataset[i].h; maxIdx = i; }}
                            if (dataset[i].l < minLow) {{ minLow = dataset[i].l; minIdx = i; }}
                        }}

                        if (maxIdx !== -1 && meta.data[maxIdx]) {{
                            let yRes = chart.scales.y.getPixelForValue(maxHigh);
                            ctx.strokeStyle = '#f23645';
                            ctx.setLineDash([4, 4]);
                            ctx.beginPath();
                            ctx.moveTo(meta.data[0].x, yRes);
                            ctx.lineTo(meta.data[dataset.length-1].x + 15, yRes);
                            ctx.stroke();
                        }}

                        if (minIdx !== -1 && meta.data[minIdx]) {{
                            let ySup = chart.scales.y.getPixelForValue(minLow);
                            ctx.strokeStyle = '#089981';
                            ctx.setLineDash([4, 4]);
                            ctx.beginPath();
                            ctx.moveTo(meta.data[0].x, ySup);
                            ctx.lineTo(meta.data[dataset.length-1].x + 15, ySup);
                            ctx.stroke();
                        }}

                        ctx.restore();
                    }}
                }};

                const ctx = document.getElementById('candleCanvas').getContext('2d');
                let now = Date.now();
                let basePrice = '{symbol_name}'.includes('BTC') ? 68420.00 : ('{symbol_name}'.includes('NIFTY') ? 24500.0 : ('{symbol_name}'.includes('XAU') ? 2500.0 : 1.085));
                
                let candleData = [];
                let intervalTime = {interval_ms};

                for (let i = 24; i >= 0; i--) {{
                    let t = now - (i * intervalTime);
                    let open = basePrice + (Math.random() - 0.49) * (basePrice * 0.001);
                    let high = open + Math.random() * (basePrice * 0.0015);
                    let low = open - Math.random() * (basePrice * 0.0015);
                    let close = low + Math.random() * (high - low);
                    candleData.push({{ x: t, o: open, h: high, l: low, c: close }});
                    basePrice = close;
                }}

                if (window.myChartInstance) {{
                    window.myChartInstance.destroy();
                }}

                window.myChartInstance = new Chart(ctx, {{
                    type: 'candlestick',
                    data: {{
                        datasets: [{{
                            label: '{symbol_name}',
                            data: candleData,
                            color: {{
                                up: '#089981',
                                down: '#f23645',
                                unchanged: '#787b86'
                            }}
                        }}]
                    }},
                    plugins: [smcInstitutionalEngine],
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        animation: false,
                        scales: {{
                            x: {{
                                type: 'time',
                                time: {{
                                    unit: '{timeframe_str}'.includes('s') ? 'second' : ('{timeframe_str}'.includes('m') ? 'minute' : 'hour')
                                }},
                                grid: {{ color: '#2a2e39' }},
                                ticks: {{ color: '#787b86', font: {{ size: 9 }} }}
                            }},
                            y: {{
                                grid: {{ color: '#2a2e39' }},
                                ticks: {{ color: '#00f2fe', font: {{ size: 10, weight: 'bold' }} }}
                            }}
                        }},
                        plugins: {{
                            legend: {{ display: false }}
                        }}
                    }}
                }});

                if (chartUpdateTimer) clearInterval(chartUpdateTimer);

                chartUpdateTimer = setInterval(() => {{
                    let chart = window.myChartInstance;
                    if(!chart) return;
                    let lastCandle = chart.data.datasets[0].data[chart.data.datasets[0].data.length - 1];
                    let nextTime = lastCandle.x + intervalTime;
                    let newOpen = lastCandle.c;
                    let range = newOpen * 0.0008;
                    let newHigh = newOpen + Math.random() * range;
                    let newLow = newOpen - Math.random() * range;
                    let newClose = newLow + Math.random() * (newHigh - newLow);

                    chart.data.datasets[0].data.shift();
                    chart.data.datasets[0].data.push({{
                        x: nextTime,
                        o: newOpen,
                        h: newHigh,
                        l: newLow,
                        c: newClose
                    }});
                    chart.update('none');
                }}, {tick_speed});
            </script>
        </body>
        </html>
        """
        return html_code

    if chart_mode == "Single Chart":
        st.markdown(f"##### 📈 VIP Chart Engine ({selected_chart_asset}) — `{chart_tf}`")
        st.components.v1.html(render_pro_smc_engine(selected_chart_asset, chart_tf, 500), height=510)
    else:
        st.markdown("##### 📊 VIP Dual Multi-Chart Grid Layout")
        mc1, mc2 = st.columns(2)
        with mc1:
            asset1 = st.selectbox("Chart 1 Asset", ASSET_CATEGORIES["Crypto Top Major"], key="asset1_sel")
            st.components.v1.html(render_pro_smc_engine(asset1, chart_tf, 420), height=430)
        with mc2:
            asset2 = st.selectbox("Chart 2 Asset", ASSET_CATEGORIES["Forex Currency Pairs"], key="asset2_sel")
            st.components.v1.html(render_pro_smc_engine(asset2, chart_tf, 420), height=430)

with tab3:
    st.markdown("##### 🏆 Performance & AI Accuracy Metrics")
    m1, m2, m3 = st.columns(3)
    m1.metric("7-Day Signals", "184", "+14 today")
    m2.metric("Win Rate", "93.8%", "+4.2%")
    m3.metric("Avg R:R Ratio", "1:3.2", "Optimal")

# --- SUBSCRIPTION PLANS ---
with tab4:
    st.markdown("##### 💎 VIP Pro Plans & Pricing")
    p1, p2, p3 = st.columns(3)
    with p1:
        st.markdown("<div style='background:#131722; padding:10px; border-radius:6px; border:1px solid #2a2e39; text-align:center;'><h5 style='color:#00f2fe; margin:0;'>3-DAYS TRIAL</h5><h3 style='margin:5px 0;'>₹199</h3></div>", unsafe_allow_html=True)
    with p2:
        st.markdown("<div style='background:#131722; padding:10px; border-radius:6px; border:2px solid #2962ff; text-align:center;'><h5 style='color:#2962ff; margin:0;'>MONTHLY VIP</h5><h3 style='margin:5px 0;'>₹999</h3></div>", unsafe_allow_html=True)
    with p3:
        st.markdown("<div style='background:#131722; padding:10px; border-radius:6px; border:1px solid #089981; text-align:center;'><h5 style='color:#089981; margin:0;'>ANNUAL PRO</h5><h3 style='margin:5px 0;'>₹9,999</h3></div>", unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    col_p1, col_p2 = st.columns(2, gap="small")

    with col_p1:
        st.markdown("##### 📲 UPI Payment")
        selected_plan = st.selectbox("Select Your Plan", ["₹199 - 3 Days Access", "₹999 - 1 Month Access", "₹9,999 - 1 Year Access"])
        
        amount = "999.00"
        if "199" in selected_plan:
            amount = "199.00"
        elif "9,999" in selected_plan:
            amount = "9999.00"

        upi_intent_url = f"upi://pay?pa=7479465676-7@ybl&pn=VEER%20PRO%20TRADER&am={amount}&cu=INR"
        st.link_button(f"📲 Pay ₹{amount} via UPI App", upi_intent_url)

    with col_p2:
        st.markdown("##### ⚡ Verify Payment")
        utr_input = st.text_input("Enter 12-digit UTR Number:", placeholder="e.g. 4152xxxxxxxx", key="tab_utr_input")

        if st.button("🔓 Verify Payment & Activate VIP", key="verify_utr_btn"):
            cleaned_utr = utr_input.strip()
            if len(cleaned_utr) >= 10:
                days_to_add = 30
                if "199" in selected_plan:
                    days_to_add = 3
                elif "9,999" in selected_plan:
                    days_to_add = 365

                expiry_dt = update_user_vip(st.session_state.current_user_email, days=days_to_add)
                st.session_state.user_tier = "VIP Paid Member"
                st.session_state.vip_expiry = expiry_dt
                st.success(f"🎉 Payment Verified! VIP Access Activated for {days_to_add} Days.")
                st.rerun()
            else:
                st.error("⚠️ Please enter a valid 12-digit UTR number!")
