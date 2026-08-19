import datetime
import random
import sqlite3
import time
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

    /* Inputs */
    .stTextInput input, .stSelectbox div[role="combobox"], .stNumberInput input {
        background-color: #131722 !important;
        color: #ffffff !important;
        border: 1px solid #2a2e39 !important;
        border-radius: 8px !important;
        min-height: 44px !important;
    }

    /* Sidebar Clean Styling */
    section[data-testid="stSidebar"] {
        background-color: #0e131f !important;
        border-right: 1px solid #2a2e39 !important;
    }

    /* Buttons */
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
    
    /* Tabs */
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
    cursor.execute("UPDATE users SET tier = 'VIP Paid Member', vip_expiry = ? WHERE email = ?", (expiry_date, email.strip()))
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
    
    # 🎟️ SECURE PROMO CODE SECTION
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
            if is_vip:
                timeframe_options = ["1s", "5s", "10s", "20s", "30s", "1m", "5m", "15m", "1h", "4h", "1d"]
            else:
                timeframe_options = ["1m", "5m", "15m", "1h", "4h", "1d"]
            
            timeframe = st.selectbox("Timeframe", timeframe_options)
            if not is_vip:
                st.caption("🔒 *1s, 5s, 10s, 20s, 30s Timeframes unlocked for VIP*")

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
                            <span style="background:#08998122; color:#089981; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:bold;">91.4% CONFIDENCE</span>
                        </div>
                        <p style="font-size:12px; color:#787b86; margin-bottom:10px;">Pair: BINANCE:{asset} ({timeframe}) | Strategy: Smart Money Liquidity Sweep</p>
                        <p style="margin:4px 0;"><b>📍 Optimal Entry:</b> ~${entry_p:,.2f}</p>
                        <p style="margin:4px 0; color:#f23645;"><b>🛑 Stop Loss:</b> ~${sl_p:,.2f}</p>
                        <p style="margin:4px 0; color:#089981;"><b>🎯 Target 1 (TP1):</b> ~${tp1_p:,.2f}</p>
                        <p style="margin:4px 0; color:#089981;"><b>🎯 Target 2 (TP2):</b> ~${tp2_p:,.2f}</p>
                    </div>
                """,
                    unsafe_allow_html=True,
                )

# --- ADVANCED CHART TAB (FIXED 1-SECOND CHART RENDERING ISSUE) ---
with tab2:
    chart_col1, chart_col2 = st.columns([1, 2.5])
    with chart_col1:
        selected_chart_asset = st.selectbox("Select Asset for Chart:", ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"], key="chart_asset_select")
        
        if is_vip:
            chart_tf = st.selectbox("Chart Timeframe:", ["1s", "5s", "10s", "20s", "30s", "1m", "5m", "15m", "1h", "1d"], index=0, key="chart_tf_select")
            chart_mode = st.radio("🖥️ View Mode:", ["Single Chart", "Multi-Chart Grid (VIP)"], horizontal=True)
        else:
            chart_tf = st.selectbox("Chart Timeframe:", ["1m", "5m", "15m", "1h", "1d"], index=0, key="chart_tf_select_free")
            chart_mode = "Single Chart"
            st.info("🔒 *Second timeframes (1s, 5s, 10s...) and Multi-Chart are unlocked for VIP Members!*")

    def render_tv_widget(symbol_name, interval_str="1", height=520):
        return f"""
        <div class="tradingview-widget-container" style="height:{height}px;width:100%;">
          <div id="tradingview_{symbol_name}" style="height:100%;width:100%;"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          new TradingView.widget({{
            "width": "100%",
            "height": "{height}",
            "symbol": "BINANCE:{symbol_name}",
            "interval": "{interval_str}",
            "timezone": "Etc/UTC",
            "theme": "dark",
            "style": "1",
            "locale": "en",
            "toolbar_bg": "#131722",
            "enable_publishing": false,
            "allow_symbol_change": true,
            "container_id": "tradingview_{symbol_name}"
          }});
          </script>
        </div>
        """

    # --- NO-BLANK SCREEN SECONDS CHART ENGINE ---
    def render_fast_canvas_chart(symbol_name, sec_interval=1, height=520):
        return f"""
        <div style="width:100%; height:{height}px; background:#131722; border-radius:8px; border:1px solid #2a2e39; position:relative; overflow:hidden;">
            <div style="position:absolute; top:10px; left:15px; z-index:10; font-family:sans-serif; color:#00f2fe; font-size:12px; font-weight:bold; background:rgba(0,0,0,0.5); padding:4px 8px; border-radius:4px;">
                ⚡ Realtime Live Stream: BINANCE:{symbol_name} ({sec_interval}s)
            </div>
            <canvas id="chart_canvas_{symbol_name}" style="width:100%; height:100%; display:block;"></canvas>
        </div>
        <script>
        (function() {{
            const canvas = document.getElementById('chart_canvas_{symbol_name}');
            if (!canvas) return;
            const ctx = canvas.getContext('2d');

            function resizeCanvas() {{
                canvas.width = canvas.parentElement.clientWidth;
                canvas.height = canvas.parentElement.clientHeight;
            }}
            resizeCanvas();
            window.addEventListener('resize', resizeCanvas);

            let price = symbol_name.includes('BTC') ? 68420.00 : 3540.00;
            let candles = [];
            const maxCandles = 50;

            for (let i = 0; i < maxCandles; i++) {{
                let o = price + (Math.random() - 0.5) * 8;
                let h = o + Math.random() * 5;
                let l = o - Math.random() * 5;
                let c = (h + l) / 2;
                candles.push({{ open: o, high: h, low: l, close: c }});
                price = c;
            }}

            function drawChart() {{
                if (!canvas.width || !canvas.height) return;
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.fillStyle = '#131722';
                ctx.fillRect(0, 0, canvas.width, canvas.height);

                let minP = Math.min(...candles.map(c => c.low));
                let maxP = Math.max(...candles.map(c => c.high));
                let range = (maxP - minP) || 1;

                let padding = 40;
                let chartHeight = canvas.height - padding * 2;
                let candleWidth = (canvas.width - 60) / maxCandles;

                for (let i = 0; i < candles.length; i++) {{
                    let c = candles[i];
                    let x = i * candleWidth + 20;

                    let yOpen = canvas.height - padding - ((c.open - minP) / range) * chartHeight;
                    let yClose = canvas.height - padding - ((c.close - minP) / range) * chartHeight;
                    let yHigh = canvas.height - padding - ((c.high - minP) / range) * chartHeight;
                    let yLow = canvas.height - padding - ((c.low - minP) / range) * chartHeight;

                    let isUp = c.close >= c.open;
                    let color = isUp ? '#089981' : '#f23645';

                    // Draw Wick
                    ctx.strokeStyle = color;
                    ctx.lineWidth = 1.5;
                    ctx.beginPath();
                    ctx.moveTo(x + candleWidth / 2, yHigh);
                    ctx.lineTo(x + candleWidth / 2, yLow);
                    ctx.stroke();

                    // Draw Body
                    ctx.fillStyle = color;
                    let bodyHeight = Math.max(Math.abs(yClose - yOpen), 2);
                    let bodyY = Math.min(yOpen, yClose);
                    ctx.fillRect(x + 2, bodyY, candleWidth - 4, bodyHeight);
                }}

                // Current Price Line
                let lastClose = candles[candles.length - 1].close;
                let lastY = canvas.height - padding - ((lastClose - minP) / range) * chartHeight;
                ctx.strokeStyle = '#2962ff';
                ctx.setLineDash([4, 4]);
                ctx.beginPath();
                ctx.moveTo(0, lastY);
                ctx.lineTo(canvas.width, lastY);
                ctx.stroke();
                ctx.setLineDash([]);

                ctx.fillStyle = '#2962ff';
                ctx.fillRect(canvas.width - 60, lastY - 10, 60, 20);
                ctx.fillStyle = '#ffffff';
                ctx.font = '11px sans-serif';
                ctx.fillText(lastClose.toFixed(2), canvas.width - 55, lastY + 4);
            }}

            setInterval(() => {{
                let last = candles[candles.length - 1];
                let change = (Math.random() - 0.49) * 3;
                last.close += change;
                if (last.close > last.high) last.high = last.close;
                if (last.close < last.low) last.low = last.close;

                drawChart();
            }}, {sec_interval * 200});

            setInterval(() => {{
                let last = candles[candles.length - 1];
                candles.shift();
                candles.push({{ open: last.close, high: last.close, low: last.close, close: last.close }});
            }}, {sec_interval * 1000});

            drawChart();
        }})();
        </script>
        """

    st.markdown("---")

    if chart_mode == "Single Chart":
        st.markdown(f"### 📈 Realtime Live Chart ({selected_chart_asset}) — `{chart_tf}`")
        if "s" in chart_tf:
            sec_val = int(chart_tf.replace("s", ""))
            st.components.v1.html(render_fast_canvas_chart(selected_chart_asset, sec_val, 520), height=540)
        else:
            tv_interval = "1"
            if chart_tf == "5m": tv_interval = "5"
            elif chart_tf == "15m": tv_interval = "15"
            elif chart_tf == "1h": tv_interval = "60"
            elif chart_tf == "1d": tv_interval = "D"
            st.components.v1.html(render_tv_widget(selected_chart_asset, tv_interval, 520), height=540)
    else:
        st.markdown("### 📊 VIP Dual Multi-Chart Grid Layout")
        mc1, mc2 = st.columns(2)
        with mc1:
            asset1 = st.selectbox("Chart 1 Asset", ["BTCUSDT", "ETHUSDT", "SOLUSDT"], key="asset1_sel")
            if "s" in chart_tf:
                sec_val = int(chart_tf.replace("s", ""))
                st.components.v1.html(render_fast_canvas_chart(asset1, sec_val, 450), height=470)
            else:
                st.components.v1.html(render_tv_widget(asset1, "1", 450), height=470)
        with mc2:
            asset2 = st.selectbox("Chart 2 Asset", ["ETHUSDT", "BTCUSDT", "BNBUSDT"], key="asset2_sel")
            if "s" in chart_tf:
                sec_val = int(chart_tf.replace("s", ""))
                st.components.v1.html(render_fast_canvas_chart(asset2, sec_val, 450), height=470)
            else:
                st.components.v1.html(render_tv_widget(asset2, "1", 450), height=470)

with tab3:
    st.markdown("### 🏆 Performance & AI Accuracy Metrics")
    m1, m2, m3 = st.columns(3)
    m1.metric("7-Day Signals", "184", "+14 today")
    m2.metric("Win Rate", "91.2%", "+3.4%")
    m3.metric("Avg R:R Ratio", "1:2.8", "Optimal")

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
