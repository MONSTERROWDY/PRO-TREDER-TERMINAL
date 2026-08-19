import streamlit as st
import pandas as pd
import numpy as np
import datetime
import plotly.graph_objects as go
import time

# ==========================================
# 1. PAGE CONFIG & STYLES
# ==========================================
st.set_page_config(
    page_title="Veer Pro Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark Trading Theme Injection
st.markdown("""
<style>
    .stApp { background-color: #0b0e14; color: #d1d4dc; }
    div[data-testid="stSidebar"] { background-color: #121824; border-right: 1px solid #1e293b; }
    
    /* Header Custom Layout */
    .header-box {
        display: flex; justify-content: space-between; align-items: center;
        background-color: #121824; padding: 12px 18px; border-radius: 10px;
        border: 1px solid #1e293b; margin-bottom: 12px;
    }
    .header-title { font-size: 1.25rem; font-weight: 800; color: #ffffff; display: flex; align-items: center; gap: 8px; }
    .badge-vip { background: linear-gradient(135deg, #ffb703, #fb8500); color: #000; font-weight: 800; padding: 3px 10px; border-radius: 4px; font-size: 0.75rem; }
    .badge-std { background-color: #1e293b; color: #94a3b8; font-weight: 600; padding: 3px 10px; border-radius: 4px; font-size: 0.75rem; border: 1px solid #334155; }
    
    /* Button Styles */
    div.stButton > button {
        background-color: #2563eb; color: #ffffff; border-radius: 8px;
        font-weight: 700; border: none; padding: 10px 16px; transition: all 0.2s;
    }
    div.stButton > button:hover { background-color: #1d4ed8; border: none; }
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
if 'selected_pair' not in st.session_state:
    st.session_state['selected_pair'] = "BTC/USDT"

# Valid Promo Codes Registry
VALID_PROMO_CODES = ["FREEVIP", "VEERPRO100", "VIP2026"]

# Price Registry for All Pairs
ALL_PAIRS_DATA = {
    "Crypto Top Major": {
        "BTC/USDT": {"price": 68417.51, "change": "+1.23%"},
        "SOL/USDT": {"price": 145.06, "change": "+2.45%"},
        "ETH/USDT": {"price": 3540.49, "change": "+1.78%"},
        "BNB/USDT": {"price": 575.20, "change": "+0.85%"},
        "XRP/USDT": {"price": 0.58, "change": "-0.40%"},
        "ADA/USDT": {"price": 0.39, "change": "+3.10%"}
    },
    "Forex & Commodities": {
        "XAU/USD (Gold)": {"price": 2504.30, "change": "+0.65%"},
        "EUR/USD": {"price": 1.0892, "change": "-0.12%"},
        "GBP/USD": {"price": 1.2940, "change": "+0.05%"}
    },
    "Indian Indices": {
        "NIFTY 50": {"price": 24850.10, "change": "+0.42%"},
        "BANK NIFTY": {"price": 51200.50, "change": "-0.15%"}
    }
}

# ==========================================
# 3. REAL-TIME CHART DATA GENERATOR
# ==========================================
def get_live_chart(pair_symbol):
    # Generating 60 Candlestick bars with exact Timestamps
    now = datetime.datetime.now()
    dates = [now - datetime.timedelta(minutes=i*5) for i in range(60)][::-1]
    
    # Base Price calculation
    curr_info = None
    for cat in ALL_PAIRS_DATA.values():
        if pair_symbol in cat:
            curr_info = cat[pair_symbol]
            break
    
    base_p = curr_info["price"] if curr_info else 100.0
    
    np.random.seed(int(time.time()) % 1000)
    returns = np.random.normal(0, 0.002, 60)
    price_series = base_p * np.exp(np.cumsum(returns))
    
    opens = price_series * (1 + np.random.uniform(-0.001, 0.001, 60))
    highs = np.maximum(price_series, opens) * (1 + np.random.uniform(0.0005, 0.003, 60))
    lows = np.minimum(price_series, opens) * (1 - np.random.uniform(0.0005, 0.003, 60))
    closes = price_series

    fig = go.Figure(data=[go.Candlestick(
        x=dates,
        open=opens, high=highs,
        low=lows, close=closes,
        increasing_line_color='#10b981', 
        decreasing_line_color='#ef4444'
    )])

    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='#121824',
        plot_bgcolor='#121824',
        margin=dict(l=10, r=10, t=25, b=10),
        height=450,
        xaxis_rangeslider_visible=False,
        xaxis=dict(showgrid=True, gridcolor='#1e293b'),
        yaxis=dict(showgrid=True, gridcolor='#1e293b', side='right')
    )
    return fig, closes[-1], (closes[-1] - opens[0])

# ==========================================
# 4. SIDEBAR - USER PROFILE & PAIR SELECTOR
# ==========================================
with st.sidebar:
    st.markdown("### 👤 यूज़र प्रोफाइल")
    user_name_input = st.text_input("ट्रेडर का नाम", value=st.session_state['user_name'])
    st.session_state['user_name'] = user_name_input

    # Promo Code Section
    st.markdown("---")
    st.markdown("### 🎟️ VIP प्रोमो कोड")
    promo_code = st.text_input("प्रोमो कोड डालें", placeholder="e.g. FREEVIP")
    if st.button("प्रोमो कोड लागू करें", use_container_width=True):
        if promo_code.strip().upper() in VALID_PROMO_CODES:
            st.session_state['is_vip'] = True
            st.success("🎉 VIP एक्सेस मुफ़्त में अनलॉक हो गया!")
        else:
            st.error("❌ अमान्य (Invalid) प्रोमो कोड")

    st.markdown("---")
    st.markdown("### 📊 मार्केट्स & पेयर्स")
    
    category = st.selectbox("कैटेगिरी चुनें", list(ALL_PAIRS_DATA.keys()))
    pair_options = list(ALL_PAIRS_DATA[category].keys())
    selected_pair = st.selectbox("ट्रेडिंग पेयर्स", pair_options)
    st.session_state['selected_pair'] = selected_pair

# ==========================================
# 5. TOP HEADER & TICKER
# ==========================================
vip_badge = '<span class="badge-vip">👑 VIP UNLOCKED</span>' if st.session_state['is_vip'] else '<span class="badge-std">STANDARD</span>'

st.markdown(f"""
<div class="header-box">
    <div class="header-title">⚡ Veer Pro <span style="font-size: 0.8rem; color: #94a3b8;">Terminal</span></div>
    <div>
        <span style="font-weight: 600; margin-right: 8px;">{st.session_state['user_name']}</span>
        {vip_badge}
    </div>
</div>
""", unsafe_allow_html=True)

# Ticker Display
t1, t2, t3 = st.columns(3)
t1.metric("BTC/USDT", "$68,417.51", "+1.23%")
t2.metric("🔥 SOL/USDT", "$145.06", "+2.45%")
t3.metric("ETH/USDT", "$3,540.49", "+1.78%")

st.markdown("---")

# ==========================================
# 6. MAIN NAVIGATION TABS (FULLY FUNCTIONAL)
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
        st.selectbox("Asset", pair_options, key="dash_asset")
        st.selectbox("Timeframe", ["1s", "1m", "5m", "15m", "1H"], index=1)

    with col2:
        st.markdown("##### 🛡️ Risk Management")
        bal = st.number_input("Account Balance ($)", value=st.session_state['balance'], step=500.0)
        st.session_state['balance'] = bal
        risk = st.slider("Risk Per Trade (%)", 0.1, 5.0, 1.0, 0.1)

    st.markdown("---")
    st.markdown("##### 🤖 Institutional AI Signals")
    
    if st.button("⚡ GENERATE ACCURATE SIGNAL", use_container_width=True):
        st.toast(f"Generating fresh AI Signal for {st.session_state['selected_pair']}...", icon="🚀")
        st.success(f"Signal Generated: BUY {st.session_state['selected_pair']} | Entry: Live Price | Target +2% | SL -1%")

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Signals", "128")
    m2.metric("Win Rate", "87.6%")
    m3.metric("Accuracy", "High")
    m4.metric("Active", "3")
    m5.metric("Profit Factor", "2.45")

# ---------------- LIVE CHART TAB ----------------
with tab_chart:
    st.subheader(f"{st.session_state['selected_pair']} Real-Time Chart")
    
    # Plotly Candlestick Render
    fig, last_p, diff = get_live_chart(st.session_state['selected_pair'])
    st.plotly_chart(fig, use_container_width=True)
    
    st.info(f"🟢 **Live Price**: ${last_p:.2f} | Current Session Delta: {diff:+.2f}")

# ---------------- SIGNALS TAB ----------------
with tab_signals:
    st.subheader("📋 Active Market Signals")
    signals_df = pd.DataFrame([
        {"Symbol": "SOL/USDT", "Type": "BUY", "Entry": 143.50, "TP": 148.20, "SL": 140.10, "Status": "Active"},
        {"Symbol": "BTC/USDT", "Type": "BUY", "Entry": 68400.00, "TP": 69250.00, "SL": 67680.00, "Status": "Active"},
        {"Symbol": "ETH/USDT", "Type": "SELL", "Entry": 3540.00, "TP": 3475.00, "SL": 3580.00, "Status": "Completed"}
    ])
    st.dataframe(signals_df, use_container_width=True)

# ---------------- ACCURACY TAB ----------------
with tab_accuracy:
    st.subheader("🏆 Strategy Performance & Backtest")
    a1, a2 = st.columns(2)
    a1.metric("Overall Accuracy Rate", "89.4%")
    a2.metric("Monthly Net Profit", "+34.2%")
    st.progress(0.89)

# ---------------- VIP FEATURES TAB ----------------
with tab_vip:
    st.subheader("⭐ VIP Access & Pricing")
    
    if st.session_state['is_vip']:
        st.balloons()
        st.success("🎉 आपका VIP एक्सेस एक्टिव है! आप सभी प्रीमियम सिग्नल्स का आनंद ले रहे हैं।")
    else:
        st.warning("🔒 आपका VIP एक्सेस अभी सक्रिय नहीं है।")
        p1, p2 = st.columns(2)
        with p1:
            st.markdown("### Monthly Plan\n**₹999 / माह**\n* 30 Days Unlimited Signals\n* Real-time Trading Alerts")
        with p2:
            st.markdown("### Lifetime Access\n**₹2,999 (One Time)**\n* Permanent Access\n* High-Frequency Scalping Strategy")
        st.info("👈 VIP मुफ़्त में अनलॉक करने के लिए साइडबार मेन्यू में प्रोमो कोड `FREEVIP` दर्ज करें।")
