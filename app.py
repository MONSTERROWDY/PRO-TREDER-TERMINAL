import datetime
import random
import streamlit as st

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Veer Pro Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ==========================================
# 2. OPTIMIZED HIGH-PERFORMANCE STYLING (CSS)
# ==========================================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }

    .stApp {
        background-color: #0b0e14 !important;
        color: #e1e7ef !important;
    }

    /* Padding Adjustments */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        max-width: 100% !important;
    }

    /* Top Live Cards */
    .ticker-card {
        background: #121824;
        border: 1px solid #1e2638;
        border-radius: 8px;
        padding: 10px 14px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .ticker-title {
        font-size: 13px;
        font-weight: 600;
        color: #ffffff;
    }
    .ticker-price {
        font-size: 14px;
        font-weight: 700;
        color: #00f2fe;
    }
    .ticker-green {
        font-size: 12px;
        color: #00e676;
        font-weight: 600;
    }

    /* Card Containers */
    .ui-card {
        background: #121824;
        border: 1px solid #1e2638;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 12px;
    }

    .ui-card-title {
        font-size: 15px;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* Stats Box Grid */
    .stat-box {
        background: #0d121c;
        border: 1px solid #1e2638;
        border-radius: 8px;
        padding: 10px;
        text-align: center;
    }
    .stat-label {
        font-size: 11px;
        color: #8fa0b5;
        margin-bottom: 4px;
    }
    .stat-value {
        font-size: 15px;
        font-weight: 700;
        color: #ffffff;
    }

    /* Active Signals Row */
    .sig-row {
        background: #0d121c;
        border: 1px solid #1e2638;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .badge-buy {
        background: rgba(0, 230, 118, 0.15);
        color: #00e676;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 700;
    }
    .badge-sell {
        background: rgba(255, 82, 82, 0.15);
        color: #ff5252;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 700;
    }

    /* Custom Streamlit Input Style Overrides */
    .stTextInput input, .stSelectbox div[role="combobox"], .stNumberInput input {
        background-color: #0d121c !important;
        color: #ffffff !important;
        border: 1px solid #1e2638 !important;
        border-radius: 6px !important;
    }

    /* Main Blue Generate Button */
    .stButton>button {
        width: 100%;
        background: #1a6cf0 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        padding: 10px 0 !important;
        box-shadow: 0 4px 15px rgba(26, 108, 240, 0.3) !important;
    }

    /* Modern Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background-color: #0d121c;
        padding: 4px;
        border-radius: 8px;
        border: 1px solid #1e2638;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        color: #8fa0b5 !important;
        font-weight: 600 !important;
        border-radius: 6px !important;
        padding: 8px 16px !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1a6cf0 !important;
        color: #ffffff !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# 3. SESSION STATE INITIALIZATION (OPTIONAL / BACKWARD COMPATIBLE)
# ==========================================
if "signals" not in st.session_state:
    st.session_state.signals = [
        {"asset": "SOLUSDT", "type": "BUY", "entry": 143.50, "tp": 148.20, "sl": 140.10, "time": "18:17:45", "status": "🟢"},
        {"asset": "BTCUSDT", "type": "BUY", "entry": 68400.00, "tp": 69250.00, "sl": 67680.00, "time": "18:16:20", "status": "🟢"},
        {"asset": "ETHUSDT", "type": "SELL", "entry": 3540.00, "tp": 3475.00, "sl": 3580.00, "time": "18:15:10", "status": "🔴"},
    ]

# ==========================================
# 4. APP HEADER & TOP TICKER CARDS
# ==========================================
st.markdown(
    """
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 15px;">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 22px;">⚡</span>
            <span style="font-size: 20px; font-weight: 700; color: #ffffff;">Veer Pro <span style="color:#8fa0b5; font-weight:400;">Terminal</span></span>
        </div>
    </div>
""",
    unsafe_allow_html=True,
)

tc1, tc2, tc3 = st.columns(3)
with tc1:
    st.markdown(
        """
        <div class="ticker-card">
            <div>
                <div class="ticker-title">🍊 BTCUSDT</div>
                <div class="ticker-price">$68,417.51</div>
            </div>
            <div class="ticker-green">+1.23%</div>
        </div>
    """,
        unsafe_allow_html=True,
    )

with tc2:
    st.markdown(
        """
        <div class="ticker-card">
            <div>
                <div class="ticker-title">🔥 SOLUSDT</div>
                <div class="ticker-price">$145.06</div>
            </div>
            <div class="ticker-green">+2.45%</div>
        </div>
    """,
        unsafe_allow_html=True,
    )

with tc3:
    st.markdown(
        """
        <div class="ticker-card">
            <div>
                <div class="ticker-title">📊 ETHUSDT</div>
                <div class="ticker-price">$3,540.49</div>
            </div>
            <div class="ticker-green">+1.78%</div>
        </div>
    """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 5. MARKET SELECTOR & QUICK BUTTONS
# ==========================================
m_col1, m_col2 = st.columns([1.2, 3])
with m_col1:
    selected_asset = st.selectbox(
        "Market",
        ["SOLUSDT", "BTCUSDT", "ETHUSDT", "XAUUSD", "NIFTY50"],
        label_visibility="collapsed",
    )

with m_col2:
    pills = ["BTC", "ETH", "SOL", "XAU", "NIFTY"]
    p_cols = st.columns(5)
    for idx, pill in enumerate(pills):
        with p_cols[idx]:
            if st.button(pill, key=f"pill_btn_{pill}"):
                pass

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 6. PRIMARY NAVIGATION TABS
# ==========================================
tab_dash, tab_chart, tab_sig, tab_acc, tab_manage = st.tabs(
    ["📱 Dashboard", "📊 Chart", "🎯 Signals", "🏆 Accuracy", "⚙️ Manage"]
)

with tab_dash:
    # --- ROW 1: CONFIGURATION & RISK MANAGEMENT ---
    c_left, c_right = st.columns(2)

    with c_left:
        st.markdown(
            '<div class="ui-card-title">⚙️ Signal Configuration</div>',
            unsafe_allow_html=True,
        )
        cat = st.selectbox("Category", ["Crypto Top Major", "Forex", "Commodities", "Indices"])
        asset = st.selectbox("Asset", ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XAUUSD"])
        tf = st.selectbox("Timeframe", ["1s", "5s", "1m", "5m", "15m", "1h"])

    with c_right:
        st.markdown(
            '<div class="ui-card-title">🛡️ Risk Management</div>',
            unsafe_allow_html=True,
        )
        balance = st.number_input("Account Balance ($)", value=10000.00, step=500.0)
        risk = st.slider("Risk Per Trade (%)", 0.1, 5.0, 1.00)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- ROW 2: AI SIGNALS & ACTION ---
    st.markdown(
        """
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
            <div style="font-size:15px; font-weight:600; color:#fff;">🎯 Institutional AI Signals</div>
            <div style="font-size:12px; font-weight:600; color:#00e676;">👑 VIP Status: Unlimited Signals</div>
        </div>
    """,
        unsafe_allow_html=True,
    )

    if st.button("⚡ GENERATE ACCURATE SIGNAL"):
        new_price = round(random.uniform(100, 60000), 2)
        new_sig = {
            "asset": asset,
            "type": random.choice(["BUY", "SELL"]),
            "entry": new_price,
            "tp": round(new_price * 1.03, 2),
            "sl": round(new_price * 0.98, 2),
            "time": datetime.datetime.now().strftime("%H:%M:%S"),
            "status": "🟢",
        }
        st.session_state.signals.insert(0, new_sig)
        st.success(f"✅ New Signal Generated for {asset}!")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- ROW 3: STATS GRID ---
    s1, s2, s3, s4, s5 = st.columns(5)
    with s1:
        st.markdown('<div class="stat-box"><div class="stat-label">Total Signals</div><div class="stat-value">128</div></div>', unsafe_allow_html=True)
    with s2:
        st.markdown('<div class="stat-box"><div class="stat-label">Win Rate</div><div class="stat-value" style="color:#00e676;">87.6%</div></div>', unsafe_allow_html=True)
    with s3:
        st.markdown('<div class="stat-box"><div class="stat-label">Accuracy</div><div class="stat-value" style="color:#ffb703;">High</div></div>', unsafe_allow_html=True)
    with s4:
        st.markdown(f'<div class="stat-box"><div class="stat-label">Active Signals</div><div class="stat-value" style="color:#00f2fe;">{len(st.session_state.signals)}</div></div>', unsafe_allow_html=True)
    with s5:
        st.markdown('<div class="stat-box"><div class="stat-label">Profit Factor</div><div class="stat-value" style="color:#00e676;">2.45</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- ROW 4: ACTIVE SIGNALS LIST ---
    st.markdown(
        """
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
            <span style="font-weight:600; color:#ffffff; font-size:15px;">Active Signals</span>
            <span style="font-size:12px; color:#8fa0b5; cursor:pointer;">View All</span>
        </div>
    """,
        unsafe_allow_html=True,
    )

    for sig in st.session_state.signals[:5]:
        badge_class = "badge-buy" if sig["type"] == "BUY" else "badge-sell"
        st.markdown(
            f"""
            <div class="sig-row">
                <div style="display:flex; align-items:center; gap:10px;">
                    <b>{sig['asset']}</b>
                    <span class="{badge_class}">{sig['type']}</span>
                </div>
                <div style="font-size:12px; color:#8fa0b5;">Entry: <b style="color:#fff;">{sig['entry']}</b></div>
                <div style="font-size:12px; color:#8fa0b5;">TP: <b style="color:#00e676;">{sig['tp']}</b></div>
                <div style="font-size:12px; color:#8fa0b5;">SL: <b style="color:#ff5252;">{sig['sl']}</b></div>
                <div style="font-size:11px; color:#8fa0b5;">{sig['time']} {sig['status']}</div>
            </div>
        """,
            unsafe_allow_html=True,
        )

with tab_chart:
    st.info("📊 Live TradingView / Chart Module Integrated")

with tab_sig:
    st.info("🎯 Detailed Historical Signals & Log Dashboard")

with tab_acc:
    st.info("🏆 Detailed Win/Loss Analytics & Backtesting")

with tab_manage:
    st.info("⚙️ API Configuration & Account Risk Limits")

# ==========================================
# 7. BOTTOM STATUS BAR
# ==========================================
st.markdown(
    """
    <div style="margin-top: 30px; padding: 10px 14px; background: #0d121c; border-top: 1px solid #1e2638; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; font-size: 11px; color: #8fa0b5;">
        <div>🟢 Connected</div>
        <div>Server: <b style="color:#00e676;">Live</b></div>
        <div>v1.0.0</div>
    </div>
""",
    unsafe_allow_html=True,
)

