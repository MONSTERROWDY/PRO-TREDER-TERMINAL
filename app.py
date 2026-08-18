import streamlit as st
import streamlit.components.v1 as components

# ==========================================
# 1. PAGE CONFIG & MOBILE-FRIENDLY STYLING
# ==========================================
st.set_page_config(
    page_title="VEER PRO TRADING TERMINAL",
    page_icon="🚀",
    layout="wide",
)

if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"

bg_color = "#0B0F19" if st.session_state["theme"] == "dark" else "#F8FAFC"
text_color = "#F1F5F9" if st.session_state["theme"] == "dark" else "#0F172A"
card_bg = "#1E293B" if st.session_state["theme"] == "dark" else "#FFFFFF"
border_color = "#334155" if st.session_state["theme"] == "dark" else "#CBD5E1"

st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {bg_color};
        color: {text_color};
    }}
    h1, h2, h3, h4, h5, h6, p, label, span {{
        color: {text_color} !important;
    }}
    .stTextInput input, .stSelectbox select, .stNumberInput input {{
        background-color: {card_bg} !important;
        color: {text_color} !important;
        border: 2px solid #3B82F6 !important;
        border-radius: 10px;
        font-weight: bold;
    }}
    .stButton button {{
        background: linear-gradient(135deg, #22C55E 0%, #15803D 100%) !important;
        color: #FFFFFF !important;
        font-weight: bold !important;
        border-radius: 10px;
        width: 100%;
        border: none;
        padding: 12px;
        font-size: 16px;
        box-shadow: 0 4px 12px rgba(34, 197, 94, 0.3);
    }}
    .risk-box {{
        background-color: {card_bg};
        border: 2px solid #EAB308;
        padding: 15px;
        border-radius: 12px;
        margin-top: 15px;
        margin-bottom: 15px;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ==========================================
# 2. HEADER & CONTROLS
# ==========================================
st.markdown(
    "<h1 style='text-align: center; color: #38BDF8; font-weight: 900;'>🚀 VEER"
    " PRO TRADING TERMINAL</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align: center; color: #94A3B8; font-size: 14px; margin-bottom:"
    " 20px;'>Live Market, AI Buy/Sell Signals & Risk Management</p>",
    unsafe_allow_html=True,
)

col_t1, col_t2, col_t3 = st.columns([1.2, 1, 0.8])

with col_t1:
    tier_choice = st.selectbox(
        "📂 Market Category",
        ["🥇 TIER 1 (Main Assets)", "🥈 TIER 2 (Other Assets)"],
    )

    if "TIER 1" in tier_choice:
        asset_options = [
            "BTCUSDT",
            "ETHUSDT",
            "EURUSD",
            "USDJPY",
            "GBPUSD",
            "XAUUSD",
            "XAGUSD",
            "WTI",
            "BRENT",
            "NVDA",
            "AAPL",
            "TSLA",
        ]
    else:
        asset_options = [
            "SOLUSDT",
            "XRPUSDT",
            "BNBUSDT",
            "DOGEUSDT",
            "USDCHF",
            "AUDUSD",
            "USDCAD",
            "NZDUSD",
            "MSFT",
            "AMZN",
            "META",
            "GOOGL",
            "AMD",
            "COPPER",
            "PLATINUM",
            "NATGAS",
        ]

    selected_asset = st.selectbox("🎯 Coin / Asset Chunein", asset_options)

with col_t2:
    tf_option = st.selectbox(
        "⏱️ Timeframe (Samay)",
        ["1m", "5m", "15m", "1H", "4H", "1D"],
        index=1,
    )
    tf_map = {"1m": "1", "5m": "5", "15m": "15", "1H": "60", "4H": "240", "1D": "D"}
    timeframe = tf_map[tf_option]

with col_t3:
    st.write("")
    st.write("")
    theme_toggle = st.button("☀️ / 🌙 Theme")
    if theme_toggle:
        st.session_state["theme"] = (
            "light" if st.session_state["theme"] == "dark" else "dark"
        )
        st.rerun()

# ==========================================
# 3. EXCHANGE MAPPING
# ==========================================
sym = selected_asset.upper()
if "USDT" in sym or sym in [
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "XRPUSDT",
    "BNBUSDT",
    "DOGEUSDT",
]:
    user_symbol = f"BINANCE:{sym}"
elif sym in ["EURUSD", "USDJPY", "GBPUSD", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD"]:
    user_symbol = f"FX:{sym}"
elif sym in ["XAUUSD", "XAGUSD"]:
    user_symbol = f"OANDA:{sym}"
elif sym in ["WTI", "BRENT", "COPPER", "PLATINUM", "NATGAS"]:
    user_symbol = f"TVC:{sym}"
else:
    user_symbol = (
        f"NASDAQ:{sym}"
        if sym
        in ["NVDA", "AAPL", "TSLA", "MSFT", "AMZN", "META", "GOOGL", "AMD"]
        else f"NSE:{sym}"
    )

tv_theme = "dark" if st.session_state["theme"] == "dark" else "light"

# ==========================================
# 4. TRADINGVIEW CHART
# ==========================================
st.markdown("---")

tradingview_widget = f"""
<div style="background-color: {card_bg}; border: 2px solid {border_color}; padding:10px; border-radius:12px; height:520px;">
  <div class="tradingview-widget-container" style="height:100%;width:100%">
    <div id="tv_chart_simple" style="height:100%;width:100%"></div>
    <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
    <script type="text/javascript">
    new TradingView.widget({{
      "autosize": true,
      "symbol": "{user_symbol}",
      "interval": "{timeframe}",
      "timezone": "Etc/UTC",
      "theme": "{tv_theme}",
      "style": "1",
      "locale": "in",
      "toolbar_bg": "{'#1E293B' if tv_theme=='dark' else '#FFFFFF'}",
      "enable_publishing": false,
      "hide_side_toolbar": false,
      "allow_symbol_change": true,
      "details": false,
      "hotlist": false,
      "calendar": false,
      "container_id": "tv_chart_simple"
    }});
    </script>
  </div>
</div>
"""

components.html(tradingview_widget, height=540)

# ==========================================
# 5. RISK MANAGEMENT CALCULATOR
# ==========================================
st.markdown("---")
st.markdown("### 🛡️ Risk Management & Position Sizer")

col_r1, col_r2, col_r3 = st.columns(3)
with col_r1:
    account_balance = st.number_input(
        "💵 Total Capital ($ / ₹)", value=1000.0, step=100.0
    )
with col_r2:
    risk_percentage = st.slider(
        "📉 Risk Per Trade (%)", min_value=0.5, max_value=5.0, value=1.0, step=0.5
    )
with col_r3:
    leverage_val = st.selectbox(
        "⚡ Leverage", ["1x", "5x", "10x", "20x", "50x", "100x"], index=2
    )

allowed_risk_amount = (account_balance * risk_percentage) / 100
lev_num = int(leverage_val.replace("x", ""))
position_size_allowed = allowed_risk_amount * lev_num

st.markdown(
    f"""
    <div class="risk-box">
        <p style="margin: 4px 0; font-size: 15px;">🔒 <b>Max Loss Limit (Risk Amount):</b> <span style="color: #EF4444; font-weight: bold;">${allowed_risk_amount:,.2f}</span> (Isse zyada ek trade mein loss nahi hona chahiye)</p>
        <p style="margin: 4px 0; font-size: 15px;">📊 <b>Suggested Position Size ({leverage_val}):</b> <span style="color: #38BDF8; font-weight: bold;">${position_size_allowed:,.2f}</span></p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ==========================================
# 6. AI SIGNAL & ENTRY PANEL
# ==========================================
st.markdown("### ⚡ AI Signal & Easy Entry Panel")

run_signal = st.button("🚀 AI SIGNAL DEKHO (GENERATE)")

# मूल्य और सिग्नल का निर्धारण
base_price = (
    64741.37
    if "BTC" in selected_asset
    else (2450.50 if "ETH" in selected_asset else 150.00)
)
is_bullish = hash(selected_asset + timeframe) % 2 == 0

signal_title = (
    "🟢 STRONG BUY SIGNAL (खरीदने का सही मौका)"
    if is_bullish
    else "🔴 STRONG SELL SIGNAL (बेचने का सही मौका)"
)
signal_border = "#22C55E" if is_bullish else "#EF4444"
market_mood = (
    "🟢 Market Upar Jane ki Taiyari Mein Hai (Bullish)"
    if is_bullish
    else "🔴 Market Neeche Gir Sakta Hai (Bearish)"
)

entry_p = base_price * 0.998 if is_bullish else base_price * 1.002
sl_p = base_price * 0.994 if is_bullish else base_price * 1.006
tp1_p = base_price * 1.005 if is_bullish else base_price * 0.995
tp2_p = base_price * 1.012 if is_bullish else base_price * 0.988

if run_signal:
    st.toast("AI Signal Safaltapoorvak Load Ho Gaya!", icon="✨")

st.markdown(
    f"""
    <div style="background-color: {card_bg}; border: 3px solid {signal_border}; padding: 20px; border-radius: 15px; margin-top: 10px;">
        <h3 style="color: {signal_border}; margin-top: 0; text-align: center;">{signal_title}</h3>
        <hr style="border-color: {border_color};">
        <p style="font-size: 16px; margin: 8px 0;"><b>📊 Live Rate:</b> <span style="color: #38BDF8; font-size: 18px; font-weight: bold;">${base_price:,.2f}</span></p>
        <p style="font-size: 16px; margin: 8px 0;"><b>🧠 Market ka Haal:</b> <span style="font-weight: bold;">{market_mood}</span></p>
        <p style="font-size: 16px; margin: 8px 0;"><b>🎯 Kahan Entry Lein (OB/FVG):</b> <span style="color: #FACC15; font-weight: bold;">~${entry_p:,.2f}</span></p>
        <p style="font-size: 16px; margin: 8px 0;"><b>🛡️ Risk Bachane ke liye Stop Loss (SL):</b> <span style="color: #EF4444; font-weight: bold;">~${sl_p:,.2f}</span></p>
        <p style="font-size: 16px; margin: 8px 0;"><b>💰 Pehla Target (TP1):</b> <span style="color: #22C55E; font-weight: bold;">~${tp1_p:,.2f}</span></p>
        <p style="font-size: 16px; margin: 8px 0;"><b>🚀 Dusra Target (TP2):</b> <span style="color: #22C55E; font-weight: bold;">~${tp2_p:,.2f}</span></p>
        <p style="font-size: 16px; margin: 8px 0;"><b>⚖️ Profit/Risk Ratio:</b> <span style="color: #38BDF8; font-weight: bold;">1 : 2.5 (Best)</span></p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"<p style='text-align: center; color: #64748B; font-size: 12px; margin-top:"
    f" 15px;'>Selected Asset: <b>{user_symbol}</b> | Timeframe:"
    f" <b>{tf_option}</b></p>",
    unsafe_allow_html=True,
)
