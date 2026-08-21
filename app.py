# VEER PRO TERMINAL
# Multi-Market AI Trading & Paper Trading Dashboard
# ============================================================

import sqlite3
import hashlib
import secrets
import time
from datetime import datetime, timedelta

import pandas as pd
import requests
import streamlit as st
import plotly.graph_objects as go


# ============================================================
# 1. PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Veer Pro Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# 2. GLOBAL CSS
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background:
            radial-gradient(
                circle at 50% 0%,
                #171b23 0%,
                #0b0e11 45%,
                #07090c 100%
            );
    }

    html, body, [class*="css"] {
        font-family: Inter, Arial, sans-serif;
    }

    h1, h2, h3, h4, h5, h6 {
        color: #f5f5f5 !important;
    }

    p, label, span {
        color: #c8ccd3;
    }

    .main-title {
        font-size: 34px;
        font-weight: 900;
        letter-spacing: -1px;
        color: #fcd535;
        margin-bottom: 2px;
    }

    .subtitle {
        color: #848e9c;
        font-size: 13px;
        margin-bottom: 20px;
    }

    .card {
        background: linear-gradient(
            145deg,
            #181c24,
            #101318
        );
        border: 1px solid #2b313a;
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 12px;
    }

    .metric-title {
        color: #848e9c;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: .7px;
    }

    .metric-value {
        color: #ffffff;
        font-size: 24px;
        font-weight: 800;
        margin-top: 5px;
    }

    .green {
        color: #0ecb81 !important;
        font-weight: 800;
    }

    .red {
        color: #f6465d !important;
        font-weight: 800;
    }

    .yellow {
        color: #fcd535 !important;
        font-weight: 800;
    }

    .signal {
        border: 1px solid #fcd535;
        background:
            linear-gradient(
                145deg,
                #241e0b,
                #12100a
            );
        border-radius: 14px;
        padding: 20px;
        box-shadow: 0 0 25px rgba(252,213,53,.08);
    }

    .signal-title {
        color: #fcd535;
        font-size: 22px;
        font-weight: 900;
    }

    .small-muted {
        color: #848e9c;
        font-size: 11px;
    }

    .vip {
        border: 1px solid #fcd535;
        border-radius: 10px;
        padding: 12px;
        text-align: center;
        background: #211b08;
        color: #fcd535;
        font-weight: 800;
    }

    .status-live {
        color: #0ecb81;
        font-weight: 800;
    }

    .status-paper {
        color: #fcd535;
        font-weight: 800;
    }

    .stButton > button {
        width: 100%;
        min-height: 42px;
        border-radius: 8px;
        font-weight: 800;
        border: 1px solid #2b313a;
        background: linear-gradient(
            135deg,
            #fcd535,
            #f0b90b
        );
        color: #0b0e11;
    }

    .stButton > button:hover {
        background: #ffffff;
        color: #000000;
    }

    input, textarea {
        background-color: #0d1014 !important;
        color: white !important;
    }

    [data-testid="stSidebar"] {
        background:
            linear-gradient(
                180deg,
                #101318,
                #080a0d
            );
        border-right: 1px solid #242932;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 3. DATABASE
# ============================================================

DB_FILE = "users_database.db"


def db():
    return sqlite3.connect(
        DB_FILE,
        check_same_thread=False
    )


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt.encode(),
        120000,
    ).hex()

    return f"{salt}${hashed}"


def verify_password(password: str, stored: str) -> bool:

    # Backward compatibility with old plain-text database
    if "$" not in stored:
        return secrets.compare_digest(password, stored)

    try:
        salt, expected = stored.split("$", 1)

        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            salt.encode(),
            120000,
        ).hex()

        return secrets.compare_digest(
            actual,
            expected
        )

    except Exception:
        return False


