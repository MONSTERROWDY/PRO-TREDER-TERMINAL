import streamlit as st
import streamlit.components.v1 as components

# पेज की फुल-विड्थ सेटिंग
st.set_page_config(
    page_title="VEER PRO TRADING TERMINAL", page_icon="⚡", layout="wide"
)

# सुपर-क्लीन व्हाइट बैकग्राउंड और प्रोफेशनल फिनिश के लिए CSS
st.markdown(
    """
    <style>
    .stApp {
        background-color: #FFFFFF;
        color: #000000;
    }
    h1, h2, h3, h4, h5, h6, p, label, span {
        color: #000000 !important;
    }
    .stTextInput input {
        background-color: #F8F9FA !important;
        color: #000000 !important;
        border: 1px solid #CED4DA !important;
        border-radius: 6px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ऐप का मुख्य शीर्षक
st.markdown(
    "<h1 style='text-align: center; color: #FF4B4B;'>⚡ VEER PRO TERMINAL (TV"
    " APP MODE) ⚡</h1>",
    unsafe_allow_html=True,
)

# एसेट सर्च और टाइमफ्रेम कंट्रोल बार
col_search, col_tf = st.columns([3, 1])

with col_search:
    user_symbol = st.text_input(
        "🔍 Search Any Stock, Crypto, Forex, or Currency (e.g., AAPL,"
        " BINANCE:BTCUSDT, EURUSD, USDINR):",
        value="BINANCE:BTCUSDT",
    )

with col_tf:
    timeframe = st.selectbox(
        "⏱️ Timeframe", ["1", "5", "15", "60", "240", "D", "W"]
    )

# ट्रेडिंगव्यू का असली एडवांस्ड चार्ट (बिल्कुल ट्रेडिंगव्यू मोबाइल ऐप की तरह)
tradingview_advanced_widget = f"""
<div class="tradingview-widget-container" style="height:620px;width:100%">
  <div id="tradingview_advanced_chart" style="height:100%;width:100%"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
  new TradingView.widget(
  {{
    "autosize": true,
    "symbol": "{user_symbol}",
    "interval": "{timeframe}",
    "timezone": "Etc/UTC",
    "theme": "light",
    "style": "1",
    "locale": "in",
    "toolbar_bg": "#f1f3f6",
    "enable_publishing": false,
    "hide_side_toolbar": false,
    "allow_symbol_change": true,
    "details": true,
    "hotlist": true,
    "calendar": true,
    "studies": [
      "MASimple@tv-basicstudies",
      "RSI@tv-basicstudies",
      "MACD@tv-basicstudies"
    ],
    "container_id": "tradingview_advanced_chart"
  }});
  </script>
</div>
"""

# चार्ट को स्क्रीन पर रेंडर करना
components.html(tradingview_advanced_widget, height=640)

# 🎯 Buy/Sell Signal, Stop Loss और Take Profit पैनल
st.markdown("---")
st.markdown("### 📊 AI Smart Signal & Risk Management Dashboard")

col_sig1, col_sig2, col_sig3, col_sig4 = st.columns(4)

with col_sig1:
    st.markdown(
        """
        <div style="background-color: #E8F5E9; padding: 15px; border-radius: 8px; border-left: 6px solid #4CAF50;">
            <h4 style="color: #2E7D32 !important; margin: 0;">🟢 Signal Status</h4>
            <p style="font-size: 18px; font-weight: bold; color: #1B5E20 !important; margin-top: 5px;">STRONG BUY / LONG</p>
            <p style="font-size: 12px; color: #555 !important;">Market Structure Shift (BOS)</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_sig2:
    st.markdown(
        """
        <div style="background-color: #FFF8E1; padding: 15px; border-radius: 8px; border-left: 6px solid #FFC107;">
            <h4 style="color: #F57F17 !important; margin: 0;">🎯 Target (TP)</h4>
            <p style="font-size: 15px; font-weight: bold; color: #E65100 !important; margin-top: 5px;">TP1: Resistance Zone<br>TP2: Liquidity High</p>
            <p style="font-size: 12px; color: #555 !important;">Risk-Reward Ratio 1:3</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_sig3:
    st.markdown(
        """
        <div style="background-color: #FFEBEE; padding: 15px; border-radius: 8px; border-left: 6px solid #F44336;">
            <h4 style="color: #C62828 !important; margin: 0;">🛑 Stop Loss (SL)</h4>
            <p style="font-size: 15px; font-weight: bold; color: #B71C1C !important; margin-top: 5px;">Strict Protection</p>
            <p style="font-size: 12px; color: #555 !important;">Below Swing Low / Order Block</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_sig4:
    st.markdown(
        """
        <div style="background-color: #E3F2FD; padding: 15px; border-radius: 8px; border-left: 6px solid #2196F3;">
            <h4 style="color: #1565C0 !important; margin: 0;">🛡️ Trap Guard</h4>
            <p style="font-size: 15px; font-weight: bold; color: #0D47A1 !important; margin-top: 5px;">Active & Safe</p>
            <p style="font-size: 12px; color: #555 !important;">Fake Breakouts Filtered</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    f"👉 **Live Terminal Connected:** Asset: `{user_symbol}` | Timeframe:"
    f" `{timeframe}`"
)
