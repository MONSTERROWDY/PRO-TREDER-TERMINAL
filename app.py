import streamlit as st
import pandas as pd
import numpy as np
import datetime
import time

# ==========================================
# 1. PAGE CONFIGURATION & LAYOUT
# ==========================================
st.set_page_config(
    page_title="वीर प्रो ट्रेडिंग टर्मिनल",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. ADVANCED STYLES & OVERFLOW FIX (CSS)
# ==========================================
st.markdown("""
<style>
    /* Global Background & Font */
    .stApp {
        background-color: #0b0e14;
        color: #d1d4dc;
    }
    
    /* Header Responsive Layout - Fixes Name and Title Cutoff */
    .veer-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: #131722;
        padding: 14px 20px;
        border-bottom: 2px solid #1e222d;
        border-radius: 8px;
        margin-bottom: 15px;
        flex-wrap: wrap;
        gap: 12px;
        width: 100%;
    }

    .veer-title {
        font-size: clamp(1.2rem, 2.5vw, 1.7rem);
        font-weight: 800;
        color: #2962ff;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        margin: 0;
        letter-spacing: 0.5px;
    }

    .veer-user-info {
        display: flex;
        align-items: center;
        gap: 12px;
        max-width: 100%;
    }

    .veer-user-name {
        font-size: 1rem;
        font-weight: 600;
        color: #e0e3eb;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 200px;
    }

    /* VIP and Standard Badges */
    .badge-vip {
        background-color: #ffb703;
        color: #000000;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 800;
        letter-spacing: 0.5px;
        box-shadow: 0 0 10px rgba(255, 183, 3, 0.4);
    }

    .badge-standard {
        background-color: #2a2e39;
        color: #787b86;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
        border: 1px solid #363a45;
    }

    /* Metric Cards Fix */
    div[data-testid="stMetricValue"] {
        font-size: 1.4rem !important;
        font-weight: 700 !important;
    }

    /* Fast Button Transitions */
    div.stButton > button {
        width: 100%;
        background-color: #1e222d;
        color: #d1d4dc;
        border: 1px solid #2a2e39;
        border-radius: 6px;
        font-weight: 600;
        transition: all 0.15s ease-in-out;
    }

    div.stButton > button:hover {
        background-color: #2962ff;
        color: #ffffff;
        border-color: #2962ff;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. FAST CACHED DATA GENERATOR (NO LAG)
# ==========================================
@st.cache_data(ttl=60)
def generate_market_data(symbol, days=100):
    np.random.seed(42)
    dates = pd.date_range(end=datetime.datetime.now(), periods=days)
    base_price = 22000 if "NIFTY" in symbol else (48000 if "BANK" in symbol else 65000)
    
    returns = np.random.normal(0.0005, 0.015, size=days)
    price_path = base_price * np.exp(np.cumsum(returns))
    
    df = pd.DataFrame({
        'Date': dates,
        'Close': price_path,
        'Open': price_path * (1 + np.random.uniform(-0.005, 0.005, days)),
        'High': price_path * (1 + np.random.uniform(0.001, 0.01, days)),
        'Low': price_path * (1 - np.random.uniform(0.001, 0.01, days)),
        'Volume': np.random.randint(100000, 5000000, days)
    })
    
    # Technical Indicators
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['RSI'] = 50 + np.random.uniform(-20, 20, days)
    return df

# ==========================================
# 4. USER & SESSION STATE (VIP ACCESS FIX)
# ==========================================
user_name = "वीर प्रो ट्रेडर"

# VIP Access Fix: Default set to False (Normal User)
if 'is_vip' not in st.session_state:
    st.session_state['is_vip'] = False

if 'active_symbol' not in st.session_state:
    st.session_state['active_symbol'] = "NIFTY 50"

# ==========================================
# 5. HEADER RENDER
# ==========================================
is_vip = st.session_state['is_vip']
vip_badge_html = '<span class="badge-vip">VIP ACCESS</span>' if is_vip else '<span class="badge-standard">STANDARD</span>'

st.markdown(f"""
<div class="veer-header">
    <h1 class="veer-title" title="वीर प्रो ट्रेडिंग टर्मिनल">वीर प्रो ट्रेडिंग टर्मिनल</h1>
    <div class="veer-user-info">
        <span class="veer-user-name" title="{user_name}">{user_name}</span>
        {vip_badge_html}
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 6. SIDEBAR CONTROLS & WATCHLIST
# ==========================================
with st.sidebar:
    st.title("⚙️ कंट्रोल पैनल")
    
    # VIP Toggle Access (For Admin Testing Only)
    with st.expander("🔐 रोल मैनेजमेंट (Admin)"):
        st.session_state['is_vip'] = st.checkbox("VIP Access सक्षम करें", value=st.session_state['is_vip'])
        if st.session_state['is_vip']:
            st.success("VIP स्टेटस एक्टिवेटेड!")
        else:
            st.info("स्टैंडर्ड यूज़र मोड चालू है।")

    st.subheader("📋 वॉचलिस्ट")
    symbols = ["NIFTY 50", "BANK NIFTY", "FINNIFTY", "BTC/USDT", "RELIANCE", "TCS"]
    selected_symbol = st.selectbox("सिंबल चुनें", symbols, index=symbols.index(st.session_state['active_symbol']))
    st.session_state['active_symbol'] = selected_symbol

    st.markdown("---")
    st.subheader("📊 टाइमफ्रेम")
    timeframe = st.radio("टाइमफ्रेम बदलें", ["1m", "5m", "15m", "1H", "1D"], index=2, horizontal=True)

    st.markdown("---")
    st.subheader("🛠️ इंडिकेटर्स")
    show_sma = st.checkbox("SMA (20/50)", value=True)
    show_rsi = st.checkbox("RSI (14)", value=True)
    show_volume = st.checkbox("वॉल्यूम (Volume)", value=True)

# ==========================================
# 7. MAIN DASHBOARD CONTENT
# ==========================================
data = generate_market_data(selected_symbol)
latest = data.iloc[-1]
prev = data.iloc[-2]

chg = latest['Close'] - prev['Close']
pct_chg = (chg / prev['Close']) * 100

# Top Market Metrics Row
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("लास्ट प्राइस", f"₹{latest['Close']:.2f}", f"{chg:+.2f} ({pct_chg:+.2f}%)")
m2.metric("24h हाई", f"₹{latest['High']:.2f}")
m3.metric("24h लो", f"₹{latest['Low']:.2f}")
m4.metric("RSI (14)", f"{latest['RSI']:.1f}")
m5.metric("वॉल्यूम", f"{latest['Volume']:,}")

st.markdown("---")

# Navigation Tabs
tab_chart, tab_orders, tab_positions, tab_analytics, tab_vip = st.tabs([
    "📈 लाइव चार्ट", 
    "📝 ऑर्डर्स", 
    "💼 पोजीशन", 
    "📊 एनालिसिस", 
    "⭐ VIP फीचर्स"
])

# --- TAB 1: CHART ---
with tab_chart:
    st.subheader(f"{selected_symbol} - टेक्निकल चार्ट ({timeframe})")
    
    chart_data = data.set_index('Date')[['Close']]
    if show_sma:
        chart_data['SMA_20'] = data.set_index('Date')['SMA_20']
        chart_data['SMA_50'] = data.set_index('Date')['SMA_50']
        
    st.line_chart(chart_data, height=420)

    if show_volume:
        st.caption("वॉल्यूम ट्रेंड")
        st.bar_chart(data.set_index('Date')['Volume'], height=130)

# --- TAB 2: ORDERS ---
with tab_orders:
    st.subheader("ऑर्डर बुक")
    col_buy, col_sell = st.columns(2)
    
    with col_buy:
        st.markdown("### 🟢 बाइंग ऑर्डर (Quick Buy)")
        buy_qty = st.number_input("मात्रा (Quantity)", min_value=1, value=50, key="b_qty")
        buy_price = st.number_input("ऑर्डर प्राइस", value=float(round(latest['Close'], 2)), key="b_prc")
        if st.button("BUY ORDER प्लेस करें", use_container_width=True):
            st.success(f"सफलतापूर्वक {buy_qty} Qty @ ₹{buy_price} पर Buy Order प्लेस हुआ!")

    with col_sell:
        st.markdown("### 🔴 सेलिंग ऑर्डर (Quick Sell)")
        sell_qty = st.number_input("मात्रा (Quantity)", min_value=1, value=50, key="s_qty")
        sell_price = st.number_input("ऑर्डर प्राइस", value=float(round(latest['Close'], 2)), key="s_prc")
        if st.button("SELL ORDER प्लेस करें", use_container_width=True):
            st.error(f"सफलतापूर्वक {sell_qty} Qty @ ₹{sell_price} पर Sell Order प्लेस हुआ!")

# --- TAB 3: POSITIONS ---
with tab_positions:
    st.subheader("आपकी ओपन पोजीशन")
    positions_df = pd.DataFrame([
        {"Symbol": "NIFTY 22200 CE", "Type": "BUY", "Qty": 100, "Avg Price": 125.50, "LTP": 142.00, "P&L": "+1650.00"},
        {"Symbol": "BANKNIFTY 48000 PE", "Type": "SELL", "Qty": 30, "Avg Price": 310.00, "LTP": 285.00, "P&L": "+750.00"}
    ])
    st.dataframe(positions_df, use_container_width=True)

# --- TAB 4: ANALYTICS ---
with tab_analytics:
    st.subheader("मार्केट डेप्थ & टेक्निकल इंडिकेटर्स")
    a1, a2 = st.columns(2)
    with a1:
        st.write("**बाय/सेल डेप्थ रेशियो**")
        st.progress(0.62)
        st.caption("62% Buyers | 38% Sellers")
    with a2:
        st.write("**ट्रेंड मोमेंटम**")
        st.info("Bullish (बुलिश मोमेंटम मजबूत है)")

# --- TAB 5: VIP FEATURES ---
with tab_vip:
    st.subheader("VIP ट्रेडिंग सिग्नल्स & प्रीमियम टूल्स")
    
    # VIP ACCESS CHECK
    if st.session_state['is_vip']:
        st.success("🎉 आपका VIP एक्सेस सक्रिय है!")
        st.markdown("""
        * **ऑटो-ट्रेडिंग सिग्नल्स**: BUY NIFTY @ 22150 | Target: 22300 | StopLoss: 22080
        * **इंस्टीट्यूशनल डेटा**: FII / DII नेट बाइंग डेटा लाइव अपडेट्स
        * **अल्गो-स्ट्रेटेजी**: High Frequency Scalping Enabled
        """)
    else:
        st.warning("🔒 यह फीचर केवल VIP यूजर्स के लिए उपलब्ध है।")
        st.info("VIP एक्सेस पाने के लिए एडमिन से संपर्क करें या अपने अकाउंट को अपग्रेड करें।")

# ==========================================
# 8. FOOTER
# ==========================================
st.markdown("---")
st.caption("© 2026 वीर प्रो ट्रेडिंग टर्मिनल | अल्ट्रा-फास्ट और ऑप्टिमाइज्ड इंजन")
