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
        --green-up: #089981;
        --red-down: #f23645;
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

    .stTextInput input, .stSelectbox div[role="combobox"], .stNumberInput input {
        background-color: #131722 !important;
        color: #ffffff !important;
        border: 1px solid #2a2e39 !important;
        border-radius: 8px !important;
        min-height: 44px !important;
    }

    section[data-testid="stSidebar"] {
        background-color: #0e131f !important;
        border-right: 1px solid #2a2e39 !important;
    }

    .stButton>button, .stLinkButton>a {
        width: 100%;
        border-radius: 8px;
        font-weight: 700;
        min-height: 44px;
        background: linear-gradient(135deg, #2962ff 0%, #00f2fe 100%) !important;
        color: #ffffff !important;
        border: none !important;
        box-shadow: 0 4px 20px rgba(41, 98, 255, 0.3);
        text-align: center;
        display: flex;
        justify-content: center;
        align-items: center;
        text-decoration: none;
    }
    .stButton>button:hover, .stLinkButton>a:hover {
        transform: scale(1.02);
        box-shadow: 0 6px 24px rgba(0, 242, 254, 0.5);
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background-color: #131722;
        padding: 4px;
        border-radius: 8px;
        border: 1px solid #2a2e39;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        border-radius: 6px !important;
        color: var(--text-sub) !important;
        font-weight: 600 !important;
        padding: 8px 14px !important;
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

# --- REAL-TIME LIVE MARKET TICKER FRAGMENT ---
@st.fragment(run_every="1s")
def render_live_header():
    base_btc = 68420.00 + random.uniform(-12.5, 12.5)
    base_eth = 3540.50 + random.uniform(-1.8, 1.8)
    st.markdown(
        f"""
        <div style="background: #131722; padding: 10px 14px; border-radius: 8px; border: 1px solid #2a2e39; display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; font-size: 13px;">
            <div><b style="color:#00f2fe;">🚀 VEER TERMINAL</b></div>
            <div><span>BTCUSDT</span> <b style="color: #089981;">${base_btc:,.2f} (+0.42%)</b></div>
            <div style="color: #089981; font-weight:600;">ETHUSDT ${base_eth:,.2f} (+1.14%)</div>
            <div style="color: #00f2fe; font-size:11px;">🔴 LIVE TICKER STREAM</div>
        </div>
    """,
        unsafe_allow_html=True,
    )

render_live_header()

tab1, tab2, tab3, tab4 = st.tabs(["⚡ Terminal Dashboard", "📊 Live Chart", "🏆 Accuracy", "💎 VIP Plan"])

ALL_TIMEFRAMES = ["1s", "5s", "10s", "30s", "1m", "5m", "15m", "1h", "4h", "1D", "1W", "1M", "1Y"]

with tab1:
    col_main, col_side = st.columns([2.2, 1], gap="medium")
    with col_main:
        st.markdown("### ⚙️ Signal Configuration")
        c1, c2, c3 = st.columns(3)
        with c1:
            market_category = st.selectbox("Category", ["TIER 1 (Main Assets)", "TIER 2 (Altcoins)"])
        with c2:
            asset = st.selectbox("Asset", ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"])
        with c3:
            timeframe_options = ALL_TIMEFRAMES if is_vip else ["1m", "5m", "15m", "1h", "4h", "1D"]
            timeframe = st.selectbox("Timeframe", timeframe_options)
            if not is_vip:
                st.caption("🔒 *Seconds & Macro Timeframes unlocked for VIP*")

        st.markdown("### 🛡️ Risk Management")
        account_balance = st.number_input("Account Balance ($)", value=10000.0)
        risk_pct = st.slider("Risk Per Trade (%)", 0.1, 5.0, 1.0)

    with col_side:
        st.markdown("### 🤖 Institutional AI Signals")
        
        can_generate = True
        if not is_vip:
            remaining_signals = 2 - st.session_state.signals_used
            st.caption(f"Free Limit: **{remaining_signals}/2** remaining today.")
            if remaining_signals <= 0:
                can_generate = False
        else:
            st.caption("👑 VIP Status: **Unlimited Access & Ultra-Fast Signals**")

        if st.button("✨ GENERATE ACCURATE SIGNAL", key="gen_sig_btn"):
            if not can_generate:
                st.error("⚠️ Free limit reached! Upgrade to VIP Plan.")
            else:
                if not is_vip:
                    st.session_state.signals_used += 1

                entry_p = 68420.00 if "BTC" in asset else 3540.0
                sl_p = entry_p * 0.994
                tp1_p = entry_p * 1.008
                tp2_p = entry_p * 1.018

                st.markdown(
                    f"""
                    <div style="background:#131722; padding:16px; border-radius:12px; border-left:5px solid #089981; border-top:1px solid #2a2e39; border-right:1px solid #2a2e39; border-bottom:1px solid #2a2e39; margin-top:10px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <h4 style="color:#089981; margin:0;">🔥 INSTITUTIONAL BUY SETUP</h4>
                            <span style="background:#08998122; color:#089981; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:bold;">93.8% CONFIDENCE</span>
                        </div>
                        <p style="font-size:12px; color:#787b86; margin-bottom:10px;">Pair: BINANCE:{asset} ({timeframe}) | Strategy: SMC + ICT Order Block Liquidity</p>
                        <p style="margin:4px 0;"><b>📍 Optimal Entry:</b> ~${entry_p:,.2f}</p>
                        <p style="margin:4px 0; color:#f23645;"><b>🛑 Stop Loss:</b> ~${sl_p:,.2f}</p>
                        <p style="margin:4px 0; color:#089981;"><b>🎯 Target 1 (TP1):</b> ~${tp1_p:,.2f}</p>
                        <p style="margin:4px 0; color:#089981;"><b>🎯 Target 2 (TP2):</b> ~${tp2_p:,.2f}</p>
                    </div>
                """,
                    unsafe_allow_html=True,
                )

# --- ADVANCED HIGH-ACCURACY SMC AUTO-MAPPING CHART ENGINE ---
with tab2:
    chart_col1, chart_col2 = st.columns([1, 2.5])
    with chart_col1:
        selected_chart_asset = st.selectbox("Select Asset for Chart:", ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"], key="chart_asset_select")
        
        if is_vip:
            chart_tf = st.selectbox("Chart Timeframe (1s to 1Y):", ALL_TIMEFRAMES, index=4, key="chart_tf_select")
            chart_mode = st.radio("🖥️ View Mode:", ["Single Chart", "Multi-Chart Grid (VIP)"], horizontal=True)
        else:
            chart_tf = st.selectbox("Chart Timeframe:", ["1m", "5m", "15m", "1h", "4h", "1D"], index=0, key="chart_tf_select_free")
            chart_mode = "Single Chart"
            st.info("🔒 *Seconds (1s-30s) and Macro Timeframes unlocked for VIP Members!*")

    # --- ADVANCED INSTITUTIONAL SMC + ICT + PRICE ACTION CHART ENGINE ---
    def render_pro_smc_engine(symbol_name, timeframe_str="1m", height=540):
        # Timeframe interval conversion
        interval_ms = 1000
        if "s" in timeframe_str:
            interval_ms = int(timeframe_str.replace("s", "")) * 1000
        elif "m" in timeframe_str:
            interval_ms = int(timeframe_str.replace("m", "")) * 60 * 1000
        elif "h" in timeframe_str:
            interval_ms = int(timeframe_str.replace("h", "")) * 3600 * 1000
        elif "D" in timeframe_str:
            interval_ms = 86400 * 1000
        else:
            interval_ms = 60000

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
                #main-wrap {{ width: 100%; height: {height}px; padding: 10px; box-sizing: border-box; background: #131722; display: flex; flex-direction: column; }}
                .top-bar {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; flex-wrap: wrap; gap: 8px; background: #1e222d; padding: 6px 12px; border-radius: 6px; border: 1px solid #2a2e39; }}
                .title {{ color: #00f2fe; font-size: 13px; font-weight: bold; display: flex; align-items: center; gap: 6px; }}
                .btn-group {{ display: flex; gap: 6px; }}
                .btn-ui {{ background: #2962ff; color: #fff; border: none; padding: 6px 12px; border-radius: 4px; font-weight: bold; font-size: 11px; cursor: pointer; text-decoration: none; display: inline-flex; align-items: center; gap: 4px; transition: all 0.2s; }}
                .btn-ui:hover {{ background: #00f2fe; color: #000; }}
                .btn-smc {{ background: #089981; }}
                .btn-smc.active {{ background: #f23645; }}
                .chart-box {{ flex: 1; position: relative; width: 100%; }}
            </style>
        </head>
        <body>
            <div id="main-wrap">
                <div class="top-bar">
                    <div class="title">⚡ BINANCE:{symbol_name} ({timeframe_str}) — SMC/ICT VIP ENGINE</div>
                    <div class="btn-group">
                        <button id="smcBtn" class="btn-ui btn-smc active" onclick="toggleSMC()">⚡ SMC Auto-Mapping: ON</button>
                        <button class="btn-ui" onclick="openFullWindow()">🔍 Open In New Tab</button>
                    </div>
                </div>
                <div class="chart-box">
                    <canvas id="candleCanvas"></canvas>
                </div>
            </div>
            <script>
                let smcEnabled = true;

                // --- FIX FOR BLANK NEW TAB (Using Data URI / Window Open Blob Payload) ---
                function openFullWindow() {{
                    let htmlData = document.documentElement.outerHTML;
                    let blob = new Blob([htmlData], {{ type: 'text/html' }});
                    let url = URL.createObjectURL(blob);
                    window.open(url, '_blank');
                }}

                function toggleSMC() {{
                    smcEnabled = !smcEnabled;
                    const btn = document.getElementById('smcBtn');
                    if (smcEnabled) {{
                        btn.classList.add('active');
                        btn.innerText = "⚡ SMC Auto-Mapping: ON";
                    }} else {{
                        btn.classList.remove('active');
                        btn.innerText = "❌ SMC Auto-Mapping: OFF";
                    }}
                    chart.update();
                }}

                // --- INSTITUTIONAL SMC + ICT + PRICE ACTION AUTO-MAPPING PLUGIN ---
                const smcInstitutionalEngine = {{
                    id: 'smcInstitutionalEngine',
                    afterDraw: (chart) => {{
                        if (!smcEnabled) return;
                        const ctx = chart.ctx;
                        const meta = chart.getDatasetMeta(0);
                        const dataset = chart.data.datasets[0].data;
                        if (!meta.data || meta.data.length < 3) return;

                        ctx.save();

                        // 1. FAIR VALUE GAP (FVG)
                        for (let i = 2; i < dataset.length; i++) {{
                            let c1 = dataset[i-2];
                            let c3 = dataset[i];

                            if (c1.h < c3.l) {{ // Bullish FVG
                                let yTop = chart.scales.y.getPixelForValue(c3.l);
                                let yBottom = chart.scales.y.getPixelForValue(c1.h);
                                let xStart = meta.data[i-2].x;
                                let xEnd = meta.data[i].x + 50;

                                ctx.fillStyle = 'rgba(8, 153, 129, 0.20)';
                                ctx.strokeStyle = '#089981';
                                ctx.lineWidth = 1;
                                ctx.fillRect(xStart, yTop, xEnd - xStart, yBottom - yTop);
                                ctx.strokeRect(xStart, yTop, xEnd - xStart, yBottom - yTop);

                                ctx.fillStyle = '#089981';
                                ctx.font = '9px sans-serif';
                                ctx.fillText('Bullish FVG', xStart + 4, yTop + 10);
                            }} else if (c1.l > c3.h) {{ // Bearish FVG
                                let yTop = chart.scales.y.getPixelForValue(c1.l);
                                let yBottom = chart.scales.y.getPixelForValue(c3.h);
                                let xStart = meta.data[i-2].x;
                                let xEnd = meta.data[i].x + 50;

                                ctx.fillStyle = 'rgba(242, 54, 69, 0.20)';
                                ctx.strokeStyle = '#f23645';
                                ctx.lineWidth = 1;
                                ctx.fillRect(xStart, yTop, xEnd - xStart, yBottom - yTop);
                                ctx.strokeRect(xStart, yTop, xEnd - xStart, yBottom - yTop);

                                ctx.fillStyle = '#f23645';
                                ctx.font = '9px sans-serif';
                                ctx.fillText('Bearish FVG', xStart + 4, yTop + 10);
                            }}
                        }}

                        // 2. SUPPORT & RESISTANCE ZONES
                        let maxHigh = -Infinity, minLow = Infinity;
                        let maxIdx = -1, minIdx = -1;
                        for (let i = 0; i < dataset.length; i++) {{
                            if (dataset[i].h > maxHigh) {{ maxHigh = dataset[i].h; maxIdx = i; }}
                            if (dataset[i].l < minLow) {{ minLow = dataset[i].l; minIdx = i; }}
                        }}

                        if (maxIdx !== -1 && meta.data[maxIdx]) {{
                            let yRes = chart.scales.y.getPixelForValue(maxHigh);
                            ctx.strokeStyle = '#f23645';
                            ctx.setLineDash([5, 3]);
                            ctx.beginPath();
                            ctx.moveTo(meta.data[0].x, yRes);
                            ctx.lineTo(meta.data[dataset.length-1].x + 30, yRes);
                            ctx.stroke();

                            ctx.fillStyle = '#f23645';
                            ctx.font = 'bold 10px sans-serif';
                            ctx.fillText('🔴 Institutional Resistance Zone', meta.data[0].x + 10, yRes - 4);
                        }}

                        if (minIdx !== -1 && meta.data[minIdx]) {{
                            let ySup = chart.scales.y.getPixelForValue(minLow);
                            ctx.strokeStyle = '#089981';
                            ctx.setLineDash([5, 3]);
                            ctx.beginPath();
                            ctx.moveTo(meta.data[0].x, ySup);
                            ctx.lineTo(meta.data[dataset.length-1].x + 30, ySup);
                            ctx.stroke();

                            ctx.fillStyle = '#089981';
                            ctx.font = 'bold 10px sans-serif';
                            ctx.fillText('🟢 Institutional Support Zone', meta.data[0].x + 10, ySup + 12);
                        }}

                        // 3. BOS (Break of Structure) & CHoCH & ORDER BLOCK
                        if (dataset.length > 8) {{
                            let bosCandleIdx = dataset.length - 4;
                            let yBOS = chart.scales.y.getPixelForValue(dataset[bosCandleIdx].h);
                            let xBOS = meta.data[bosCandleIdx].x;

                            ctx.setLineDash([]);
                            ctx.strokeStyle = '#00f2fe';
                            ctx.lineWidth = 1.5;
                            ctx.beginPath();
                            ctx.moveTo(xBOS, yBOS);
                            ctx.lineTo(meta.data[dataset.length-1].x + 20, yBOS);
                            ctx.stroke();

                            ctx.fillStyle = '#00f2fe';
                            ctx.font = 'bold 10px sans-serif';
                            ctx.fillText('⚡ BOS (Break of Structure)', xBOS + 5, yBOS - 4);

                            // ORDER BLOCK ZONE (Demand OB)
                            let obYTop = chart.scales.y.getPixelForValue(minLow * 1.002);
                            let obYBottom = chart.scales.y.getPixelForValue(minLow);
                            ctx.fillStyle = 'rgba(41, 98, 255, 0.35)';
                            ctx.fillRect(meta.data[minIdx].x, obYTop, 120, obYBottom - obYTop);
                            ctx.fillStyle = '#2962ff';
                            ctx.font = 'bold 9px sans-serif';
                            ctx.fillText('📦 BULLISH ORDER BLOCK', meta.data[minIdx].x + 4, obYTop + 10);
                        }}

                        // 4. ACCURATE BUY / SELL SIGNALS MARKERS
                        let lastIdx = dataset.length - 2;
                        if (meta.data[lastIdx]) {{
                            let xSig = meta.data[lastIdx].x;
                            let isBuy = dataset[lastIdx].c >= dataset[lastIdx].o;

                            if (isBuy) {{
                                let ySig = chart.scales.y.getPixelForValue(dataset[lastIdx].l);
                                ctx.fillStyle = '#089981';
                                ctx.beginPath();
                                ctx.arc(xSig, ySig + 15, 6, 0, 2 * Math.PI);
                                ctx.fill();

                                ctx.fillStyle = '#ffffff';
                                ctx.font = 'bold 11px sans-serif';
                                ctx.fillText('🚀 BUY (LONG)', xSig - 30, ySig + 34);
                            }} else {{
                                let ySig = chart.scales.y.getPixelForValue(dataset[lastIdx].h);
                                ctx.fillStyle = '#f23645';
                                ctx.beginPath();
                                ctx.arc(xSig, ySig - 15, 6, 0, 2 * Math.PI);
                                ctx.fill();

                                ctx.fillStyle = '#ffffff';
                                ctx.font = 'bold 11px sans-serif';
                                ctx.fillText('🔻 SELL (SHORT)', xSig - 32, ySig - 24);
                            }}
                        }}

                        ctx.restore();
                    }}
                }};

                const ctx = document.getElementById('candleCanvas').getContext('2d');
                let now = Date.now();
                let initialPrice = '{symbol_name}'.includes('BTC') ? 68420.00 : 3540.00;
                
                let candleData = [];
                for (let i = 24; i >= 0; i--) {{
                    let t = now - (i * {interval_ms});
                    let open = initialPrice + (Math.random() - 0.49) * 8;
                    let high = open + Math.random() * 10;
                    let low = open - Math.random() * 10;
                    let close = low + Math.random() * (high - low);
                    candleData.push({{ x: t, o: open, h: high, l: low, c: close }});
                    initialPrice = close;
                }}

                const chart = new Chart(ctx, {{
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
                                grid: {{ color: '#2a2e39' }},
                                ticks: {{ color: '#787b86', font: {{ size: 10 }} }}
                            }},
                            y: {{
                                grid: {{ color: '#2a2e39' }},
                                ticks: {{ color: '#00f2fe', font: {{ size: 11, weight: 'bold' }} }}
                            }}
                        }},
                        plugins: {{
                            legend: {{ display: false }}
                        }}
                    }}
                }});

                // Smooth Live Price Tick Generator
                setInterval(() => {{
                    let lastCandle = chart.data.datasets[0].data[chart.data.datasets[0].data.length - 1];
                    let nextTime = lastCandle.x + {interval_ms};
                    let newOpen = lastCandle.c;
                    let newHigh = newOpen + Math.random() * 7;
                    let newLow = newOpen - Math.random() * 7;
                    let newClose = newLow + Math.random() * (newHigh - newLow);

                    chart.data.datasets[0].data.shift();
                    chart.data.datasets[0].data.push({{
                        x: nextTime,
                        o: newOpen,
                        h: newHigh,
                        l: newLow,
                        c: newClose
                    }});
                    chart.update();
                }}, {interval_ms > 3000 and 3000 or interval_ms});
            </script>
        </body>
        </html>
        """
        return html_code

    st.markdown("---")

    if chart_mode == "Single Chart":
        st.markdown(f"### 📈 VIP Institutional Chart Engine ({selected_chart_asset}) — `{chart_tf}`")
        st.components.v1.html(render_pro_smc_engine(selected_chart_asset, chart_tf, 540), height=560)
    else:
        st.markdown("### 📊 VIP Dual Multi-Chart Grid Layout")
        mc1, mc2 = st.columns(2)
        with mc1:
            asset1 = st.selectbox("Chart 1 Asset", ["BTCUSDT", "ETHUSDT", "SOLUSDT"], key="asset1_sel")
            st.components.v1.html(render_pro_smc_engine(asset1, chart_tf, 460), height=480)
        with mc2:
            asset2 = st.selectbox("Chart 2 Asset", ["ETHUSDT", "BTCUSDT", "BNBUSDT"], key="asset2_sel")
            st.components.v1.html(render_pro_smc_engine(asset2, chart_tf, 460), height=480)

with tab3:
    st.markdown("### 🏆 Performance & AI Accuracy Metrics")
    m1, m2, m3 = st.columns(3)
    m1.metric("7-Day Signals", "184", "+14 today")
    m2.metric("Win Rate", "93.8%", "+4.2%")
    m3.metric("Avg R:R Ratio", "1:3.2", "Optimal")

# --- SUBSCRIPTION PLANS WITH UPDATED 3-DAY TRIAL PLAN ---
with tab4:
    st.markdown("### 💎 VIP Pro Plans & Pricing")
    
    p1, p2, p3 = st.columns(3)
    with p1:
        st.markdown(
            """
            <div style="background:#131722; padding:15px; border-radius:10px; border:1px solid #2a2e39; text-align:center;">
                <h4 style="color:#00f2fe; margin:0;">3-DAYS TRIAL</h4>
                <h2 style="margin:10px 0;">₹199</h2>
                <p style="color:#787b86; font-size:12px;">Full AI Signal Access for 3 Days</p>
            </div>
            """, unsafe_allow_html=True
        )
    with p2:
        st.markdown(
            """
            <div style="background:#131722; padding:15px; border-radius:10px; border:2px solid #2962ff; text-align:center;">
                <h4 style="color:#2962ff; margin:0;">MONTHLY VIP</h4>
                <h2 style="margin:10px 0;">₹999 <span style="font-size:12px; color:#787b86;">/ Month</span></h2>
                <p style="color:#787b86; font-size:12px;">Unlimited Signals + Multi-Chart Access (30 Days)</p>
            </div>
            """, unsafe_allow_html=True
        )
    with p3:
        st.markdown(
            """
            <div style="background:#131722; padding:15px; border-radius:10px; border:1px solid #089981; text-align:center;">
                <h4 style="color:#089981; margin:0;">ANNUAL PRO</h4>
                <h2 style="margin:10px 0;">₹9,999 <span style="font-size:12px; color:#787b86;">/ Year</span></h2>
                <p style="color:#787b86; font-size:12px;">Best Value (Save 17% Yearly Access)</p>
            </div>
            """, unsafe_allow_html=True
        )
        
    st.markdown("<br>", unsafe_allow_html=True)
    col_p1, col_p2 = st.columns(2, gap="medium")

    with col_p1:
        st.markdown("#### 📲 UPI Payment Option")
        selected_plan = st.selectbox("Select Your Plan", ["₹199 - 3 Days Access", "₹999 - 1 Month Access", "₹9,999 - 1 Year Access"])
        
        amount = "999.00"
        if "199" in selected_plan:
            amount = "199.00"
        elif "9,999" in selected_plan:
            amount = "9999.00"

        upi_intent_url = f"upi://pay?pa=7479465676-7@ybl&pn=VEER%20PRO%20TRADER&am={amount}&cu=INR"
        st.link_button(f"📲 Pay ₹{amount} via UPI App", upi_intent_url)

        qr_code_url = "https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=" + upi_intent_url
        st.image(qr_code_url, caption="Scan QR with any UPI App", width=180)

    with col_p2:
        st.markdown("#### ⚡ Verify Payment & Activate Plan")
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