def init_db():

    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            username TEXT,
            avatar TEXT,
            tier TEXT DEFAULT 'Free User',
            created_at TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS promo_codes (
            code TEXT PRIMARY KEY,
            duration TEXT,
            max_uses INTEGER DEFAULT 1,
            used_count INTEGER DEFAULT 0,
            active INTEGER DEFAULT 1
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            symbol TEXT,
            side TEXT,
            order_type TEXT,
            price REAL,
            quantity REAL,
            total REAL,
            status TEXT,
            created_at TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS portfolio (
            email TEXT,
            symbol TEXT,
            quantity REAL,
            avg_price REAL,
            PRIMARY KEY(email, symbol)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS watchlist (
            email TEXT,
            symbol TEXT,
            PRIMARY KEY(email, symbol)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            symbol TEXT,
            condition TEXT,
            target REAL,
            active INTEGER DEFAULT 1
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            type TEXT,
            amount REAL,
            note TEXT,
            created_at TEXT
        )
        """
    )

    # Add missing columns to older database
    existing_columns = []

    try:
        cur.execute("PRAGMA table_info(users)")
        existing_columns = [
            row[1] for row in cur.fetchall()
        ]
    except Exception:
        pass

    if "created_at" not in existing_columns:
        try:
            cur.execute(
                "ALTER TABLE users ADD COLUMN created_at TEXT"
            )
        except Exception:
            pass

    # Demo admin
    cur.execute(
        "SELECT email FROM users WHERE email = ?",
        ("admin@gmail.com",)
    )

    if not cur.fetchone():

        cur.execute(
            """
            INSERT INTO users
            (email,password,name,username,avatar,tier,created_at)
            VALUES(?,?,?,?,?,?,?)
            """,
            (
                "admin@gmail.com",
                hash_password("password123"),
                "Pro Master",
                "admin_master",
                "",
                "Premium Member (Lifetime)",
                datetime.now().isoformat(),
            ),
        )

    # Promo codes
    promos = [
        ("VEER3DAYS", "3 Days"),
        ("VEERPREMIUM30", "30 Days"),
        ("VEERPREMIUM1Y", "1 Year"),
        ("VEERLIFETIME", "Lifetime"),
    ]

    for code, duration in promos:

        cur.execute(
            "SELECT code FROM promo_codes WHERE code = ?",
            (code,)
        )

        if not cur.fetchone():

            cur.execute(
                """
                INSERT INTO promo_codes
                (code,duration,max_uses,used_count,active)
                VALUES(?,?,?,?,?)
                """,
                (
                    code,
                    duration,
                    1,
                    0,
                    1,
                ),
            )

    conn.commit()
    conn.close()


init_db()


# ============================================================
# 4. USER FUNCTIONS
# ============================================================

def get_user(email):

    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT email,password,name,username,avatar,tier
        FROM users
        WHERE email=?
        """,
        (email.strip().lower(),)
    )

    row = cur.fetchone()
    conn.close()

    return row


def register_user(
    email,
    password,
    name,
    username
):

    try:

        conn = db()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO users
            (email,password,name,username,avatar,tier,created_at)
            VALUES(?,?,?,?,?,?,?)
            """,
            (
                email.lower().strip(),
                hash_password(password),
                name.strip(),
                username.strip(),
                "",
                "Free User",
                datetime.now().isoformat(),
            ),
        )

        conn.commit()
        conn.close()

        return True

    except sqlite3.IntegrityError:
        return False


def update_profile(
    email,
    name,
    username,
    avatar
):

    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE users
        SET name=?,username=?,avatar=?
        WHERE email=?
        """,
        (
            name,
            username,
            avatar,
            email,
        ),
    )

    conn.commit()
    conn.close()


# ============================================================
# 5. MARKET DATA
# ============================================================

CRYPTO_SYMBOLS = [
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
    "SOLUSDT",
    "XRPUSDT",
    "ADAUSDT",
    "DOGEUSDT",
    "AVAXUSDT",
    "LINKUSDT",
    "DOTUSDT",
]


def fetch_crypto():

    try:

        url = (
            "https://api.binance.com/api/v3/ticker/24hr"
        )

        response = requests.get(
            url,
            params={
                "symbols": str(CRYPTO_SYMBOLS)
            },
            timeout=5,
        )

        if response.status_code != 200:
            return {}

        data = response.json()

        result = {}

        for item in data:

            result[item["symbol"]] = {
                "price": float(item["lastPrice"]),
                "change": float(item["priceChangePercent"]),
                "volume": float(item["quoteVolume"]),
            }

        return result

    except Exception:
        return {}


def fallback_markets():

    return {

        "BTCUSDT": {
            "price": 68417.51,
            "change": 1.23,
            "volume": 0,
        },

        "ETHUSDT": {
            "price": 3540.49,
            "change": -0.45,
            "volume": 0,
        },

        "BNBUSDT": {
            "price": 610.25,
            "change": 0.72,
            "volume": 0,
        },

        "SOLUSDT": {
            "price": 145.06,
            "change": 2.45,
            "volume": 0,
        },

        "XRPUSDT": {
            "price": 0.61,
            "change": 1.20,
            "volume": 0,
        },

        "RELIANCE": {
            "price": 2980.50,
            "change": 0.85,
            "volume": 0,
        },

        "TATASTEEL": {
            "price": 158.20,
            "change": -0.40,
            "volume": 0,
        },

        "NIFTY": {
            "price": 24780.00,
            "change": 0.62,
            "volume": 0,
        },

        "SENSEX": {
            "price": 81100.00,
            "change": 0.41,
            "volume": 0,
        },

        "AAPL": {
            "price": 224.50,
            "change": 1.12,
            "volume": 0,
        },

        "TSLA": {
            "price": 245.80,
            "change": -1.45,
            "volume": 0,
        },

        "NVDA": {
            "price": 128.40,
            "change": 3.25,
            "volume": 0,
        },

        "EURUSD": {
            "price": 1.0924,
            "change": 0.15,
            "volume": 0,
        },

        "GBPUSD": {
            "price": 1.3012,
            "change": -0.22,
            "volume": 0,
        },

        "USDJPY": {
            "price": 147.50,
            "change": 0.45,
            "volume": 0,
        },

        "GOLD": {
            "price": 2512.40,
            "change": 0.50,
            "volume": 0,
        },

        "SILVER": {
            "price": 29.30,
            "change": 0.71,
            "volume": 0,
        },

        "CRUDEOIL": {
            "price": 76.20,
            "change": -1.10,
            "volume": 0,
        },
    }


@st.cache_data(ttl=15)
def get_market_data():

    data = fallback_markets()

    live = fetch_crypto()

    if live:
        data.update(live)

    return data


MARKETS = get_market_data()


# ============================================================
# 6. CHART DATA
# ============================================================

