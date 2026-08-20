import datetime
import sqlite3
import pandas as pd
import requests
import streamlit as st

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Veer Pro Terminal", layout="wide")

# --- DATABASE INITIALIZATION ---
def get_db_connection():
    return sqlite3.connect("veervip_terminal.db", check_same_thread=False)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Table structure updated for flexibility
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            name TEXT,
            username TEXT,
            tier TEXT DEFAULT 'VIP Platinum',
            demo_balance REAL DEFAULT 10000.0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS paper_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            symbol TEXT,
            action TEXT,
            entry_price REAL,
            amount REAL,
            leverage INTEGER,
            status TEXT DEFAULT 'OPEN',
            time TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# --- FIXED AUTHENTICATION LOGIC ---
def verify_user_credentials(input_val, password):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # यहाँ हम सीधे इनपुट को स्ट्रिप करके सर्च कर रहे हैं, बिना किसी तामझाम के
        clean_input = input_val.strip()
        
        # ईमेल (या मोबाइल नंबर) से सीधे मैच करें
        cursor.execute("SELECT email, password, name, username, tier, demo_balance FROM users WHERE email = ?", (clean_input,))
        res = cursor.fetchone()
        
        conn.close()

        if res:
            # res[1] पासवर्ड है, res[0] ईमेल/मोबाइल है
            if str(res[1]) == str(password):
                return {
                    "success": True,
                    "email": res[0],
                    "name": res[2],
                    "username": res[3],
                    "tier": res[4],
                    "balance": res[5]
                }
        return {"success": False}
    except Exception:
        return {"success": False}

# --- SESSION & UI ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align:center;'>⚡ VEER PRO LOGIN</h2>", unsafe_allow_html=True)
    with st.form("login_form"):
        login_input = st.text_input("Mobile / Email")
        login_pass = st.text_input("Password", type="password")
        submit = st.form_submit_button("Access Terminal")
        
        if submit:
            auth = verify_user_credentials(login_input, login_pass)
            if auth["success"]:
                st.session_state.logged_in = True
                st.session_state.email = auth["email"]
                st.session_state.name = auth["name"]
                st.session_state.demo_balance = auth["balance"]
                st.rerun()
            else:
                st.error("Invalid Login! Check your ID and Password.")
else:
    # --- DASHBOARD UI ---
    st.sidebar.success(f"Welcome, {st.session_state.get('name', 'User')}")
    st.write(f"Logged in as: {st.session_state.email}")
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()
    st.write("---")
    st.subheader("Market Dashboard")
    st.metric("Wallet Balance", f"${st.session_state.get('demo_balance', 0):,.2f}")
