import streamlit as st
import streamlit.components.v1 as components

# पेज की सेटिंग और लेआउट
st.set_page_config(
    page_title="VEER PRO TERMINAL", page_icon="⚡", layout="wide"
)

# बैकग्राउंड को सफेद और टेक्स्ट को काला करने के लिए कस्टम CSS (फर्स्ट क्लास परफॉरमेंस के लिए)
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
        border: 1px solid #CCC !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ऐप का मुख्य शीर्षक
st.markdown(
    "<h1 style='text-align: center; color: #FF4B4B;'>⚡ VEER PRO TERMINAL (SMC &"
    " SCALPING) ⚡</h1>",
    unsafe_allow_html=True,
)

# कैटेगरी चयन
st.markdown("### Select Category:")
category = st.radio(
    "Category", ["Crypto", "Forex", "Stock", "Metal", "Energy"], horizontal=True
)

st.markdown("### Select Asset / Symbol:")

# यूज़र के लिए सिंबल इनपुट (जहाँ से चार्ट सीधे लोड होगा)
col_input, col_tf = st.columns([2, 1])

with col_input:
    symbol = st.text_input(
        "Enter Symbol (e.g., BINANCE:BTCUSDT, EURUSD, RELIANCE):",
        value="BINANCE:BTCUSDT",
    )

with col_tf:
    timeframe = st.selectbox("Timeframe", ["1", "5", "15", "60", "D"])

# ट्रेडिंगव्यू एडवांस्ड चार्ट विजेट (जो मोबाइल और डेस्कटॉप पर बेहद तेज़ और परफेक्ट काम करेगा)
tradingview_widget = f"""
<div class="tradingview-widget-container" style="height:550px;width:100%">
  <div id="tradingview_chart" style="height:100%;width:100%"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
  new TradingView.widget(
  {{
    "width": "100%",
    "height": "550",
    "symbol": "{symbol}",
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
    "container_id": "tradingview_chart"
  }});
  </script>
</div>
"""

# चार्ट को स्क्रीन पर रेंडर करना
components.html(tradingview_widget, height=570)

st.markdown("---")
st.markdown(
    f"👉 **Connected Successfully!** Active Symbol: `{symbol}` | Timeframe:"
    f" `{timeframe}m`"
)
