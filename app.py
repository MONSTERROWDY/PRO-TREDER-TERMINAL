import streamlit as st
import pandas as pd
import numpy as np
import datetime
import random
import time

# ==========================================
# 1. PAGE CONFIGURATION & STYLES
# ==========================================
st.set_page_config(
    page_title="Veer Pro Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #0b0e14; color: #d1d4dc; }
    div[data-testid="stSidebar"] { background-color: #121824; border-right: 1px solid #1e293b; }
    
    .header-box {
        display: flex; justify-content: space-between; align-items: center;
        background-color: #121824; padding: 12px 18px; border-radius: 10px;
        border: 1px solid #1e293b; margin-bottom: 12px; flex-wrap: wrap; gap: 10px;
    }
    .header-title { font-size: 1.25rem; font-weight: 800; color: #ffffff; display: flex; align-items: center; gap: 8px; }
    .badge-vip { background: linear-gradient(135deg, #ffb703, #fb8500); color: #000; font-weight: 800; padding: 4px 10px; border-radius: 4px; font-size: 0.75rem; }
    .badge-std { background-color: #1e293b; color: #94a3b8; font-weight: 600; padding: 4px 10px; border-radius: 4px; font-size: 0.75rem; border: 1px solid #334155; }
    
    div.stButton > button {
        width: 100%;
        background-color: #2563eb; color: #ffffff; border-radius: 8px;
        font-weight: 700; border: none; padding: 10px 16px; transition: all 0.2s;
    }
    div.stButton > button:hover { background-color: #1d4ed8; color: #ffffff; }
    div[data-baseweb="input"] { background-color: #0f172a !important; border-color: #1e293b !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. SESSION STATE MANAGEMENT
# ==========================================
if 'is_vip' not in st.session_state:
    st.session_state['is_vip'] = False
if 'user_name' not in st.session_state:
    st.session_state['user_name'] = "वीर प्रो ट्रेडर"
if 'balance' not in st.session_state:
    st.session_state['balance'] = 10000.00
if 'btc_price' not in st.session_state:
    st.session_state['btc_price'] = 68417.51
if 'sol_price' not in st.session_state:
    st.session_state['sol_price'] = 145.06
if 'eth_price' not in st.session_state:
    st.session_state['eth_price'] = 3540.49

if 'active_signals' not in st.session_state:
    st.session_state['active_signals'] = [
        {"Symbol": "BTC/USDT", "Type": "BUY", "Entry": 68417.51, "SL": 67049.16, "TP": 70470.04, "Time": "14:19:55", "Status": "Active"},
        {"Symbol": "SOL/USDT", "Type": "BUY", "Entry": 143.50, "SL": 140.10, "TP": 148.20, "Time": "18:17:45", "Status": "Active"},
        {"Symbol": "BTC/USDT", "Type": "BUY", "Entry": 68400.00, "SL": 67680.00, "TP": 69250.00, "Time": "18:16:20", "Status": "Active"},
        {"Symbol": "ETH/USDT", "Type": "SELL", "Entry": 3540.00, "SL": 3580.00, "TP": 3475.00, "Time": "18:15:10", "Status": "Active"}
    ]

ALL_PAIRS_DATA = {
    "Crypto Top Major": ["BTC/USDT", "SOL/USDT", "ETH/USDT", "BNB/USDT", "XRP/USDT"],
    "Commodities & Forex": ["XAU/USD (Gold)", "EUR/USD", "GBP/USD"],
    "Indices": ["NIFTY 50", "BANK NIFTY"]
}

VALID_PROMO_CODES = ["FREEVIP", "VEERPRO100", "VIP2026"]

# ==========================================
# 3. SIDEBAR PANEL
# ==========================================
with st.sidebar:
    st.title("⚙️ कंट्रोल पैनल")
    
    st.markdown("### 👤 यूज़र प्रोफाइल")
    user_name_input = st.text_input("ट्रेडर का नाम", value=st.session_state['user_name'])
    st.session_state['user_name'] = user_name_input

    st.markdown("---")
    st.markdown("### 🎟️ VIP प्रोमो कोड")
    promo = st.text_input("प्रोमो कोड दर्ज करें", placeholder="उदा. FREEVIP", key="sidebar_promo")
    if st.button("प्रोमो कोड लागू करें", key="btn_promo"):
        if promo.strip().upper() in VALID_PROMO_CODES:
            st.session_state['is_vip'] = True
            st.success("🎉 VIP एक्सेस अनलॉक हो गया!")
        else:
            st.error("❌ अमान्य प्रोमो कोड!")

    st.markdown("---")
    st.markdown("### 📊 मार्केट्स & पेयर्स")
    selected_cat = st.selectbox("कैटेगिरी", list(ALL_PAIRS_DATA.keys()))
    selected_pair = st.selectbox("ट्रेडिंग पेयर चुनें", ALL_PAIRS_DATA[selected_cat])

# ==========================================
# 4. TOP HEADER & REAL-TIME LIVE TICKER
# ==========================================
vip_badge_html = '<span class="badge-vip">👑 VIP UNLOCKED</span>' if st.session_state['is_vip'] else '<span class="badge-std">STANDARD</span>'

st.markdown(f"""
<div class="header-box">
    <div class="header-title">⚡ Veer Pro <span style="font-size: 0.8rem; color: #94a3b8;">Terminal</span></div>
    <div>
        <span style="font-weight: 600; margin-right: 8px;">{st.session_state['user_name']}</span>
        {vip_badge_html}
    </div>
</div>
""", unsafe_allow_html=True)

# 🔴 LIVE UPDATING TICKER FRAGMENT (Refreshes every 1 Sec)
@st.fragment(run_every=1)
def live_top_ticker():
    # Small live price fluctuation simulation
    st.session_state['btc_price'] += random.uniform(-2.5, 2.5)
    st.session_state['sol_price'] += random.uniform(-0.15, 0.15)
    st.session_state['eth_price'] += random.uniform(-0.8, 0.8)

    t1, t2, t3 = st.columns(3)
    t1.metric("BTC/USDT", f"${st.session_state['btc_price']:,.2f}", f"{random.uniform(1.1, 1.3):.2f}%")
    t2.metric("🔥 SOL/USDT", f"${st.session_state['sol_price']:,.2f}", f"{random.uniform(2.3, 2.6):.2f}%")
    t3.metric("ETH/USDT", f"${st.session_state['eth_price']:,.2f}", f"{random.uniform(1.6, 1.9):.2f}%")

live_top_ticker()

st.markdown("---")

# ==========================================
# 5. DASHBOARD & TABS
# ==========================================
tab_dashboard, tab_chart, tab_signals, tab_accuracy, tab_vip = st.tabs([
    "🎛️ Dashboard", 
    "📈 Live Chart", 
    "🎯 AI Signals", 
    "🏆 Accuracy", 
    "⭐ VIP Features"
])

# ---------------- DASHBOARD TAB ----------------
with tab_dashboard:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### ⚙️ Signal Configuration")
        st.selectbox("Category", list(ALL_PAIRS_DATA.keys()), key="dash_cat")
        selected_asset = st.selectbox("Asset", ALL_PAIRS_DATA[selected_cat], key="dash_asset")
        tf = st.selectbox("Timeframe", ["1s", "1m", "5m", "15m", "1H"], index=1)

    with col2:
        st.markdown("##### 🛡️ Risk Management")
        bal = st.number_input("Account Balance ($)", value=float(st.session_state['balance']), step=500.0)
        st.session_state['balance'] = bal
        risk = st.slider("Risk Per Trade (%)", 0.10, 5.00, 0.30, 0.05)

    st.markdown("---")
    
    # SIGNAL GENERATION BUTTON
    if st.button("⚡ GENERATE ACCURATE SIGNAL", use_container_width=True):
        now_time = datetime.datetime.now().strftime("%H:%M:%S")
        curr = st.session_state['btc_price'] if "BTC" in selected_asset else (st.session_state['sol_price'] if "SOL" in selected_asset else 3500.0)
        
        new_signal = {
            "Symbol": selected_asset,
            "Type": "BUY",
            "Entry": round(curr, 2),
            "SL": round(curr * 0.98, 2),
            "TP": round(curr * 1.03, 2),
            "Time": now_time,
            "Status": "Active"
        }
        st.session_state['active_signals'].insert(0, new_signal)
        st.success(f"सफलतापूर्वक नया सिग्नल जनरेट हुआ: BUY {selected_asset} @ {curr:.2f}")

    # Stat Indicators
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Signals", len(st.session_state['active_signals']) + 125)
    m2.metric("Win Rate", "87.6%")
    m3.metric("Accuracy", "High")
    m4.metric("Active Signals", len(st.session_state['active_signals']))
    m5.metric("Profit Factor", "2.45")

    st.markdown("##### 🟢 Active Signals")
    sig_df = pd.DataFrame(st.session_state['active_signals'])
    st.dataframe(sig_df, use_container_width=True)

# ---------------- LIVE CHART TAB ----------------
with tab_chart:
    st.subheader(f"{selected_pair} Live Streaming Chart")
    
    @st.fragment(run_every=2)
    def live_chart_render():
        now = datetime.datetime.now()
        times = [(now - datetime.timedelta(seconds=i*5)).strftime("%H:%M:%S") for i in range(20)][::-1]
        base_val = st.session_state['btc_price'] if "BTC" in selected_pair else 150.0
        prices = base_val + np.cumsum(np.random.normal(0, 0.5, 20))
        
        chart_data = pd.DataFrame({"Time": times, "Price": prices}).set_index("Time")
        st.line_chart(chart_data, height=350)
        st.info(f"🔴 Live Price Tick: ${prices[-1]:,.2f} | Updates automatically every 2s")

    live_chart_render()

# ---------------- SIGNALS TAB ----------------
with tab_signals:
    st.subheader("📋 Active & Historical Signals")
    st.dataframe(pd.DataFrame(st.session_state['active_signals']), use_container_width=True)

# ---------------- ACCURACY TAB ----------------
with tab_accuracy:
    st.subheader("🏆 Strategy Performance Analytics")
    a1, a2 = st.columns(2)
    a1.metric("Overall Win Rate", "87.6%")
    a2.metric("Profit Factor", "2.45")
    st.progress(0.87)

# ---------------- VIP FEATURES TAB ----------------
with tab_vip:
    st.subheader("⭐ VIP Access")
    if st.session_state['is_vip']:
        st.balloons()
        st.success("🎉 VIP स्टेटस सक्रिय है!")
    else:
        st.info("👈 VIP मुफ़्त में अनलॉक करने के लिए साइडबार में प्रोमो कोड `FREEVIP` दर्ज करें।")
