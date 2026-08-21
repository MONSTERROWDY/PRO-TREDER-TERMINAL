# ============================================================
# VEER PRO TERMINAL
# LIVE AI ANALYSIS + DEMO TRADE + REAL MONEY LIVE ARCHITECTURE
# ============================================================

import os
import sqlite3
import hashlib
import secrets
from datetime import datetime

import pandas as pd
import requests
import streamlit as st
import plotly.graph_objects as go


# ============================================================
# 1. PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="VEER PRO TERMINAL",
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
        radial-gradient(circle at 50% 0%, #151a22 0%, #080a0d 48%, #050608 100%);
    color: #eaecef;
}

html, body, [class*="css"] {
    font-family: Inter, Arial, sans-serif;
}

h1,h2,h3,h4,h5,h6 {
    color: #f5f5f5 !important;
}

p, label, span {
    color: #c8ccd3;
}

/* TOP HEADER */

.veet-title {
    font-size: 32px;
    font-weight: 900;
    color: #fcd535 !important;
    letter-spacing: -1px;
}

.veet-subtitle {
    color: #848e9c !important;
    font-size: 12px;
}

/* CARDS */

.v-card {
    background: linear-gradient(145deg,#171b22,#0e1116);
    border: 1px solid #2b313a;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 10px;
}

.v-card:hover {
    border-color: #444b55;
}

.metric-label {
    color: #848e9c !important;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: .6px;
}

.metric-value {
    color: #ffffff !important;
    font-size: 23px;
    font-weight: 900;
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

/* LIVE */

.live-badge {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 20px;
    background: rgba(14,203,129,.12);
    border: 1px solid #0ecb81;
    color: #0ecb81 !important;
    font-size: 11px;
    font-weight: 900;
}

/* AI */

.ai-card {
    background:
        linear-gradient(145deg,#211b08,#0e0c07);
    border: 1px solid #fcd535;
    border-radius: 14px;
    padding: 20px;
    box-shadow: 0 0 25px rgba(252,213,53,.08);
}

.ai-title {
    color: #fcd535 !important;
    font-size: 22px;
    font-weight: 900;
}

.ai-buy {
    color: #0ecb81 !important;
    font-size: 28px;
    font-weight: 900;
}

.ai-sell {
    color: #f6465d !important;
    font-size: 28px;
    font-weight: 900;
}

.ai-hold {
    color: #fcd535 !important;
    font-size: 28px;
    font-weight: 900;
}

/* SIDEBAR */

[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#101318,#07090c);
    border-right: 1px solid #252a32;
}

/* BUTTONS */

.stButton > button {
    width: 100%;
    min-height: 42px;
    border-radius: 8px;
    border: 1px solid #343a44;
    font-weight: 800;
    background: linear-gradient(135deg,#fcd535,#f0b90b);
    color: #090b0e;
}

.stButton > button:hover {
    background: #ffffff !important;
    color: #000000 !important;
}

/* INPUT */

input, textarea {
    background-color: #0b0e11 !important;
    color: white !important;
}

[data-baseweb="select"] > div {
    background-color: #0b0e11 !important;
    color: white !important;
}

/* TABS */

.stTabs [data-baseweb="tab"] {
    font-weight: 700;
}

/* TABLE */

[data-testid="stDataFrame"] {
    border: 1px solid #2b313a;
    border-radius: 10px;
}

/* LOGIN */

.login-box {
    max-width: 520px;
    margin: 60px auto;
    background: linear-gradient(145deg,#171b22,#0b0e11);
    border: 1px solid #2b313a;
    border-top: 3px solid #fcd535;
    border-radius: 16px;
    padding: 35px;
    box-shadow: 0 20px 60px rgba(0,0,0,.7);
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
    return sqlite3.connect(DB_FILE, check_same_thread=False)


def hash_password(password):
    salt = secrets.token_hex(16)

    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        120000,
    ).hex()

    return f"{salt}${hashed}"


def verify_password(password, stored):
    if not stored:
        return False

    # Legacy plaintext compatibility
    if "$" not in stored:
        return secrets.compare_digest(password, stored)

    try:
        salt, expected = stored.split("$", 1)

        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            120000,
        ).hex()

        return secrets.compare_digest(actual, expected)

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
        CREATE TABLE IF NOT EXISTS demo_accounts (
            email TEXT PRIMARY KEY,
            balance REAL DEFAULT 100000,
            created_at TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS demo_positions (
            email TEXT,
            symbol TEXT,
            quantity REAL,
            avg_price REAL,
            PRIMARY KEY(email,symbol)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS demo_orders (
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
        CREATE TABLE IF NOT EXISTS watchlist (
            email TEXT,
            symbol TEXT,
            PRIMARY KEY(email,symbol)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            symbol TEXT,
            target REAL,
            direction TEXT,
            active INTEGER DEFAULT 1
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS promo_codes (
            code TEXT PRIMARY KEY,
            duration TEXT,
            active INTEGER DEFAULT 1,
            used_by TEXT
        )
        """
    )

    # Admin
    cur.execute(
        "SELECT email FROM users WHERE email=?",
        ("admin@gmail.com",),
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
                datetime.utcnow().isoformat(),
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
            "SELECT code FROM promo_codes WHERE code=?",
            (code,),
        )

        if not cur.fetchone():

            cur.execute(
                """
                INSERT INTO promo_codes
                (code,duration,active)
                VALUES(?,?,1)
                """,
                (code, duration),
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
        (email.strip().lower(),),
    )

    row = cur.fetchone()

    conn.close()

    return row


def register_user(email, password, name, username):

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
                email.strip().lower(),
                hash_password(password),
                name.strip(),
                username.strip(),
                "",
                "Free User",
                datetime.utcnow().isoformat(),
            ),
        )

        conn.commit()

        # Create demo account
        cur.execute(
            """
            INSERT OR IGNORE INTO demo_accounts
            (email,balance,created_at)
            VALUES(?,?,?)
            """,
            (
                email.strip().lower(),
                100000.0,
                datetime.utcnow().isoformat(),
            ),
        )

        conn.commit()
        conn.close()

        return True

    except sqlite3.IntegrityError:
        return False


def ensure_demo_account(email):

    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT OR IGNORE INTO demo_accounts
        (email,balance,created_at)
        VALUES(?,?,?)
        """,
        (
            email,
            100000.0,
            datetime.utcnow().isoformat(),
        ),
    )

    conn.commit()
    conn.close()


def update_profile(email, name, username, avatar):

    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE users
        SET name=?,username=?,avatar=?
        WHERE email=?
        """,
        (name, username, avatar, email),
    )

    conn.commit()
    conn.close()


# ============================================================
# 5. SESSION
# ============================================================

def initialize_session():

    defaults = {
        "authenticated": False,
        "email": "",
        "name": "",
        "username": "",
        "avatar": "",
        "tier": "Free User",
        "market": "Crypto",
        "symbol": "BTCUSDT",
        "timeframe": "15m",
        "trade_mode": "DEMO TRADE",
    }

    for key, value in defaults.items():

        if key not in st.session_state:
            st.session_state[key] = value


initialize_session()


# ============================================================
# 6. LOGIN SCREEN
# ============================================================

def login_screen():

    st.markdown(
        """
        <div class="login-box">

        <div style="text-align:center">

        <div style="
            font-size:30px;
            font-weight:900;
            color:#fcd535;
        ">
        ⚡ VEER PRO
        </div>

        <div style="
            color:#848e9c;
            font-size:12px;
            margin-bottom:25px;
        ">
        LIVE AI TRADING TERMINAL
        </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_login, tab_register = st.tabs(
        ["🔐 SIGN IN", "📝 CREATE ACCOUNT"]
    )

    with tab_login:

        with st.form("login_form"):

            email = st.text_input(
                "Email",
                placeholder="name@example.com",
            )

            password = st.text_input(
                "Password",
                type="password",
            )

            submit = st.form_submit_button(
                "ACCESS TERMINAL"
            )

            if submit:

                user = get_user(email)

                if user and verify_password(
                    password,
                    user[1],
                ):

                    st.session_state.authenticated = True
                    st.session_state.email = user[0]
                    st.session_state.name = user[2]
                    st.session_state.username = (
                        user[3] or "trader"
                    )
                    st.session_state.avatar = (
                        user[4] or ""
                    )
                    st.session_state.tier = (
                        user[5] or "Free User"
                    )

                    ensure_demo_account(user[0])

                    st.rerun()

                else:

                    st.error(
                        "Invalid email or password."
                    )

    with tab_register:

        with st.form("register_form"):

            name = st.text_input("Full Name")
            username = st.text_input("Username")
            email = st.text_input("Email")
            password = st.text_input(
                "Password",
                type="password",
            )

            submit = st.form_submit_button(
                "CREATE ACCOUNT"
            )

            if submit:

                if (
                    len(name.strip()) >= 2
                    and len(username.strip()) >= 2
                    and "@" in email
                    and len(password) >= 6
                ):

                    ok = register_user(
                        email,
                        password,
                        name,
                        username,
                    )

                    if ok:

                        st.session_state.authenticated = True
                        st.session_state.email = email.lower().strip()
                        st.session_state.name = name.strip()
                        st.session_state.username = username.strip()
                        st.session_state.tier = "Free User"

                        st.success(
                            "Account created."
                        )

                        st.rerun()

                    else:

                        st.error(
                            "Email already registered."
                        )

                else:

                    st.warning(
                        "Please enter valid details. Password must be at least 6 characters."
                    )

    st.markdown(
        """
        <div style="
            text-align:center;
            color:#5f6670;
            font-size:10px;
            margin-top:20px;
        ">
        Market data availability depends on connected live providers.
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


if not st.session_state.authenticated:
    login_screen()
    st.stop()


# ============================================================
# 7. LIVE MARKET CONFIG
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


TIMEFRAME_MAP = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1H": "1h",
    "4H": "4h",
    "1D": "1d",
}


# ============================================================
# 8. LIVE CRYPTO MARKET DATA
# ============================================================

@st.cache_data(ttl=5)
def fetch_live_crypto():

    try:

        url = "https://api.binance.com/api/v3/ticker/24hr"

        response = requests.get(
            url,
            timeout=8,
        )

        response.raise_for_status()

        data = response.json()

        result = {}

        wanted = set(CRYPTO_SYMBOLS)

        for item in data:

            symbol = item.get("symbol")

            if symbol in wanted:

                result[symbol] = {
                    "price": float(
                        item["lastPrice"]
                    ),
                    "change": float(
                        item["priceChangePercent"]
                    ),
                    "volume": float(
                        item["quoteVolume"]
                    ),
                    "high": float(
                        item["highPrice"]
                    ),
                    "low": float(
                        item["lowPrice"]
                    ),
                }

        return result

    except Exception:

        return {}


MARKETS = fetch_live_crypto()


# ============================================================
# 9. LIVE CHART DATA
# ============================================================

@st.cache_data(ttl=10)
def fetch_live_chart(symbol, interval):

    try:

        response = requests.get(
            "https://api.binance.com/api/v3/klines",
            params={
                "symbol": symbol,
                "interval": interval,
                "limit": 300,
            },
            timeout=8,
        )

        response.raise_for_status()

        rows = response.json()

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(
            rows,
            columns=[
                "time",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "close_time",
                "quote_volume",
                "trades",
                "buy_base",
                "buy_quote",
                "ignore",
            ],
        )

        numeric_columns = [
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]

        for col in numeric_columns:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce",
            )

        df["time"] = pd.to_datetime(
            df["time"],
            unit="ms",
        )

        return df[
            [
                "time",
                "open",
                "high",
                "low",
                "close",
                "volume",
            ]
        ].dropna()

    except Exception:

        return pd.DataFrame()


# ============================================================
# 10. TECHNICAL INDICATORS
# ============================================================

def add_indicators(df):

    df = df.copy()

    df["EMA20"] = (
        df["close"]
        .ewm(span=20, adjust=False)
        .mean()
    )

    df["EMA50"] = (
        df["close"]
        .ewm(span=50, adjust=False)
        .mean()
    )

    df["EMA200"] = (
        df["close"]
        .ewm(span=200, adjust=False)
        .mean()
    )

    delta = df["close"].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(
        alpha=1 / 14,
        adjust=False,
    ).mean()

    avg_loss = loss.ewm(
        alpha=1 / 14,
        adjust=False,
    ).mean()

    rs = avg_gain / avg_loss.replace(
        0,
        1e-10,
    )

    df["RSI"] = 100 - (
        100 / (1 + rs)
    )

    ema12 = (
        df["close"]
        .ewm(span=12, adjust=False)
        .mean()
    )

    ema26 = (
        df["close"]
        .ewm(span=26, adjust=False)
        .mean()
    )

    df["MACD"] = ema12 - ema26

    df["MACD_SIGNAL"] = (
        df["MACD"]
        .ewm(span=9, adjust=False)
        .mean()
    )

    middle = (
        df["close"]
        .rolling(20)
        .mean()
    )

    std = (
        df["close"]
        .rolling(20)
        .std()
    )

    df["BB_MIDDLE"] = middle
    df["BB_UPPER"] = middle + 2 * std
    df["BB_LOWER"] = middle - 2 * std

    previous_close = df["close"].shift(1)

    tr1 = df["high"] - df["low"]
    tr2 = (
        df["high"] - previous_close
    ).abs()
    tr3 = (
        df["low"] - previous_close
    ).abs()

    true_range = pd.concat(
        [tr1, tr2, tr3],
        axis=1,
    ).max(axis=1)

    df["ATR"] = (
        true_range
        .rolling(14)
        .mean()
    )

    df["VOL_MA20"] = (
        df["volume"]
        .rolling(20)
        .mean()
    )

    return df


# ============================================================
# 11. AI / ALGORITHMIC SIGNAL ENGINE
# ============================================================

def generate_ai_signal(df):

    if df.empty or len(df) < 60:

        return {
            "signal": "NO SIGNAL",
            "score": 0,
            "entry": None,
            "stop": None,
            "tp1": None,
            "tp2": None,
            "tp3": None,
            "rr": None,
            "reasons": [
                "Not enough verified live market data."
            ],
        }

    df = add_indicators(df)

    last = df.iloc[-1]

    price = float(last["close"])
    atr = float(last["ATR"])

    if pd.isna(atr) or atr <= 0:

        return {
            "signal": "NO SIGNAL",
            "score": 0,
            "entry": price,
            "stop": None,
            "tp1": None,
            "tp2": None,
            "tp3": None,
            "rr": None,
            "reasons": [
                "Volatility data is not ready."
            ],
        }

    score = 50
    reasons = []

    # Trend
    if last["EMA20"] > last["EMA50"]:
        score += 10
        reasons.append(
            "EMA20 is above EMA50."
        )
    else:
        score -= 10
        reasons.append(
            "EMA20 is below EMA50."
        )

    if last["close"] > last["EMA200"]:
        score += 10
        reasons.append(
            "Price is above EMA200."
        )
    else:
        score -= 10
        reasons.append(
            "Price is below EMA200."
        )

    # RSI
    rsi = float(last["RSI"])

    if 50 <= rsi <= 68:

        score += 8
        reasons.append(
            "RSI supports positive momentum."
        )

    elif 32 <= rsi < 50:

        score -= 5
        reasons.append(
            "RSI momentum is weak."
        )

    elif rsi > 70:

        score -= 8
        reasons.append(
            "RSI is overbought."
        )

    elif rsi < 30:

        score += 5
        reasons.append(
            "RSI is deeply oversold; reversal risk is elevated."
        )

    # MACD
    if last["MACD"] > last["MACD_SIGNAL"]:

        score += 10
        reasons.append(
            "MACD momentum is bullish."
        )

    else:

        score -= 10
        reasons.append(
            "MACD momentum is bearish."
        )

    # Volume
    if (
        not pd.isna(last["VOL_MA20"])
        and last["volume"] > last["VOL_MA20"]
    ):

        score += 7
        reasons.append(
            "Current volume is above its 20-period average."
        )

    # Bollinger
    if last["close"] > last["BB_MIDDLE"]:

        score += 5
        reasons.append(
            "Price is above Bollinger midline."
        )

    else:

        score -= 5
        reasons.append(
            "Price is below Bollinger midline."
        )

    score = max(
        0,
        min(
            100,
            int(score),
        ),
    )

    # Signal
    if score >= 75:
        signal = "BUY"

    elif score >= 62:
        signal = "BUY WATCH"

    elif score <= 25:
        signal = "SELL"

    elif score <= 38:
        signal = "SELL WATCH"

    else:
        signal = "HOLD"

    # Dynamic risk levels
    entry = price

    if "BUY" in signal:

        stop = entry - (1.5 * atr)

        risk = entry - stop

        tp1 = entry + risk * 1.5
        tp2 = entry + risk * 2.0
        tp3 = entry + risk * 3.0

    elif "SELL" in signal:

        stop = entry + (1.5 * atr)

        risk = stop - entry

        tp1 = entry - risk * 1.5
        tp2 = entry - risk * 2.0
        tp3 = entry - risk * 3.0

    else:

        stop = None
        tp1 = None
        tp2 = None
        tp3 = None

    return {
        "signal": signal,
        "score": score,
        "entry": entry,
        "stop": stop,
        "tp1": tp1,
        "tp2": tp2,
        "tp3": tp3,
        "rr": 1.5 if stop else None,
        "rsi": rsi,
        "atr": atr,
        "reasons": reasons,
    }


# ============================================================
# 12. DEMO ACCOUNT
# ============================================================

def get_demo_balance(email):

    ensure_demo_account(email)

    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT balance
        FROM demo_accounts
        WHERE email=?
        """,
        (email,),
    )

    row = cur.fetchone()

    conn.close()

    return float(row[0]) if row else 0.0


def get_demo_positions(email):

    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT symbol,quantity,avg_price
        FROM demo_positions
        WHERE email=? AND quantity>0
        """,
        (email,),
    )

    rows = cur.fetchall()

    conn.close()

    return rows


def execute_demo_trade(
    email,
    symbol,
    side,
    quantity,
    price,
):

    try:

        quantity = float(quantity)
        price = float(price)

        if quantity <= 0 or price <= 0:
            return False, "Invalid quantity or price."

        total = quantity * price

        conn = db()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT balance
            FROM demo_accounts
            WHERE email=?
            """,
            (email,),
        )

        balance_row = cur.fetchone()

        balance = (
            float(balance_row[0])
            if balance_row
            else 0.0
        )

        cur.execute(
            """
            SELECT quantity,avg_price
            FROM demo_positions
            WHERE email=? AND symbol=?
            """,
            (email, symbol),
        )

        position = cur.fetchone()

        current_qty = (
            float(position[0])
            if position
            else 0.0
        )

        current_avg = (
            float(position[1])
            if position
            else 0.0
        )

        if side == "BUY":

            if total > balance:

                conn.close()

                return (
                    False,
                    "Insufficient demo balance.",
                )

            new_qty = current_qty + quantity

            if new_qty <= 0:
                new_avg = 0
            else:
                new_avg = (
                    (
                        current_qty * current_avg
                        +
                        quantity * price
                    )
                    / new_qty
                )

            cur.execute(
                """
                INSERT INTO demo_positions
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

            new_balance = balance - total

        else:

            if quantity > current_qty:

                conn.close()

                return (
                    False,
                    "Not enough demo position to sell.",
                )

            new_qty = current_qty - quantity

            cur.execute(
                """
                UPDATE demo_positions
                SET quantity=?
                WHERE email=? AND symbol=?
                """,
                (
                    new_qty,
                    email,
                    symbol,
                ),
            )

            new_balance = balance + total

        cur.execute(
            """
            UPDATE demo_accounts
            SET balance=?
            WHERE email=?
            """,
            (
                new_balance,
                email,
            ),
        )

        cur.execute(
            """
            INSERT INTO demo_orders
            (
                email,
                symbol,
                side,
                order_type,
                price,
                quantity,
                total,
                status,
                created_at
            )
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
                datetime.utcnow().isoformat(),
            ),
        )

        conn.commit()
        conn.close()

        return (
            True,
            f"Demo {side} order executed.",
        )

    except Exception as e:

        return False, str(e)


def get_demo_orders(email):

    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            id,
            symbol,
            side,
            price,
            quantity,
            total,
            status,
            created_at
        FROM demo_orders
        WHERE email=?
        ORDER BY id DESC
        LIMIT 100
        """,
        (email,),
    )

    rows = cur.fetchall()

    conn.close()

    return rows


# ============================================================
# 13. WATCHLIST
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
        (email,),
    )

    rows = [
        x[0]
        for x in cur.fetchall()
    ]

    conn.close()

    return rows


def add_watchlist(email, symbol):

    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT OR IGNORE INTO watchlist
        (email,symbol)
        VALUES(?,?)
        """,
        (email, symbol),
    )

    conn.commit()
    conn.close()


def remove_watchlist(email, symbol):

    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        DELETE FROM watchlist
        WHERE email=? AND symbol=?
        """,
        (email, symbol),
    )

    conn.commit()
    conn.close()


# ============================================================
# 14. SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div class="veet-title">
        ⚡ VEER PRO
        </div>

        <div class="veet-subtitle">
        LIVE AI TRADING TERMINAL
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    st.markdown("### 👤 ACCOUNT")

    st.write(
        f"**{st.session_state.name}**"
    )

    st.caption(
        f"@{st.session_state.username}"
    )

    st.caption(
        st.session_state.tier
    )

    st.markdown("---")

    st.markdown("### 📊 MARKET")

    available_symbols = sorted(
        MARKETS.keys()
    )

    if not available_symbols:

        st.error(
            "Live market data unavailable."
        )

        st.stop()

    selected_symbol = st.selectbox(
        "Symbol",
        available_symbols,
        index=(
            available_symbols.index(
                st.session_state.symbol
            )
            if st.session_state.symbol
            in available_symbols
            else 0
        ),
    )

    st.session_state.symbol = selected_symbol

    timeframe = st.selectbox(
        "Timeframe",
        list(TIMEFRAME_MAP.keys()),
        index=(
            list(TIMEFRAME_MAP.keys()).index(
                st.session_state.timeframe
            )
            if st.session_state.timeframe
            in TIMEFRAME_MAP
            else 2
        ),
    )

    st.session_state.timeframe = timeframe

    st.markdown("---")

    st.markdown("### 🎯 TRADING MODE")

    mode = st.radio(
        "Execution",
        [
            "DEMO TRADE",
            "REAL MONEY LIVE",
        ],
        index=(
            0
            if st.session_state.trade_mode
            == "DEMO TRADE"
            else 1
        ),
    )

    st.session_state.trade_mode = mode

    if mode == "REAL MONEY LIVE":

        st.warning(
            "Broker connection required. Real orders are disabled until a verified broker API is connected."
        )

    else:

        st.success(
            "Demo mode uses live market prices with virtual funds."
        )

    st.markdown("---")

    st.markdown("### ⭐ WATCHLIST")

    watchlist = get_watchlist(
        st.session_state.email
    )

    if watchlist:

        for item in watchlist:

            if item in MARKETS:

                info = MARKETS[item]

                st.write(
                    f"**{item}**  "
                    f"${info['price']:,.6f}"
                )

    else:

        st.caption(
            "No symbols added yet."
        )

    st.markdown("---")

    if st.button("🚪 LOG OUT"):

        for key in [
            "authenticated",
            "email",
            "name",
            "username",
            "avatar",
            "tier",
        ]:

            if key in st.session_state:
                del st.session_state[key]

        st.rerun()


# ============================================================
# 15. MAIN HEADER
# ============================================================

info = MARKETS.get(
    st.session_state.symbol
)

if not info:

    st.error(
        "Verified live data unavailable for this symbol."
    )

    st.stop()


current_price = info["price"]
change = info["change"]


st.markdown(
    f"""
    <div style="
        display:flex;
        justify-content:space-between;
        align-items:center;
        margin-bottom:10px;
    ">

    <div>
        <div class="veet-title">
            {st.session_state.symbol}
        </div>

        <div class="veet-subtitle">
            Binance verified live market data
        </div>
    </div>

    <div>
        <span class="live-badge">
            ● LIVE MARKET
        </span>
    </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 16. PRICE HEADER
# ============================================================

c1, c2, c3, c4 = st.columns(4)

with c1:

    st.markdown(
        f"""
        <div class="v-card">
        <div class="metric-label">Live Price</div>
        <div class="metric-value">
        ${current_price:,.8f}
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c2:

    css = (
        "green"
        if change >= 0
        else "red"
    )

    st.markdown(
        f"""
        <div class="v-card">
        <div class="metric-label">24H Change</div>
        <div class="metric-value {css}">
        {change:+.2f}%
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c3:

    st.markdown(
        f"""
        <div class="v-card">
        <div class="metric-label">24H High</div>
        <div class="metric-value">
        ${info['high']:,.8f}
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c4:

    st.markdown(
        f"""
        <div class="v-card">
        <div class="metric-label">24H Low</div>
        <div class="metric-value">
        ${info['low']:,.8f}
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# 17. FETCH CHART
# ============================================================

chart_df = fetch_live_chart(
    st.session_state.symbol,
    TIMEFRAME_MAP[
        st.session_state.timeframe
    ],
)

if chart_df.empty:

    st.error(
        "Live chart data is currently unavailable. No synthetic chart is shown."
    )

    st.stop()


chart_df = add_indicators(
    chart_df
)


# ============================================================
# 18. AI SIGNAL
# ============================================================

signal = generate_ai_signal(
    chart_df
)


# ============================================================
# 19. CHART + ORDER PANEL
# ============================================================

left, right = st.columns(
    [3.3, 1.2]
)


with left:

    st.markdown(
        f"""
        <div class="v-card">
        <b>{st.session_state.symbol}</b>
        &nbsp;&nbsp;
        <span class="yellow">
        {st.session_state.timeframe}
        </span>
        &nbsp;&nbsp;
        <span class="live-badge">
        LIVE
        </span>
        </div>
        """,
        unsafe_allow_html=True,
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
            increasing_line_color="#0ecb81",
            decreasing_line_color="#f6465d",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=chart_df["time"],
            y=chart_df["EMA20"],
            name="EMA 20",
            line=dict(
                color="#fcd535",
                width=1,
            ),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=chart_df["time"],
            y=chart_df["EMA50"],
            name="EMA 50",
            line=dict(
                color="#4da3ff",
                width=1,
            ),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=chart_df["time"],
            y=chart_df["EMA200"],
            name="EMA 200",
            line=dict(
                color="#c77dff",
                width=1,
            ),
        )
    )

    fig.update_layout(
        height=600,
        template="plotly_dark",
        paper_bgcolor="#080a0d",
        plot_bgcolor="#080a0d",
        margin=dict(
            l=10,
            r=10,
            t=10,
            b=10,
        ),
        xaxis=dict(
            rangeslider=dict(
                visible=False
            ),
            showgrid=True,
            gridcolor="#1e2329",
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#1e2329",
            side="right",
        ),
        legend=dict(
            orientation="h",
            y=1.02,
            x=0,
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displaylogo": False,
            "scrollZoom": True,
            "responsive": True,
        },
    )


with right:

    st.markdown(
        """
        <div class="ai-card">

        <div class="ai-title">
        🧠 LIVE AI ANALYSIS
        </div>

        <div style="
            color:#848e9c;
            font-size:11px;
            margin-top:4px;
        ">
        Algorithmic multi-factor market analysis
        </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    sig = signal["signal"]

    if "BUY" in sig:

        sig_class = "ai-buy"

    elif "SELL" in sig:

        sig_class = "ai-sell"

    else:

        sig_class = "ai-hold"

    st.markdown(
        f"""
        <div class="v-card">

        <div class="{sig_class}">
        {sig}
        </div>

        <div class="metric-label">
        AI SCORE
        </div>

        <div class="metric-value">
        {signal['score']}%
        </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    if signal["entry"]:

        st.metric(
            "ENTRY",
            f"${signal['entry']:,.8f}",
        )

    if signal["stop"]:

        st.metric(
            "STOP LOSS",
            f"${signal['stop']:,.8f}",
        )

        st.metric(
            "TARGET 1",
            f"${signal['tp1']:,.8f}",
        )

        st.metric(
            "TARGET 2",
            f"${signal['tp2']:,.8f}",
        )

        st.metric(
            "TARGET 3",
            f"${signal['tp3']:,.8f}",
        )

    st.markdown(
        f"""
        <div class="v-card">

        <div class="metric-label">
        RSI
        </div>

        <div class="metric-value">
        {signal.get('rsi', 0):.2f}
        </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button(
        "⭐ ADD TO WATCHLIST"
    ):

        add_watchlist(
            st.session_state.email,
            st.session_state.symbol,
        )

        st.success(
            "Added to watchlist."
        )

        st.rerun()


# ============================================================
# 20. AI REASONS
# ============================================================

with st.expander(
    "🧠 WHY IS THE AI GIVING THIS SIGNAL?"
):

    for reason in signal["reasons"]:

        st.write(
            "✓",
            reason,
        )

    st.caption(
        "This is an algorithmic analysis, not a guarantee of future profit."
    )


# ============================================================
# 21. TRADING PANEL
# ============================================================

st.markdown("---")

st.markdown(
    "## ⚡ ORDER PANEL"
)

trade_col1, trade_col2, trade_col3 = st.columns(
    [1, 1, 2]
)


with trade_col1:

    st.markdown(
        f"""
        <div class="v-card">

        <div class="metric-label">
        MODE
        </div>

        <div class="metric-value">
        {st.session_state.trade_mode}
        </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


with trade_col2:

    if (
        st.session_state.trade_mode
        == "DEMO TRADE"
    ):

        balance = get_demo_balance(
            st.session_state.email
        )

        st.markdown(
            f"""
            <div class="v-card">

            <div class="metric-label">
            DEMO BALANCE
            </div>

            <div class="metric-value">
            ${balance:,.2f}
            </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

    else:

        st.markdown(
            """
            <div class="v-card">

            <div class="metric-label">
            REAL MONEY
            </div>

            <div class="metric-value red">
            BROKER NOT CONNECTED
            </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


with trade_col3:

    st.markdown(
        """
        <div class="v-card">

        <div class="metric-label">
        EXECUTION STATUS
        </div>

        <div class="metric-value">
        LIVE MARKET DATA
        </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# 22. ORDER FORM
# ============================================================

order_left, order_right = st.columns(
    [1, 1]
)


with order_left:

    side = st.radio(
        "Order Side",
        ["BUY", "SELL"],
        horizontal=True,
    )

    quantity = st.number_input(
        "Quantity",
        min_value=0.0,
        value=0.001,
        step=0.001,
        format="%.8f",
    )

    order_price = st.number_input(
        "Execution Price",
        min_value=0.0,
        value=float(current_price),
        format="%.8f",
    )


with order_right:

    st.markdown(
        f"""
        <div class="v-card">

        <div class="metric-label">
        ESTIMATED ORDER VALUE
        </div>

        <div class="metric-value">
        ${quantity * order_price:,.4f}
        </div>

        <div class="small-muted">
        Price source: verified live market
        </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    if (
        st.session_state.trade_mode
        == "DEMO TRADE"
    ):

        if st.button(
            f"⚡ EXECUTE DEMO {side}"
        ):

            ok, message = execute_demo_trade(
                st.session_state.email,
                st.session_state.symbol,
                side,
                quantity,
                order_price,
            )

            if ok:
                st.success(message)
            else:
                st.error(message)

    else:

        st.button(
            "🔒 REAL MONEY ORDER — BROKER REQUIRED",
            disabled=True,
        )

        st.info(
            "No real order is sent because a verified broker API is not connected."
        )


# ============================================================
# 23. POSITIONS / ORDERS
# ============================================================

st.markdown("---")

tab_positions, tab_orders, tab_account = st.tabs(
    [
        "📊 POSITIONS",
        "📋 ORDERS",
        "👤 ACCOUNT",
    ]
)


with tab_positions:

    if (
        st.session_state.trade_mode
        == "DEMO TRADE"
    ):

        positions = get_demo_positions(
            st.session_state.email
        )

        if positions:

            position_rows = []

            for symbol, qty, avg in positions:

                live = MARKETS.get(symbol)

                if live:

                    price = live["price"]

                    pnl = (
                        price - avg
                    ) * qty

                    position_rows.append(
                        {
                            "Symbol": symbol,
                            "Quantity": qty,
                            "Avg Price": avg,
                            "Live Price": price,
                            "P&L": pnl,
                        }
                    )

            if position_rows:

                st.dataframe(
                    pd.DataFrame(
                        position_rows
                    ),
                    use_container_width=True,
                    hide_index=True,
                )

        else:

            st.info(
                "No demo positions."
            )

    else:

        st.info(
            "Real positions will appear here after a verified broker connection is added."
        )


with tab_orders:

    if (
        st.session_state.trade_mode
        == "DEMO TRADE"
    ):

        orders = get_demo_orders(
            st.session_state.email
        )

        if orders:

            df_orders = pd.DataFrame(
                orders,
                columns=[
                    "ID",
                    "Symbol",
                    "Side",
                    "Price",
                    "Quantity",
                    "Total",
                    "Status",
                    "Created",
                ],
            )

            st.dataframe(
                df_orders,
                use_container_width=True,
                hide_index=True,
            )

        else:

            st.info(
                "No demo orders yet."
            )

    else:

        st.info(
            "Real broker orders will appear here after broker integration."
        )


# ============================================================
# 24. ACCOUNT
# ============================================================

with tab_account:

    st.markdown(
        f"""
        <div class="v-card">

        <h3>Account</h3>

        <b>Name:</b>
        {st.session_state.name}

        <br>

        <b>Username:</b>
        @{st.session_state.username}

        <br>

        <b>Email:</b>
        {st.session_state.email}

        <br>

        <b>Tier:</b>
        {st.session_state.tier}

        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander(
        "✏️ Edit Profile"
    ):

        with st.form(
            "profile_form"
        ):

            new_name = st.text_input(
                "Name",
                value=st.session_state.name,
            )

            new_username = st.text_input(
                "Username",
                value=st.session_state.username,
            )

            new_avatar = st.text_input(
                "Avatar URL",
                value=st.session_state.avatar,
            )

            save = st.form_submit_button(
                "SAVE PROFILE"
            )

            if save:

                update_profile(
                    st.session_state.email,
                    new_name,
                    new_username,
                    new_avatar,
                )

                st.session_state.name = new_name
                st.session_state.username = new_username
                st.session_state.avatar = new_avatar

                st.success(
                    "Profile updated."
                )

                st.rerun()


# ============================================================
# 25. MARKET DATA STATUS
# ============================================================

st.markdown("---")

st.markdown(
    """
    <div style="
        text-align:center;
        color:#606873;
        font-size:10px;
        padding:10px;
    ">
    ⚡ VEER PRO TERMINAL |
    LIVE MARKET DATA ONLY |
    No synthetic prices |
    No guaranteed-profit claims
    </div>
    """,
    unsafe_allow_html=True,
)