@st.cache_data(ttl=30)
def get_chart_data(symbol="BTCUSDT"):

    try:

        url = (
            "https://api.binance.com/api/v3/klines"
        )

        response = requests.get(
            url,
            params={
                "symbol": symbol,
                "interval": "1h",
                "limit": 100,
            },
            timeout=5,
        )

        if response.status_code != 200:
            raise Exception()

        rows = response.json()

        df = pd.DataFrame(
            rows,
            columns=[
                "time",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "x1",
                "x2",
                "x3",
                "x4",
                "x5",
                "x6",
            ],
        )

        for col in [
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]:
            df[col] = df[col].astype(float)

        df["time"] = pd.to_datetime(
            df["time"],
            unit="ms"
        )

        return df

    except Exception:

        # Synthetic chart for non-crypto/demo markets
        base = MARKETS.get(
            symbol,
            {"price": 100}
        )["price"]

        rows = []

        price = base

        for i in range(100):

            price *= (
                1 +
                ((i % 7) - 3) / 1000
            )

            rows.append(
                {
                    "time":
                        datetime.now()
                        - timedelta(hours=100-i),

                    "open": price * .997,
                    "high": price * 1.006,
                    "low": price * .994,
                    "close": price,
                    "volume": 1000 + i * 10,
                }
            )

        return pd.DataFrame(rows)


# ============================================================
# 7. TECHNICAL ANALYSIS
# ============================================================

def calculate_indicators(df):

    df = df.copy()

    df["EMA20"] = (
        df["close"]
        .ewm(span=20)
        .mean()
    )

    df["EMA50"] = (
        df["close"]
        .ewm(span=50)
        .mean()
    )

    delta = df["close"].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss.replace(0, 1e-9)

    df["RSI"] = 100 - (
        100 / (1 + rs)
    )

    ema12 = (
        df["close"]
        .ewm(span=12)
        .mean()
    )

    ema26 = (
        df["close"]
        .ewm(span=26)
        .mean()
    )

    df["MACD"] = ema12 - ema26

    df["Signal"] = (
        df["MACD"]
        .ewm(span=9)
        .mean()
    )

    mid = (
        df["close"]
        .rolling(20)
        .mean()
    )

    std = (
        df["close"]
        .rolling(20)
        .std()
    )

    df["BB_UPPER"] = mid + 2 * std
    df["BB_LOWER"] = mid - 2 * std

    return df


# ============================================================
# 8. AI ANALYSIS ENGINE
# ============================================================

def ai_analysis(df):

    df = calculate_indicators(df)

    last = df.iloc[-1]

    score = 50
    reasons = []

    if last["EMA20"] > last["EMA50"]:
        score += 15
        reasons.append(
            "Short-term trend is above the long-term trend."
        )
    else:
        score -= 15
        reasons.append(
            "Short-term trend is below the long-term trend."
        )

    if last["RSI"] < 30:
        score += 10
        reasons.append(
            "RSI indicates an oversold condition."
        )

    elif last["RSI"] > 70:
        score -= 10
        reasons.append(
            "RSI indicates an overbought condition."
        )

    else:
        score += 5
        reasons.append(
            "RSI remains in a normal momentum zone."
        )

    if last["MACD"] > last["Signal"]:
        score += 10
        reasons.append(
            "MACD momentum is positive."
        )
    else:
        score -= 10
        reasons.append(
            "MACD momentum is negative."
        )

    score = max(0, min(100, int(score)))

    if score >= 80:
        signal = "STRONG BUY"

    elif score >= 65:
        signal = "BUY"

    elif score >= 55:
        signal = "HOLD / BULLISH"

    elif score >= 45:
        signal = "HOLD"

    elif score >= 30:
        signal = "SELL"

    else:
        signal = "STRONG SELL"

    return {
        "score": score,
        "signal": signal,
        "rsi": float(last["RSI"]),
        "macd": float(last["MACD"]),
        "ema20": float(last["EMA20"]),
        "ema50": float(last["EMA50"]),
        "reasons": reasons,
    }


# ============================================================
# 9. PORTFOLIO FUNCTIONS
# ============================================================

def get_positions(email):

    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT symbol,quantity,avg_price
        FROM portfolio
        WHERE email=? AND quantity > 0
        """,
        (email,)
    )

    rows = cur.fetchall()

    conn.close()

    return rows


def execute_paper_order(
    email,
    symbol,
    side,
    quantity,
    price,
):

    quantity = float(quantity)
    price = float(price)

    if quantity <= 0 or price <= 0:
        return False, "Invalid quantity or price."

    total = quantity * price

    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT quantity,avg_price
        FROM portfolio
        WHERE email=? AND symbol=?
        """,
        (email, symbol)
    )

    row = cur.fetchone()

    current_qty = row[0] if row else 0
    current_avg = row[1] if row else 0

    if side == "BUY":

        new_qty = current_qty + quantity

        if new_qty > 0:
            new_avg = (
                (
                    current_qty * current_avg
                    +
                    quantity * price
                )
                /
                new_qty
            )
        else:
            new_avg = price

        cur.execute(
            """
            INSERT INTO portfolio
            (email,symbol,quantity,avg_price)
            VALUES(?,?,?,?)
            ON CONFLICT(email,symbol)
            DO UPDATE SET
            quantity=excluded.quantity,
            avg_price=excluded.avg_price
            """,
            (
                email,
                symbol,
                new_qty,
                new_avg,
            ),
        )

    elif side == "SELL":

        if current_qty < quantity:
            conn.close()

            return (
                False,
                "Insufficient paper position."
            )

        new_qty = current_qty - quantity

        cur.execute(
            """
            UPDATE portfolio
            SET quantity=?
            WHERE email=? AND symbol=?
            """,
            (
                new_qty,
                email,
                symbol,
            ),
        )

    else:
        conn.close()

        return False, "Invalid side."

    cur.execute(
        """
        INSERT INTO orders
        (email,symbol,side,order_type,price,
         quantity,total,status,created_at)
        VALUES(?,?,?,?,?,?,?,?,?)
        """,
        (
            email,
            symbol,
            side,
            "MARKET",
            price,
            quantity,
            total,
            "FILLED",
            datetime.now().isoformat(),
        ),
    )

    conn.commit()
    conn.close()

    return True, f"{side} order executed successfully."


