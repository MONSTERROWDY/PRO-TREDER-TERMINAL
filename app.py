import streamlit as st

# Page configuration
st.set_page_config(
    page_title="VEER PRO TERMINAL",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed" # साइडबार को डिफॉल्ट बंद रखा है ताकि इंटरफेस क्लीन दिखे
)

# Custom CSS for Premium Colorful Dark Theme
st.markdown("""
    <style>
    /* 1. Global Deep Dark Theme */
    .stApp {
        background: radial-gradient(circle at top right, #1a1f2e, #090d16) !important;
        color: #ffffff !important;
    }

    /* 2. Optimized Sidebar (User Profile) */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #131b2e 0%, #090d16 100%) !important;
        border-right: 1px solid #1f293d;
        color: #ffffff !important;
    }

    /* Sidebar Icons & Text Brightening */
    [data-testid="stSidebar"] div, [data-testid="stSidebar"] span, [data-testid="stSidebar"] p {
        color: #e0e7ff !important;
    }

    /* 3. Colorful UI Elements */
    .stButton>button {
        background: linear-gradient(90deg, #6366f1 0%, #a855f7 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3) !important;
    }

    /* Header Icons & Title */
    h1, h2, h3 { color: #ffffff !important; }
    
    /* 4. Tab Optimization for Color */
    .stTabs [data-baseweb="tab"] {
        color: #94a3b8 !important;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        color: #6366f1 !important;
        border-bottom: 2px solid #6366f1 !important;
    }
    
    /* Remove default Streamlit padding for cleaner look */
    .block-container { padding-top: 2rem !important; }
    </style>
""", unsafe_allow_html=True)

# --- Sidebar Logic with Color Optimization ---
with st.sidebar:
    st.markdown("### 👤 User Profile")
    st.markdown("---")
    st.markdown(f"👋 **Hello, VIKAS**")
    st.markdown(f"📱 **ID:** `7479465676`")
    st.markdown(f"✨ **Status:** `Free User`")
    st.markdown("---")
    if st.button("🚪 Logout"):
        st.rerun()

# --- Main App Interface ---
st.title("🚀 VEER PRO TRADING TERMINAL")
st.markdown("---")

# Navigation Tabs
tab1, tab2, tab3 = st.tabs(["⚡ Pro Terminal", "📈 Live Chart", "🏆 Accuracy"])

with tab1:
    st.subheader("Configuration")
    market = st.selectbox("Market Category", ["TIER 1", "TIER 2 (Altcoins)"])
    asset = st.selectbox("Select Asset", ["BTCUSDT", "ETHUSDT"])
    
    # Colorful Metric Display
    col1, col2 = st.columns(2)
    col1.metric("Live Price", "$64,741", "+1.2%")
    col2.metric("Signal Status", "ACTIVE", "BULLISH")

with tab2:
    st.info("Live Chart is loading...")

with tab3:
    st.write("Accuracy: 84.5%")

# Footer
st.markdown("<br><br><p style='text-align: center; color: #475569;'>© 2026 VEER PRO TERMINAL</p>", unsafe_allow_html=True)