def get_orders(email):

    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            id,symbol,side,order_type,
            price,quantity,total,status,created_at
        FROM orders
        WHERE email=?
        ORDER BY id DESC
        LIMIT 100
        """,
        (email,)
    )

    rows = cur.fetchall()

    conn.close()

    return rows


# ============================================================
# 10. WATCHLIST
# ============================================================

def get_watchlist(email):

    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT symbol
        FROM watchlist
        WHERE email=?
        """,
        (email,)
    )

    result = [
        row[0]
        for row in cur.fetchall()
    ]

    conn.close()

    return result


def toggle_watchlist(email, symbol):

    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT symbol
        FROM watchlist
        WHERE email=? AND symbol=?
        """,
        (
            email,
            symbol,
        ),
    )

    exists = cur.fetchone()

    if exists:

        cur.execute(
            """
            DELETE FROM watchlist
            WHERE email=? AND symbol=?
            """,
            (
                email,
                symbol,
            ),
        )

    else:

        cur.execute(
            """
            INSERT INTO watchlist(email,symbol)
            VALUES(?,?)
            """,
            (
                email,
                symbol,
            ),
        )

    conn.commit()
    conn.close()


# ============================================================
# 11. SESSION
# ============================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "email" not in st.session_state:
    st.session_state.email = ""

if "name" not in st.session_state:
    st.session_state.name = ""

if "username" not in st.session_state:
    st.session_state.username = ""

if "tier" not in st.session_state:
    st.session_state.tier = "Free User"


# ============================================================
# 12. AUTH SCREEN
# ============================================================

def auth_screen():

    st.markdown(
        "<br><br>",
        unsafe_allow_html=True
    )

    left, center, right = st.columns(
        [1, 1.5, 1]
    )

    with center:

        st.markdown(
            """
            <div class="card">

            <div style="
                text-align:center;
                font-size:32px;
                font-weight:900;
                color:#fcd535;
            ">
                ⚡ VEER PRO
            </div>

            <div style="
                text-align:center;
                color:#848e9c;
                margin-bottom:25px;
            ">
                AI Multi-Market Trading Terminal
            </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        login_tab, register_tab = st.tabs(
            [
                "🔐 Sign In",
                "📝 Create Account",
            ]
        )

        with login_tab:

            with st.form("login"):

                email = st.text_input(
                    "Email"
                )

                password = st.text_input(
                    "Password",
                    type="password"
                )

                submit = st.form_submit_button(
                    "ACCESS TERMINAL"
                )

                if submit:

                    user = get_user(
                        email.strip().lower()
                    )

                    if (
                        user
                        and verify_password(
                            password,
                            user[1]
                        )
                    ):

                        # Upgrade old plaintext password
                        if "$" not in user[1]:

                            conn = db()
                            cur = conn.cursor()

                            cur.execute(
                                """
                                UPDATE users
                                SET password=?
                                WHERE email=?
                                """,
                                (
                                    hash_password(password),
                                    user[0],
                                ),
                            )

                            conn.commit()
                            conn.close()

                        st.session_state.logged_in = True
                        st.session_state.email = user[0]
                        st.session_state.name = user[2]
                        st.session_state.username = (
                            user[3] or "trader"
                        )
                        st.session_state.tier = (
                            user[5] or "Free User"
                        )

                        st.rerun()

                    else:

                        st.error(
                            "Invalid email or password."
                        )

        with register_tab:

            with st.form("register"):

                name = st.text_input(
                    "Full Name"
                )

                username = st.text_input(
                    "Username"
                )

                email = st.text_input(
                    "Email"
                )

                password = st.text_input(
                    "Password",
                    type="password"
                )

                submit = st.form_submit_button(
                    "CREATE ACCOUNT"
                )

                if submit:

                    if (
                        not name
                        or not username
                        or not email
                        or len(password) < 6
                    ):

                        st.warning(
                            "Please fill all fields. "
                            "Password must contain at least 6 characters."
                        )

                    else:

                        created = register_user(
                            email,
                            password,
                            name,
                            username,
                        )

                        if created:

                            st.success(
                                "Account created. Please sign in."
                            )

                        else:

                            st.error(
                                "Email already exists."
                            )

        st.markdown(
            """
            <div class="small-muted"
                 style="text-align:center;margin-top:15px;">
            Demo Admin:
            admin@gmail.com / password123
            </div>
            """,
            unsafe_allow_html=True,
        )


if not st.session_state.logged_in:

    auth_screen()

    st.stop()


# ============================================================
# 13. SIDEBAR
# ============================================================

email = st.session_state.email

with st.sidebar:

    st.markdown(
        """
        <div style="
            font-size:24px;
            font-weight:900;
            color:#fcd535;
        ">
        ⚡ VEER PRO
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption(
        "AI Multi-Market Terminal"
    )

    if (
        "Premium" in st.session_state.tier
        or "Lifetime" in st.session_state.tier
    ):

        st.markdown(
            """
            <div class="vip">
            👑 VIP ELITE MEMBER
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    menu = st.radio(
        "NAVIGATION",
        [
            "🏠 Dashboard",
            "📊 Markets",
            "⚡ Trade",
            "🤖 AI Signals",
            "💼 Portfolio",
            "⭐ Watchlist",
            "🔔 Alerts",
            "📈 Backtest",
            "👤 Profile",
            "👑 Subscription",
            "🛠️ Admin",
        ],
    )

    st.markdown("---")

    st.markdown(
        f"""
        **User:** {st.session_state.name}

        **@{st.session_state.username}**

        **Tier:** `{st.session_state.tier}`

        **Mode:** 🟡 PAPER TRADING
        """
    )

    if st.button("🚪 Logout"):

        st.session_state.logged_in = False
        st.session_state.email = ""

        st.rerun()


# ============================================================
# 14. DASHBOARD
# ============================================================

if menu == "🏠 Dashboard":

    st.markdown(
        '<div class="main-title">Veer Pro Dashboard</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="subtitle">'
        'Professional market intelligence and paper trading terminal'
        '</div>',
        unsafe_allow_html=True,
    )

    positions = get_positions(email)

    total_value = 0

    position_rows = []

    for symbol, qty, avg in positions:

        price = MARKETS.get(
            symbol,
            {"price": avg}
        )["price"]

        value = qty * price

        total_value += value

        position_rows.append(
            {
                "Symbol": symbol,
                "Quantity": qty,
                "Avg Price": avg,
                "Current Price": price,
                "Value": value,
                "P&L":
                    (price - avg) * qty,
            }
        )

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.markdown(
            f"""
            <div class="card">
            <div class="metric-title">
            Portfolio Value
            </div>
            <div class="metric-value">
            ${total_value:,.2f}
            </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:

        pnl = sum(
            row["P&L"]
            for row in position_rows
        )

        cls = "green" if pnl >= 0 else "red"

        st.markdown(
            f"""
            <div class="card">
            <div class="metric-title">
            Unrealized P&L
            </div>
            <div class="metric-value {cls}">
            ${pnl:,.2f}
            </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:

        st.markdown(
            """
            <div class="card">
            <div class="metric-title">
            Trading Mode
            </div>
            <div class="metric-value yellow">
            PAPER
            </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c4:

        st.markdown(
            f"""
            <div class="card">
            <div class="metric-title">
            Market Assets
            </div>
            <div class="metric-value">
            {len(MARKETS)}
            </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.subheader("🔥 Market Movers")

    mover_rows = []

    for symbol, data in MARKETS.items():

        mover_rows.append(
            {
                "Symbol": symbol,
                "Price": data["price"],
                "24H %": data["change"],
            }
        )

    mover_df = pd.DataFrame(
        mover_rows
    ).sort_values(
        "24H %",
        ascending=False
    )

    st.dataframe(
        mover_df,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# 15. MARKETS
# ============================================================

elif menu == "📊 Markets":

    st.markdown(
        '<div class="main-title">Markets</div>',
        unsafe_allow_html=True,
    )

    categories = {
        "Crypto": [
            "BTCUSDT",
            "ETHUSDT",
            "BNBUSDT",
            "SOLUSDT",
            "XRPUSDT",
            "ADAUSDT",
            "DOGEUSDT",
        ],

        "Indian Market": [
            "NIFTY",
            "SENSEX",
            "RELIANCE",
            "TATASTEEL",
        ],

        "US Stocks": [
            "AAPL",
            "TSLA",
            "NVDA",
        ],

        "Forex": [
            "EURUSD",
            "GBPUSD",
            "USDJPY",
        ],

        "Commodities": [
            "GOLD",
            "SILVER",
            "CRUDEOIL",
        ],
    }

    category = st.selectbox(
        "Market Category",
        list(categories.keys())
    )

    rows = []

    for symbol in categories[category]:

        data = MARKETS.get(
            symbol,
            {
                "price": 0,
                "change": 0,
                "volume": 0,
            }
        )

        rows.append(
            {
                "Symbol": symbol,
                "Price": data["price"],
                "24H Change %": data["change"],
                "Volume": data["volume"],
            }
        )

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# 16. TRADE
# ============================================================

elif menu == "⚡ Trade":

    st.markdown(
        '<div class="main-title">Trading Terminal</div>',
        unsafe_allow_html=True,
    )

    st.warning(
        "Paper Trading Mode — orders do not use real money."
    )

    symbol = st.selectbox(
        "Trading Pair / Asset",
        list(MARKETS.keys())
    )

    data = MARKETS[symbol]

    price = data["price"]

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "Price",
            f"{price:,.4f}"
        )

    with c2:
        st.metric(
            "24H Change",
            f"{data['change']:.2f}%"
        )

    with c3:
        st.metric(
            "AI Status",
            "Available"
        )

    chart_df = get_chart_data(
        symbol
    )

    chart_df = calculate_indicators(
        chart_df
    )

    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(
            x=chart_df["time"],
            open=chart_df["open"],
            high=chart_df["high"],
            low=chart_df["low"],
            close=chart_df["close"],
            name="Price",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=chart_df["time"],
            y=chart_df["EMA20"],
            name="EMA 20",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=chart_df["time"],
            y=chart_df["EMA50"],
            name="EMA 50",
        )
    )

    fig.update_layout(
        height=550,
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        margin=dict(
            l=10,
            r=10,
            t=30,
            b=10,
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    st.subheader("Place Paper Order")

    col1, col2 = st.columns(2)

    with col1:

        side = st.radio(
            "Side",
            [
                "BUY",
                "SELL",
            ],
            horizontal=True,
        )

        quantity = st.number_input(
            "Quantity",
            min_value=0.000001,
            value=0.001,
            step=0.001,
        )

    with col2:

        order_type = st.selectbox(
            "Order Type",
            [
                "MARKET",
            ]
        )

        trade_price = st.number_input(
            "Execution Price",
            min_value=0.000001,
            value=float(price),
        )

    if st.button(
        f"🚀 {side} {symbol}"
    ):

        ok, message = execute_paper_order(
            email,
            symbol,
            side,
            quantity,
            trade_price,
        )

        if ok:
            st.success(message)
            st.rerun()
        else:
            st.error(message)


# ============================================================
# 17. AI SIGNALS
# ============================================================

elif menu == "🤖 AI Signals":

    st.markdown(
        '<div class="main-title">AI Market Scanner</div>',
        unsafe_allow_html=True,
    )

    symbol = st.selectbox(
        "Select Asset",
        list(MARKETS.keys())
    )

    df = get_chart_data(symbol)

    result = ai_analysis(df)

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "AI Score",
            f"{result['score']}/100"
        )

    with c2:
        st.metric(
            "Signal",
            result["signal"]
        )

    with c3:
        st.metric(
            "RSI",
            f"{result['rsi']:.2f}"
        )

    with c4:
        st.metric(
            "24H Change",
            f"{MARKETS[symbol]['change']:.2f}%"
        )

    st.markdown(
        f"""
        <div class="signal">
            <div class="signal-title">
            🤖 {symbol} — {result['signal']}
            </div>

            <p>
            AI Technical Score:
            <b>{result['score']}/100</b>
            </p>

            <p>
            This is an analytical signal, not a guarantee of profit.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Analysis Factors")

    for reason in result["reasons"]:

        st.write(
            f"• {reason}"
        )

    st.subheader("Indicators")

    indicator_df = pd.DataFrame(
        [
            {
                "Indicator": "RSI",
                "Value": result["rsi"],
            },
            {
                "Indicator": "EMA 20",
                "Value": result["ema20"],
            },
            {
                "Indicator": "EMA 50",
                "Value": result["ema50"],
            },
            {
                "Indicator": "MACD",
                "Value": result["macd"],
            },
        ]
    )

    st.dataframe(
        indicator_df,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# 18. PORTFOLIO
# ============================================================

elif menu == "💼 Portfolio":

    st.markdown(
        '<div class="main-title">Portfolio</div>',
        unsafe_allow_html=True,
    )

    positions = get_positions(email)

    if not positions:

        st.info(
            "Your paper portfolio is empty. "
            "Open the Trade section to place a paper order."
        )

    else:

        rows = []

        for symbol, qty, avg in positions:

            current = MARKETS.get(
                symbol,
                {"price": avg}
            )["price"]

            value = qty * current
            pnl = (current - avg) * qty

            rows.append(
                {
                    "Asset": symbol,
                    "Quantity": qty,
                    "Average": avg,
                    "Current": current,
                    "Value": value,
                    "P&L": pnl,
                }
            )

        df = pd.DataFrame(rows)

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
        )

        st.subheader(
            "Portfolio Allocation"
        )

        if df["Value"].sum() > 0:

            fig = go.Figure(
                data=[
                    go.Pie(
                        labels=df["Asset"],
                        values=df["Value"],
                        hole=.55,
                    )
                ]
            )

            fig.update_layout(
                template="plotly_dark"
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )


# ============================================================
# 19. WATCHLIST
# ============================================================

elif menu == "⭐ Watchlist":

    st.markdown(
        '<div class="main-title">Watchlist</div>',
        unsafe_allow_html=True,
    )

    selected = st.selectbox(
        "Add / Remove Asset",
        list(MARKETS.keys())
    )

    if st.button(
        "⭐ Toggle Watchlist"
    ):

        toggle_watchlist(
            email,
            selected
        )

        st.rerun()

    watchlist = get_watchlist(
        email
    )

    if not watchlist:

        st.info(
            "Your watchlist is empty."
        )

    else:

        rows = []

        for symbol in watchlist:

            data = MARKETS[symbol]

            rows.append(
                {
                    "Symbol": symbol,
                    "Price": data["price"],
                    "24H Change %":
                        data["change"],
                }
            )

        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# 20. ALERTS
# ============================================================

elif menu == "🔔 Alerts":

    st.markdown(
        '<div class="main-title">Price Alerts</div>',
        unsafe_allow_html=True,
    )

    symbol = st.selectbox(
        "Asset",
        list(MARKETS.keys())
    )

    condition = st.selectbox(
        "Condition",
        [
            "ABOVE",
            "BELOW",
        ]
    )

    target = st.number_input(
        "Target Price",
        min_value=0.000001,
        value=float(
            MARKETS[symbol]["price"]
        ),
    )

    if st.button(
        "🔔 Create Alert"
    ):

        conn = db()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO alerts
            (email,symbol,condition,target,active)
            VALUES(?,?,?,?,1)
            """,
            (
                email,
                symbol,
                condition,
                target,
            ),
        )

        conn.commit()
        conn.close()

        st.success(
            "Alert created."
        )

    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id,symbol,condition,target,active
        FROM alerts
        WHERE email=?
        ORDER BY id DESC
        """,
        (email,)
    )

    alerts = cur.fetchall()

    conn.close()

    if alerts:

        st.dataframe(
            pd.DataFrame(
                alerts,
                columns=[
                    "ID",
                    "Symbol",
                    "Condition",
                    "Target",
                    "Active",
                ],
            ),
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# 21. BACKTEST
# ============================================================

elif menu == "📈 Backtest":

    st.markdown(
        '<div class="main-title">Strategy Backtester</div>',
        unsafe_allow_html=True,
    )

    symbol = st.selectbox(
        "Asset",
        [
            "BTCUSDT",
            "ETHUSDT",
            "SOLUSDT",
        ]
    )

    starting_capital = st.number_input(
        "Starting Capital",
        min_value=100.0,
        value=10000.0,
        step=100.0,
    )

    fast_period = st.number_input(
        "Fast EMA",
        min_value=2,
        max_value=50,
        value=20,
    )

    slow_period = st.number_input(
        "Slow EMA",
        min_value=10,
        max_value=200,
        value=50,
    )

    if st.button(
        "▶ Run Backtest"
    ):

        df = get_chart_data(
            symbol
        )

        df["FAST"] = (
            df["close"]
            .ewm(
                span=fast_period
            )
            .mean()
        )

        df["SLOW"] = (
            df["close"]
            .ewm(
                span=slow_period
            )
            .mean()
        )

        capital = starting_capital
        position = 0
        entry = 0
        trades = 0
        wins = 0

        for i in range(1, len(df)):

            fast_now = df.iloc[i]["FAST"]
            slow_now = df.iloc[i]["SLOW"]

            fast_prev = df.iloc[i-1]["FAST"]
            slow_prev = df.iloc[i-1]["SLOW"]

            current = df.iloc[i]["close"]

            # BUY crossover
            if (
                position == 0
                and fast_prev <= slow_prev
                and fast_now > slow_now
            ):

                position = capital / current
                entry = current
                capital = 0
                trades += 1

            # SELL crossover
            elif (
                position > 0
                and fast_prev >= slow_prev
                and fast_now < slow_now
            ):

                capital = position * current

                if current > entry:
                    wins += 1

                position = 0

        if position > 0:

            capital = position * df.iloc[-1]["close"]

        profit = capital - starting_capital

        return_pct = (
            profit / starting_capital
        ) * 100

        win_rate = (
            wins / trades * 100
            if trades
            else 0
        )

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Final Capital",
            f"${capital:,.2f}"
        )

        c2.metric(
            "Profit",
            f"${profit:,.2f}"
        )

        c3.metric(
            "Return",
            f"{return_pct:.2f}%"
        )

        c4.metric(
            "Win Rate",
            f"{win_rate:.2f}%"
        )

        st.info(
            "Backtest results are historical simulations and "
            "do not guarantee future performance."
        )


# ============================================================
# 22. PROFILE
# ============================================================

elif menu == "👤 Profile":

    st.markdown(
        '<div class="main-title">Profile</div>',
        unsafe_allow_html=True,
    )

    user = get_user(email)

    if user:

        with st.form("profile"):

            name = st.text_input(
                "Full Name",
                value=user[2],
            )

            username = st.text_input(
                "Username",
                value=user[3] or "",
            )

            avatar = st.text_input(
                "Avatar URL",
                value=user[4] or "",
            )

            if st.form_submit_button(
                "SAVE PROFILE"
            ):

                update_profile(
                    email,
                    name,
                    username,
                    avatar,
                )

                st.session_state.name = name
                st.session_state.username = username

                st.success(
                    "Profile updated."
                )

        st.markdown("---")

        st.write(
            f"**Email:** {email}"
        )

        st.write(
            f"**Subscription:** {user[5]}"
        )


# ============================================================
# 23. SUBSCRIPTION
# ============================================================

elif menu == "👑 Subscription":

    st.markdown(
        '<div class="main-title">Premium Subscription</div>',
        unsafe_allow_html=True,
    )

    st.info(
        f"Current Tier: {st.session_state.tier}"
    )

    code = st.text_input(
        "Enter Promo Code"
    )

    if st.button(
        "👑 Redeem Premium"
    ):

        code = code.strip().upper()

        conn = db()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT duration,max_uses,used_count,active
            FROM promo_codes
            WHERE code=?
            """,
            (code,)
        )

        row = cur.fetchone()

        if (
            row
            and row[3] == 1
            and row[2] < row[1]
        ):

            duration = row[0]

            tier = (
                f"Premium Member ({duration})"
            )

            cur.execute(
                """
                UPDATE users
                SET tier=?
                WHERE email=?
                """,
                (
                    tier,
                    email,
                ),
            )

            cur.execute(
                """
                UPDATE promo_codes
                SET used_count=used_count+1
                WHERE code=?
                """,
                (code,)
            )

            conn.commit()
            conn.close()

            st.session_state.tier = tier

            st.success(
                f"Premium activated: {duration}"
            )

            st.rerun()

        else:

            conn.close()

            st.error(
                "Invalid, inactive, or already-used promo code."
            )

    st.markdown("---")

    c1, c2, c3 = st.columns(3)

    with c1:

        st.markdown(
            """
            <div class="card">
            <h3>FREE</h3>
            <p>Basic market dashboard</p>
            <p>Basic watchlist</p>
            <p>Paper trading</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:

        st.markdown(
            """
            <div class="card">
            <h3>PRO</h3>
            <p>Advanced technical analysis</p>
            <p>AI scanner</p>
            <p>Backtesting</p>
            <p>Alerts</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:

        st.markdown(
            """
            <div class="card">
            <h3>ELITE</h3>
            <p>Advanced AI tools</p>
            <p>Portfolio analytics</p>
            <p>Advanced integrations</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# 24. ADMIN
# ============================================================

elif menu == "🛠️ Admin":

    if email != "admin@gmail.com":

        st.error(
            "Admin access required."
        )

        st.stop()

    st.markdown(
        '<div class="main-title">Admin Control Center</div>',
        unsafe_allow_html=True,
    )

    conn = db()
    cur = conn.cursor()

    cur.execute(
        "SELECT COUNT(*) FROM users"
    )

    total_users = cur.fetchone()[0]

    cur.execute(
        """
        SELECT COUNT(*)
        FROM users
        WHERE tier LIKE '%Premium%'
        """
    )

    premium_users = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM orders"
    )

    total_orders = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM promo_codes"
    )

    total_promos = cur.fetchone()[0]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Total Users",
        total_users
    )

    c2.metric(
        "Premium Users",
        premium_users
    )

    c3.metric(
        "Orders",
        total_orders
    )

    c4.metric(
        "Promo Codes",
        total_promos
    )

    st.markdown("---")

    st.subheader(
        "Registered Users"
    )

    cur.execute(
        """
        SELECT
            email,
            name,
            username,
            tier,
            created_at
        FROM users
        ORDER BY created_at DESC
        """
    )

    users = cur.fetchall()

    st.dataframe(
        pd.DataFrame(
            users,
            columns=[
                "Email",
                "Name",
                "Username",
                "Tier",
                "Created",
            ],
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader(
        "Grant Subscription"
    )

    if users:

        emails = [
            row[0]
            for row in users
        ]

        target = st.selectbox(
            "Select User",
            emails,
        )

        tier = st.selectbox(
            "Tier",
            [
                "Free User",
                "Premium Member (3 Days)",
                "Premium Member (30 Days)",
                "Premium Member (1 Year)",
                "Premium Member (Lifetime)",
            ],
        )

        if st.button(
            "🚀 Grant Access"
        ):

            cur.execute(
                """
                UPDATE users
                SET tier=?
                WHERE email=?
                """,
                (
                    tier,
                    target,
                ),
            )

            conn.commit()

            st.success(
                f"{tier} granted to {target}"
            )

            st.rerun()

    st.subheader(
        "Create Promo Code"
    )

    promo_code = st.text_input(
        "Promo Code"
    )

    duration = st.selectbox(
        "Duration",
        [
            "3 Days",
            "30 Days",
            "1 Year",
            "Lifetime",
        ],
    )

    max_uses = st.number_input(
        "Maximum Uses",
        min_value=1,
        value=1,
        step=1,
    )

    if st.button(
        "➕ Create Promo"
    ):

        try:

            cur.execute(
                """
                INSERT INTO promo_codes
                (code,duration,max_uses,used_count,active)
                VALUES(?,?,?,?,?)
                """,
                (
                    promo_code.strip().upper(),
                    duration,
                    max_uses,
                    0,
                    1,
                ),
            )

            conn.commit()

            st.success(
                "Promo code created."
            )

        except sqlite3.IntegrityError:

            st.error(
                "Promo code already exists."
            )

    conn.close()


# ============================================================
# 25. FOOTER
# ============================================================

st.markdown(
    """
    <div style="
        text-align:center;
        margin-top:50px;
        padding:20px;
        border-top:1px solid #242932;
        color:#626975;
        font-size:11px;
    ">
        ⚡ VEER PRO TERMINAL
        • Multi-Market Analytics
        • AI-Assisted Analysis
        • Paper Trading
        <br><br>
        Market data may be delayed or unavailable.
        AI signals are analytical tools and are not financial advice.
        Trading involves risk, including possible loss of capital.
    </div>
    """,
    unsafe_allow_html=True,
)
